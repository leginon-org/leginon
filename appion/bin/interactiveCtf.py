#!/usr/bin/env python

import os
import wx
import sys
import time
import math
import copy
import numpy
import random
import matplotlib
from multiprocessing import Process
matplotlib.use('WXAgg')
#matplotlib.use('gtk')
from matplotlib import pyplot
from PIL import Image
#import subprocess
from appionlib import apDog
from appionlib import apParam
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apDatabase
from appionlib import appionLoop2
from appionlib import apInstrument
from appionlib.apCtf import ctftools, ctfnoise, ctfdb, sinefit, canny, findroots
from appionlib.apCtf import genctf, ctfpower, ctfres, ctfinsert, ransac, findastig
from appionlib.apCtf import ctfdisplay
from appionlib.apImage import imagefile, imagefilter, imagenorm, imagestat
#Leginon
import leginon.polygon
from leginon.gui.wx import ImagePanel, ImagePanelTools, TargetPanel, TargetPanelTools
from pyami import mrc, fftfun, imagefun, ellipse, primefactor
from scipy import ndimage
import scipy.stats
from leginon.gui.wx.Entry import FloatEntry, IntEntry, EVT_ENTRY


##
##
## Refine CTF 2d Dialog
##
##

class RefineCTFDialog(wx.Dialog):
	#==================
	def __init__(self, parent):
		self.parent = parent
		wx.Dialog.__init__(self, self.parent.frame, -1, "Refine CTF 2D")

		inforow = wx.FlexGridSizer(4, 4, 15, 15) #4 row, 4 col
		inforow.AddGrowableCol(1)

		if 'defocus1' in self.parent.ctfvalues and self.parent.ctfvalues['defocus1'] is not None:
			def1str = "%.3e" % self.parent.ctfvalues['defocus1']
		else:
			def1str = "0.0e00"
		label = wx.StaticText(self, -1, "Defocus 1: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.def1Value = FloatEntry(self, -1, allownone=False, chars=18, value=def1str)
		label2 = wx.StaticText(self, -1, "m", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.def1Tog = wx.ToggleButton(self, -1, "Refine")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleDef1, self.def1Tog)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.def1Value, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.def1Tog, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		if 'defocus2' in self.parent.ctfvalues and self.parent.ctfvalues['defocus2'] is not None:
			def2str = "%.3e" % self.parent.ctfvalues['defocus2']
		else:
			def2str = "0.0e00"
		label = wx.StaticText(self, -1, "Defocus 2: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.def2Value = FloatEntry(self, -1, allownone=False, chars=18, value=def2str)

		label2 = wx.StaticText(self, -1, "m", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.def2Tog = wx.ToggleButton(self, -1, "Refine")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleDef2, self.def2Tog)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.def2Value, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.def2Tog, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		if 'amplitude_contrast' in self.parent.ctfvalues and self.parent.ctfvalues['amplitude_contrast'] is not None:
			ampconstr  = "%.3f" % self.parent.ctfvalues['amplitude_contrast']
		else:
			ampconstr  = "0.0"
		label = wx.StaticText(self, -1, "Amp Contrast: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.ampconValue = FloatEntry(self, -1, allownone=False, chars=12, value=ampconstr)
		label2 = wx.StaticText(self, -1, " ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.ampconTog = wx.ToggleButton(self, -1, "Refine")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleAmpCon, self.ampconTog)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.ampconValue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.ampconTog, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		if 'angle_astigmatism' in self.parent.ctfvalues and self.parent.ctfvalues['angle_astigmatism'] is not None:
			anglestr  = "%.2f" % self.parent.ctfvalues['angle_astigmatism']
		else:
			anglestr  = "0.0"
		label = wx.StaticText(self, -1, "Angle Astig: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.angleValue = FloatEntry(self, -1, allownone=False, chars=12, value=anglestr)
		label2 = wx.StaticText(self, -1, "deg", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.angleTog = wx.ToggleButton(self, -1, "Locked")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleAngle, self.angleTog)
		self.angleValue.Enable(False)
		self.angleTog.SetValue(1)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.angleValue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.angleTog, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		summaryrow = wx.GridSizer(1,2) #1 row, 2 col
		label = wx.StaticText(self, -1, "Resolution (Angstroms): ", style=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		self.reslabel = wx.StaticText(self, -1, " unknown ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		summaryrow.Add(label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		summaryrow.Add(self.reslabel, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		#label = wx.StaticText(self, -1, "Iterations: ", style=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		#self.iterlabel = wx.StaticText(self, -1, " none ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		#summaryrow.Add(label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		#summaryrow.Add(self.iterlabel, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		buttonrow = wx.GridSizer(1,3) #1 row, 3 col
		self.cancelrefineCtf = wx.Button(self, wx.ID_CANCEL, '&Cancel')
		self.applyctfvalues = wx.Button(self, wx.ID_APPLY, '&Apply')
		self.runrefineCtf = wx.Button(self, -1, '&Run')
		self.Bind(wx.EVT_BUTTON, self.onRunLeastSquares, self.runrefineCtf)
		self.Bind(wx.EVT_BUTTON, self.onApplyCTFValues, self.applyctfvalues)
		buttonrow.Add(self.cancelrefineCtf, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.applyctfvalues, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.runrefineCtf, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)

		## merge rows together
		self.sizer = wx.FlexGridSizer(3,1) #3 row, 1 col
		self.sizer.AddGrowableCol(0)
		self.sizer.Add(inforow, 0, wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(summaryrow, 0, wx.EXPAND|wx.ALL, 5)
		self.sizer.Add(buttonrow, 0, wx.EXPAND|wx.ALL, 5)
		self.SetSizerAndFit(self.sizer)

		#self.onToggleAngle(True)

	#==================
	def onToggleDef1(self, evt):
		if self.def1Tog.GetValue() is True:
			self.def1Value.Enable(False)
			self.def1Tog.SetLabel("Locked")
		else:
			self.def1Value.Enable(True)
			self.def1Tog.SetLabel("Refine")

	#==================
	def onToggleDef2(self, evt):
		if self.def2Tog.GetValue() is True:
			self.def2Value.Enable(False)
			self.def2Tog.SetLabel("Locked")
		else:
			self.def2Value.Enable(True)
			self.def2Tog.SetLabel("Refine")

	#==================
	def onToggleAmpCon(self, evt):
		if self.ampconTog.GetValue() is True:
			self.ampconValue.Enable(False)
			self.ampconTog.SetLabel("Locked")
		else:
			self.ampconValue.Enable(True)
			self.ampconTog.SetLabel("Refine")

	#==================
	def onToggleAngle(self, evt):
		if self.angleTog.GetValue() is True:
			self.angleValue.Enable(False)
			self.angleTog.SetLabel("Locked")
		else:
			self.angleValue.Enable(True)
			self.angleTog.SetLabel("Refine")

	#==================
	def onRunLeastSquares(self, evt):
		def1   = self.def1Value.GetValue()
		def2   = self.def2Value.GetValue()
		ampcon = self.ampconValue.GetValue()
		## ellip angle is positive toward y-axis, ctf angle is negative toward y-axis
		ellipangle = -self.angleValue.GetValue()
		cs = self.parent.ctfvalues['cs']
		wv = self.parent.wavelength
		volts = self.parent.ctfvalues['volts']

		#SET refine Flags 
		refineFlags = numpy.array((
			not self.def1Tog.GetValue(),
			not self.def2Tog.GetValue(),
			not self.angleTog.GetValue(),
			not self.ampconTog.GetValue(),
			), dtype=numpy.bool)

		radial_array, angle_array, normPSD = self.parent.getTwoDProfile()

		radial_array = radial_array.ravel()
		angle_array = angle_array.ravel()
		normPSD = normPSD.ravel()

		sortind = numpy.argsort(radial_array)
		radial_array = radial_array[sortind]
		angle_array = angle_array[sortind]
		normPSD = normPSD[sortind]

		weights = None
		if self.parent.checkNormalized(msg=False) is True:
			print "using weights from resolution profile"
			### get the data
			oldzavg = (def1+def2)/2.0
			pixelrdata, raddata, PSDarray = self.parent.getOneDProfile(full=False)
			peaks = ctftools.getCtfExtrema(oldzavg, self.parent.freq*1e10, cs, 
				volts, ampcon, numzeros=250, zerotype="peak")
			ctffitdata = genctf.generateCTF1d(raddata*1e10, focus=oldzavg, cs=cs,
				volts=volts, ampconst=ampcon, failParams=False)
			### get the confidence
			confraddata, confdata = ctfres.getCorrelationProfile(raddata, PSDarray, ctffitdata, peaks, self.parent.freq)
			### get the weights
			weights, firstpoint, lastpoint = ctfres.getWeightsForXValues(raddata, confraddata, confdata)
		if weights is None or len(weights) < 10 or 1/raddata[lastpoint] > 12:
			print "weighting to 30-8 range"
			weights = numpy.zeros(radial_array.shape, dtype=numpy.float64)
			firstpoint = numpy.searchsorted(radial_array, 1/30.)
			lastpoint = numpy.searchsorted(radial_array, 1/8.)
			weights[firstpoint:lastpoint] = 1

		newvalues = sinefit.refineCTF(radial_array[firstpoint:lastpoint]*1e10, angle_array[firstpoint:lastpoint], 
			ampcon, def1, def2, ellipangle, normPSD[firstpoint:lastpoint], cs, wv, refineFlags, weights[firstpoint:lastpoint])

		if newvalues is None:
			apDisplay.printWarning("onRefineCTF failed")
			return

		ampcon, def1, def2, ellipangle = newvalues

		self.def1Value.SetValue(round(def1*1e6,3)/1e6)
		self.def2Value.SetValue(round(def2*1e6,3)/1e6)
		self.ampconValue.SetValue(round(ampcon,4))
		self.angleValue.SetValue(round(-ellipangle,4))
		resValue = self.parent.onGetResolution(None, show=False)
		self.reslabel.SetLabel(str(round(resValue,5)))

	#==================
	def onApplyCTFValues(self, evt):
		self.Close()
		self.parent.ctfvalues['defocus1'] = self.def1Value.GetValue()
		self.parent.ctfvalues['defocus2'] = self.def2Value.GetValue()
		self.parent.ctfvalues['amplitude_contrast'] = self.ampconValue.GetValue()
		self.parent.ctfvalues['angle_astigmatism'] = self.angleValue.GetValue()
		self.parent.convertCtfToEllipse()

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
		self.button.SetToggle(True)

	#--------------------
	def Draw(self, dc):
		### check if button is depressed
		if not self.button.GetToggle():
			return
		### need CTF information
		if not self.app.ctfvalues or not 'defocus2' in self.app.ctfvalues.keys():
			return
		if self.app.freq is None:
			return

		dc.SetPen(wx.Pen(self.color, self.penwidth))
		width = self.imagepanel.bitmap.GetWidth()
		height = self.imagepanel.bitmap.GetHeight()

		if self.imagepanel.scaleImage():
			width /= self.imagepanel.scale[0]
			height /= self.imagepanel.scale[1]
		center = width/2, height/2
		#x, y = self.imagepanel.image2view(center)

		numzeros = 20

		radii1 = ctftools.getCtfExtrema(self.app.ctfvalues['defocus1'], self.app.freq*1e10,
			self.app.ctfvalues['cs'], self.app.ctfvalues['volts'], self.app.ctfvalues['amplitude_contrast'],
			numzeros=numzeros, zerotype="valleys")
		radii2 = ctftools.getCtfExtrema(self.app.ctfvalues['defocus2'], self.app.freq*1e10,
			self.app.ctfvalues['cs'], self.app.ctfvalues['volts'], self.app.ctfvalues['amplitude_contrast'],
			numzeros=numzeros, zerotype="valleys")

		s1 = 1.0/math.sqrt(radii1[0]*self.app.wavelength)
		s2 = 1.0/math.sqrt(radii2[0]*self.app.wavelength)

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
		
			## ellip angle is positve toward y-axis, ctf angle is positive toward y-axis
			alpha = math.radians(self.app.ctfvalues['angle_astigmatism'])

			points = ellipse.generate_ellipse(major, minor, alpha,
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

		inforow = wx.FlexGridSizer(2, 4, 5, 5) #row, col
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
		self.ampconvalue = FloatEntry(self, -1, allownone=False, min=-1.0, max=1.0, chars=16, value="0")
		self.ampconvalue.SetMinSize((entrywidth, -1))
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.ampconvalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		label = wx.StaticText(self, -1, "Angle: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.angleValue = FloatEntry(self, -1, allownone=False, min=-90, max=90, chars=16, value="0")
		self.angleValue.SetMinSize((entrywidth, -1))
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.angleValue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

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
		self.parent.ctfvalues['angle_astigmatism'] = self.angleValue.GetValue()
		self.parent.convertCtfToEllipse()

##################################
##
##################################

class EditMicroscopeDialog(wx.Dialog):
	#==================
	def __init__(self, parent):
		self.parent = parent
		wx.Dialog.__init__(self, self.parent.frame, -1, "Edit Microscope Parameters")

		inforow = wx.FlexGridSizer(3, 3, 5, 5) #row, col
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
		self.ellipseParams = None
		#self.ctfvalues = {
		#	'defocus1': 1e-6, 'defocus2': 1e-6,
		#	'volts': 120000, 'cs': 2e-3, 'angle_astigmatism': 45.0,
		#	'amplitude_contrast': 0.07, 'apix': 1.5, }
		#self.ctfvalues = {
		#	'defocus1': None, 'defocus2': None,
		#	'volts': None, 'cs': None, 'angle_astigmatism': None,
		#	'amplitude_contrast': None, 'apix': None, }
		#self.freq = 1.0/self.ctfvalues['apix']
		self.ctfvalues = {}
		self.freq = None
		self.imagestatcache = {}
		self.imagestatcachefull = {}
		self.ellipratio = 1.0
		self.ellipangle = 0.0
		self.ringwidth = 2
		self.submit = False
	
		self.debug = False
		self.flatcutrad = None
		self.edgeMap = None
		self.bestvalues = None
		self.bestres = 1000.
		self.bestellipse = None

		self.maxAmpCon = 0.25
		self.minAmpCon = 0.02

		wx.App.__init__(self)

	#---------------------------------------
	def OnInit(self):
		self.deselectcolor = wx.Colour(240,240,240)

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

		self.panel.addTargetTool('First Valley', color=wx.Colour(220,20,20),
			target=True, shape='x')
		self.panel.setTargets('First Valley', [])
		self.panel.selectiontool.setDisplayed('First Valley', True)
		self.panel.selectiontool.setTargeting('First Valley', True)

		self.panel.addTargetTool('First Valley Fit', color=wx.Colour(251,236,93),
			target=False, shape='polygon')
		self.panel.setTargets('First Valley Fit', [])
		self.panel.selectiontool.setDisplayed('First Valley Fit', True)

		self.panel.SetMinSize((300,300))
		self.sizer.Add(self.panel, 1, wx.EXPAND)
		### END IMAGE PANEL

		### BEGIN BUTTONS ROW
		self.buttonrow = wx.FlexGridSizer(0,8)

		label = wx.StaticText(self.frame, -1, "Database:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, wx.ID_REVERT_TO_SAVED, 'Revert')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRevert, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.editparam_dialog = EditParamsDialog(self)
		wxbutton = wx.Button(self.frame, -1, 'CTF Params...')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onEditParams, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.editscope_dialog = EditMicroscopeDialog(self)
		wxbutton = wx.Button(self.frame, -1, 'Scope Params...')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onEditScope, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.refinectf_dialog = RefineCTFDialog(self)
		self.refinectf = wx.Button(self.frame, -1, 'Refine CTF...')
		self.frame.Bind(wx.EVT_BUTTON, self.onRefineCTF, self.refinectf)
		self.buttonrow.Add(self.refinectf, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		wxbutton = wx.Button(self.frame, -1, 'Prev Best')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onPrevBest, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Load CTF')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onLoadCTF, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Save 1D')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onSave1DProfile, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Full Auto')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onFullAuto, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Rotation Auto')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRotationAuto, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Auto RANSAC')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onAutoRANSAC, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Auto Norm')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onAutoNormalize, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "Filters:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Gauss blur')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onGaussBlur, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'DoG enhance')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onDoGenhance, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Rotation blur')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRotBlur, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Median filter')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onMedianFilter, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Z+')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onIncreaseDefocus, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Z-')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onDecreaseDefocus, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "First Valley fit:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.firstvalley = wx.Button(self.frame, -1, 'Fit Points')
		self.firstvalley.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onCalcFirstValley, self.firstvalley)
		self.buttonrow.Add(self.firstvalley, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Water Shed')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onWaterShed, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, wx.ID_CLEAR, 'Clear')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onClear, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "Normalization:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'TriSection Normalize')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onFullTriSectionNormalize, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Subt 2D Box Filter')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onSubt2dBoxFilter, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Subt Fit Valleys')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onSubtFitValleys, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Norm Fit Peaks')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onNormFitPeaks, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Clip Data 0-1')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onClipData, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Edge Find')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onCannyEdge, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'RANSAC')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRANSAC, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Grid Search')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onGridSearch, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Find Roots')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onFindRoots, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Find Astig')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onFindAstig, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Fix Amp Con')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onFixAmpContrast, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Delete Corner')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onDeleteCorners, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Flat Center')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onFlatCenter, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "Averaging:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.rotavg = wx.Button(self.frame, -1, 'Rot Avg')
		self.rotavg.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRotAverage, self.rotavg)
		self.buttonrow.Add(self.rotavg, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Ellip Avg')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onEllipAverage, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, '*Ellip Distort*')
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

		wxbutton = wx.Button(self.frame, -1, 'Amp Contrast')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRefineAmpContrast, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Refine 1D CTF')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRefineCTFOneDimension, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		wxbutton = wx.Button(self.frame, -1, 'Refine 2D CTF')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onRefineCTFOLD, wxbutton)
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

		wxbutton = wx.Button(self.frame, -1, 'Check Final Res')
		wxbutton.SetMinSize((-1, buttonheight))
		self.Bind(wx.EVT_BUTTON, self.onCheckFinalRes, wxbutton)
		self.buttonrow.Add(wxbutton, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.next = wx.Button(self.frame, wx.ID_FORWARD, 'Forward')
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
	def getTwoDProfile(self):
		"""
		common function to retrieve 2D image data

		radial_array, angle_array, imagedata = self.getOneDProfile()
		"""
		t0 = time.time()
		## get the data
		imagedata = self.panel.numericdata

		## create a grid of distance from the center
		shape = imagedata.shape
		xhalfshape = shape[0]/2.0
		x = numpy.arange(-xhalfshape, xhalfshape, 1) + 0.5
		yhalfshape = shape[1]/2.0
		y = numpy.arange(-yhalfshape, yhalfshape, 1) + 0.5
		xx, yy = numpy.meshgrid(x, y)
		# get radial component
		pixelradial = xx**2 + yy**2 - 0.5
		pixelradial = numpy.sqrt(pixelradial)
		# convert to meters
		radial_array = pixelradial*self.freq
		# angular component
		## angle array is positve toward y-axis
		angle_array = numpy.arctan2(-yy,xx)

		#filter the data in the array
		outerEdgeDist = radial_array[shape[0]/2, 1]

		radial_array = radial_array.ravel()
		angle_array = angle_array.ravel()
		imagedata_array = imagedata.ravel()

		imagedata_array = imagedata_array[numpy.where(radial_array < outerEdgeDist)]
		angle_array     = angle_array[numpy.where(radial_array < outerEdgeDist)]
		radial_array    = radial_array[numpy.where(radial_array < outerEdgeDist)]

		innerDist = 1/40. # 40 angstroms
		imagedata_array = imagedata_array[numpy.where(radial_array > innerDist)]
		angle_array     = angle_array[numpy.where(radial_array > innerDist)]
		radial_array    = radial_array[numpy.where(radial_array > innerDist)]

		### done
		apDisplay.printColor("Get 2D profile complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")

		return radial_array, angle_array, imagedata_array

	#---------------------------------------
	def getOneDProfile(self, full=False):
		"""
		common function to convert 2D image into 1D profile

		pixelrdata, raddata, PSDarray = self.getOneDProfile()
		"""
		t0 = time.time()
		imagedata = self.panel.numericdata
		if self.ellipseParams is None:
			self.ellipratio = 1.0
			self.ellipangle = 0.0
		else:
			self.ellipratio = self.ellipseParams['a']/self.ellipseParams['b']
			self.ellipangle = math.degrees(self.ellipseParams['alpha'])

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
				PSDarray = self.PSDarraycachefull
			else:
				pixelrdata = self.pixelrdatacache
				PSDarray = self.PSDarraycache
		elif self.ellipseParams is None:
			apDisplay.printWarning("doing a rotational average not elliptical")
			pixelrdata, PSDarray = ctftools.rotationalAverage(imagedata, self.ringwidth, full=full)
		else:
			pixelrdata, PSDarray = ctftools.ellipticalAverage(imagedata,
				self.ellipratio, self.ellipangle, self.ringwidth, full=full)
		raddata = pixelrdata*self.freq

		### cache values for next time
		if full is True:
			self.pixelrdatacachefull = pixelrdata
			self.PSDarraycachefull = PSDarray
			self.imagestatcachefull = statcache
		else:
			self.pixelrdatacache = pixelrdata
			self.PSDarraycache = PSDarray
			self.imagestatcache = statcache

		### done
		apDisplay.printColor("Get 1D profile complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")

		return pixelrdata, raddata, PSDarray

	#---------------------------------------
	def onEditParams(self, evt):
		print self.ctfvalues
		if 'defocus1' in self.ctfvalues:
			self.editparam_dialog.def1value.SetValue(self.ctfvalues['defocus1'])
		if 'defocus2' in self.ctfvalues:
			self.editparam_dialog.def2value.SetValue(self.ctfvalues['defocus2'])
		if 'amplitude_contrast' in self.ctfvalues:
			self.editparam_dialog.ampconvalue.SetValue(self.ctfvalues['amplitude_contrast'])
		if 'angle_astigmatism' in self.ctfvalues:
			while self.ctfvalues['angle_astigmatism'] < -90:
				self.ctfvalues['angle_astigmatism'] += 180
			while self.ctfvalues['angle_astigmatism'] > 90:
				self.ctfvalues['angle_astigmatism'] -= 180
			self.editparam_dialog.angleValue.SetValue(self.ctfvalues['angle_astigmatism'])
		self.editparam_dialog.Show()
		apDisplay.printColor("Edit params complete", "cyan")

	#---------------------------------------
	def onEditScope(self, evt):
		print self.ctfvalues
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
	def onPrevBest(self, evt):
		t0 = time.time()

		if self.bestvalues is None:
			print "no best values found"
			return

		print self.bestvalues
		print self.ctfvalues

		self.ctfvalues['amplitude_contrast'] = self.bestvalues['amplitude_contrast']
		self.ctfvalues['defocus1'] = self.bestvalues['defocus1']
		self.ctfvalues['defocus2'] = self.bestvalues['defocus2']
		self.ctfvalues['angle_astigmatism'] = self.bestvalues['angle_astigmatism']

		self.convertCtfToEllipse()

		apDisplay.printColor("d1=%.3e\td2=%.3e\tratio=%.3f\tang=%.2f\tac=%.4f"%(
			self.ctfvalues['defocus1'], self.ctfvalues['defocus2'],
			self.ctfvalues['defocus2']/self.ctfvalues['defocus1'],
			self.ctfvalues['angle_astigmatism'], self.ctfvalues['amplitude_contrast']), "magenta")

		print self.ctfvalues

		self.panel.UpdateDrawing()

		apDisplay.printColor("Restore Previous Best CTF Parameters complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return


	#---------------------------------------
	def onLoadCTF(self, evt):
		t0 = time.time()
		ctfdata = ctfdb.getBestCtfByResolution(self.imgdata)
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

		self.panel.UpdateDrawing()

		apDisplay.printColor("Load CTF complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onFullAuto(self, evt):
		t0 = time.time()
		self.onAutoRANSAC(evt)

		self.onFlatCenter(evt)
		self.onEllipAverage(evt)

		self.onAutoNormalize(evt)

		res = self.onGetResolution(evt, show=False)
		lastres = res*2
		while lastres > res:
			lastres = res*0.99
			self.onRefineCTFOneDimension(evt)
			res = self.onGetResolution(evt, show=False)

		apDisplay.printColor("Full Auto complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onRotationAuto(self, evt):
		t0 = time.time()
		self.onFlatCenter(evt)
		self.onMedianFilter(evt)
		self.ctfvalues['defocus1'] = (self.mindef + self.maxdef)/2.0
		self.ctfvalues['defocus2'] = (self.mindef + self.maxdef)/2.0
		self.ellipratio = 1.0
		self.ctfvalues['angle_astigmatism'] = 0.0
		self.ctfvalues['amplitude_contrast'] = 0.07
		self.onSubt2dBoxFilter(evt)
		self.onRotAverage(evt)
		self.onDeleteCorners(evt)

		self.onGridSearch(evt)

		self.onRevert(evt)
		#self.onPrevBest(evt)
		self.onFlatCenter(evt)
		self.onMedianFilter(evt)
		self.onRotAverage(evt)

		self.onAutoNormalize(evt)

		res = self.onGetResolution(evt, show=False)
		lastres = res*2
		while res < lastres:
			lastres = res*0.99
			self.onRefineCTFOneDimension(evt)
			res = self.onGetResolution(evt, show=False)

		self.onPrevBest(evt)
		res = self.onGetResolution(evt, show=False)
		lastres = res*2
		while res < lastres:
			lastres = res*0.99
			self.onRefineCTFOneDimension(evt)
			res = self.onGetResolution(evt, show=False)

		self.onPrevBest(evt)

		apDisplay.printColor("Rotation Auto complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return


	#---------------------------------------
	def onAutoRANSAC(self, evt):
		t0 = time.time()
		self.onFlatCenter(evt)
		self.onRotBlur(evt)
		self.onDoGenhance(evt)
		self.onDeleteCorners(evt)
		self.panel.UpdateDrawing()

		self.onCannyEdge(evt)
		self.panel.UpdateDrawing()

		self.onRANSAC(evt)
		self.panel.UpdateDrawing()

		self.onRevert(evt)
		self.onFlatCenter(evt)
		#self.onDoGenhance(evt)
		self.onSubt2dBoxFilter(evt)

		self.onEllipAverage(evt)
		self.onDeleteCorners(evt)

		self.onGridSearch(evt)
		self.onRefineAmpContrast(evt)

		self.onRevert(evt)

		self.panel.UpdateDrawing()

		apDisplay.printColor("Auto RANSAC complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onAutoNormalize(self, evt):
		t0 = time.time()

		if not 'defocus2' in self.ctfvalues.keys():
			dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		self.onFlatCenter(evt)
		self.onFullTriSectionNormalize(evt)
		for i in range(1):
			self.onSubtFitValleys(evt)
			self.onNormFitPeaks(evt)
			self.onClipData(evt)

		self.onFlatCenter(evt)
		self.onDeleteCorners(evt)

		self.panel.UpdateDrawing()

		apDisplay.printColor("Auto Normalize complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def convertCtfToEllipse(self):
		t0 = time.time()
		if self.ctfvalues is None:
			return

		## set ellipse params
		if self.ellipseParams is None:
			self.ellipseParams = {}
		a = ctftools.getCtfExtrema(self.ctfvalues['defocus1'], self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=1, zerotype="valleys")
		self.ellipseParams['a'] = a[0]
		b = ctftools.getCtfExtrema(self.ctfvalues['defocus2'], self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=1, zerotype="valleys")
		self.ellipseParams['b'] = b[0]
		## ellip angle is positive toward y-axis, ctf angle is negative toward y-axis
		self.ellipseParams['alpha'] = -math.radians(self.ctfvalues['angle_astigmatism'])

	#---------------------------------------
	def convertEllipseToCtf(self, node=4):
		t0 = time.time()
		if self.ellipseParams is None:
			return

		self.ellipratio = self.ellipseParams['a']/self.ellipseParams['b']
		self.ellipangle = math.degrees(self.ellipseParams['alpha'])

		#print self.ellipseParams
		if not 'amplitude_contrast' in self.ctfvalues:
			self.ctfvalues['amplitude_contrast'] = 0.0
		## ellip angle is positive toward y-axis, ctf angle is negative toward y-axis
		self.ctfvalues['angle_astigmatism'] = -self.ellipangle
		#print "wavelength", self.wavelength

		#rename values for shorter equation below
		wv = self.wavelength
		cs = self.ctfvalues['cs']
		phi = math.asin(self.ctfvalues['amplitude_contrast'])
		#node = 4, # this is the first local minima of CTF^2 best for picking
		#node = 3, # this is the first downward zero crossing of CTF^2 best for ransac

		#note: a > b then def1 < def2
		#major axis
		s1 = (self.ellipseParams['a']*self.freq)*1e10
		numer = node * math.pi + 2 * math.pi * cs * wv**3 * s1**4 - 4 * phi
		denom = 4 * math.pi * wv * s1**2
		self.ctfvalues['defocus1'] = numer/denom

		#minor axis
		s2 = (self.ellipseParams['b']*self.freq)*1e10
		numer = node * math.pi + 2 * math.pi * cs * wv**3 * s2**4 - 4 * phi
		denom = 4 * math.pi * wv * s2**2
		self.ctfvalues['defocus2'] = numer/denom

		apDisplay.printColor("def1=%.3e\tdef2=%.3e\tratio=%.3f\tangle=%.2f\tampcont=%.4f"%(
			self.ctfvalues['defocus1'], self.ctfvalues['defocus2'],
			self.ctfvalues['defocus2']/self.ctfvalues['defocus1'],
			self.ctfvalues['angle_astigmatism'], self.ctfvalues['amplitude_contrast']), "magenta")

	#---------------------------------------
	def onCalcFirstValley(self, evt):
		t0 = time.time()
		center = numpy.array(self.panel.numericdata.shape)/2.0

		points = self.panel.getTargetPositions('First Valley')
		apDisplay.printMsg("You have %d points to fit in the valley ring"%(len(points)))
		if len(points) < 3:
			dialog = wx.MessageDialog(self.frame, "Need to pick more than 3 points first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		self.ellipseParams = ellipse.solveEllipseOLS(points, center)
		self.convertEllipseToCtf()
		epoints = ellipse.generate_ellipse(self.ellipseParams['a'],
			self.ellipseParams['b'], self.ellipseParams['alpha'], self.ellipseParams['center'],
			numpoints=30, noise=None, method="step", integers=True)
		self.panel.setTargets('First Valley Fit', epoints)
		apDisplay.printColor("def1=%.3e\tdef2=%.3e\tratio=%.3f\tangle=%.2f\tampcont=%.4f"%(
			self.ctfvalues['defocus1'], self.ctfvalues['defocus2'],
			self.ctfvalues['defocus2']/self.ctfvalues['defocus1'],
			self.ctfvalues['angle_astigmatism'], self.ctfvalues['amplitude_contrast']), "magenta")
		apDisplay.printColor("Calc First Valley complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onGaussBlur(self, evt):
		t0 = time.time()
		imagedata = self.panel.numericdata
		gaussdata = ndimage.gaussian_filter(imagedata, 2, mode='wrap')
		self.panel.setImage(gaussdata)

		apDisplay.printColor("Gauss blur complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onDoGenhance(self, evt):
		t0 = time.time()
		imagedata = self.panel.numericdata
		enhance = apDog.diffOfGauss(imagedata, pixrad=10, k=1.2)
		self.panel.setImage(enhance)

		apDisplay.printColor("DoG enhance complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onRotBlur(self, evt):
		t0 = time.time()
		imagedata = self.panel.numericdata
		angle = 1 #degrees
		rotateCCW1 = ndimage.interpolation.rotate(imagedata, angle, 
			order=1, mode='reflect', reshape=False)
		rotateCW1 = ndimage.interpolation.rotate(imagedata, -angle, 
			order=1, mode='reflect', reshape=False)
		rotateCCW2 = ndimage.interpolation.rotate(imagedata, 3*angle, 
			order=1, mode='reflect', reshape=False)
		rotateCW2 = ndimage.interpolation.rotate(imagedata, -3*angle, 
			order=1, mode='reflect', reshape=False)
		rotblurdata = numpy.median(numpy.array((imagedata,rotateCW1,rotateCCW1,rotateCW2,rotateCCW2)), axis=0)
		self.panel.setImage(rotblurdata)

		apDisplay.printColor("Rotation blur complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onMedianFilter(self, evt):
		t0 = time.time()
		imagedata = self.panel.numericdata
		meddata = ndimage.median_filter(imagedata, 3, mode='wrap')
		meddata = ndimage.interpolation.shift(meddata, (-0.5,-0.5), order=1)
		self.panel.setImage(meddata)

		apDisplay.printColor("Median filter complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onIncreaseDefocus(self, evt):
		t0 = time.time()
		zavg = (self.ctfvalues['defocus2']+self.ctfvalues['defocus1'])/2.0
		zdiff = self.ctfvalues['defocus2'] - self.ctfvalues['defocus1']
		shift = zavg*0.05
		zdiff += shift*zdiff/zavg
		zavg  += shift
		self.ctfvalues['defocus1'] = zavg - zdiff/2.
		self.ctfvalues['defocus2'] = zavg + zdiff/2.

		apDisplay.printColor("Increase defocus from %.3e to %3e"
			%(zavg - shift, zavg ), "magenta")

		self.panel.UpdateDrawing()

		apDisplay.printColor("Increase defocus complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onDecreaseDefocus(self, evt):
		t0 = time.time()
		zavg = (self.ctfvalues['defocus2']+self.ctfvalues['defocus1'])/2.0
		zdiff = self.ctfvalues['defocus2'] - self.ctfvalues['defocus1']
		shift = zavg*0.05
		zdiff -= shift*zdiff/zavg
		zavg  -= shift
		self.ctfvalues['defocus1'] = zavg - zdiff/2.
		self.ctfvalues['defocus2'] = zavg + zdiff/2.

		apDisplay.printColor("Decrease defocus from %.3e to %3e"
			%(zavg + shift, zavg), "magenta")

		self.panel.UpdateDrawing()

		apDisplay.printColor("Decrease defocus complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onWaterShed(self, evt):
		t0 = time.time()
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

		self.ellipseParams = ellipse.solveEllipseOLS(points, center)
		self.convertEllipseToCtf()
		epoints = ellipse.generate_ellipse(self.ellipseParams['a'],
			self.ellipseParams['b'], self.ellipseParams['alpha'], self.ellipseParams['center'],
			numpoints=30, noise=None, method="step", integers=True)
		self.panel.setTargets('First Valley Fit', epoints)
		apDisplay.printColor("def1=%.3e\tdef2=%.3e\tratio=%.3f\tangle=%.2f\tampcont=%.4f"%(
			self.ctfvalues['defocus1'], self.ctfvalues['defocus2'],
			self.ctfvalues['defocus2']/self.ctfvalues['defocus1'],
			self.ctfvalues['angle_astigmatism'], self.ctfvalues['amplitude_contrast']), "magenta")

		self.panel.UpdateDrawing()

		apDisplay.printColor("Water Shed complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def funcrad(self, r, rdata=None, zdata=None):
		return numpy.interp(r, rdata, zdata)

	#---------------------------------------
	def onRotAverage(self, evt):
		t0 = time.time()
		# do a rotational average of the image
		imagedata = self.panel.numericdata
		pixelrdata, PSDarray = ctftools.rotationalAverage(imagedata, self.ringwidth, full=True)
		apDisplay.printWarning("doing a rotational average not elliptical")
		rotavgimage = imagefun.fromRadialFunction(self.funcrad, imagedata.shape,
			rdata=pixelrdata, zdata=PSDarray)
		self.panel.setImage(rotavgimage)
		apDisplay.printColor("Rotational Average complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onEllipAverage(self, evt):
		t0 = time.time()
		# do an elliptical average of the image
		if self.ellipseParams is None:
			dialog = wx.MessageDialog(self.frame, "Need ellipse parameters first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		self.ellipratio = self.ellipseParams['a']/self.ellipseParams['b']
		self.ellipangle = math.degrees(self.ellipseParams['alpha'])

		if abs(self.ellipratio - 1.0) < 1e-6:
			apDisplay.printWarning("Ellipse ratio is one, using rotational average, %.3f"
				%(self.ellipratio))
			self.onRotAverage(evt)
			return
		elif self.ellipratio < 1.0:
			apDisplay.printWarning("Ellipse ratio is less than one: %.3f"%(self.ellipratio))

		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=True)
		apDisplay.printColor("Elliptical average ratio = %.3f, angle %.3f"
			%(self.ellipratio,self.ellipangle), "cyan")

		imagedata = self.panel.numericdata
		ellipavgimage = ctftools.unEllipticalAverage(pixelrdata, PSDarray,
			self.ellipratio, self.ellipangle, imagedata.shape)
		self.panel.setImage(ellipavgimage)
		apDisplay.printColor("Elliptical Average complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onEllipDistort(self, evt):
		t0 = time.time()
		# do an elliptical average of the image
		if self.ellipseParams is None:
			dialog = wx.MessageDialog(self.frame, "Need ellipse parameters first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		self.ellipratio = self.ellipseParams['a']/self.ellipseParams['b']
		#astig angle convention: this angle is used to average xy data, so positive
		self.ellipangle = math.degrees(self.ellipseParams['alpha'])
		imagedata = self.panel.numericdata
		pixelrdata, PSDarray = ctftools.ellipticalAverage(imagedata,
			self.ellipratio, self.ellipangle, self.ringwidth, full=True)
		#distort the pixelrdata
		distortrdata = pixelrdata**2/pixelrdata.max()
		ellipavgimage = ctftools.unEllipticalAverage(distortrdata, PSDarray,
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
		t0 = time.time()
		if not 'defocus2' in self.ctfvalues.keys():
			dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		if self.checkNormalized() is False:
			return

		meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])

		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=False)

		PSDarray -= PSDarray.min()
		PSDarray /= numpy.abs(PSDarray).max()

		"""
		peakradii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=100, zerotype="peaks")
		valleyradii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=100, zerotype="valleys")
		firstpeak = peakradii[0]
		firstpeakindex = numpy.searchsorted(raddata, firstpeak*self.freq)
		"""

		genctfdata = genctf.generateCTF1d(raddata*1e10, focus=meandefocus, cs=self.cs,
			volts=self.volts, ampconst=self.ctfvalues['amplitude_contrast'])

		thirtyindex = numpy.searchsorted(raddata, 1/30.)
		tenindex = numpy.searchsorted(raddata, 1/8.)

		## normalize the data
		PSDarray -= (PSDarray[thirtyindex:tenindex]).min()
		PSDarray /= numpy.abs(PSDarray[thirtyindex:tenindex]).max()

		confidence = scipy.stats.pearsonr(PSDarray[thirtyindex:tenindex], genctfdata[thirtyindex:tenindex])[0]

		pyplot.clf()
		raddatasq = raddata**2
		"""
		for radius in peakradii:
			index = numpy.searchsorted(raddata, radius*self.freq)
			if index > raddata.shape[0] - 1:
				break
			pyplot.axvline(x=raddatasq[index], linewidth=1, color="cyan", alpha=0.5)
		for radius in valleyradii:
			index = numpy.searchsorted(raddata, radius*self.freq)
			if index > raddata.shape[0] - 1:
				break
			pyplot.axvline(x=raddatasq[index], linewidth=1, color="gold", alpha=0.5)
		"""
		pyplot.plot(raddatasq[thirtyindex:tenindex], PSDarray[thirtyindex:tenindex], '.', color="gray")
		pyplot.plot(raddatasq[thirtyindex:tenindex], PSDarray[thirtyindex:tenindex], 'k-',)
		pyplot.plot(raddatasq[thirtyindex:tenindex], genctfdata[thirtyindex:tenindex], 'r--',)
		#pyplot.xlim(xmin=raddatasq[firstpeakindex-1], xmax=raddatasq.max())
		#pyplot.ylim(ymin=-0.05, ymax=1.05)
		pyplot.xlim(xmin=1/30.**2, ymax=1/8.**2)
		pyplot.title("30-10 Confidence value of %.4f"%(confidence))
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()
		apDisplay.printColor("Confidence value of %.4f complete"%(confidence), "magenta")

		apDisplay.printColor("Confidence complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onGetResolution(self, env, meandefocus=None, show=True):
		t0 = time.time()
		if meandefocus is None and not 'defocus2' in self.ctfvalues.keys():
			if show is True:
				dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
					'Error', wx.OK|wx.ICON_ERROR)
				dialog.ShowModal()
				dialog.Destroy()
			return

		if self.checkNormalized() is False and show is True:
			return

		### get the data
		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=False)

		if meandefocus is None:
			meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])

		peaks = ctftools.getCtfExtrema(meandefocus, self.freq*1e10, self.ctfvalues['cs'], 
			self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'], numzeros=250, zerotype="peak")

		ctffitdata = genctf.generateCTF1d(raddata*1e10, focus=meandefocus, cs=self.ctfvalues['cs'],
			volts=self.ctfvalues['volts'], ampconst=self.ctfvalues['amplitude_contrast'], failParams=False)

		### get the confidence
		confraddata, confdata = ctfres.getCorrelationProfile(raddata, PSDarray, ctffitdata, peaks, self.freq)

		res5 = ctfres.getResolutionFromConf(confraddata, confdata, limit=0.5)
		res8 = ctfres.getResolutionFromConf(confraddata, confdata, limit=0.8)

		if res8 is None:
			res8 = 100
		if res5 is None:
			res5 = 100

		if (res8+res5) < self.bestres and self.minAmpCon < self.ctfvalues['amplitude_contrast'] < self.maxAmpCon:
			apDisplay.printColor("Congrats! Saving best resolution values %.3e and %.2f"
				%(meandefocus, self.ctfvalues['amplitude_contrast']), "green")
			self.bestres = (res8+res5)
			self.bestvalues = copy.deepcopy(self.ctfvalues)
			self.bestvalues['defocus'] = meandefocus
			self.bestellipse = copy.deepcopy(self.ellipseParams)
		else:
			print "not saving values %.2f, need an average better than %.2f"%((res8+res5), self.bestres)


		if show is True:
			### Show the data
			raddatasq = raddata**2
			confraddatasq = confraddata**2
			peakradii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=2, zerotype="peaks")
			firstpeak = peakradii[0]
			fpi = numpy.searchsorted(raddata, peakradii[0]*self.freq) #firstpeakindex

			## normalize the data
			PSDarray -= (PSDarray[fpi:]).min()
			PSDarray /= numpy.abs(PSDarray[fpi:]).max()

			pyplot.clf()
			### raw powerspectra data
			pyplot.plot(raddatasq[fpi:], PSDarray[fpi:], '-', color="red", alpha=0.5, linewidth=1)
			### ctf fit data
			pyplot.plot(raddatasq[fpi:], ctffitdata[fpi:], '-', color="black", alpha=0.5, linewidth=1)
			### confidence profile
			pyplot.plot(confraddatasq, confdata, '.', color="blue", alpha=0.9, markersize=10)
			pyplot.plot(confraddatasq, confdata, '-', color="blue", alpha=0.9, linewidth=2)

			"""
			locs, labels = pyplot.xticks()
			newlocs = []
			newlabels = []
			for loc in locs:
				res = round(1.0/math.sqrt(loc),1)
				label = "1/%.1fA"%(res)
				newloc = 1.0/res**2
				newlocs.append(newloc)
				newlabels.append(label)
			pyplot.xticks(newlocs, newlabels)
			"""

			pyplot.axvline(x=1/res8**2, linewidth=2, color="gold")
			pyplot.axvline(x=1/res5**2, linewidth=2, color="red")

		
			pyplot.title("Resolution values of %.3fA at 0.8 and %.3fA at 0.5"%(res8,res5))
			pyplot.xlim(xmin=raddatasq[fpi-1], xmax=raddatasq.max())
			#pyplot.ylim(ymin=-0.05, ymax=1.05)
			pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
				bottom=0.05, left=0.05, top=0.95, right=0.95, )
			pyplot.show()

		self.printBestValues()

		apDisplay.printColor("Resolution values of %.4fA at 0.8 and %.4fA at 0.5"
			%(res8,res5), "magenta")

		apDisplay.printColor("Resolution complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return res5

	#---------------------------------------
	def onSave1DProfile(self, evt):
		t0 = time.time()
		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=False)
		s = raddata*1e10
		filename = "profile.dat"
		f = open(filename, "w")
		for i in range(len(PSDarray)):
			f.write("%.8f\t%.8f\n"%(s[i], PSDarray[i]))
		f.close()
		apDisplay.printColor("Save 1d profile to %s complete in %s"
			%(filename, apDisplay.timeString(time.time()-t0)), "cyan")

	#---------------------------------------
	def onGridSearch(self, evt):
		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=False)

		#location of first zero is linear with 1/sqrt(z)
		maxVal = 1.0/math.sqrt(self.mindef)
		minVal = 1.0/math.sqrt(self.maxdef)
		randNum = (random.random() + random.random() + random.random()) / 3.0
		stepSize = 20 * randNum

		invGuesses = numpy.arange(minVal, maxVal, stepSize)
		random.shuffle(invGuesses)
		bestres = 1000.0
		resVals = []
		print "Guessing %d different defocus values"%(len(invGuesses))
		for invDefocus in invGuesses:
			defocus = 1.0/invDefocus**2
			avgres = self.onGetResolution(evt, meandefocus=defocus, show=False)
			apDisplay.printColor("Def %.3e; Res %.1f"%(defocus, avgres), "cyan")
			resVals.append(avgres)
			if avgres < bestres:
				bestdef = defocus
				bestres = avgres

		pyplot.clf()
		pyplot.plot(1.0e6/numpy.power(invGuesses,2), resVals, "o")
		#pyplot.axis('auto')
		#pyplot.ylim(ymin=5, ymax=80)
		pyplot.yscale('log')
		pyplot.show()

		zavg = (self.ctfvalues['defocus2']+self.ctfvalues['defocus1'])/2.0
		zdiff = self.ctfvalues['defocus2'] - self.ctfvalues['defocus1']
		newzdiff = zdiff*bestdef/zavg
		self.ctfvalues['defocus1'] = bestdef - newzdiff/2.
		self.ctfvalues['defocus2'] = bestdef + newzdiff/2.

		return bestdef

	#---------------------------------------
	def onFindRoots(self, evt):
		"""
		takes a normalized power spectra and attempts to find its roots
		and use the roots to estimate the defocus
		"""
		t0 = time.time()

		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=False)

		if PSDarray.min() > 0:
			dialog = wx.MessageDialog(self.frame, "Power spectra needs to cross zero",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		newzavg = findroots.estimateDefocus(raddata, PSDarray, cs=self.cs, wavelength=self.wavelength, 
			amp_con=self.ctfvalues['amplitude_contrast'], mindef=self.mindef, maxdef=self.maxdef)

		zavg = (self.ctfvalues['defocus2']+self.ctfvalues['defocus1'])/2.0
		zdiff = self.ctfvalues['defocus2'] - self.ctfvalues['defocus1']
		newzdiff = zdiff*newzavg/zavg
		self.ctfvalues['defocus1'] = newzavg - newzdiff/2.
		self.ctfvalues['defocus2'] = newzavg + newzdiff/2.

	#---------------------------------------
	def onFindAstig(self, evt):
		"""
		find astigmatism
		"""
		t0 = time.time()

		normPSD = self.panel.numericdata

		#radial_array, angle_array, normPSD = self.getTwoDProfile()
		zavg = (self.ctfvalues['defocus2']+self.ctfvalues['defocus1'])/2.0
		#res = self.onGetResolution(evt)

		self.ellipseParams = findastig.findAstigmatism(normPSD, self.freq, zavg, None, self.ctfvalues)

		self.convertEllipseToCtf(node=4)

		return


	#---------------------------------------
	def onFixAmpContrast(self, evt):
		"""
		fix amp contrast < 0 or amp contrast > 0.3, by adjusting defocus
		"""
		t0 = time.time()

		if self.ctfvalues['amplitude_contrast'] > self.minAmpCon and self.ctfvalues['amplitude_contrast'] < self.maxAmpCon:
			return

		newdefocus = (self.ctfvalues['defocus2']+self.ctfvalues['defocus1'])/2.0 
		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=False)

		if self.checkNormalized(msg=False) is True:
			print "using limits from resolution profile"
			### get the data
			peaks = ctftools.getCtfExtrema(newdefocus, self.freq*1e10, self.ctfvalues['cs'], 
				self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'], numzeros=250, zerotype="peak")
			ctffitdata = genctf.generateCTF1d(raddata*1e10, focus=newdefocus, cs=self.ctfvalues['cs'],
				volts=self.ctfvalues['volts'], ampconst=self.ctfvalues['amplitude_contrast'], failParams=False)
			### get the confidence
			confraddata, confdata = ctfres.getCorrelationProfile(raddata, PSDarray, ctffitdata, peaks, self.freq)
			### get the weights
			weights, lowerbound, upperbound = ctfres.getWeightsForXValues(raddata, confraddata, confdata)
		if weights is None or len(weights) < 10 or 1/raddata[upperbound] > 12:
			lowerbound = numpy.searchsorted(raddata, 1/30.)
			upperbound = numpy.searchsorted(raddata, 1/8.)		

		bad = True
		olddef1 = self.ctfvalues['defocus1']
		olddef2 = self.ctfvalues['defocus2']
		count = 0
		while count < 20:
			count += 1
			amplitudecontrast = sinefit.refineAmplitudeContrast(raddata[lowerbound:upperbound]*1e10, newdefocus, 
				PSDarray[lowerbound:upperbound], self.ctfvalues['cs'], self.wavelength, msg=False)
			if amplitudecontrast is None:
				apDisplay.printWarning("FAILED to fix amplitude contrast")
				self.ctfvalues['defocus1'] = olddef1
				self.ctfvalues['defocus2'] = olddef2
				return
			elif amplitudecontrast < self.minAmpCon:
				apDisplay.printColor("Amp Cont: %.3f too small, decrease defocus %.3e"%
					(amplitudecontrast, newdefocus), "blue")
				scaleFactor = 0.99 - abs(amplitudecontrast)/5.
				newdefocus = newdefocus*scaleFactor
			elif amplitudecontrast > self.maxAmpCon:
				apDisplay.printColor("Amp Cont: %.3f too large, increase defocus %.3e"%
					(amplitudecontrast, newdefocus), "cyan")
				scaleFactor = 1.01 + (amplitudecontrast - 0.5)/5.
				newdefocus = newdefocus*scaleFactor
			else:
				apDisplay.printColor("Amp Cont: %.3f in range!!!  defocus %.3e"%
					(amplitudecontrast, newdefocus), "green")
				avgres = self.onGetResolution(evt, meandefocus=newdefocus)
				self.ctfvalues['amplitude_contrast'] = amplitudecontrast
				break

			avgres = self.onGetResolution(evt, meandefocus=newdefocus)
			if avgres < self.bestres:
				defocus = newdefocus

		if count > 20:
			apDisplay.printWarning("FAILED to fix amplitude contrast")
			self.ctfvalues['defocus1'] = olddef1
			self.ctfvalues['defocus2'] = olddef2
			if self.ctfvalues['amplitude_contrast'] > self.maxAmpCon:
				self.ctfvalues['amplitude_contrast'] = self.maxAmpCon
			elif self.ctfvalues['amplitude_contrast'] < self.minAmpCon:
				self.ctfvalues['amplitude_contrast'] = self.minAmpCon
			return

		zavg = (self.ctfvalues['defocus2']+self.ctfvalues['defocus1'])/2.0
		zdiff = self.ctfvalues['defocus2'] - self.ctfvalues['defocus1']
		newzdiff = zdiff*newdefocus/zavg
		self.ctfvalues['defocus1'] = newdefocus - newzdiff/2.
		self.ctfvalues['defocus2'] = newdefocus + newzdiff/2.

		return

	#---------------------------------------
	def onRefineAmpContrast(self, evt):
		t0 = time.time()
		if not 'defocus2' in self.ctfvalues.keys():
			dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		self.onGetResolution(evt, show=False)

		meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])

		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=False)
		# convert to meters
		s = raddata*1e10
		thirtyindex = numpy.searchsorted(raddata, 1/30.)
		tenindex = numpy.searchsorted(raddata, 1/8.)

		weights = None
		if self.checkNormalized(msg=False) is True:
			print "using weights from resolution profile"
			### get the data
			peaks = ctftools.getCtfExtrema(meandefocus, self.freq*1e10, self.ctfvalues['cs'], 
				self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'], numzeros=250, zerotype="peak")
			ctffitdata = genctf.generateCTF1d(raddata*1e10, focus=meandefocus, cs=self.ctfvalues['cs'],
				volts=self.ctfvalues['volts'], ampconst=self.ctfvalues['amplitude_contrast'], failParams=False)
			### get the confidence
			confraddata, confdata = ctfres.getCorrelationProfile(raddata, PSDarray, ctffitdata, peaks, self.freq)
			### get the weights
			weights, firstpoint, lastpoint = ctfres.getWeightsForXValues(raddata, confraddata, confdata)
		if weights is None or len(weights) < 10 or 1/raddata[lastpoint] > 12:
			print "weighting to 30-8 range"
			weights = numpy.zeros(raddata.shape, dtype=numpy.float64)
			firstpoint = numpy.searchsorted(raddata, 1/30.)
			lastpoint = numpy.searchsorted(raddata, 1/8.)		
			weights[firstpoint:lastpoint] = 1
	
		amplitudecontrast = sinefit.refineAmplitudeContrast(s[firstpoint:lastpoint], meandefocus, 
			PSDarray[firstpoint:lastpoint], self.ctfvalues['cs'], self.wavelength, 
			weights[firstpoint:lastpoint])

		if amplitudecontrast is None:
			apDisplay.printWarning("onRefineAmpContrast failed")
			return

		apDisplay.printColor("amplitude contrast change from %.4f to %.4f"
			%(self.ctfvalues['amplitude_contrast'], amplitudecontrast), "cyan")
		self.ctfvalues['amplitude_contrast'] = amplitudecontrast

		self.onFixAmpContrast(evt)

		self.panel.UpdateDrawing()
		apDisplay.printColor("Refine Amplitude Contrast complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onRefineCTFOneDimension(self, evt):
		t0 = time.time()
		if not 'defocus2' in self.ctfvalues.keys():
			dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		self.onGetResolution(evt, show=False)

		oldzavg = (self.ctfvalues['defocus2']+self.ctfvalues['defocus1'])/2.0

		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=False)
		# convert to meters
		s = raddata*1e10
		thirtyindex = numpy.searchsorted(raddata, 1/30.)
		tenindex = numpy.searchsorted(raddata, 1/8.)

		weights = None
		if self.checkNormalized(msg=False) is True:
			print "using weights from resolution profile"
			### get the data
			peaks = ctftools.getCtfExtrema(oldzavg, self.freq*1e10, self.ctfvalues['cs'], 
				self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'], numzeros=250, zerotype="peak")
			ctffitdata = genctf.generateCTF1d(raddata*1e10, focus=oldzavg, cs=self.ctfvalues['cs'],
				volts=self.ctfvalues['volts'], ampconst=self.ctfvalues['amplitude_contrast'], failParams=False)
			### get the confidence
			confraddata, confdata = ctfres.getCorrelationProfile(raddata, PSDarray, ctffitdata, peaks, self.freq)
			### get the weights
			weights, firstpoint, lastpoint = ctfres.getWeightsForXValues(raddata, confraddata, confdata)
		if weights is None or len(weights) < 10 or 1/raddata[lastpoint] > 12:
			print "weighting to 30-8 range"
			weights = numpy.zeros(raddata.shape, dtype=numpy.float64)
			firstpoint = numpy.searchsorted(raddata, 1/30.)
			lastpoint = numpy.searchsorted(raddata, 1/8.)		
			weights[firstpoint:lastpoint] = 1

		results = sinefit.refineCTFOneDimension(s[firstpoint:lastpoint], 
			self.ctfvalues['amplitude_contrast'], oldzavg, PSDarray[firstpoint:lastpoint], 
			self.ctfvalues['cs'], self.wavelength, weights[firstpoint:lastpoint])

		if results is None:
			apDisplay.printWarning("onRefineCTFOneDimension failed")
			return

		ampcon = results[0]
		zavg = results[1]

		apDisplay.printColor("amplitude contrast change from %.4f to %.4f"
			%(self.ctfvalues['amplitude_contrast'], ampcon), "magenta")

		self.ctfvalues['amplitude_contrast'] = ampcon

		def1ratio = self.ctfvalues['defocus1']/oldzavg
		def2ratio = self.ctfvalues['defocus2']/oldzavg
		self.ctfvalues['defocus1'] = zavg * def1ratio
		self.ctfvalues['defocus2'] = zavg * def2ratio

		apDisplay.printColor("defocus change from %.3e to %.3e"
			%(oldzavg, zavg), "magenta")

		self.onFixAmpContrast(evt)

		self.panel.UpdateDrawing()
		apDisplay.printColor("Refine CTF 1D complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onRefineCTFOLD(self, evt):
		t0 = time.time()
		if not 'defocus2' in self.ctfvalues.keys():
			dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		self.onGetResolution(evt, show=False)

		radial_array, angle_array, normPSD = self.getTwoDProfile()

		radial_array = radial_array.ravel()
		angle_array = angle_array.ravel()
		normPSD = normPSD.ravel()

		sortind = numpy.argsort(radial_array)
		radial_array = radial_array[sortind]
		angle_array = angle_array[sortind]
		normPSD = normPSD[sortind]

		z1 = self.ctfvalues['defocus1']
		z2 = self.ctfvalues['defocus2']
		cs = self.ctfvalues['cs']
		wv = self.wavelength
		ampcon = self.ctfvalues['amplitude_contrast']
		## ellip angle is positive toward y-axis, ctf angle is negative toward y-axis
		ellipangle = -self.ctfvalues['angle_astigmatism']

		weights = None
		if self.checkNormalized(msg=False) is True:
			print "using weights from resolution profile"
			### get the data
			oldzavg = (self.ctfvalues['defocus2']+self.ctfvalues['defocus1'])/2.0
			pixelrdata, raddata, PSDarray = self.getOneDProfile(full=False)
			peaks = ctftools.getCtfExtrema(oldzavg, self.freq*1e10, self.ctfvalues['cs'], 
				self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'], numzeros=250, zerotype="peak")
			ctffitdata = genctf.generateCTF1d(raddata*1e10, focus=oldzavg, cs=self.ctfvalues['cs'],
				volts=self.ctfvalues['volts'], ampconst=self.ctfvalues['amplitude_contrast'], failParams=False)
			### get the confidence
			confraddata, confdata = ctfres.getCorrelationProfile(raddata, PSDarray, ctffitdata, peaks, self.freq)
			### get the weights
			weights, firstpoint, lastpoint = ctfres.getWeightsForXValues(raddata, confraddata, confdata)
		if weights is None or len(weights) < 10 or 1/raddata[lastpoint] > 12:
			print "weighting to 30-8 range"
			weights = numpy.zeros(radial_array.shape, dtype=numpy.float64)
			firstpoint = numpy.searchsorted(radial_array, 1/30.)
			lastpoint = numpy.searchsorted(radial_array, 1/8.)
			weights[firstpoint:lastpoint] = 1

		values = sinefit.refineCTF(radial_array[firstpoint:lastpoint]*1e10, angle_array[firstpoint:lastpoint], 
			ampcon, z1, z2, ellipangle, normPSD[firstpoint:lastpoint], cs, wv, weights[firstpoint:lastpoint])

		if values is None:
			apDisplay.printWarning("onRefineCTF failed")
			return

		ampcon, z1, z2, ellipangle = values
		self.ctfvalues['defocus1'] = z1
		self.ctfvalues['defocus2'] = z2
		self.ctfvalues['amplitude_contrast'] = ampcon
		## ellip angle is positive toward y-axis, ctf angle is negative toward y-axis
		self.ctfvalues['angle_astigmatism'] = -ellipangle

		self.onFixAmpContrast(evt)

		self.panel.UpdateDrawing()
		apDisplay.printColor("Refine CTF complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onRefineCTF(self, evt):
		#self.onUpdate(None)
		t0 = time.time()
		if not 'defocus2' in self.ctfvalues.keys():
			dialog = wx.MessageDialog(self.frame, "Need a defocus estimate first.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		resValue = self.onGetResolution(evt, show=False)

		self.refinectf_dialog.def1Value.SetValue(round(self.ctfvalues['defocus1']*1e6,3)/1e6)
		self.refinectf_dialog.def2Value.SetValue(round(self.ctfvalues['defocus2']*1e6,3)/1e6)
		self.refinectf_dialog.ampconValue.SetValue(round(self.ctfvalues['amplitude_contrast'],4))
		self.refinectf_dialog.angleValue.SetValue(round(self.ctfvalues['angle_astigmatism'],4))
		self.refinectf_dialog.reslabel.SetLabel(str(round(resValue,5)))

		self.refinectf_dialog.Show()
		#values are then modified, if the user selected apply in tiltDialog

		apDisplay.printColor("Refine CTF complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onSubt2dBoxFilter(self, evt):
		t0 = time.time()
		imagedata = self.panel.numericdata
		imagestat.printImageInfo(imagedata)

		boxsize = min(128, min(imagedata.shape)/10)

		boxfilter = ndimage.uniform_filter(imagedata, 128)

		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=True)
		imagestat.printImageInfo(PSDarray)
		pixelrdata, boxdata = ctftools.ellipticalAverage(boxfilter,
			self.ellipratio, self.ellipangle, self.ringwidth, full=True)
		imagestat.printImageInfo(boxdata)

		pyplot.clf()
		pyplot.subplot(1,2,1)
		xdata = (raddata)**2
		pyplot.plot(xdata, PSDarray, 'k-', alpha=0.75)
		pyplot.plot(xdata, boxdata, 'r-',)
		pyplot.xlim(xmax=xdata.max())
		#pyplot.ylim(ymin=PSDarray.min(), ymax=PSDarray.max())
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
		self.panel.UpdateDrawing()

		imagestat.printImageInfo(normaldata)
		apDisplay.printColor("Subtact 2D Box complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onCannyEdge(self, evt):
		t0 = time.time()
		print "onCannyEdge"
		#if self.checkNormalized() is False:
		#	return

		minpeaks = ctftools.getCtfExtrema(self.maxdef, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], 0.0,
			numzeros=2, zerotype="peaks")
		minEdgeRadius = minpeaks[0]

		maxvalleys = ctftools.getCtfExtrema(self.mindef, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], 0.0,
			numzeros=2, zerotype="valleys")
		maxEdgeRadius = maxvalleys[0]

		imagedata = self.panel.numericdata

		edges = canny.canny_edges(imagedata, low_thresh=0.01,
			minEdgeRadius=minEdgeRadius, maxEdgeRadius=maxEdgeRadius)
		#minedges=2500, maxedges=15000,
		invedges = numpy.fliplr(numpy.flipud(edges))
		self.edgeMap = numpy.logical_and(edges, invedges)
		edges = self.edgeMap * (imagedata.max()/self.edgeMap.max())
		imagedata = imagedata + 2*edges
		self.panel.setImage(imagedata)
		apDisplay.printColor("Canny Edge complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onRANSAC(self, evt):
		t0 = time.time()
		print "onRANSAC"
		if self.edgeMap is None:
			return

		edgeThresh = 3
		ellipseParams = ransac.ellipseRANSAC(self.edgeMap, edgeThresh)
		if ellipseParams is None:
			return

		fitEllipse1 = ransac.generateEllipseRangeMap2(ellipseParams, edgeThresh, self.edgeMap.shape)
		fitEllipse2 = ransac.generateEllipseRangeMap2(ellipseParams, edgeThresh*3, self.edgeMap.shape)
		outlineEllipse = fitEllipse2 - fitEllipse1
		# image is draw upside down
		#outlineEllipse = numpy.flipud(outlineEllipse)

		imagedata = self.panel.numericdata
		imagedata = imagedata + 0.5*outlineEllipse*imagedata.max()
		self.panel.setImage(imagedata)

		self.ellipseParams = ellipseParams

		self.convertEllipseToCtf(node=3)

		apDisplay.printColor("RANSAC complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onClipData(self, evt):
		t0 = time.time()
		#if self.checkNormalized() is False:
		#	return
		imagedata = self.panel.numericdata
		imagedata = numpy.where(imagedata > 2.0, 2.0, imagedata)
		imagedata = numpy.where(imagedata < -1.0, -1.0, imagedata)
		self.panel.setImage(imagedata)
		apDisplay.printColor("Clip Data complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return


	#---------------------------------------
	def onFlatCenter(self, evt):
		t0 = time.time()
		if self.flatcutrad is None:
			self.flatcutrad = 1/150.
		else:
			self.flatcutrad *= 1.05
		## get the data
		imagedata = self.panel.numericdata

		## create a grid of distance from the center
		shape = imagedata.shape
		xhalfshape = shape[0]/2.0
		x = numpy.arange(-xhalfshape, xhalfshape, 1) + 0.5
		yhalfshape = shape[1]/2.0
		y = numpy.arange(-yhalfshape, yhalfshape, 1) + 0.5
		xx, yy = numpy.meshgrid(x, y)
		# get radial component
		pixelradial = xx**2 + yy**2 - 0.5
		angstromradial = numpy.sqrt(pixelradial)*self.freq

		#filter the data in the array
		centerpts1 = numpy.where(angstromradial < self.flatcutrad*1.25, True, False)
		centerpts2 = numpy.where(angstromradial > self.flatcutrad, True, False)
		ringdata = imagedata[numpy.logical_and(centerpts1,centerpts2)]
		cutval = numpy.median(ringdata)
		imagedata = numpy.where(angstromradial < self.flatcutrad, cutval, imagedata)

		self.panel.setImage(imagedata)
		apDisplay.printColor("Flat Center complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onDeleteCorners(self, evt):
		t0 = time.time()
		## get the data
		imagedata = self.panel.numericdata

		## create a grid of distance from the center
		shape = imagedata.shape
		xhalfshape = shape[0]/2.0
		x = numpy.arange(-xhalfshape, xhalfshape, 1) + 0.5
		yhalfshape = shape[1]/2.0
		y = numpy.arange(-yhalfshape, yhalfshape, 1) + 0.5
		xx, yy = numpy.meshgrid(x, y)
		# get radial component
		pixelradial = xx**2 + yy**2 - 0.5

		#filter the data in the array
		outerEdgeDist = pixelradial[shape[0]/2-2, 2]
		cornerdata = imagedata[numpy.where(pixelradial > outerEdgeDist)]
		cornerdata = numpy.where(cornerdata < 0, 0, cornerdata)
		cutval = (cornerdata.max() + cornerdata.mean())/2.0
		if cutval < 0:
			cutval = 0
		imagedata = numpy.where(pixelradial > outerEdgeDist, cutval, imagedata)

		self.panel.setImage(imagedata)
		apDisplay.printColor("Delete Corners complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onFullTriSectionNormalize(self, evt):
		t0 = time.time()
		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=False)
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
			valleydata = ctfnoise.peakExtender(raddata, PSDarray, valleyradii, "below")
		else:
			valleydata = ndimage.minimum_filter(PSDarray, 4)

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
		normexpPSDarray2d = numpy.exp(imagedata2d) - numpy.exp(noisedata2d)
		normlogPSDarray2d = numpy.log(numpy.where(normexpPSDarray2d<1, 1, normexpPSDarray2d))

		self.panel.setImage(normlogPSDarray2d)
		newpixx, newx, normlogPSDarray = self.getOneDProfile(full=False)

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
			peakdata = ctfnoise.peakExtender(raddata, normlogPSDarray, peakradii, "above")
		else:
			peakdata = ndimage.maximum_filter(normlogPSDarray, 4)

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
		normnormexpPSDarray2d = normexpPSDarray2d / numpy.exp(envelopdata2d)

		self.panel.setImage(normnormexpPSDarray2d)
		newpixx, newx, normnormexpPSDarray = self.getOneDProfile(full=False)

		pyplot.clf()
		pyplot.subplot(3,1,1)
		raddatasq = raddata**2
		pyplot.plot(raddatasq, normnormexpPSDarray, 'k.',)
		a = pyplot.plot(raddatasq, PSDarray, 'k-', alpha=0.5)
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
		#pyplot.ylim(ymin=noisedata.min(), ymax=PSDarray[part1start:].max())

		pyplot.subplot(3,1,2)
		a = pyplot.plot(raddatasq, normlogPSDarray, 'k.',)
		a = pyplot.plot(raddatasq, normlogPSDarray, 'k-', alpha=0.5)
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
		#pyplot.ylim(ymin=normlogPSDarray[part1start:].min(), ymax=envelopdata.max())

		pyplot.subplot(3,1,3)
		pyplot.plot(raddatasq, normnormexpPSDarray, 'k.',)
		pyplot.plot(raddatasq, normnormexpPSDarray, 'k-', alpha=0.5)
		pyplot.xlim(xmax=raddatasq.max())

		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		apDisplay.printColor("TriSection complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onSubtFitValleys(self, evt):
		t0 = time.time()
		meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])

		valleyradii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=250, zerotype="valleys")
		extrema = numpy.array(valleyradii, dtype=numpy.float64)*self.freq

		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=True)
		extremedata = ctfnoise.peakExtender(raddata, PSDarray, extrema, "below")
		extremedata = ndimage.gaussian_filter1d(extremedata, 1)

		imagedata = self.panel.numericdata
		extreme2d = ctftools.unEllipticalAverage(pixelrdata, extremedata,
			self.ellipratio, self.ellipangle, imagedata.shape)

		pyplot.clf()
		raddatasq = raddata**2
		maxshow = int(raddatasq.shape[0]/math.sqrt(2))
		pyplot.plot(raddatasq[:maxshow], PSDarray[:maxshow], 'k-', )
		pyplot.plot(raddatasq[:maxshow], PSDarray[:maxshow], 'k.', )
		pyplot.plot(raddatasq[:maxshow], extremedata[:maxshow], 'b-', )
		for radius in valleyradii:
			index = numpy.searchsorted(raddata, radius*self.freq)
			if index > maxshow:
				break
			pyplot.axvline(x=raddatasq[index], linewidth=1, color="cyan", alpha=0.95)
		pyplot.xlim(xmin=raddatasq[0], xmax=raddatasq[maxshow])
		#pyplot.ylim(ymin=-0.05, ymax=1.05)
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		normaldata = imagedata - extreme2d
		#normaldata = numpy.where(normaldata < -0.2, -0.2, normaldata)
		self.panel.setImage(normaldata)
		apDisplay.printColor("Subtract Valleys complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onNormFitPeaks(self, evt):
		t0 = time.time()
		meandefocus = math.sqrt(self.ctfvalues['defocus1']*self.ctfvalues['defocus2'])

		peakradii = ctftools.getCtfExtrema(meandefocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=250, zerotype="peaks")
		extrema = numpy.array(peakradii, dtype=numpy.float64)*self.freq

		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=True)
		extremedata = ctfnoise.peakExtender(raddata, PSDarray, extrema, "above")
		extremedata = ndimage.gaussian_filter1d(extremedata, 1)

		imagedata = self.panel.numericdata
		extreme2d = ctftools.unEllipticalAverage(pixelrdata, extremedata,
			self.ellipratio, self.ellipangle, imagedata.shape)

		pyplot.clf()
		raddatasq = raddata**2
		maxshow = int(raddatasq.shape[0]/math.sqrt(2))
		pyplot.plot(raddatasq[:maxshow], PSDarray[:maxshow], 'k-', )
		pyplot.plot(raddatasq[:maxshow], PSDarray[:maxshow], 'k.', )
		pyplot.plot(raddatasq[:maxshow], extremedata[:maxshow], 'b-', )
		for radius in peakradii:
			index = numpy.searchsorted(raddata, radius*self.freq)
			if index > maxshow:
				break
			pyplot.axvline(x=raddatasq[index], linewidth=1, color="gold", alpha=0.95)
		pyplot.xlim(xmin=raddatasq[0], xmax=raddatasq[maxshow])
		#pyplot.ylim(ymin=-0.05, ymax=1.05)
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

		normaldata = imagedata / extreme2d
		#normaldata = numpy.where(normaldata > 1.2, 1.2, normaldata)
		#normaldata = numpy.where(normaldata < -0.2, -0.2, normaldata)
		self.panel.setImage(normaldata)
		apDisplay.printColor("Normalize Peaks complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")
		return

	#---------------------------------------
	def onShowPlot(self, evt):
		t0 = time.time()
		pixelrdata, raddata, PSDarray = self.getOneDProfile(full=False)
		pixelrdata, raddatafull, PSDarrayfull = self.getOneDProfile(full=True)

		imagestat.printImageInfo(PSDarray)

		pyplot.clf()
		pyplot.plot(raddatafull**2, PSDarrayfull, 'r--', alpha=0.5)
		pyplot.plot(raddata**2, PSDarray, 'k-',)
		fullmax = (raddatafull**2).max()
		normmax = (raddata**2).max()
		usemax = (fullmax + normmax)/2.0
		pyplot.xlim(xmax=usemax)
		pyplot.ylim(ymin=PSDarray[5:].min(), ymax=PSDarray[5:].max())
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()
		apDisplay.printColor("Show plot complete", "cyan")
		return

	#---------------------------------------
	def copyDataToAppionLoop(self):
		self.appionloop.ctfvalues = {}
		#paramlist = ['angle_astigmatism', 'amplitude_contrast', 'defocus1', 'defocus2']
		self.appionloop.ctfvalues.update(self.ctfvalues)
		#print self.appionloop.ctfvalues
		## Cs in mm
		self.appionloop.ctfvalues['cs'] *= 1000
		## some shift in angle astig, cannot explain at moment
		#self.appionloop.ctfvalues['angle_astigmatism'] += 90
		self.appionloop.assess = self.assess
		self.ctfvalues = {}

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
		self.assessnone.SetBackgroundColour(wx.Colour(200,200,0))
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
		self.assesskeep.SetBackgroundColour(wx.Colour(0,200,0))
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
		self.assessreject.SetBackgroundColour(wx.Colour(200,0,0))
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

	#====================================
	#====================================
	def printBestValues(self):
		if self.bestvalues is None:
			return
		avgRes = self.bestres/2.0
		defocus = self.bestvalues['defocus']
		ampCon = self.bestvalues['amplitude_contrast']
		if self.bestellipse is None:
			apDisplay.printColor("Prev Best :: avgRes=%.1f :: def=%.2e, NO ASTIG, ampCon=%.2f"
				%(avgRes, defocus, ampCon), "green")
		else:
			ratio = (self.bestellipse['a']/self.bestellipse['b'])**2
			angle = -math.degrees(self.bestellipse['alpha'])
			apDisplay.printColor("Prev Best :: avgRes=%.1f :: def=%.2e, ratio=%.2f, ang=%.1f, ampCon=%.2f"
				%(avgRes, defocus, ratio, angle, ampCon), "green")
		return

	#---------------------------------------
	def onCheckFinalRes(self, evt):
		self.printBestValues()
		newctdata = copy.deepcopy(self.ctfvalues)
		newctdata['cs'] *= 1000
		fftpath = os.path.join(self.appionloop.fftsdir, apDisplay.short(self.imgdata['filename'])+'.powerspec.mrc')
		if os.path.isfile(fftpath) and fftpath in self.appionloop.freqdict.keys():
			fftfreq = self.appionloop.freqdict[fftpath]
		else:
			return
		ctfdisplaydict = ctfdisplay.makeCtfImages(self.imgdata, newctdata, fftpath, fftfreq, twod=False)
		ctfvalue = ctfdb.getBestCtfByResolution(self.imgdata, msg=True)
		apDisplay.printColor("Resolution values %.2f and %.2f"
				%(ctfdisplaydict['res50'], ctfdisplaydict['res80']), "magenta")
		#avgRes = (ctfdisplaydict['res50'] + ctfdisplaydict['res80'])/2.0
		#apDisplay.printColor("Curr Val :: avgRes=%.1f :: def=%.2e, ratio=%.2f, ang=%.1f, ampCon=%.2f"
		#	%(avgRes, defocus, ratio, angle, ampCon), "green")

		return

	#---------------------------------------
	def onNext(self, evt):
		if not self.appionloop:
			dialog = wx.MessageDialog(self.frame,
				"Are you sure you want to Quit?", 
				'Quit?', wx.NO|wx.YES|wx.ICON_QUESTION)
			if dialog.ShowModal() == wx.ID_NO:
				dialog.Destroy()
				return
			dialog.Destroy()

		if self.ctfvalues['amplitude_contrast'] < self.minAmpCon or self.ctfvalues['amplitude_contrast'] > self.maxAmpCon:
			dialog = wx.MessageDialog(self.frame, 
				"Please fix amplitude contrast, invalid value (%.2f)."%(self.ctfvalues['amplitude_contrast']),
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		self.submit = True

		self.flatcutrad = 1/150.

		if self.appionloop:
			self.copyDataToAppionLoop()
			self.Exit()
		else:
			wx.Exit()

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
		self.ctfrundata = None
		opdir = os.path.join(self.params['rundir'], "opimages")
		if not os.path.isdir(opdir):
			os.mkdir(opdir)
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
		time.sleep(0.1)
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

	#======================
	def commitToDatabase(self, imgdata):
		"""
		information needed to commit
		* defocus 1
		* defocus 2
		* angle astig
		* amplitude contrast
		all stored in self.ctfvalues
		"""
		if self.app.submit is False:
			print "main window was closed, quitting program"
			sys.exit(1)

		if self.assess != self.assessold and self.assess is not None:
			#imageaccessor run is always named run1
			apDatabase.insertImgAssessmentStatus(imgdata, 'run1', self.assess)

		if ( not 'defocus1' in self.ctfvalues 
				or self.ctfvalues['defocus1'] is None
				or not 'defocus2' in self.ctfvalues
				or self.ctfvalues['defocus2'] is None
				or not 'amplitude_contrast' in self.ctfvalues
				or self.ctfvalues['amplitude_contrast'] is None
				or not 'angle_astigmatism' in self.ctfvalues
				or self.ctfvalues['angle_astigmatism'] is None):
			return False
		
		if self.ctfrundata is None:
			self.insertRunData()

		fftpath = os.path.join(self.fftsdir, apDisplay.short(imgdata['filename'])+'.powerspec.mrc')
		if os.path.isfile(fftpath) and fftpath in self.freqdict.keys():
			freq = self.freqdict[fftpath]
		else:
			fftpath = None
			freq = None

		ctfinsert.validateAndInsertCTFData(imgdata, self.ctfvalues, self.ctfrundata, 
			self.params['rundir'], fftpath, freq)
		#p = Process(target=ctfinsert.validateAndInsertCTFData, 
		#	args=(imgdata, self.ctfvalues, self.ctfrundata, self.params['rundir']))
		#p.start()
		#p.join()
		return True

	#======================
	def reprocessImage(self, imgdata):
		"""
		Returns
		True, if an image should be reprocessed
		False, if an image was processed and should NOT be reprocessed
		None, if image has not yet been processed
		e.g. a confidence less than 80%
		"""
		if self.params['reprocess'] is None:
			return True

		ctfvalue = ctfdb.getBestCtfByResolution(imgdata, msg=False)
		#print ctfvalue

		if ctfvalue is None:
			return True

		avgres = (ctfvalue['resolution_80_percent'] + ctfvalue['resolution_50_percent'])/2.0
		print "avgres %.3f -- %s"%(avgres, apDisplay.short(imgdata['filename']))

		if avgres < self.params['reprocess']:
			return False
		return True

	#======================
	def insertRunData(self):
		runq=appiondata.ApAceRunData()
		runq['name']    = self.params['runname']
		runq['session'] = self.getSessionData()
		runq['hidden']  = False
		runq['path']    = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq.insert()
		self.ctfrundata = runq

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
		self.parser.add_option("--mindef", dest="mindef", type="float", default=0.5e-6,
			help="minimum defocus to search (in meters; default = 0.5e-6)")
		self.parser.add_option("--maxdef", dest="maxdef", type="float", default=5.0e-6,
			help="maximum defocus to search (in meters; default = 5.0e-6)")

		self.samples = ('stain','ice')
		self.parser.add_option("--sample", dest="sample",
			default="ice", type="choice", choices=self.samples,
			help="sample type: "+str(self.samples), metavar="TYPE")

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
			if self.reprocessImage(imgdata) is False:
				sys.stderr.write("image %d of %d -- no reprocess\n"%(count, len(self.imgtree)))
				continue
			count += 1
			self.fftsdir
			fftpath = os.path.join(self.fftsdir, apDisplay.short(imgdata['filename'])+'.powerspec.mrc')
			#if self.params['continue'] is True and os.path.isfile(fftpath) and fftpath in self.freqdict.keys():
			if os.path.isfile(fftpath) and fftpath in self.freqdict.keys():
				sys.stderr.write("image %d of %d -- finished\n"%(count, len(self.imgtree)))
				#print "already processed: ",apDisplay.short(imgdata['filename'])
			else:
				if os.path.isfile(fftpath):
					os.remove(fftpath)
				sys.stderr.write("image %d of %d\n"%(count, len(self.imgtree)))
				self.processAndSaveFFT(imgdata, fftpath)
				self.saveFreqFile()

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
		fftarray, freq = ctfpower.power(imgarray, apix, mask_radius=0.5, fieldsize=self.params['fieldsize'])
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


		### reset important values
		self.app.bestres = 1e10
		self.app.bestvalues = None
		self.app.bestellipse = None

		self.app.imgdata = imgdata
		self.app.volts = imgdata['scope']['high tension']
		self.app.ringwidth = self.params['ringwidth']
		self.app.mindef = self.params['mindef']
		self.app.maxdef = self.params['maxdef']
		self.app.submit = False
		self.app.wavelength = ctftools.getTEMLambda(self.app.volts)
		self.app.cs = apInstrument.getCsValueFromSession(self.getSessionData())*1e-3
		self.app.ctfvalues.update({
			'volts': self.app.volts,
			'cs': self.app.cs,
			'apix': self.app.apix,
		})

		#set vital stats
		self.app.vitalstats.SetLabel("Vital Stats: Image "+str(self.stats['count'])
			+" of "+str(self.stats['imagecount'])+", "
			+" image name: "+imgdata['filename'])
		#run the ctf
		self.ctfvalues = {}
		self.app.MainLoop()

		return

#---------------------------------------
#---------------------------------------
if __name__ == '__main__':
	imgLoop = ManualCTF()
	imgLoop.run()
	#a = imagefile.readJPG("/data01/appion/11jul05a/extract/manctf2/"
	#	+"11jul05a_11jan06b_00002sq_00002hl_v01_00002en2.fft.jpg")
