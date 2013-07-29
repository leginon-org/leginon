#!/usr/bin/env python

import os
import wx
import sys
import time
import math
import numpy
import matplotlib
matplotlib.use('WXAgg')
#matplotlib.use('gtk')
from matplotlib import pyplot
from PIL import Image
#import subprocess
from appionlib import apParam
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apInstrument
from appionlib import apDatabase
from appionlib import appionLoop2
from appionlib.apImage import imagefile, imagefilter, imagenorm, imagestat
from appionlib.apCtf import ctftools, ctfnoise, ctfdb, sinefit, genctf, ctfpower, ctfres, ctfinsert
#Leginon
import leginon.polygon
from leginon.gui.wx import ImagePanel, ImagePanelTools, TargetPanel, TargetPanelTools
from pyami import mrc, fftfun, imagefun, ellipse, primefactor
from scipy import ndimage
import scipy.stats
from leginon.gui.wx.Entry import FloatEntry, IntEntry, EVT_ENTRY

##################################
##
##################################

class ManualCTFPanel(TargetPanel.TargetImagePanel):
	def __init__(self, parent, id, callback=None, tool=True):
		TargetPanel.TargetImagePanel.__init__(self, parent, id, callback=callback, tool=tool)

	#---------------------------------------
	def addTarget(self, name, x, y):
		### check for out of bounds particles
		if x < 2 or y < 2:
			return
		if x > self.imagedata.shape[1] or y > self.imagedata.shape[0]:
			return
		### continue as normal
		return self._getSelectionTool().addTarget(name, x, y)

	#---------------------------------------
	def openImageFile(self, filename):
		self.filename = filename
		print filename
		if filename is None:
			self.setImage(None)
		elif filename[-4:] == '.mrc':
			image = mrc.read(filename).astype(numpy.float64)
			self.setImage(image)
		else:
			img = Image.open(filename)
			img.load()
			image = imagefile.imageToArray(img).astype(numpy.float64)
			self.setImage(image)

	#--------------------
	def setImage(self, imagedata):
		if isinstance(imagedata, numpy.ndarray):
			self.numericdata = imagedata
			self.setNumericImage(imagedata)
		elif isinstance(imagedata, Image.Image):
			self.setPILImage(imagedata)
			stats = arraystats.all(imagedata)
			self.statspanel.set(stats)
			self.sizer.SetItemMinSize(self.statspanel, self.statspanel.GetSize())
			self.sizer.Layout()
		elif imagedata is None:
			self.clearImage()
			self.statspanel.set({})
			self.sizer.SetItemMinSize(self.statspanel, self.statspanel.GetSize())
			self.sizer.Layout()
		else:
			raise TypeError('Invalid image data type for setting image')

##################################
##
##################################

class ThonRingTool(ImagePanelTools.ImageTool):
	def __init__(self, app, panel, sizer):
		self.color = wx.Colour(255,231,00) #gold, ffd700
		self.penwidth = 2
		bitmap = leginon.gui.wx.TargetPanelBitmaps.getTargetIconBitmap(self.color, shape='o')
		tooltip = 'Show Thon Rings'
		cursor = None
		self.app = app
		ImagePanelTools.ImageTool.__init__(self, panel, sizer, bitmap, tooltip, cursor, False)

	#--------------------
	def Draw(self, dc):
		### check if button is depressed
		if not self.button.GetToggle():
			#print "Button is off"
			return
		### need CTF information
		if not self.app.ctfvalues or not 'defocus2' in self.app.ctfvalues.keys():
			#print "No CTF info"
			#print self.app.ctfvalues
			return
		dc.SetPen(wx.Pen(self.color, self.penwidth))
		width = self.imagepanel.bitmap.GetWidth()
		height = self.imagepanel.bitmap.GetHeight()

		if self.imagepanel.scaleImage():
			width /= self.imagepanel.scale[0]
			height /= self.imagepanel.scale[1]
		center = width/2, height/2
		#x, y = self.imagepanel.image2view(center)

		numzeros = 28
		#print "Getting valley locations"
		#print self.app.ctfvalues.keys()
		radii1 = ctftools.getCtfExtrema(self.app.ctfvalues['defocus1'], self.app.freq*1e10,
			self.app.ctfvalues['cs'], self.app.ctfvalues['volts'], self.app.ctfvalues['amplitude_contrast'],
			numzeros=numzeros, zerotype="valleys")
		radii2 = ctftools.getCtfExtrema(self.app.ctfvalues['defocus2'], self.app.freq*1e10,
			self.app.ctfvalues['cs'], self.app.ctfvalues['volts'], self.app.ctfvalues['amplitude_contrast'],
			numzeros=numzeros, zerotype="valleys")
		#print "rad1_0, rad2_0", radii1[0], radii2[0]
		s1 = 1.0/math.sqrt(radii1[0]*self.app.wavelength)
		s2 = 1.0/math.sqrt(radii2[0]*self.app.wavelength)
		#print "calc s1, s2", s1, s2

		foundzeros = min(len(radii1), len(radii2))
		for i in range(foundzeros):
			# because |def1| < |def2| ==> firstzero1 > firstzero2
			major = radii1[i]
			minor = radii2[i]
			if self.app.debug is True:
				print ("major=%.1f, minor=%.1f, angle=%.1f"
					%(major, minor, self.app.ctfvalues['angle_astigmatism']))
			if minor > width/1.95:
				# this limits how far we draw out the ellipses: sqrt(3) to corner, just 2 inside line
				break

			### determine number of points to use to draw ellipse, minimize distance btw points
			#isoceles triangle, b: radius ot CTF ring, a: distance btw points
			#a = 2 * b sin (theta/2)
			#a / 2b = sin(theta/2)
			#theta = 2 * asin (a/2b)
			#numpoints = 2 pi / theta
			## define a to be 5 pixels
			a = 5
			theta = 2.0 * math.asin (a/(2.0*major))
			skipfactor = 3
			## multiple by skipfactor to remove unsightly seam lines
			numpoints = int(math.ceil(2.0*math.pi/theta/skipfactor))*skipfactor + 1

			### for some reason, we need to give a negative angle here
			self.ellipangle = -math.radians(self.app.ctfvalues['angle_astigmatism'])
			points = ellipse.generate_ellipse(major, minor, self.ellipangle,
				center, numpoints, None, "step", True)
			x = points[:,0]
			y = points[:,1]

			## wrap around to end
			x = numpy.hstack((x, [x[0],]))
			y = numpy.hstack((y, [y[0],]))

			numsteps = int(math.floor((len(x)-2)/skipfactor))
			for j in range(numsteps):
				k = j*skipfactor
				xk, yk = self.imagepanel.image2view((x[k], y[k]))
				#if i == 0:
				#	print j, (x[k], y[k]), (xk, yk), center
				xk1, yk1 = self.imagepanel.image2view((x[k+1], y[k+1]))
				dc.DrawLine(xk, yk, xk1, yk1)
				#dc.DrawLine(x[k], y[k], x[k+1], y[k+1])

	#--------------------
	def OnToggle(self, value):
		self.imagepanel.UpdateDrawing()

##################################
##
##################################

class EditParamsDialog(wx.Dialog):
	#==================
	def __init__(self, parent):
		self.parent = parent
		wx.Dialog.__init__(self, self.parent.frame, -1, "Edit CTF Parameters")

		inforow = wx.FlexGridSizer(2, 2, 5, 5) #row, col
		entrywidth = 120

		label = wx.StaticText(self, -1, "Defocus 1: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.def1value = FloatEntry(self, -1, allownone=False, min=0, max=100e-6, chars=16, value="0")
		self.def1value.SetMinSize((entrywidth, -1))
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.def1value, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		label = wx.StaticText(self, -1, "Defocus 2: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.def2value = FloatEntry(self, -1, allownone=False, min=0, max=100e-6, chars=16, value="0")
		self.def2value.SetMinSize((entrywidth, -1))
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.def2value, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		label = wx.StaticText(self, -1, "Amp Contrast: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.ampconvalue = FloatEntry(self, -1, allownone=False, min=0, max=0.5, chars=16, value="0")
		self.ampconvalue.SetMinSize((entrywidth, -1))
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.ampconvalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		label = wx.StaticText(self, -1, "Angle: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.anglevalue = FloatEntry(self, -1, allownone=False, min=-90, max=180, chars=16, value="0")
		self.anglevalue.SetMinSize((entrywidth, -1))
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.anglevalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.cancel = wx.Button(self, wx.ID_CANCEL, '&Cancel')
		self.save = wx.Button(self, wx.ID_SAVE, '&Save')
		self.Bind(wx.EVT_BUTTON, self.onSave, self.save)
		buttonrow = wx.GridSizer(1,2)
		buttonrow.Add(self.cancel, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.save, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)

		self.sizer = wx.FlexGridSizer(2,1)
		self.sizer.Add(inforow, 0, wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(buttonrow, 0, wx.EXPAND|wx.ALL, 5)
		self.SetSizerAndFit(self.sizer)

	#==================
	def onSave(self, evt):
		self.Close()
		self.parent.ctfvalues['defocus1'] = self.def1value.GetValue()
		self.parent.ctfvalues['defocus2'] = self.def2value.GetValue()
		self.parent.ctfvalues['amplitude_contrast'] = self.ampconvalue.GetValue()
		self.parent.ctfvalues['angle_astigmatism'] = self.anglevalue.GetValue()
		self.parent.convertCtfToEllipse()

##################################
##
##################################

class EditMicroscopeDialog(wx.Dialog):
	#==================
	def __init__(self, parent):
		self.parent = parent
		wx.Dialog.__init__(self, self.parent.frame, -1, "Edit Microscope Parameters")

		inforow = wx.FlexGridSizer(2, 3, 5, 5) #row, col
		entrywidth = 120

		label = wx.StaticText(self, -1, "Cs: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.csvalue = FloatEntry(self, -1, allownone=False, min=0, max=100, chars=16, value="0")
		self.csvalue.SetMinSize((entrywidth, -1))
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.csvalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		label = wx.StaticText(self, -1, "mm", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, "Adj. apix: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.apixvalue = FloatEntry(self, -1, allownone=False, min=0, max=100, chars=16, value="0")
		self.apixvalue.SetMinSize((entrywidth, -1))
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.apixvalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		label = wx.StaticText(self, -1, "A", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, "high tension: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.kvoltsvalue = IntEntry(self, -1, allownone=False, min=0, max=1000, chars=16, value="0")
		self.kvoltsvalue.SetMinSize((entrywidth, -1))
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.kvoltsvalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		label = wx.StaticText(self, -1, "kV", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		self.cancel = wx.Button(self, wx.ID_CANCEL, '&Cancel')
		self.save = wx.Button(self, wx.ID_SAVE, '&Save')
		self.Bind(wx.EVT_BUTTON, self.onSave, self.save)
		buttonrow = wx.GridSizer(1,2)
		buttonrow.Add(self.cancel, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.save, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)

		self.sizer = wx.FlexGridSizer(2,1)
		self.sizer.Add(inforow, 0, wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(buttonrow, 0, wx.EXPAND|wx.ALL, 5)
		self.SetSizerAndFit(self.sizer)

	#==================
	def onSave(self, evt):
		self.Close()
		#changes for cs
		if self.parent.ctfvalues['cs'] != self.csvalue.GetValue()/1e3:
			apDisplay.printMsg("Change Cs value")
			self.parent.cs = self.csvalue.GetValue()/1e3
			self.parent.ctfvalues['cs'] = self.parent.cs

		#changes for volts
		if self.parent.ctfvalues['volts'] != self.kvoltsvalue.GetValue()*1e3:
			apDisplay.printMsg("Change kVolts value")
			self.parent.volts = self.kvoltsvalue.GetValue()*1e3
			self.parent.ctfvalues['volts'] = self.parent.volts
			self.parent.wavelength = ctftools.getTEMLambda(self.parent.volts)

		#changes for pixel size / freq
		if self.parent.ctfvalues['apix'] != self.apixvalue.GetValue():
			apDisplay.printMsg("Change apix value")
			oldapix = self.parent.ctfvalues['apix']
			oldfreq = self.parent.freq
			self.parent.apix = self.apixvalue.GetValue()
			self.parent.ctfvalues['apix'] = self.parent.apix
			#oldfreq = 1/(width*oldpixel); width = 1/(oldfreq*oldpixel)
			#newfreq = 1/(width*newpixel);
			#newfreq = oldfreq*oldpixel/newpixel
			self.parent.freq = oldfreq*oldapix/self.parent.apix

		# for good measure
		self.parent.convertCtfToEllipse()

##################################
##
##################################

class CTFApp(wx.App):
	def __init__(self, shape='+', size=16):
		self.shape = shape
		self.size = size
		self.ellipse_params = None
		self.ctfvalues = {
			'defocus1': 1e-6, 'defocus2': 1e-6,
			'volts': 120000, 'cs': 2e-3, 'angle_astigmatism': 45.0,
			'amplitude_contrast': 0.07, 'apix': 1.5, }
		self.ctfvalues = {}
		self.imagestatcache = {}
		self.imagestatcachefull = {}
		self.ellipratio = 1.0
		self.ellipangle = 0.0
		self.ringwidth = 2
		self.freq = None
		self.debug = False
		wx.App.__init__(self)

	#---------------------------------------
	def OnInit(self):
		self.deselectcolor = wx.Color(240,240,240)

		self.frame = wx.Frame(None, -1, 'Manual CTF')
		self.sizer = wx.FlexGridSizer(3,1)
		self.ctfrun = None
		buttonheight = 35

		### VITAL STATS
		self.vitalstats = wx.StaticText(self.frame, -1, "Vital Stats:  ", style=wx.ALIGN_LEFT)
		#self.vitalstats.SetMinSize((100, buttonheight))
		self.sizer.Add(self.vitalstats, 1, wx.EXPAND|wx.ALL, 3)

		### BEGIN IMAGE PANEL
		self.panel = ManualCTFPanel(self.frame, -1)
		self.panel.originaltargets = {}

		self.panel.addTool(ThonRingTool(self, self.panel, self.panel.toolsizer))

		self.panel.addTargetTool('First Valley', color=wx.Color(220,20,20),
			target=True, shape='x')
		self.panel.setTargets('First Valley', [])
		self.panel.selectiontool.setDisplayed('First Valley', True)
		self.panel.selectiontool.setTargeting('First Valley', True)

		self.panel.addTargetTool('First Valley Fit', color=wx.Color(251,236,93),
			target=False, shape='polygon')
		self.panel.setTargets('First Valley Fit', [])
		self.panel.selectiontool.setDisplayed('First Valley Fit', True)

		self.panel.SetMinSize((300,300))
		self.sizer.Add(self.panel, 1, wx.EXPAND)
		### END IMAGE PANEL

		### BEGIN BUTTONS ROW
		self.buttonrow = wx.FlexGridSizer(1,8)

		label = wx.StaticText(self.frame, -1, "Database:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, wx.ID_REVERT_TO_SAVED, 'Revert')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRevert, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.editparam_dialog = EditParamsDialog(self)
		wxbutton = wx.Button(self.frame, -1, '&Edit CTF Params...')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onEditParams, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.editscope_dialog = EditMicroscopeDialog(self)
		wxbutton = wx.Button(self.frame, -1, '&Edit Scope Params...')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onEditScope, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, wx.ID_OPEN, '&Load CTF')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onLoadCTF, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "Filters:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Gauss &blur')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onGaussBlur, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, '&Median filter')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onMedianFilter, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, '&Invert')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onInvert, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "First Valley fit:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.firstvalley = wx.Button(self.frame, -1, '&Fit Points')
		self.firstvalley.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onCalcFirstValley, self.firstvalley)
		self.buttonrow.Add(self.firstvalley, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, '&Water Shed')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onWaterShed, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, wx.ID_CLEAR, 'Clear')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onClear, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "Normalization:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, '&Full 1 Normalize')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onFullNormalize, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Full &TriModal Normalize')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onFullTriModalNormalize, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, '&Subt Fit Valleys')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onSubtFitValleys, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, '&Norm Fit Peaks')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onNormFitPeaks, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, '&Clip Data 0-1')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onClipData, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "Averaging:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.rotavg = wx.Button(self.frame, -1, '&Rot Avg')
		self.rotavg.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRotAverage, self.rotavg)
		self.buttonrow.Add(self.rotavg, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, '&Ellip Avg')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onEllipAverage, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, '*Ellip &Distort*')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onEllipDistort, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "View data:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Show 1D Plot')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onShowPlot, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Get Conf')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onGetConf, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Get Res')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onGetResolution, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)


		label = wx.StaticText(self.frame, -1, "Refinement:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, '&Amp Contrast')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onFitAmpContrast, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, '&Refine CTF')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRefineCTF, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Refine CTF with Cs')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRefineCTFwithCs, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Refine 1/2 CTF')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRefineHalfCTF, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)


		label = wx.StaticText(self.frame, -1, "Image Assessment:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.assessnone = wx.ToggleButton(self.frame, -1, "&None")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleNone, self.assessnone)
		self.assessnone.SetValue(0)
		#self.assessnone.SetBackgroundColour(self.selectcolor)
		self.assessnone.SetMinSize((-1, buttonheight))
		self.buttonrow.Add(self.assessnone, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.assesskeep = wx.ToggleButton(self.frame, -1, "&Keep")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleKeep, self.assesskeep)
		self.assesskeep.SetValue(0)
		self.assesskeep.SetMinSize((-1, buttonheight))
		self.buttonrow.Add(self.assesskeep, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.assessreject = wx.ToggleButton(self.frame, -1, "Re&ject")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleReject, self.assessreject)
		self.assessreject.SetValue(0)
		self.assessreject.SetMinSize((-1, buttonheight))
		self.buttonrow.Add(self.assessreject, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "Finish:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.next = wx.Button(self.frame, wx.ID_FORWARD, '&Forward')
		self.next.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onNext, self.next)
		self.buttonrow.Add(self.next, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		### END BUTTONS ROW
		self.sizer.Add(self.buttonrow, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
		self.sizer.AddGrowableRow(1)
		self.sizer.AddGrowableCol(0)
		self.frame.SetSizerAndFit(self.sizer)
		self.SetTopWindow(self.frame)
		self.frame.Show(True)
		return True

	#---------------------------------------
	def getOneDProfile(self, full=False):
		"""
		common function to convert 2D image into 1D profile

		pixelrdata, raddata, rotdata = self.getOneDProfile()
		"""
		t0 = time.time()
		imagedata = self.panel.numericdata
		if self.ellipse_params is None:
			self.ellipratio = 1.0
			self.ellipangle = 0.0
		else:
			self.ellipratio = self.ellipse_params['a']/self.ellipse_params['b']
			self.ellipangle = -math.degrees(self.ellipse_params['alpha'])

		statcache = {
			'mean': imagedata.mean(),
			'stdev': imagedata.std(),
			'shape': imagedata.shape,
			'ratio': self.ellipratio,
			'angle': self.ellipangle,
			'full': full,
		}

		### check to see if we can use cached value
		useCache = False
		if not full and self.imagestatcache:
			useCache = True
			for key in statcache:
				if not full and statcache[key] != self.imagestatcache[key]:
					#print key, statcache[key], self.imagestatcache[key]
					useCache = False
					break
		if full and self.imagestatcachefull:
			useCache = True
			for key in statcache:
				if full and statcache[key] != self.imagestatcachefull[key]:
					#print key, statcache[key], self.imagestatcachefull[key]
					useCache = False
					break

		### get the data
		if useCache is True:
			apDisplay.printMsg("using cache 1D profile data")
			if full is True:
				pixelrdata = self.pixelrdatacachefull
				rotdata = self.rotdatacachefull
			else:
				pixelrdata = self.pixelrdatacache
				rotdata = self.rotdatacache
		elif self.ellipse_params is None:
			apDisplay.printWarning("doing a rotational average not elliptical")
			pixelrdata, rotdata = ctftools.rotationalAverage(imagedata, self.ringwidth, full=full)
		else:
			pixelrdata, rotdata = ctftools.ellipticalAverage(imagedata,
				self.ellipratio, self.ellipangle, self.ringwidth, full=full)
		raddata = pixelrdata*self.freq

		### cache values for next time
		if full is True:
			self.pixelrdatacachefull = pixelrdata
			self.rotdatacachefull = rotdata
			self.imagestatcachefull = statcache
		else:
			self.pixelrdatacache = pixelrdata
			self.rotdatacache = rotdata
			self.imagestatcache = statcache

		### done
		apDisplay.printColor("Get 1D profile complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")

		return pixelrdata, raddata, rotdata

	#---------------------------------------
	def onEditParams(self, evt):
		if 'defocus1' in self.ctfvalues:
			self.editparam_dialog.def1value.SetValue(self.ctfvalues['defocus1'])
		if 'defocus2' in self.ctfvalues:
			self.editparam_dialog.def2value.SetValue(self.ctfvalues['defocus2'])
		if 'amplitude_contrast' in self.ctfvalues:
			self.editparam_dialog.ampconvalue.SetValue(self.ctfvalues['amplitude_contrast'])
		if 'angle_astigmatism' in self.ctfvalues:
			self.editparam_dialog.anglevalue.SetValue(self.ctfvalues['angle_astigmatism'])
		self.editparam_dialog.Show()
		apDisplay.printColor("Edit params complete", "cyan")

	#---------------------------------------
	def onEditScope(self, evt):
		if 'cs' in self.ctfvalues:
			self.editscope_dialog.csvalue.SetValue(self.ctfvalues['cs']*1e3)
		if 'apix' in self.ctfvalues:
			self.editscope_dialog.apixvalue.SetValue(self.ctfvalues['apix'])
		if 'volts' in self.ctfvalues:
			self.editscope_dialog.kvoltsvalue.SetValue(int(self.ctfvalues['volts']/1e3))
		self.editscope_dialog.Show()
		apDisplay.printColor("Edit microscope complete", "cyan")


	#---------------------------------------
	def onQuit(self, evt):
		wx.Exit()

	#---------------------------------------
	def onLoadCTF(self, evt):
		ctfdata, conf = ctfdb.getBestCtfValueForImage(self.imgdata)
		if ctfdata is None:
			dialog = wx.MessageDialog(self.frame, "No CTF values were found.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		self.ctfvalues['amplitude_contrast'] = ctfdata['amplitude_contrast']
		if abs(ctfdata['defocus1']) <= abs(ctfdata['defocus2']):
			### normal acceptable defocus
			self.ctfvalues['defocus1'] = abs(ctfdata['defocus1'])
			self.ctfvalues['defocus2'] = abs(ctfdata['defocus2'])
			self.ctfvalues['angle_astigmatism'] = ctfdata['angle_astigmatism']
		else:
			### flipped
			apDisplay.printWarning("flipped defocus values")
			self.ctfvalues['defocus2'] = abs(ctfdata['defocus1'])
			self.ctfvalues['defocus1'] = abs(ctfdata['defocus2'])
			self.ctfvalues['angle_astigmatism'] = ctfdata['angle_astigmatism'] + 90
		if self.ctfvalues['angle_astigmatism'] > 90:
			self.ctfvalues['angle_astigmatism'] -= 180

		self.convertCtfToEllipse()

		apDisplay.printColor("d1=%.3e\td2=%.3e\tratio=%.3f\tang=%.2f\tac=%.4f\tcf1=%.2f\tcf2=%.2f"%(
			self.ctfvalues['defocus1'], self.ctfvalues['defocus2'],
			self.ctfvalues['defocus2']/self.ctfvalues['defocus1'],
			self.ctfvalues['angle_astigmatism'], self.ctfvalues['amplitude_contrast'],
			ctfdata['confidence'], ctfdata['confidence_d']), "magenta")
		apDisplay.printColor("Load CTF complete", "cyan")

	#---------------------------------------
	def convertCtfToEllipse(self):
		if self.ctfvalues is None:
			return

		## set ellipse params
		if self.ellipse_params is None:
			self.ellipse_params = {}
		a = ctftools.getCtfExtrema(self.ctfvalues['defocus1'], self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=1, zerotype="valleys")
		self.ellipse_params['a'] = a[0]
		b = ctftools.getCtfExtrema(self.ctfvalues['defocus2'], self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=1, zerotype="valleys")
		self.ellipse_params['b'] = b[0]
		#angle_astigmatism = -math.degrees(self.ellipse_params['alpha'])
		self.ellipse_params['alpha'] = -math.radians(self.ctfvalues['angle_astigmatism'])

	#---------------------------------------
	def convertEllipseToCtf(self):
		if self.ellipse_params is None:
			return

		self.ellipratio = self.ellipse_params['a']/self.ellipse_params['b']
		self.ellipangle = -math.degrees(self.ellipse_params['alpha'])

		#print self.ellipse_params
		self.ctfvalues['amplitude_contrast'] = 0.0
		self.ctfvalues['angle_astigmatism'] = self.ellipangle
		#print "wavelength", self.wavelength

		#minor axis
		s = (self.ellipse_params['a']*self.freq)*1e10
		#print "s1", s
		self.ctfvalues['defocus1'] = (1.0/(self.wavelength * s**2)
			- 0.5*self.wavelength**2*self.ctfvalues['cs']*s**2)

		#major axis
		s = (self.ellipse_params['b']*self.freq)*1e10
		#print "s2", s
		self.ctfvalues['defocus2'] = (1.0/(self.wavelength * s**2)
			- 0.5*self.wavelength**2*self.ctfvalues['cs']*s**2)
		apDisplay.printColor("def1=%.3e\tdef2=%.3e\tratio=%.3f\tangle=%.2f\tampcont=%.4f"%(
			self.ctfvalues['defocus1'], self.ctfvalues['defocus2'],
			self.ctfvalues['defocus2']/self.ctfvalues['defocus1'],
			self.ctfvalues['angle_astigmatism'], self.ctfvalues['amplitude_contrast']), "magenta")

	#---------------------------------------
	def onCalcFirstValley(self, evt):
		center = numpy.array(self.panel.numericdata.shape)/2.0

		points = self.panel.getTargetPositions('First Valley')
		apDisplay.printMsg("You have %d points to fit in the valley ring"%(len(points)))
		if len(points) < 3:
			dialog = wx.MessageDialog(self.frame, "Need to pick more than 3 points first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		self.ellipse_params = ellipse.solveEllipseOLS(points, center)
		self.convertEllipseToCtf()
		epoints = ellipse.generate_ellipse(self.ellipse_params['a'],
			self.ellipse_params['b'], self.ellipse_params['alpha'], self.ellipse_params['center'],
			numpoints=30, noise=None, method="step", integers=True)
		self.panel.setTargets('First Valley Fit', epoints)
		apDisplay.printColor("def1=%.3e\tdef2=%.3e\tratio=%.3f\tangle=%.2f\tampcont=%.4f"%(
			self.ctfvalues['defocus1'], self.ctfvalues['defocus2'],
			self.ctfvalues['defocus2']/self.ctfvalues['defocus1'],
			self.ctfvalues['angle_astigmatism'], self.ctfvalues['amplitude_contrast']), "magenta")
		apDisplay.printColor("Calc first valley complete", "cyan")

	#---------------------------------------
	def onGaussBlur(self, evt):
		imagedata = self.panel.numericdata
		gaussdata = ndimage.gaussian_filter(imagedata, 2)
		self.panel.setImage(gaussdata)
		apDisplay.printColor("Gauss blur complete", "cyan")
		return

	#---------------------------------------
	def onMedianFilter(self, evt):
		imagedata = self.panel.numericdata
		meddata = ndimage.median_filter(imagedata, 2)
		meddata = ndimage.interpolation.shift(meddata, (-0.5,-0.5), order=1)
		self.panel.setImage(meddata)
		apDisplay.printColor("Median filter complete", "cyan")
		return


	#---------------------------------------
	def onInvert(self, evt):
		imagedata = self.panel.numericdata
		self.panel.setImage(-imagedata)
		apDisplay.printColor("Invert complete", "cyan")
		return

	#---------------------------------------
	def onWaterShed(self, evt):
		##requires 1 clicked point
		points = self.panel.getTargetPositions('First Valley')
		apDisplay.printMsg("You have %d points to fit in the valley ring"%(len(points)))
		if len(points) < 1:
			dialog = wx.MessageDialog(self.frame, "Need to pick a point first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		imagedata = self.panel.numericdata

		#16 is best for 2048
		fsize = int(imagedata.shape[0]/2048. * 8)
		#print "fsize=", fsize

		##prepare CTF data for watershed, only finds peaks so invert
		imagedata = ndimage.gaussian_filter(imagedata, fsize)
		inputarray = -imagedata + imagedata.max()

		##create markers using picked point
		center = numpy.array(imagedata.shape)/2.0
		newcenter = center.astype(numpy.uint16)
		#print "newcenter=", newcenter
		markers = numpy.zeros(inputarray.shape, dtype=numpy.int8)

		points = numpy.array(points, dtype=numpy.int16)
		#print points
		## set the ring points to the highest value processed last
		xp = numpy.array(points[:,1], dtype=numpy.uint16)
		yp = numpy.array(points[:,0], dtype=numpy.uint16)
		#print xp, yp
		markers[xp, yp] = 100

		## set inner points to 3
		markers[newcenter[1], newcenter[0]] = 30
		xpbad = numpy.array((points[:,1] - newcenter[1])*0.4 + newcenter[1], dtype=numpy.uint16)
		ypbad = numpy.array((points[:,0] - newcenter[0])*0.4 + newcenter[0], dtype=numpy.uint16)
		markers[xpbad, ypbad] = 30
		xpbad = numpy.array((points[:,1] - newcenter[1])*0.8 + newcenter[1], dtype=numpy.uint16)
		ypbad = numpy.array((points[:,0] - newcenter[0])*0.8 + newcenter[0], dtype=numpy.uint16)
		markers[xpbad, ypbad] = 30
		## set outer points to 2
		xpbad = numpy.array((points[:,1] - newcenter[1])*1.2 + newcenter[1], dtype=numpy.uint16)
		ypbad = numpy.array((points[:,0] - newcenter[0])*1.2 + newcenter[0], dtype=numpy.uint16)
		markers[xpbad, ypbad] = 20
		xpbad = numpy.array((points[:,1] - newcenter[1])*1.6 + newcenter[1], dtype=numpy.uint16)
		ypbad = numpy.array((points[:,0] - newcenter[0])*1.6 + newcenter[0], dtype=numpy.uint16)
		markers[xpbad, ypbad] = 20
		markers[0,0] = 20

		## do a blurring

		markers = ndimage.maximum_filter(markers, fsize)
		#print "markers="
		#imagestat.printImageInfo(markers)

		#rescale the input array
		xp, yp = numpy.where(markers==100)
		minmarker = inputarray[xp, yp].min()
		maxmarker = inputarray[xp, yp].max()
		markrange = maxmarker - minmarker
		#print "MARKER MIN/MAX: %.1f - %.1f"%(minmarker, maxmarker)
		#min/max should be within 5 pixels for method to work
		inputarray = 5.0/markrange * inputarray
		minmarker = inputarray[xp, yp].min()
		maxmarker = inputarray[xp, yp].max()
		#make sure it falls within range of 2^16 = 65536
		if maxmarker > 50000:
			inputarray -= maxmarker + 2**15
		if minmarker < 0:
			inputarray += minmarker + 2**15

		inputarray = numpy.array(inputarray, dtype=numpy.uint16)

		#print "inputarray="
		#imagestat.printImageInfo(inputarray)

		### perform watershed
		watershed = ndimage.measurements.watershed_ift(inputarray, markers)

		pyplot.clf()
		pyplot.subplot(1,2,1)
		pyplot.title("selected points as input")
		pyplot.xticks([], [])
		pyplot.yticks([], [])
		pyplot.imshow(markers)
		pyplot.gray()
		pyplot.imshow(inputarray, alpha=0.75)
		pyplot.gray()
		pyplot.imshow(markers, alpha=0.25)
		pyplot.gray()
		pyplot.subplot(1,2,2)
		pyplot.title("final watershed area")
		pyplot.xticks([], [])
		pyplot.yticks([], [])
		pyplot.imshow(watershed)
		pyplot.gray()
		pyplot.imshow(inputarray, alpha=0.75)
		pyplot.gray()
		pyplot.imshow(watershed, alpha=0.5)
		pyplot.gray()
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		#print "watershed="
		#imagestat.printImageInfo(watershed)
		#print watershed

		if watershed.mean() < 1:
			dialog = wx.MessageDialog(self.frame, "Watershed failed",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		xwater, ywater = numpy.where(watershed==100)

		points = numpy.transpose(numpy.vstack((xwater, ywater)))
		pointpercent = 100*len(points)/float(inputarray.shape[0]*inputarray.shape[1])
		apDisplay.printMsg("You have %d points to fit in the valley ring (%.2f percent)"
			%(len(points), pointpercent))
		# 8% of total pixels
		if pointpercent > 8:
			dialog = wx.MessageDialog(self.frame,
				"Too many points relative to size of the image (%.2f percent)"
				%(pointpercent), 'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		center = numpy.array(imagedata.shape)/2.0

		self.ellipse_params = ellipse.solveEllipseOLS(points, center)
		self.convertEllipseToCtf()
		epoints = ellipse.generate_ellipse(self.ellipse_params['a'],
			self.ellipse_params['b'], self.ellipse_params['alpha'], self.ellipse_params['center'],
			numpoints=30, noise=None, method="step", integers=True)
		self.panel.setTargets('First Valley Fit', epoints)
		apDisplay.printColor("def1=%.3e\tdef2=%.3e\tratio=%.3f\tangle=%.2f\tampcont=%.4f"%(
			self.ctfvalues['defocus1'], self.ctfvalues['defocus2'],
			self.ctfvalues['defocus2']/self.ctfvalues['defocus1'],
			self.ctfvalues['angle_astigmatism'], self.ctfvalues['amplitude_contrast']), "magenta")
		apDisplay.printColor("Water shed method complete", "cyan")

	#---------------------------------------
	def funcrad(self, r, rdata=None, zdata=None):
		return numpy.interp(r, rdata, zdata)

	#---------------------------------------
	def onRotAverage(self, evt):
		# do a rotational average of the image
		imagedata = self.panel.numericdata
		pixelrdata, rotdata = ctftools.rotationalAverage(imagedata, self.ringwidth, full=True)
		apDisplay.printWarning("doing a rotational average not elliptical")
		rotavgimage = imagefun.fromRadialFunction(self.funcrad, imagedata.shape,
			rdata=pixelrdata, zdata=rotdata)
		self.panel.setImage(rotavgimage)
		apDisplay.printColor("Rotational average complete", "cyan")

	#---------------------------------------
	def onEllipAverage(self, evt):
		# do an elliptical average of the image
		if self.ellipse_params is None:
			dialog = wx.MessageDialog(self.frame, "Need ellipse parameters first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		self.ellipratio = self.ellipse_params['a']/self.ellipse_params['b']
		self.ellipangle = -math.degrees(self.ellipse_params['alpha'])

		if abs(self.ellipratio - 1.0) < 1e-6:
			apDisplay.printWarning("Ellipse ratio is one, using rotational average, %.3f"
				%(self.ellipratio))
			self.onRotAverage(evt)
			return
		elif self.ellipratio < 1.0:
			apDisplay.printWarning("Ellipse ratio is less than one: %.3f"%(self.ellipratio))

		pixelrdata, raddata, rotdata = self.getOneDProfile(full=True)
		apDisplay.printColor("Elliptical average ratio = %.3f, angle %.3f"
			%(self.ellipratio,self.ellipangle), "cyan")

		imagedata = self.panel.numericdata
		ellipavgimage = ctftools.unEllipticalAverage(pixelrdata, rotdata,
			self.ellipratio, self.ellipangle, imagedata.shape)
		self.panel.setImage(ellipavgimage)
		apDisplay.printColor("Elliptical average complete", "cyan")

	#---------------------------------------
	def onEllipDistort(self, evt):
		# do an elliptical average of the image
		if self.ellipse_params is None:
			dialog = wx.MessageDialog(self.frame, "Need ellipse parameters first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		self.ellipratio = self.ellipse_params['a']/self.ellipse_params['b']
		self.ellipangle = -math.degrees(self.ellipse_params['alpha'])
		imagedata = self.panel.numericdata
		pixelrdata, rotdata = ctftools.ellipticalAverage(imagedata,
			self.ellipratio, self.ellipangle, self.ringwidth, full=True)
		#distort the pixelrdata
		distortrdata = pixelrdata**2/pixelrdata.max()
		ellipavgimage = ctftools.unEllipticalAverage(distortrdata, rotdata,
			self.ellipratio, self.ellipangle, imagedata.shape)
		self.panel.setImage(ellipavgimage)
		apDisplay.printColor("Elliptical distrotion complete", "cyan")

	#---------------------------------------
	def checkNormalized(self, msg=True):
		imagedata = self.panel.numericdata
		smallshape = numpy.array(imagedata.shape)/3
		centerimage = imagefilter.frame_cut(imagedata, smallshape)
		lowerbound = centerimage.mean() - 2*centerimage.std()
		if abs(centerimage.min()) > 1.0 and abs(lowerbound) > 1.0:
			if msg is True:
				dialog = wx.MessageDialog(self.frame, "You need to subtract the noise function.",
					'Error', wx.OK|wx.ICON_ERROR)
				dialog.ShowModal()
				dialog.Destroy()
				imagestat.printImageInfo(centerimage)
			return False
		upperbound = centerimage.mean() + 2*centerimage.std()
		if centerimage.max() > 2.0 and upperbound > 2.0:
			if msg is True:
				dialog = wx.MessageDialog(self.frame, "You need to normalize the envelop.",
					'Error', wx.OK|wx.ICON_ERROR)
				dialog.ShowModal()
				dialog.Destroy()
				imagestat.printImageInfo(centerimage)
			return False
		return True

	#---------------------------------------
	def onGetConf(self, env):
		if not 'defocus2' in self.ctfvalues.keys():
			dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		if self.checkNormalized() is False:
			return

		meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])

		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)

		peakradii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=100, zerotype="peaks")
		valleyradii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=100, zerotype="valleys")
		firstpeak = peakradii[0]
		firstpeakindex = numpy.searchsorted(raddata, firstpeak*self.freq)

		genctfdata = genctf.generateCTF1d(raddata*1e10, focus=meandefocus, cs=self.cs,
			volts=self.volts, ampconst=self.ctfvalues['amplitude_contrast'])

		confidence = scipy.stats.pearsonr(rotdata[firstpeakindex:], genctfdata[firstpeakindex:])[0]

		pyplot.clf()
		raddatasq = raddata**2
		for radius in peakradii:
			index = numpy.searchsorted(raddata, radius*self.freq)
			if index > raddata.shape[0] - 1:
				break
			pyplot.axvline(x=raddatasq[index], linewidth=1, color="cyan", alpha=0.95)
		for radius in valleyradii:
			index = numpy.searchsorted(raddata, radius*self.freq)
			if index > raddata.shape[0] - 1:
				break
			pyplot.axvline(x=raddatasq[index], linewidth=1, color="gold", alpha=0.95)
		pyplot.plot(raddatasq[firstpeakindex:], rotdata[firstpeakindex:], '.', color="gray")
		pyplot.plot(raddatasq[firstpeakindex:], rotdata[firstpeakindex:], 'k-',)
		pyplot.plot(raddatasq[firstpeakindex:], genctfdata[firstpeakindex:], 'r--',)
		pyplot.xlim(xmin=raddatasq[firstpeakindex-1], xmax=raddatasq.max())
		pyplot.ylim(ymin=-0.05, ymax=1.05)
		pyplot.title("Confidence value of %.4f"%(confidence))
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()
		apDisplay.printColor("Confidence value of %.4f complete"%(confidence), "cyan")

		return

	#---------------------------------------
	def onGetResolution(self, env):
		if not 'defocus2' in self.ctfvalues.keys():
			dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		if self.checkNormalized() is False:
			return

		### get the data
		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)
		meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])

		### get the confidence
		confraddata, confdata = ctfres.getCorrelationProfile(raddata, rotdata, meandefocus, self.freq, 
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'])

		res5 = ctfres.getResolutionFromConf(confraddata, confdata, limit=0.5)
		res8 = ctfres.getResolutionFromConf(confraddata, confdata, limit=0.8)

		genctfdata = genctf.generateCTF1d(raddata*1e10, focus=meandefocus, cs=self.cs,
			volts=self.volts, ampconst=self.ctfvalues['amplitude_contrast'])

		### Show the data
		raddatasq = raddata**2
		confraddatasq = confraddata**2
		peakradii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=2, zerotype="peaks")
		firstpeak = peakradii[0]
		fpi = numpy.searchsorted(raddata, peakradii[0]*self.freq) #firstpeakindex
		pyplot.clf()
		### raw powerspectra data
		pyplot.plot(raddatasq[fpi:], rotdata[fpi:], '-', color="red", alpha=0.5, linewidth=1)
		### ctf fit data
		pyplot.plot(raddatasq[fpi:], genctfdata[fpi:], '-', color="black", alpha=0.5, linewidth=1)
		### confidence profile
		pyplot.plot(confraddatasq, confdata, '.', color="blue", alpha=0.9, markersize=10)
		pyplot.plot(confraddatasq, confdata, '-', color="blue", alpha=0.9, linewidth=2)

		locs, labels = pyplot.xticks()
		newlocs = []
		newlabels = []
		for loc in locs:
			if loc < xmin:
				continue
			res = round(1.0/math.sqrt(loc),1)
			label = "1/%.1fA"%(res)
			newloc = 1.0/res**2
			newlocs.append(newloc)
			newlabels.append(label)
		pyplot.xticks(newlocs, newlabels)

		pyplot.axvline(x=1/res8**2, linewidth=2, color="gold")
		pyplot.axvline(x=1/res5**2, linewidth=2, color="red")

		pyplot.title("Resolution values of %.3fA at 0.8 and %.3fA at 0.5"%(res8,res5))
		pyplot.xlim(xmin=raddatasq[fpi-1], xmax=raddatasq.max())
		pyplot.ylim(ymin=-0.05, ymax=1.05)
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		apDisplay.printColor("Resolution values of %.4fA at 0.8 and %.4fA at 0.5"%(res8,res5), "cyan")

		return

	#---------------------------------------
	def onNeilNormalize(self, evt):
		self.onSubtBoxFilter(evt)
		self.onSubtTrimodalNoise(evt)
		self.onNormTrimodalEnvelop(evt)
		self.onSubtTrimodalNoise(evt)
		self.onNormTrimodalEnvelop(evt)
		apDisplay.printColor("Neil normalize complete", "cyan")

	#---------------------------------------
	def onFitAmpContrast(self, evt):
		if not 'defocus2' in self.ctfvalues.keys():
			dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		if self.checkNormalized() is False:
			return

		meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])

		# high pass filter the center
		#get first zero
		radii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=1, zerotype="peaks")
		firstpeak = radii[0]

		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)
		s = raddata*1e10

		#requires a defocus, use geometric mean it is the defocus of the elliptical average
		ws2 = s**2 * self.wavelength * math.pi * meandefocus
		amplitudecontrast = sinefit.refineAmplitudeContrast(ws2[firstpeak:],
			rotdata[firstpeak:], self.ctfvalues['amplitude_contrast'])
		if amplitudecontrast is None:
			dialog = wx.MessageDialog(self.frame, "Ampltiude constrast adjustment failed, bad fit.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		apDisplay.printColor("amplitude contrast change from %.4f to %.4f"
			%(self.ctfvalues['amplitude_contrast'], amplitudecontrast), "cyan")
		self.ctfvalues['amplitude_contrast'] = amplitudecontrast
		apDisplay.printColor("Fit amplitude contrast complete", "cyan")

	#---------------------------------------
	def onRefineCTF(self, evt):
		if not 'defocus2' in self.ctfvalues.keys():
			dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		if self.checkNormalized() is False:
			return

		meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])
		apDisplay.printMsg("Mean defocus is %.3e (from %.3e and %.3e)"
			%(meandefocus, self.ctfvalues['defocus1'], self.ctfvalues['defocus2']))

		# high pass filter the center
		#get first zero
		radii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=1, zerotype="peaks")
		firstpeak = radii[0]

		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)

		values = sinefit.refineCTF(raddata[firstpeak:], rotdata[firstpeak:], self.ctfvalues)

		if values is None:
			dialog = wx.MessageDialog(self.frame, "CTF refine failed, bad fit.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.Destroy()
			return
		newdefocus, amplitudecontrast = values

		if self.ellipratio < 1:
			apDisplay.printWarning("Ellipse ratio is less than 1")

		### elliptical ratio is preserved
		defocus1 = newdefocus / self.ellipratio
		defocus2 = newdefocus * self.ellipratio
		newdefocusratio = math.sqrt(defocus2/defocus1)
		olddefocusratio = math.sqrt(self.ctfvalues['defocus2']/self.ctfvalues['defocus1'])
		apDisplay.printColor("mean defocus change from %.5e to %.5e"
			%(meandefocus, newdefocus), "cyan")
		apDisplay.printColor("defocus 1 change from %.5e to %.5e"
			%(self.ctfvalues['defocus1'], defocus1), "cyan")
		apDisplay.printColor("defocus 2 change from %.5e to %.5e"
			%(self.ctfvalues['defocus2'], defocus2), "cyan")
		apDisplay.printColor("ellip ratio no change from %.5f to %.5f"
			%(olddefocusratio, newdefocusratio), "cyan")

		self.ctfvalues['defocus1'] = defocus1
		self.ctfvalues['defocus2'] = defocus2
		self.ctfvalues['amplitude_contrast'] = amplitudecontrast

		apDisplay.printColor("Refind CTF complete", "cyan")
		return

	#---------------------------------------
	def onRefineCTFwithCs(self, evt):
		if not 'defocus2' in self.ctfvalues.keys():
			dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		if self.checkNormalized() is False:
			return

		meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])
		apDisplay.printMsg("Mean defocus is %.3e (from %.3e and %.3e)"
			%(meandefocus, self.ctfvalues['defocus1'], self.ctfvalues['defocus2']))

		# high pass filter the center
		#get first zero
		radii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=1, zerotype="peaks")
		firstpeak = radii[0]

		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)

		values = sinefit.refineCTFwithCs(raddata[firstpeak:], rotdata[firstpeak:], self.ctfvalues)

		if values is None:
			dialog = wx.MessageDialog(self.frame, "CTF refine failed, bad fit.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.Destroy()
			return
		newdefocus, amplitudecontrast = values

		if self.ellipratio < 1:
			apDisplay.printWarning("Ellipse ratio is less than 1")

		### elliptical ratio is preserved
		defocus1 = newdefocus / self.ellipratio
		defocus2 = newdefocus * self.ellipratio
		newdefocusratio = math.sqrt(defocus2/defocus1)
		olddefocusratio = math.sqrt(self.ctfvalues['defocus2']/self.ctfvalues['defocus1'])
		apDisplay.printColor("mean defocus change from %.5e to %.5e"
			%(meandefocus, newdefocus), "cyan")
		apDisplay.printColor("defocus 1 change from %.5e to %.5e"
			%(self.ctfvalues['defocus1'], defocus1), "cyan")
		apDisplay.printColor("defocus 2 change from %.5e to %.5e"
			%(self.ctfvalues['defocus2'], defocus2), "cyan")
		apDisplay.printColor("ellip ratio no change from %.5f to %.5f"
			%(olddefocusratio, newdefocusratio), "cyan")

		self.ctfvalues['defocus1'] = defocus1
		self.ctfvalues['defocus2'] = defocus2
		self.ctfvalues['amplitude_contrast'] = amplitudecontrast

		apDisplay.printColor("Refind CTF with Cs complete", "cyan")
		return

	#---------------------------------------
	def onRefineHalfCTF(self, evt):
		if not 'defocus2' in self.ctfvalues.keys():
			dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		if self.checkNormalized() is False:
			return

		meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])

		# high pass filter the center
		#get first zero
		radii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=1, zerotype="peaks")
		firstpeak = radii[0]

		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)
		s = raddata*1e10

		#requires a defocus, use defocus2 it is the defocus of the elliptical average
		ws2 = s**2 * self.wavelength * math.pi
		ampcontrast = self.ctfvalues['amplitude_contrast']
		stopindex = (len(ws2)-firstpeak)/2 + firstpeak
		values = sinefit.refineCTF(ws2[firstpeak:stopindex],
			rotdata[firstpeak:stopindex], meandefocus, ampcontrast)
		if values is None:
			return

		newdefocus, amplitudecontrast = values
		apDisplay.printColor("amplitude contrast change from %.5f to %.5f"
			%(self.ctfvalues['amplitude_contrast'], amplitudecontrast), "cyan")
		self.ctfvalues['amplitude_contrast'] = amplitudecontrast

		if self.ellipratio < 1:
			apDisplay.printWarning("Ellipse ratio is less than 1")

		### elliptical ratio is preserved
		defocus1 = meandefocus / math.sqrt(self.ellipratio)
		defocus2 = meandefocus * math.sqrt(self.ellipratio)

		apDisplay.printColor("defocus 1 change from %.5e to %.5e"
			%(self.ctfvalues['defocus1'], defocus1), "cyan")
		apDisplay.printColor("defocus 2 change from %.5e to %.5e"
			%(self.ctfvalues['defocus2'], defocus2), "cyan")

		self.ctfvalues['defocus1'] = defocus1
		self.ctfvalues['defocus2'] = defocus2
		apDisplay.printColor("Refind 1/2 CTF 1d complete", "cyan")
		return

	#---------------------------------------
	def onSubtBoxFilter(self, evt):
		pixelrdata, raddata, rotdata = self.getOneDProfile(full=True)
		imagedata = self.panel.numericdata

		if rotdata.min() > 0:
			newrotdata = numpy.sqrt(rotdata)
			didsqrt = True
		else:
			didsqrt = False
			newrotdata = rotdata

		boxfilter = ndimage.uniform_filter1d(newrotdata, 256)

		pyplot.clf()
		xdata = (pixelrdata*self.freq)**2
		pyplot.plot(xdata, newrotdata, 'k.',)
		pyplot.plot(xdata, boxfilter, 'r-',)
		pyplot.xlim(xmax=xdata.max())
		pyplot.ylim(ymin=newrotdata.min(), ymax=newrotdata.max())
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		if didsqrt:
			boxfilter = boxfilter**2

		box2d = ctftools.unEllipticalAverage(pixelrdata, boxfilter,
			self.ellipratio, self.ellipangle, imagedata.shape)
		normaldata = imagedata - box2d

		self.panel.setImage(normaldata)

		imagestat.printImageInfo(normaldata)
		apDisplay.printColor("Subtract Box Filter complete", "cyan")

	#---------------------------------------
	def onSubt2dBoxFilter(self, evt):
		imagedata = self.panel.numericdata
		imagestat.printImageInfo(imagedata)

		boxfilter = ndimage.uniform_filter(imagedata, 256)

		pixelrdata, raddata, rotdata = self.getOneDProfile(full=True)
		imagestat.printImageInfo(rotdata)
		pixelrdata, boxdata = ctftools.ellipticalAverage(boxfilter,
			self.ellipratio, self.ellipangle, self.ringwidth, full=True)
		imagestat.printImageInfo(boxdata)

		pyplot.clf()
		pyplot.subplot(1,2,1)
		xdata = (raddata)**2
		pyplot.plot(xdata, rotdata, 'k-', alpha=0.75)
		pyplot.plot(xdata, boxdata, 'r-',)
		pyplot.xlim(xmax=xdata.max())
		pyplot.ylim(ymin=rotdata.min(), ymax=rotdata.max())
		pyplot.subplot(1,2,2)
		pyplot.imshow(boxfilter)
		pyplot.xticks([], [])
		pyplot.yticks([], [])
		pyplot.gray()
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		normaldata = imagedata - boxfilter

		self.panel.setImage(normaldata)

		imagestat.printImageInfo(normaldata)
		apDisplay.printColor("Subtract 2D Box Filter complete", "cyan")

	#---------------------------------------
	def onSubtGaussFilter(self, evt):
		pixelrdata, raddata, rotdata = self.getOneDProfile(full=True)

		if rotdata.min() > 0:
			newrotdata = numpy.sqrt(rotdata)
			didsqrt = True
		else:
			didsqrt = False
			newrotdata = rotdata

		gaussfilter = ndimage.gaussian_filter1d(newrotdata, 256)

		pyplot.clf()
		xdata = (pixelrdata*self.freq)**2
		pyplot.plot(xdata, newrotdata, 'k.',)
		pyplot.plot(xdata, gaussfilter, 'r-',)
		pyplot.xlim(xmax=xdata.max())
		pyplot.ylim(ymin=newrotdata.min(), ymax=newrotdata.max())
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		if didsqrt:
			gaussfilter = gaussfilter**2

		imagedata = self.panel.numericdata
		gauss2d = ctftools.unEllipticalAverage(pixelrdata, gaussfilter,
			self.ellipratio, self.ellipangle, imagedata.shape)
		normaldata = imagedata - gauss2d

		self.panel.setImage(normaldata)

		imagestat.printImageInfo(normaldata)
		apDisplay.printColor("Subtract Gauss Filter complete", "cyan")

	#---------------------------------------
	def onSubtNoise(self, evt):
		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)

		# high pass filter the center
		if 'defocus1' in self.ctfvalues.keys():
			#get first zero
			radii = ctftools.getCtfExtrema(self.ctfvalues['defocus1'], self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=1, zerotype="valleys")
			firstvalley = radii[0]
		else:
			#set first zero to 1/50A
			#1/resolution = freq * (# of pixels from center)
			firstvalley = int(1.0/(self.freq*50))
		raddata = pixelrdata*self.freq
		firstvalleyindex = numpy.searchsorted(raddata, self.freq*firstvalley)
		apDisplay.printColor("First valley: %.1f -> %d (1/%.1f A)"
			%(firstvalley, firstvalleyindex, 1/(firstvalley*self.freq)), "yellow")

		CtfNoise = ctfnoise.CtfNoise()
		noisefitparams = CtfNoise.modelCTFNoise(raddata[firstvalleyindex:],
			rotdata[firstvalleyindex:], "below")
		noisedata = CtfNoise.noiseModel(noisefitparams, raddata)

		pyplot.clf()
		raddatasq = raddata**2
		pyplot.plot(raddatasq, rotdata, 'k.',)
		pyplot.plot(raddatasq, rotdata, 'k-', alpha=0.5)
		pyplot.plot(raddatasq[firstvalleyindex:], noisedata[firstvalleyindex:], 'b-', )
		pyplot.xlim(xmax=raddatasq.max())
		pyplot.ylim(ymin=noisedata.min(), ymax=rotdata[firstvalleyindex:].max())
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		imagedata = self.panel.numericdata
		noise2d = ctftools.unEllipticalAverage(pixelrdata, noisedata,
			self.ellipratio, self.ellipangle, imagedata.shape)
		self.expdata = numpy.exp(imagedata) - numpy.exp(noise2d)
		normaldata = numpy.log(numpy.abs(self.expdata))
		#normaldata = numpy.where(normaldata < -0.2, -0.2, normaldata)
		self.panel.setImage(normaldata)

		imagestat.printImageInfo(normaldata)
		apDisplay.printColor("Subtract Noise complete", "cyan")

	#---------------------------------------
	def onClipData(self, evt):
		if self.checkNormalized() is False:
			return
		imagedata = self.panel.numericdata
		imagedata = numpy.where(imagedata > 2.0, 2.0, imagedata)
		imagedata = numpy.where(imagedata < -1.0, -1.0, imagedata)
		self.panel.setImage(imagedata)

	#---------------------------------------
	def onFullNormalize(self, evt):
		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)
		imagedata2d = self.panel.numericdata

		if self.checkNormalized(msg=False) is True:
			dialog = wx.MessageDialog(self.frame, "Full normalize only works on raw data.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			imagestat.printImageInfo(centerimage)
			return

		# skip the center
		if 'defocus1' in self.ctfvalues.keys():
			#get first zero
			radii = ctftools.getCtfExtrema(self.ctfvalues['defocus1'], self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=1, zerotype="valleys")
			firstvalley = radii[0]
		else:
			#set first zero to 1/70A
			#1/resolution = freq * (# of pixels from center)
			firstvalley = int(1.0/(self.freq*70))
		raddata = pixelrdata*self.freq
		firstvalleyindex = numpy.searchsorted(raddata, self.freq*firstvalley)
		apDisplay.printColor("First valley: %.1f -> %d (1/%.1f A)"
			%(firstvalley, firstvalleyindex, 1/(firstvalley*self.freq)), "yellow")

		CtfNoise = ctfnoise.CtfNoise()
		noisefitparams = CtfNoise.modelCTFNoise(raddata[firstvalleyindex:],
			rotdata[firstvalleyindex:], "below")
		noisedata = CtfNoise.noiseModel(noisefitparams, raddata)
		noisedata2d = ctftools.unEllipticalAverage(pixelrdata, noisedata,
			self.ellipratio, self.ellipangle, imagedata2d.shape)

		print "imagedata2d="
		imagestat.printImageInfo(imagedata2d)
		print "noisedata2d="
		imagestat.printImageInfo(noisedata2d)

		normexprotdata2d = numpy.exp(imagedata2d) - numpy.exp(noisedata2d)
		print "normexprotdata2d="
		imagestat.printImageInfo(normexprotdata2d)

		normlogrotdata2d = numpy.log(numpy.where(normexprotdata2d<1, 1, normexprotdata2d))
		#normlogrotdata2d = numpy.log(numpy.abs(normexprotdata2d))
		print "normlogrotdata2d="
		imagestat.printImageInfo(normlogrotdata2d)

		self.panel.setImage(normlogrotdata2d)

		newpixx, newx, normlogrotdata = self.getOneDProfile(full=False)
		print "normlogrotdata="
		imagestat.printImageInfo(normlogrotdata)

		# high pass filter the center
		if 'defocus1' in self.ctfvalues.keys():
			#get first zero
			meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])
			radii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=1, zerotype="peaks")
			firstpeak = radii[0]
		else:
			#set first zero to 1/50A
			#1/resolution = freq * (# of pixels from center)
			firstpeak = 1.0/(self.freq*50)

		firstpeakindex = numpy.searchsorted(raddata, firstpeak*self.freq)
		apDisplay.printColor("First peak: %.1f (1/%.1f A)"%
			(firstpeakindex, 1/(firstpeak*self.freq)), "yellow")

		CtfNoise = ctfnoise.CtfNoise()
		envelopfitparams = CtfNoise.modelCTFNoise(raddata[firstpeakindex:],
			normlogrotdata[firstpeakindex:], "above")
		envelopdata = CtfNoise.noiseModel(envelopfitparams, raddata)
		print "envelopdata="
		imagestat.printImageInfo(envelopdata)
		envelopdata2d = ctftools.unEllipticalAverage(pixelrdata, envelopdata,
			self.ellipratio, self.ellipangle, imagedata2d.shape)
		print "envelopdata2d="
		imagestat.printImageInfo(envelopdata2d)

		normnormexprotdata2d = normexprotdata2d / numpy.exp(envelopdata2d)
		print "normnormexprotdata2d="
		imagestat.printImageInfo(normnormexprotdata2d)
		#normnormlogrotdata2d = numpy.log(numpy.where(normnormexprotdata2d<0.1, 0.1, normnormexprotdata2d))
		#normnormlogrotdata2d = numpy.log(numpy.abs(normnormexprotdata2d))
		#print "normnormlogrotdata2d="
		#imagestat.printImageInfo(normnormexprotdata2d)

		self.panel.setImage(normnormexprotdata2d)

		newpixx, newx, normnormexprotdata = self.getOneDProfile(full=False)
		print "normnormexprotdata="
		imagestat.printImageInfo(normnormexprotdata)

		pyplot.clf()
		pyplot.subplot(3,1,1)
		raddatasq = raddata**2
		pyplot.plot(raddatasq, rotdata, 'k.',)
		pyplot.plot(raddatasq, rotdata, 'k-', alpha=0.5)
		pyplot.plot(raddatasq[firstvalleyindex:], noisedata[firstvalleyindex:], 'b-', )
		pyplot.xlim(xmax=raddatasq.max())
		pyplot.ylim(ymin=noisedata.min(), ymax=rotdata[firstvalleyindex:].max())

		pyplot.subplot(3,1,2)
		pyplot.plot(raddatasq, normlogrotdata, 'k.',)
		pyplot.plot(raddatasq, normlogrotdata, 'k-', alpha=0.5)
		pyplot.plot(raddatasq[firstpeakindex:], envelopdata[firstpeakindex:], 'r-', )
		pyplot.xlim(xmax=raddatasq.max())
		pyplot.ylim(ymin=normlogrotdata[firstpeakindex:].min(), ymax=envelopdata.max())

		pyplot.subplot(3,1,3)
		pyplot.plot(raddatasq, normnormexprotdata, 'k.',)
		pyplot.plot(raddatasq, normnormexprotdata, 'k-', alpha=0.5)
		pyplot.xlim(xmax=raddatasq.max())

		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		apDisplay.printColor("Full Normalize complete", "cyan")

	#---------------------------------------
	def onFullTriModalNormalize(self, evt):
		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)
		imagedata2d = self.panel.numericdata

		if self.checkNormalized(msg=False) is True:
			dialog = wx.MessageDialog(self.frame, "Full normalize only works on raw data.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			imagestat.printImageInfo(centerimage)
			return

		### 
		### PART 1: BACKGROUND NOISE SUBTRACTION
		### 

		# skip the center
		if 'defocus1' in self.ctfvalues.keys():
			#get first zero
			valleys = ctftools.getCtfExtrema(self.ctfvalues['defocus1'], self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=250, zerotype="valleys")
			firstvalley = valleys[0]
			valleyradii = numpy.array(valleys, dtype=numpy.float64)*self.freq
		else:
			#set first zero to 1/70A
			#1/resolution = freq * (# of pixels from center)
			firstvalley = int(1.0/(self.freq*70))
			valleyradii = None
		raddata = pixelrdata*self.freq
		firstvalleyindex = numpy.searchsorted(raddata, self.freq*firstvalley)
		apDisplay.printColor("First valley: %.1f -> %d (1/%.1f A)"
			%(firstvalley, firstvalleyindex, 1/(firstvalley*self.freq)), "yellow")

		### split the function up in first 3/5 and last 3/5 of data with 1/5 overlap
		numpoints = len(raddata) - firstvalleyindex
		part1start = firstvalleyindex
		part1end = int(firstvalleyindex + numpoints*6/10.)
		part2start = int(firstvalleyindex + numpoints*5/10.)
		part2end = int(firstvalleyindex + numpoints*9/10.)
		part3start = int(firstvalleyindex + numpoints*8/10.)
		part3end = len(raddata)

		CtfNoise = ctfnoise.CtfNoise()
		if valleyradii is None:
			valleydata = ctfnoise.peakExtender(raddata, rotdata, valleyradii, "below")
		else:
			valleydata = ndimage.minimum_filter(rotdata, 4)

		## first part data
		noisefitparams1 = CtfNoise.modelCTFNoise(raddata[part1start:part1end],
			valleydata[part1start:part1end], "below")
		noisedata1 = CtfNoise.noiseModel(noisefitparams1, raddata)

		## second part data
		noisefitparams2 = CtfNoise.modelCTFNoise(raddata[part2start:part2end],
			valleydata[part2start:part2end], "below")
		noisedata2 = CtfNoise.noiseModel(noisefitparams2, raddata)

		## third part data
		noisefitparams3 = CtfNoise.modelCTFNoise(raddata[part3start:part3end],
			valleydata[part3start:part3end], "below")
		noisedata3 = CtfNoise.noiseModel(noisefitparams3, raddata)

		## merge data
		scale = numpy.arange(part1end-part2start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata1 = noisedata1[part2start:part1end]*(1-scale) + noisedata2[part2start:part1end]*scale
		scale = numpy.arange(part2end-part3start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata2 = noisedata2[part3start:part2end]*(1-scale) + noisedata3[part3start:part2end]*scale

		mergedata = numpy.hstack((noisedata1[:part2start], overlapdata1,
			noisedata2[part1end:part3start], overlapdata2,
			noisedata3[part2end:]))

		noisedata = mergedata
		noisedata2d = ctftools.unEllipticalAverage(pixelrdata, noisedata,
			self.ellipratio, self.ellipangle, imagedata2d.shape)

		### DO THE SUBTRACTION
		normexprotdata2d = numpy.exp(imagedata2d) - numpy.exp(noisedata2d)
		normlogrotdata2d = numpy.log(numpy.where(normexprotdata2d<1, 1, normexprotdata2d))

		self.panel.setImage(normlogrotdata2d)
		newpixx, newx, normlogrotdata = self.getOneDProfile(full=False)

		### 
		### PART 2: ENVELOPE NORMALIZATION
		### 

		# high pass filter the center
		if 'defocus1' in self.ctfvalues.keys():
			#get first zero
			meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])
			peaks = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=250, zerotype="peaks")
			firstpeak = peaks[0]
			peakradii = numpy.array(peaks, dtype=numpy.float64)*self.freq
		else:
			#set first zero to 1/50A
			#1/resolution = freq * (# of pixels from center)
			firstpeak = 1.0/(self.freq*50)
			peakradii = None

		firstpeakindex = numpy.searchsorted(raddata, firstpeak*self.freq)
		apDisplay.printColor("First peak: %.1f (1/%.1f A)"%
			(firstpeakindex, 1/(firstpeak*self.freq)), "yellow")

		### split the function up in first 3/5 and last 3/5 of data with 1/5 overlap
		numpoints = len(raddata) - firstpeakindex
		part1start = firstpeakindex
		part1end = int(firstpeakindex + numpoints*6/10.)
		part2start = int(firstpeakindex + numpoints*5/10.)
		part2end = int(firstpeakindex + numpoints*9/10.)
		part3start = int(firstpeakindex + numpoints*8/10.)
		part3end = len(raddata)

		CtfNoise = ctfnoise.CtfNoise()
		if peakradii is None:
			peakdata = ctfnoise.peakExtender(raddata, normlogrotdata, peakradii, "above")
		else:
			peakdata = ndimage.maximum_filter(normlogrotdata, 4)

		## first part data
		envelopfitparams1 = CtfNoise.modelCTFNoise(raddata[part1start:part1end],
			peakdata[part1start:part1end], "above")
		envelopdata1 = CtfNoise.noiseModel(envelopfitparams1, raddata)

		## second part data
		envelopfitparams2 = CtfNoise.modelCTFNoise(raddata[part2start:part2end],
			peakdata[part2start:part2end], "above")
		envelopdata2 = CtfNoise.noiseModel(envelopfitparams2, raddata)

		## third part data
		envelopfitparams3 = CtfNoise.modelCTFNoise(raddata[part3start:part3end],
			peakdata[part3start:part3end], "above")
		envelopdata3 = CtfNoise.noiseModel(envelopfitparams3, raddata)

		## merge data
		scale = numpy.arange(part1end-part2start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata1 = envelopdata1[part2start:part1end]*(1-scale) + envelopdata2[part2start:part1end]*scale
		scale = numpy.arange(part2end-part3start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata2 = envelopdata2[part3start:part2end]*(1-scale) + envelopdata3[part3start:part2end]*scale

		mergedata = numpy.hstack((envelopdata1[:part2start], overlapdata1,
			envelopdata2[part1end:part3start], overlapdata2,
			envelopdata3[part2end:]))
		envelopdata = mergedata

		envelopdata2d = ctftools.unEllipticalAverage(pixelrdata, envelopdata,
			self.ellipratio, self.ellipangle, imagedata2d.shape)
		normnormexprotdata2d = normexprotdata2d / numpy.exp(envelopdata2d)

		self.panel.setImage(normnormexprotdata2d)
		newpixx, newx, normnormexprotdata = self.getOneDProfile(full=False)

		pyplot.clf()
		pyplot.subplot(3,1,1)
		raddatasq = raddata**2
		pyplot.plot(raddatasq, normnormexprotdata, 'k.',)
		a = pyplot.plot(raddatasq, rotdata, 'k-', alpha=0.5)
		a = pyplot.plot(raddatasq, valleydata, 'k-', alpha=0.5)
		b = pyplot.plot(raddatasq[firstvalleyindex:], noisedata[firstvalleyindex:], '--', color="purple", linewidth=2)
		c = pyplot.plot(raddatasq[part1start:part1end],
			noisedata1[part1start:part1end], 'b-', alpha=0.5, linewidth=2)
		d = pyplot.plot(raddatasq[part2start:part2end],
			noisedata2[part2start:part2end], 'r-', alpha=0.5, linewidth=2)
		e = pyplot.plot(raddatasq[part3start:part3end],
			noisedata3[part3start:part3end], '-', alpha=0.5, linewidth=2, color="green")
		pyplot.legend([a, b, c, d, e], ["data", "merge", "part 1", "part 2", "part 3"])
		pyplot.xlim(xmax=raddatasq.max())
		pyplot.ylim(ymin=noisedata.min(), ymax=rotdata[part1start:].max())

		pyplot.subplot(3,1,2)
		a = pyplot.plot(raddatasq, normlogrotdata, 'k.',)
		a = pyplot.plot(raddatasq, normlogrotdata, 'k-', alpha=0.5)
		a = pyplot.plot(raddatasq, peakdata, 'k-', alpha=0.5)
		b = pyplot.plot(raddatasq, mergedata, '--', color="purple", linewidth=2)
		c = pyplot.plot(raddatasq[part1start:part1end],
			envelopdata1[part1start:part1end], 'b-', alpha=0.5, linewidth=2)
		d = pyplot.plot(raddatasq[part2start:part2end],
			envelopdata2[part2start:part2end], 'r-', alpha=0.5, linewidth=2)
		e = pyplot.plot(raddatasq[part3start:part3end],
			envelopdata3[part3start:part3end], '-', alpha=0.5, linewidth=2, color="green")
		pyplot.legend([a, b, c, d, e], ["data", "merge", "part 1", "part 2", "part 3"])
		pyplot.xlim(xmax=raddatasq.max())
		pyplot.ylim(ymin=normlogrotdata[part1start:].min(), ymax=envelopdata.max())

		pyplot.subplot(3,1,3)
		pyplot.plot(raddatasq, normnormexprotdata, 'k.',)
		pyplot.plot(raddatasq, normnormexprotdata, 'k-', alpha=0.5)
		pyplot.xlim(xmax=raddatasq.max())

		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		apDisplay.printColor("Full Normalize complete", "cyan")

	#---------------------------------------
	def onSubtTrimodalNoise(self, evt):
		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)

		# high pass filter the center
		if 'defocus1' in self.ctfvalues.keys():
			#get first zero
			radii = ctftools.getCtfExtrema(self.ctfvalues['defocus1'], self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=1, zerotype="valleys")
			firstvalley = radii[0]
		else:
			#set first zero to 1/50A
			#1/resolution = freq * (# of pixels from center)
			firstvalley = int(1.0/(self.freq*50))
		raddata = pixelrdata*self.freq
		firstvalleyindex = numpy.searchsorted(raddata, self.freq*firstvalley)
		apDisplay.printColor("First valley: %.1f -> %d (1/%.1f A)"
			%(firstvalley, firstvalleyindex, 1/(firstvalley*self.freq)), "yellow")

		### split the function up in first 3/5 and last 3/5 of data with 1/5 overlap
		numpoints = len(raddata) - firstvalleyindex
		part1start = firstvalleyindex
		part1end = int(firstvalleyindex + numpoints*6/10.)
		part2start = int(firstvalleyindex + numpoints*5/10.)
		part2end = int(firstvalleyindex + numpoints*9/10.)
		part3start = int(firstvalleyindex + numpoints*8/10.)
		part3end = len(raddata)

		CtfNoise = ctfnoise.CtfNoise()

		## first part data
		noisefitparams1 = CtfNoise.modelCTFNoise(raddata[part1start:part1end],
			rotdata[part1start:part1end], "below")
		noisedata1 = CtfNoise.noiseModel(noisefitparams1, raddata)

		## second part data
		noisefitparams2 = CtfNoise.modelCTFNoise(raddata[part2start:part2end],
			rotdata[part2start:part2end], "below")
		noisedata2 = CtfNoise.noiseModel(noisefitparams2, raddata)

		## third part data
		noisefitparams3 = CtfNoise.modelCTFNoise(raddata[part3start:part3end],
			rotdata[part3start:part3end], "below")
		noisedata3 = CtfNoise.noiseModel(noisefitparams3, raddata)

		## merge data
		scale = numpy.arange(part1end-part2start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata1 = noisedata1[part2start:part1end]*(1-scale) + noisedata2[part2start:part1end]*scale
		scale = numpy.arange(part2end-part3start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata2 = noisedata2[part3start:part2end]*(1-scale) + noisedata3[part3start:part2end]*scale

		mergedata = numpy.hstack((noisedata1[:part2start], overlapdata1,
			noisedata2[part1end:part3start], overlapdata2,
			noisedata3[part2end:]))

		pyplot.clf()
		a = pyplot.plot(raddata**2, rotdata, 'k.',)
		b = pyplot.plot(raddata**2, mergedata, '--', color="purple", linewidth=2)
		c = pyplot.plot(raddata[part1start:part1end]**2,
			noisedata1[part1start:part1end], 'b-', alpha=0.5, linewidth=2)
		d = pyplot.plot(raddata[part2start:part2end]**2,
			noisedata2[part2start:part2end], 'r-', alpha=0.5, linewidth=2)
		e = pyplot.plot(raddata[part3start:part3end]**2,
			noisedata3[part3start:part3end], '-', alpha=0.5, linewidth=2, color="green")
		pyplot.legend([a, b, c, d, e], ["data", "merge", "part 1", "part 2", "part 3"])
		pyplot.xlim(xmax=(raddata**2).max())
		pyplot.ylim(ymin=mergedata[firstvalleyindex:].min(), ymax=rotdata[firstvalleyindex-1:].max())
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		imagedata = self.panel.numericdata
		noise2d = ctftools.unEllipticalAverage(pixelrdata, mergedata,
			self.ellipratio, self.ellipangle, imagedata.shape)
		normaldata = imagedata - noise2d
		#normaldata = numpy.where(normaldata < -0.2, -0.2, normaldata)
		self.panel.setImage(normaldata)

		#imagestat.printImageInfo(normaldata)
		apDisplay.printColor("Subtract Trimodal Noise complete", "cyan")

	#---------------------------------------
	def onSubtFitValleys(self, evt):
		meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])

		valleyradii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=250, zerotype="valleys")
		extrema = numpy.array(valleyradii, dtype=numpy.float64)*self.freq

		pixelrdata, raddata, rotdata = self.getOneDProfile(full=True)
		extremedata = ctfnoise.peakExtender(raddata, rotdata, extrema, "below")
		extremedata = ndimage.gaussian_filter1d(extremedata, 1)

		imagedata = self.panel.numericdata
		extreme2d = ctftools.unEllipticalAverage(pixelrdata, extremedata,
			self.ellipratio, self.ellipangle, imagedata.shape)

		pyplot.clf()
		raddatasq = raddata**2
		maxshow = int(raddatasq.shape[0]/math.sqrt(2))
		pyplot.plot(raddatasq[:maxshow], rotdata[:maxshow], 'k-', )
		pyplot.plot(raddatasq[:maxshow], rotdata[:maxshow], 'k.', )
		pyplot.plot(raddatasq[:maxshow], extremedata[:maxshow], 'b-', )
		for radius in valleyradii:
			index = numpy.searchsorted(raddata, radius*self.freq)
			if index > maxshow:
				break
			pyplot.axvline(x=raddatasq[index], linewidth=1, color="cyan", alpha=0.95)
		pyplot.xlim(xmin=raddatasq[0], xmax=raddatasq[maxshow])
		pyplot.ylim(ymin=-0.05, ymax=1.05)
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		normaldata = imagedata - extreme2d
		#normaldata = numpy.where(normaldata < -0.2, -0.2, normaldata)
		self.panel.setImage(normaldata)
		apDisplay.printColor("Subtract Fit Valleys complete", "cyan")

	#---------------------------------------
	def onNormFitPeaks(self, evt):
		meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])

		peakradii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=250, zerotype="peaks")
		extrema = numpy.array(peakradii, dtype=numpy.float64)*self.freq

		pixelrdata, raddata, rotdata = self.getOneDProfile(full=True)
		extremedata = ctfnoise.peakExtender(raddata, rotdata, extrema, "above")
		extremedata = ndimage.gaussian_filter1d(extremedata, 1)

		imagedata = self.panel.numericdata
		extreme2d = ctftools.unEllipticalAverage(pixelrdata, extremedata,
			self.ellipratio, self.ellipangle, imagedata.shape)

		pyplot.clf()
		raddatasq = raddata**2
		maxshow = int(raddatasq.shape[0]/math.sqrt(2))
		pyplot.plot(raddatasq[:maxshow], rotdata[:maxshow], 'k-', )
		pyplot.plot(raddatasq[:maxshow], rotdata[:maxshow], 'k.', )
		pyplot.plot(raddatasq[:maxshow], extremedata[:maxshow], 'b-', )
		for radius in peakradii:
			index = numpy.searchsorted(raddata, radius*self.freq)
			if index > maxshow:
				break
			pyplot.axvline(x=raddatasq[index], linewidth=1, color="gold", alpha=0.95)
		pyplot.xlim(xmin=raddatasq[0], xmax=raddatasq[maxshow])
		pyplot.ylim(ymin=-0.05, ymax=1.05)
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		normaldata = imagedata / extreme2d
		#normaldata = numpy.where(normaldata > 1.2, 1.2, normaldata)
		#normaldata = numpy.where(normaldata < -0.2, -0.2, normaldata)
		self.panel.setImage(normaldata)
		apDisplay.printColor("Subtract Fit Valleys complete", "cyan")

	#---------------------------------------
	def onNormEnvelop(self, evt):
		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)

		# high pass filter the center
		if 'defocus1' in self.ctfvalues.keys():
			#get first zero
			meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])
			radii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=1, zerotype="peaks")
			firstpeak = radii[0]
		else:
			#set first zero to 1/50A
			#1/resolution = freq * (# of pixels from center)
			firstpeak = 1.0/(self.freq*50)
		raddata = pixelrdata*self.freq
		firstpeakindex = numpy.searchsorted(raddata, firstpeak*self.freq)
		apDisplay.printColor("First peak: %.1f (1/%.1f A)"%
			(firstpeakindex, 1/(firstpeak*self.freq)), "yellow")

		CtfNoise = ctfnoise.CtfNoise()
		envelopfitparams = CtfNoise.modelCTFNoise(raddata[firstpeakindex:],
			rotdata[firstpeakindex:], "above")
		envelopdata = CtfNoise.noiseModel(envelopfitparams, raddata)

		pyplot.clf()
		pyplot.plot(raddata**2, rotdata, 'k.',)
		pyplot.plot(raddata[firstpeakindex:]**2, envelopdata[firstpeakindex:], 'r-', )
		pyplot.xlim(xmax=(raddata**2).max())
		pyplot.ylim(ymin=rotdata.min(), ymax=envelopdata.max())
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		imagedata = self.panel.numericdata
		envelop2d = ctftools.unEllipticalAverage(pixelrdata, envelopdata,
			self.ellipratio, self.ellipangle, imagedata.shape)
		self.expdata = self.expdata / numpy.exp(envelop2d)
		normaldata = numpy.log(numpy.abs(self.expdata))

		self.panel.setImage(normaldata)
		apDisplay.printColor("Normalize envelope complete", "cyan")

	#---------------------------------------
	def onNormTrimodalEnvelop(self, evt):
		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)

		# high pass filter the center
		if 'defocus1' in self.ctfvalues.keys():
			#get first zero
			meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])
			radii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=1, zerotype="peaks")
			firstpeak = radii[0]
		else:
			#set first zero to 1/50A
			#1/resolution = freq * (# of pixels from center)
			firstpeak = int(1.0/(self.freq*50))
		raddata = pixelrdata*self.freq
		firstpeakindex = numpy.searchsorted(raddata, self.freq*firstpeak)
		apDisplay.printColor("First peak: %.1f (1/%.1f A)"%
			(firstpeakindex, 1/(firstpeak*self.freq)), "yellow")

		### split the function up in first 3/5 and last 3/5 of data with 1/5 overlap
		numpoints = len(raddata) - firstpeakindex
		part1start = firstpeakindex
		part1end = int(firstpeakindex + numpoints*6/10.)
		part2start = int(firstpeakindex + numpoints*5/10.)
		part2end = int(firstpeakindex + numpoints*9/10.)
		part3start = int(firstpeakindex + numpoints*8/10.)
		part3end = len(raddata)

		CtfNoise = ctfnoise.CtfNoise()

		## first part data
		envelopfitparams1 = CtfNoise.modelCTFNoise(raddata[part1start:part1end],
			rotdata[part1start:part1end], "above")
		envelopdata1 = CtfNoise.noiseModel(envelopfitparams1, raddata)

		## second part data
		envelopfitparams2 = CtfNoise.modelCTFNoise(raddata[part2start:part2end],
			rotdata[part2start:part2end], "above")
		envelopdata2 = CtfNoise.noiseModel(envelopfitparams2, raddata)

		## third part data
		envelopfitparams3 = CtfNoise.modelCTFNoise(raddata[part3start:part3end],
			rotdata[part3start:part3end], "above")
		envelopdata3 = CtfNoise.noiseModel(envelopfitparams3, raddata)

		## merge data
		scale = numpy.arange(part1end-part2start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata1 = envelopdata1[part2start:part1end]*(1-scale) + envelopdata2[part2start:part1end]*scale
		scale = numpy.arange(part2end-part3start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata2 = envelopdata2[part3start:part2end]*(1-scale) + envelopdata3[part3start:part2end]*scale

		mergedata = numpy.hstack((envelopdata1[:part2start], overlapdata1,
			envelopdata2[part1end:part3start], overlapdata2,
			envelopdata3[part2end:]))

		pyplot.clf()
		a = pyplot.plot(raddata**2, rotdata, 'k.',)
		b = pyplot.plot(raddata**2, mergedata, '--', color="purple", linewidth=2)
		c = pyplot.plot(raddata[part1start:part1end]**2,
			envelopdata1[part1start:part1end], 'b-', alpha=0.5, linewidth=2)
		d = pyplot.plot(raddata[part2start:part2end]**2,
			envelopdata2[part2start:part2end], 'r-', alpha=0.5, linewidth=2)
		e = pyplot.plot(raddata[part3start:part3end]**2,
			envelopdata3[part3start:part3end], '-', alpha=0.5, linewidth=2, color="green")
		pyplot.legend([a, b, c, d, e], ["data", "merge", "part 1", "part 2", "part 3"])
		pyplot.xlim(xmax=(raddata**2).max())
		pyplot.ylim(ymin=rotdata[firstpeakindex-1:].min(), ymax=mergedata[firstpeakindex-1:].max())
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		imagedata = self.panel.numericdata
		envelop2d = ctftools.unEllipticalAverage(pixelrdata, mergedata,
			self.ellipratio, self.ellipangle, imagedata.shape)
		normaldata = imagedata / envelop2d
		#normaldata = numpy.where(normaldata > 1.2, 1.2, normaldata)
		#normaldata = numpy.where(normaldata < -0.2, -0.2, normaldata)
		self.panel.setImage(normaldata)

		imagestat.printImageInfo(normaldata)
		apDisplay.printColor("Normalize Trimodal Envelop complete", "cyan")

	#---------------------------------------
	def onShowPlot(self, evt):
		pixelrdata, raddata, rotdata = self.getOneDProfile(full=False)
		pixelrdata, raddatafull, rotdatafull = self.getOneDProfile(full=True)

		imagestat.printImageInfo(rotdata)

		pyplot.clf()
		pyplot.plot(raddatafull**2, rotdatafull, 'r--', alpha=0.5)
		pyplot.plot(raddata**2, rotdata, 'k-',)
		fullmax = (raddatafull**2).max()
		normmax = (raddata**2).max()
		usemax = (fullmax + normmax)/2.0
		pyplot.xlim(xmax=usemax)
		pyplot.ylim(ymin=rotdata[5:].min(), ymax=rotdata[5:].max())
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()
		apDisplay.printColor("Show plot complete", "cyan")
		return

	#---------------------------------------
	def onNext(self, evt):
		self.appionloop.targets = {}
		self.appionloop.assess = self.finalAssessment()
		self.Exit()

	#---------------------------------------
	def finalAssessment(self):
		if self.assessnone.GetValue() is True:
			return None
		elif self.assesskeep.GetValue() is True:
			return True
		elif self.assessreject.GetValue() is True:
			return False
		return None

	#---------------------------------------
	def setAssessStatus(self):
		if self.appionloop.assess is True:
			self.onToggleKeep(None)
		elif self.appionloop.assess is False:
			self.onToggleReject(None)
		else:
			self.onToggleNone(None)

	#---------------------------------------
	def onToggleNone(self, evt):
		self.assessnone.SetValue(1)
		self.assessnone.SetBackgroundColour(wx.Color(200,200,0))
		self.assesskeep.SetValue(0)
		self.assesskeep.SetBackgroundColour(self.deselectcolor)
		self.assessreject.SetValue(0)
		self.assessreject.SetBackgroundColour(self.deselectcolor)
		self.assess = None

	#---------------------------------------
	def onToggleKeep(self, evt):
		self.assessnone.SetValue(0)
		self.assessnone.SetBackgroundColour(self.deselectcolor)
		self.assesskeep.SetValue(1)
		self.assesskeep.SetBackgroundColour(wx.Color(0,200,0))
		self.assessreject.SetValue(0)
		self.assessreject.SetBackgroundColour(self.deselectcolor)
		self.assess = True

	#---------------------------------------
	def onToggleReject(self, evt):
		self.assessnone.SetValue(0)
		self.assessnone.SetBackgroundColour(self.deselectcolor)
		self.assesskeep.SetValue(0)
		self.assesskeep.SetBackgroundColour(self.deselectcolor)
		self.assessreject.SetValue(1)
		self.assessreject.SetBackgroundColour(wx.Color(200,0,0))
		self.assess = False

	#---------------------------------------
	def onClear(self, evt):
		self.panel.setTargets('First Valley', [])
		apDisplay.printColor("Clear picks complete", "cyan")

	#---------------------------------------
	def onRevert(self, evt):
		self.panel.setImage(self.panel.originalarray)
		apDisplay.printColor("Revert image complete", "cyan")

	#---------------------------------------
	def targetsToArray(self, targets):
		a = []
		for t in targets:
			if t.x and t.y:
				a.append([ int(t.x), int(t.y) ])
		na = numpy.array(a, dtype=numpy.int32)
		return na

##################################
##################################
##################################
## APPION LOOP
##################################
##################################
##################################

class ManualCTF(appionLoop2.AppionLoop):
	def onInit(self):
		super(ManualCTF,self).onInit()
		self.trace = False
		self.ctfrun = None
		return

	#---------------------------------------
	def setApp(self):
		self.app = CTFApp(
			shape = self.canonicalShape(self.params['shape']),
			size =  self.params['shapesize'],
		)
		return

	#---------------------------------------
	def readFreqFile(self):
		self.freqfile = os.path.join(self.params['rundir'], "fft_frequencies.dat")
		self.freqdict = {}
		if os.path.isfile(self.freqfile):
			f = open(self.freqfile, "r")
			for line in f:
				sline = line.strip()
				if sline[0] == "#":
					continue
				bits = sline.split('\t')
				freq = float(bits[0].strip())
				fftpath = bits[1].strip()
				self.freqdict[fftpath] = freq
			f.close()
		apDisplay.printMsg("Read %d powerspec files from freqfile"%(len(self.freqdict)))
		return

	#---------------------------------------
	def saveFreqFile(self):
		if not self.freqdict:
			return
		f = open(self.freqfile, "w")
		f.write("#frequency	fft file\n")
		keys = self.freqdict.keys()
		keys.sort()
		for key in keys:
			f.write("%.8e\t%s\n"%(self.freqdict[key], key))
		f.close()
		return

	#---------------------------------------
	def preLoopFunctions(self):
		self.fftsdir = os.path.join(self.params['rundir'], "ffts")
		apParam.createDirectory(self.fftsdir, warning=(not self.quiet))
		self.readFreqFile()
		if self.params['sessionname'] is not None:
			self.processAndSaveAllImages()
		self.setApp()
		self.app.appionloop = self

	#---------------------------------------
	def postLoopFunctions(self):
		self.app.frame.Destroy()
		apDisplay.printMsg("Finishing up")
		time.sleep(20)
		apDisplay.printMsg("finished")
		wx.Exit()

	#---------------------------------------
	def processImage(self, imgdata):
		fftpath = os.path.join(self.fftsdir, apDisplay.short(imgdata['filename'])+'.powerspec.mrc')
		if not os.path.isfile(fftpath):
			self.processAndSaveFFT(imgdata, fftpath)
		self.saveFreqFile()
		self.runManualCTF(imgdata, fftpath)

		return

	#---------------------------------------
	def commitToDatabase(self, imgdata):
		if self.assess != self.assessold and self.assess is not None:
			#imageaccessor run is always named run1
			apDatabase.insertImgAssessmentStatus(imgdata, 'run1', self.assess)
		self.insertCtfRun(imgdata)
		ctfinsert.validateAndInsertCTFData(imgdata, self.ctfvalues, self.ctfrun, self.params['rundir'])
		return

	#---------------------------------------
	def insertCtfRun(self, imgdata):
		if isinstance(self.ctfrun, appiondata.ApAceRunData):
			return False

		# first create an aceparam object
		paramq = appiondata.ApXmippCtfParamsData()
		paramq['fieldsize'] = self.params['fieldsize']

		# create an acerun object
		runq = appiondata.ApAceRunData()
		runq['name'] = self.params['runname']
		runq['session'] = imgdata['session'];

		# see if acerun already exists in the database
		runnames = runq.query(results=1)

		if (runnames):
			if not (runnames[0]['xmipp_ctf_params'] == paramq):
				for i in runnames[0]['xmipp_ctf_params']:
					if runnames[0]['xmipp_ctf_params'][i] != paramq[i]:
						apDisplay.printWarning("the value for parameter '"+str(i)+"' is different from before")
				apDisplay.printError("All parameters for a single CTF estimation run must be identical! \n"+\
						     "please check your parameter settings.")
			self.ctfrun = runnames[0]
			return False

		#create path
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['hidden'] = False
		# if no run entry exists, insert new run entry into db
		runq['xmipp_ctf_params'] = paramq
		runq.insert()
		self.ctfrun = runq
		return True

	#---------------------------------------
	def setupParserOptions(self):
		### Input value options
		self.parser.add_option("--shape", dest="shape", default='+',
			help="pick shape")
		self.parser.add_option("--shapesize", dest="shapesize", type="int", default=16,
			help="shape size")
		self.parser.add_option("--fieldsize", dest="fieldsize", type="int",
			help="field size to use for sub-field averaging in power spectra calculation")
		self.parser.add_option("--reslimit", "--resolution-limit", dest="reslimit", type="float", default=6.0,
			help="outer resolution limit (in Angstroms) to clip the fft image")
		self.parser.add_option("--ringwidth", dest="ringwidth", type="float", default=2.0,
			help="number of radial pixels to average during elliptical average")

	#---------------------------------------
	def checkConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		if self.params['reslimit'] > 50 or self.params['reslimit'] < 1.0:
			apDisplay.printError("Resolution limit is in Angstroms")

		return

	###################################################
	##### END PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	###################################################

	def canonicalShape(self, shape):
		if shape == '.'    or shape == 'point':
			return '.'
		elif shape == '+'  or shape == 'plus':
			return '+'
		elif shape == '[]' or shape == 'square' or shape == 'box':
			return '[]'
		elif shape == '<>' or shape == 'diamond':
			return '<>'
		elif shape == 'x'  or shape == 'cross':
			return 'x'
		elif shape == '*'  or shape == 'star':
			return '*'
		elif shape == 'o'  or shape == 'circle':
			return 'o'
		else:
			apDisplay.printError("Unknown pointer shape: "+shape)

	#---------------------------------------
	def getParticlePicks(self, imgdata):
		return []

	#---------------------------------------
	def particlesToTargets(self, particles):
		targets = {}
		return targets

	#---------------------------------------
	def processAndSaveAllImages(self):
		sys.stderr.write("Pre-processing image FFTs\n")
		#print self.params
		count = 0
		total = len(self.imgtree)
		for imgdata in self.imgtree:
			count += 1
			self.fftsdir
			fftpath = os.path.join(self.fftsdir, apDisplay.short(imgdata['filename'])+'.powerspec.mrc')
			if self.params['continue'] is True and os.path.isfile(fftpath) and fftpath in self.freqdict.keys():
				sys.stderr.write(".")
				#print "already processed: ",apDisplay.short(imgdata['filename'])
			else:
				if os.path.isfile(fftpath):
					os.remove(fftpath)
				sys.stderr.write("#")
				self.processAndSaveFFT(imgdata, fftpath)

			if count % 60 == 0:
				sys.stderr.write(" %d left\n" % (total-count))

	#---------------------------------------
	def processAndSaveFFT(self, imgdata, fftpath):
		if os.path.isfile(fftpath) and fftpath in self.freqdict.keys():
			return False

		### downsize and filter leginon image
		if self.params['uncorrected']:
			imgarray = imagefilter.correctImage(imgdata, params)
		else:
			imgarray = imgdata['image']

		### calculate power spectra
		apix = apDatabase.getPixelSize(imgdata)
		fftarray, freq = ctfpower.power(imgarray, apix, mask_radius=1, fieldsize=self.params['fieldsize'])
		#fftarray = imagefun.power(fftarray, mask_radius=1)

		fftarray = ndimage.median_filter(fftarray, 2)

		## preform a rotational average and remove peaks
		rotfftarray = ctftools.rotationalAverage2D(fftarray)
		stdev = rotfftarray.std()
		rotplus = rotfftarray + stdev*4
		fftarray = numpy.where(fftarray > rotplus, rotfftarray, fftarray)

		### save to jpeg
		self.freqdict[fftpath] = freq
		mrc.write(fftarray, fftpath)

		return True

	#---------------------------------------
	def runManualCTF(self, imgdata, fftpath):
		#reset targets
		self.targets = {}
		self.app.panel.setTargets('First Valley', [])
		self.targets['First Valley'] = []

		#set the assessment and viewer status
		self.assessold = apDatabase.checkInspectDB(imgdata)
		self.assess = self.assessold
		self.app.setAssessStatus()

		#open new file
		fftarray = mrc.read(fftpath).astype(numpy.float64)
		print self.freqdict.keys()
		freq = self.freqdict[fftpath]

		### clip image
		# convert res limit into pixel distance
		fftwidth = fftarray.shape[0]
		maxres = 2.0/(freq*fftwidth)
		if maxres > self.params['reslimit']:
			apDisplay.printError("Cannot get requested resolution %.1fA > %.1fA"
				%(maxres, self.params['reslimit']))
		limitwidth = int(math.ceil(2.0/(self.params['reslimit']*freq)))
		print limitwidth, self.params['reslimit'], freq
		limitwidth = primefactor.getNextEvenPrime(limitwidth)
		requestres = 2.0/(freq*limitwidth)
		if limitwidth > fftwidth:
			apDisplay.printError("Cannot get requested resolution"
				+(" %.1fA > %.1fA for widths %d > %d"
				%(maxres, requestres, limitwidth, fftwidth)))
		apDisplay.printMsg("Requested resolution OK: "
			+(" %.1fA < %.1fA with fft widths %d < %d"
			%(maxres, requestres, limitwidth, fftwidth)))
		newshape = (limitwidth, limitwidth)
		fftarray = imagefilter.frame_cut(fftarray, newshape)

		self.app.panel.originalarray = fftarray
		self.app.panel.setImage(fftarray)

		### spacing parameters
		self.app.freq = freq
		fftwidth = min(fftarray.shape)
		self.app.apix = 1.0/(fftwidth*freq)

		self.app.imgdata = imgdata
		self.app.volts = imgdata['scope']['high tension']
		self.app.ringwidth = self.params['ringwidth']
		self.app.wavelength = ctftools.getTEMLambda(self.app.volts)
		self.app.cs = apInstrument.getCsValueFromSession(self.getSessionData())*1e-3
		self.app.ctfvalues.update({
			'volts': self.app.volts,
			'cs': self.app.cs,
			'apix': self.app.apix,
		})

		targets = self.getParticlePicks(imgdata)

		#set vital stats
		self.app.vitalstats.SetLabel("Vital Stats: Image "+str(self.stats['count'])
			+" of "+str(self.stats['imagecount'])+", inserted "+str(self.stats['peaksum'])+" picks, "
			+" image name: "+imgdata['filename'])
		#run the ctf
		self.app.MainLoop()

		return

#---------------------------------------
#---------------------------------------
if __name__ == '__main__':
	imgLoop = ManualCTF()
	imgLoop.run()
	#a = imagefile.readJPG("/data01/appion/11jul05a/extract/manctf2/"
	#	+"11jul05a_11jan06b_00002sq_00002hl_v01_00002en2.fft.jpg")
