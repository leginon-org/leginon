import wx
import os
import math
import glob
import numpy
import pprint
from leginon.gui.wx.Entry import FloatEntry, IntEntry, EVT_ENTRY
try:
	import radermacher
except:
	print "using slow tilt angle calculator"
	import slowmacher as radermacher
from appionlib import apDog
from appionlib import apFile
from appionlib import apPeaks
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
from appionlib.apTilt import apTiltTransform

##
##
## Fit Theta Dialog
##
##

class FitThetaDialog(wx.Dialog):
	#==================
	def __init__(self, parent):
		self.parent = parent
		self.theta = self.parent.data['theta']
		wx.Dialog.__init__(self, self.parent.frame, -1, "Measure Tilt Angle, Theta")

		inforow = wx.FlexGridSizer(3, 3, 15, 15)
		thetastr = ("****** %3.3f ******" % self.theta)
		label = wx.StaticText(self, -1, "Current tilt angle:  ",
			style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.tiltvalue = wx.StaticText(self, -1, thetastr, style=wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)
		#self.tiltvalue = FloatEntry(self, -1, allownone=True, chars=5, value=thetastr)
		label3 = wx.StaticText(self, -1, "degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.tiltvalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		inforow.Add(label3, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		arealimstr = str(int(self.parent.data['arealim']))
		label = wx.StaticText(self, -1, "Minimum Triangle Area:  ",
			style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.arealimit = IntEntry(self, -1, allownone=False, chars=8, value=arealimstr)
		label2 = wx.StaticText(self, -1, "square pixels", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.arealimit, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		label = wx.StaticText(self, -1, "Triangles Used:  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.trilabel1 = wx.StaticText(self, -1, "  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.trilabel2 = wx.StaticText(self, -1, "  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		inforow.Add(self.trilabel1, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		inforow.Add(self.trilabel2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.canceltiltang = wx.Button(self, wx.ID_CANCEL, '&Cancel')
		self.applytiltang = wx.Button(self,  wx.ID_APPLY, '&Apply')
		self.runtiltang = wx.Button(self, -1, '&Run')
		self.Bind(wx.EVT_BUTTON, self.onRunTiltAng, self.runtiltang)
		self.Bind(wx.EVT_BUTTON, self.onApplyTiltAng, self.applytiltang)
		buttonrow = wx.GridSizer(1,3)
		buttonrow.Add(self.canceltiltang, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.applytiltang, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.runtiltang, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)

		self.sizer = wx.FlexGridSizer(2,1)
		self.sizer.Add(inforow, 0, wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(buttonrow, 0, wx.EXPAND|wx.ALL, 5)
		self.SetSizerAndFit(self.sizer)

	#==================
	def onRunTiltAng(self, evt):
		arealim  = self.arealimit.GetValue()
		self.parent.data['arealim'] = arealim
		targets1 = self.parent.panel1.getTargets('Picked')
		a1 = self.parent.targetsToArray(targets1)
		targets2 = self.parent.panel2.getTargets('Picked')
		a2 = self.parent.targetsToArray(targets2)
		na1 = numpy.array(a1, dtype=numpy.int32)
		na2 = numpy.array(a2, dtype=numpy.int32)
		self.fittheta = radermacher.tiltang(na1, na2, arealim)
		#pprint.pprint(self.fittheta)
		if self.fittheta and 'wtheta' in self.fittheta:
			self.fittheta['point1'], self.fittheta['point2'] = \
				apTiltTransform.getPointsFromArrays(a1, a2, self.parent.data['shiftx'], self.parent.data['shifty'])
			self.theta = self.fittheta['wtheta']
			self.thetadev = self.fittheta['wthetadev']
			thetastr = ("%3.3f +/- %2.2f" % (self.theta, self.thetadev))
			self.tiltvalue.SetLabel(label=thetastr)
			tristr = apDisplay.orderOfMag(self.fittheta['numtri'])+" of "+apDisplay.orderOfMag(self.fittheta['tottri'])
			self.trilabel1.SetLabel(label=tristr)
			percent = str("%")
			tristr = (" (%3.1f " % (100.0 * self.fittheta['numtri'] / float(self.fittheta['tottri'])))+"%) "
			self.trilabel2.SetLabel(label=tristr)

	#==================
	def onApplyTiltAng(self, evt):
		self.Close()
		self.parent.data['theta'] = self.theta
		self.parent.data['tiltanglefitdata'] = self.fittheta
		self.parent.data['point1'] = self.fittheta['point1']
		self.parent.data['point2'] = self.fittheta['point2']

		self.parent.onUpdate(evt)

##
##
## Fit All Least Squares Dialog
##
##

class FitAllDialog(wx.Dialog):
	#==================
	def __init__(self, parent):
		self.parent = parent
		wx.Dialog.__init__(self, self.parent.frame, -1, "Least Squares Optimization")
		self.lsfit = None

		inforow = wx.FlexGridSizer(5, 4, 15, 15)

		thetastr = "%3.3f" % self.parent.data['theta']
		label = wx.StaticText(self, -1, "Tilt angle (theta):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		#self.tiltvalue = wx.StaticText(self, -1, thetastr, style=wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)
		self.thetavalue = FloatEntry(self, -1, allownone=False, chars=8, value=thetastr)
		label2 = wx.StaticText(self, -1, "degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.thetatog = wx.ToggleButton(self, -1, "Refine")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleTheta, self.thetatog)
		#self.thetavalue.Enable(False)
		#self.thetatog.SetValue(1)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.thetavalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.thetatog, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		gammastr = "%3.3f" % self.parent.data['gamma']
		label = wx.StaticText(self, -1, "Image 1 Rotation (gamma):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.gammavalue = FloatEntry(self, -1, allownone=False, chars=8, value=gammastr)
		label2 = wx.StaticText(self, -1, "degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.gammatog = wx.ToggleButton(self, -1, "Refine")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleGamma, self.gammatog)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.gammavalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.gammatog, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		phistr = "%3.3f" % self.parent.data['phi']
		label = wx.StaticText(self, -1, "Image 2 Rotation (phi):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.phivalue = FloatEntry(self, -1, allownone=False, chars=8, value=phistr)
		label2 = wx.StaticText(self, -1, "degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.phitog = wx.ToggleButton(self, -1, "Refine")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onTogglePhi, self.phitog)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.phivalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.phitog, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		scalestr = "%3.3f" % self.parent.data['scale']
		label = wx.StaticText(self, -1, "Scaling factor:  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.scalevalue = FloatEntry(self, -1, allownone=False, chars=8, value=scalestr)
		label2 = wx.StaticText(self, -1, " ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.scaletog = wx.ToggleButton(self, -1, "Locked")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleScale, self.scaletog)
		self.scalevalue.Enable(False)
		self.scaletog.SetValue(1)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.scalevalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.scaletog, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		shiftxstr = "%3.3f" % self.parent.data['shiftx']
		shiftystr = "%3.3f" % self.parent.data['shifty']
		label = wx.StaticText(self, -1, "Shift (x,y) pixels:  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.shiftxvalue = FloatEntry(self, -1, allownone=False, chars=8, value=shiftxstr)
		self.shiftyvalue = FloatEntry(self, -1, allownone=False, chars=8, value=shiftystr)
		self.shifttog = wx.ToggleButton(self, -1, "Refine")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleShift, self.shifttog)
		#self.shiftxvalue.Enable(False)
		#self.shiftyvalue.Enable(False)
		#self.shifttog.SetValue(1)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.shiftxvalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.shiftyvalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.shifttog, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		summaryrow = wx.GridSizer(1,4)
		label = wx.StaticText(self, -1, "RMSD (pixels):  ", style=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		self.rmsdlabel = wx.StaticText(self, -1, " unknown ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		summaryrow.Add(label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		summaryrow.Add(self.rmsdlabel, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, "Iterations: ", style=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		self.iterlabel = wx.StaticText(self, -1, " none ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		summaryrow.Add(label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		summaryrow.Add(self.iterlabel, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		self.cancelfitall = wx.Button(self, wx.ID_CANCEL, '&Cancel')
		self.applyfitall = wx.Button(self,  wx.ID_APPLY, '&Apply')
		self.runfitall = wx.Button(self, -1, '&Run')
		self.Bind(wx.EVT_BUTTON, self.onRunLeastSquares, self.runfitall)
		self.Bind(wx.EVT_BUTTON, self.onApplyLeastSquares, self.applyfitall)
		buttonrow = wx.GridSizer(1,3)
		buttonrow.Add(self.cancelfitall, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.applyfitall, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.runfitall, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)

		self.sizer = wx.FlexGridSizer(3,1)
		self.sizer.Add(inforow, 0, wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(summaryrow, 0, wx.EXPAND|wx.ALL, 5)
		self.sizer.Add(buttonrow, 0, wx.EXPAND|wx.ALL, 5)
		self.SetSizerAndFit(self.sizer)

		self.onToggleScale(True)

	#==================
	def onToggleTheta(self, evt):
		if self.thetatog.GetValue() is True:
			self.thetavalue.Enable(False)
			self.thetatog.SetLabel("Locked")
		else:
			self.thetavalue.Enable(True)
			self.thetatog.SetLabel("Refine")

	#==================
	def onToggleGamma(self, evt):
		if self.gammatog.GetValue() is True:
			self.gammavalue.Enable(False)
			self.gammatog.SetLabel("Locked")
		else:
			self.gammavalue.Enable(True)
			self.gammatog.SetLabel("Refine")

	#==================
	def onTogglePhi(self, evt):
		if self.phitog.GetValue() is True:
			self.phivalue.Enable(False)
			self.phitog.SetLabel("Locked")
		else:
			self.phivalue.Enable(True)
			self.phitog.SetLabel("Refine")

	#==================
	def onTogglePhi(self, evt):
		if self.phitog.GetValue() is True:
			self.phivalue.Enable(False)
			self.phitog.SetLabel("Locked")
		else:
			self.phivalue.Enable(True)
			self.phitog.SetLabel("Refine")

	#==================
	def onToggleScale(self, evt):
		if self.scaletog.GetValue() is True:
			self.scalevalue.Enable(False)
			self.scaletog.SetLabel("Locked")
		else:
			self.scalevalue.Enable(True)
			self.scaletog.SetLabel("Refine")

	#==================
	def onToggleShift(self, evt):
		if self.shifttog.GetValue() is True:
			self.shiftxvalue.Enable(False)
			self.shiftyvalue.Enable(False)
			self.shifttog.SetLabel("Locked")
		else:
			self.shiftxvalue.Enable(True)
			self.shiftyvalue.Enable(True)
			self.shifttog.SetLabel("Refine")

	#==================
	def onRunLeastSquares(self, evt):
		theta  = self.thetavalue.GetValue()
		gamma  = self.gammavalue.GetValue()
		phi    = self.phivalue.GetValue()
		scale  = self.scalevalue.GetValue()
		shiftx = self.shiftxvalue.GetValue()
		shifty = self.shiftyvalue.GetValue()
		#SET XSCALE
		xscale = numpy.array((
			not self.thetatog.GetValue(),
			not self.gammatog.GetValue(),
			not self.phitog.GetValue(),
			not self.scaletog.GetValue(),
			not self.shifttog.GetValue(),
			not self.shifttog.GetValue(),
			), dtype=numpy.float32)
		#GET TARGETS
		targets1 = self.parent.panel1.getTargets('Picked')
		a1 = self.parent.targetsToArray(targets1)
		targets2 = self.parent.panel2.getTargets('Picked')
		a2 = self.parent.targetsToArray(targets2)
		if len(a1) > len(a2):
			print "shorten a1"
			a1 = a1[0:len(a2),:]
		elif len(a2) > len(a1):
			print "shorten a2"
			a2 = a2[0:len(a1),:]
		self.lsfit = apTiltTransform.willsq(a1, a2, theta, gamma, phi, scale, shiftx, shifty, xscale)
		#pprint.pprint(self.lsfit)
		self.thetavalue.SetValue(round(self.lsfit['theta'],5))
		self.gammavalue.SetValue(round(self.lsfit['gamma'],5))
		self.phivalue.SetValue(round(self.lsfit['phi'],5))
		self.scalevalue.SetValue(round(self.lsfit['scale'],5))
		self.shiftxvalue.SetValue(round(self.lsfit['shiftx'],5))
		self.shiftyvalue.SetValue(round(self.lsfit['shifty'],5))
		self.rmsdlabel.SetLabel(str(round(self.lsfit['rmsd'],5)))
		self.iterlabel.SetLabel(str(self.lsfit['iter']))

	#==================
	def onApplyLeastSquares(self, evt):
		self.Close()
		self.parent.data['leastsqfitdata'] = self.lsfit
		self.parent.data['theta']  = self.thetavalue.GetValue()
		self.parent.data['gamma']  = self.gammavalue.GetValue()
		self.parent.data['phi']    = self.phivalue.GetValue()
		self.parent.data['scale']  = self.scalevalue.GetValue()
		self.parent.data['shiftx'] = self.shiftxvalue.GetValue()
		self.parent.data['shifty'] = self.shiftyvalue.GetValue()
		self.parent.data['rmsd']   = self.lsfit['rmsd']
		self.parent.data['point1'] = self.lsfit['point1']
		self.parent.data['point2'] = self.lsfit['point2']

		self.parent.onUpdate(evt)


##
##
## Dog Picker Dialog
##
##

class DogPickerDialog(wx.Dialog):
	#==================
	def __init__(self, parent):
		self.parent = parent
		wx.Dialog.__init__(self, self.parent.frame, -1, "DoG Auto Particle Picker")

		inforow = wx.FlexGridSizer(3, 2, 15, 15)

		"""
		label = wx.StaticText(self, -1, "Pixel Size (A):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.apix = FloatEntry(self, -1, allownone=False, chars=5, value="1.0")
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.apix, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		"""

		label = wx.StaticText(self, -1, "Particle diameter (pixels):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.diam = FloatEntry(self, -1, allownone=False, chars=5, value="100.0")
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.diam, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		label = wx.StaticText(self, -1, "Diameter range (pixels):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.srange = FloatEntry(self, -1, allownone=False, chars=5, value="20.0")
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.srange, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		label = wx.StaticText(self, -1, "Number of sizes:  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.numslices = IntEntry(self, -1, allownone=False, chars=3, value="2")
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.numslices, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		label = wx.StaticText(self, -1, "Threshold:  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.thresh = FloatEntry(self, -1, allownone=False, chars=5, value="0.7")
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.thresh, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		label = wx.StaticText(self, -1, "Particle contrast:",
			style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add((1,1), 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		self.whitePart = wx.RadioButton(self, -1, 'Light on Dark (stain)', (10, 10), style=wx.RB_GROUP)
		self.blackPart = wx.RadioButton(self, -1, 'Dark on Light (ice)', (10, 30))
		self.Bind(wx.EVT_RADIOBUTTON, self.partContrast, id=self.whitePart.GetId())
		self.Bind(wx.EVT_RADIOBUTTON, self.partContrast, id=self.blackPart.GetId())
		self.partContrast(True)
		inforow.Add(self.whitePart, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.blackPart, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, "Max Peaks:  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.maxpeaks = IntEntry(self, -1, allownone=False, chars=5, value="500")
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.maxpeaks, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		label = wx.StaticText(self, -1, "Please wait after running",
			style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add((1,1), 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		self.canceldog = wx.Button(self, wx.ID_CANCEL, '&Cancel')
		self.rundog = wx.Button(self, wx.ID_OK, '&Run')
		self.Bind(wx.EVT_BUTTON, self.onRunDogPicker, self.rundog)
		buttonrow = wx.GridSizer(1,2)
		buttonrow.Add(self.canceldog, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.rundog, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)

		self.sizer = wx.FlexGridSizer(2,1)
		self.sizer.Add(inforow, 0, wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(buttonrow, 0, wx.EXPAND|wx.ALL, 5)
		self.SetSizerAndFit(self.sizer)

	#==================
	def partContrast(self, evt):
		if self.whitePart.GetValue() is True:
			return False
		return True

	#==================
	def onRunDogPicker(self, evt):
		apDisplay.printColor("===============\nRunning experimental DoGPicker","cyan")

		### remove existing maps
		lefts = glob.glob("maps/leftimage.dogmap*.jpg")
		for imgname in lefts:
			apFile.removeFile(imgname, warn=False)
		rights = glob.glob("maps/rightimage.dogmap*.jpg")
		for imgname in rights:
			apFile.removeFile(imgname, warn=False)

		pixdiam = self.diam.GetValue()
		sizerange = self.srange.GetValue()
		thresh = self.thresh.GetValue()
		invert = self.partContrast(None)
		maxpeaks = self.maxpeaks.GetValue()
		numslices  = self.numslices.GetValue()

		if invert is True:
			apDisplay.printMsg("Picking dark particles on light backgound, i.e. ice")
		else:
			apDisplay.printMsg("Picking light particles on dark backgound, i.e. stain")

		self.Close()

		apParam.createDirectory("maps")
		#1. set DoG parameters / hack to use existing pipeline function
		dogparams = {
			'apix': 1.0, # set to 1 because we are using pixels
			'bin': 1.0, # set to 1 because we are using pixels
			'diam': pixdiam, # diameter of particles
			'sizerange': sizerange, # diameter range of particles
			'numslices': numslices, # number of slices to perform
			'kfactor': 1.2, # does not matter

			'overlapmult': 1.5,
			'rundir': os.getcwd(),
			'maxpeaks': maxpeaks,
			'maxthresh': None,
			'thresh': thresh,
			'maxsize': 0.2,
			'peaktype': 'maximum',
			'background': False,
			'doubles': False,
		}

		#2a. get image 1
		img1 = numpy.asarray(self.parent.panel1.imagedata, dtype=numpy.float32)
		if invert is True:
			img1 = apImage.invertImage(img1)

		#3a. run DoG picker on image 1
		dogarrays1 = apDog.diffOfGaussParam(img1, dogparams)

		#4a: threshold & find peaks image 1
		imgdict1 = { 'filename': 'leftimage', 'image': img1, }
		peaktree1 = apPeaks.findPeaks(imgdict1, dogarrays1, dogparams, maptype="dogmap", pikfile=False)

		#5a: insert into self.parent.picks1
		self.parent.picks1 = self.peaktreeToPicks(peaktree1)
	
		#===

		#2b: get image 2
		img2 = numpy.asarray(self.parent.panel2.imagedata, dtype=numpy.float32)
		if invert is True:
			img2 = apImage.invertImage(img2)

		#3b. run DoG picker on image 2
		dogarrays2 = apDog.diffOfGaussParam(img2, dogparams)

		#4b: threshold & find peaks image 2
		imgdict2 = { 'filename': 'rightimage', 'image': img2, }
		peaktree2 = apPeaks.findPeaks(imgdict2, dogarrays2, dogparams, maptype="dogmap", pikfile=False)

		#5b: insert into self.parent.picks2
		self.parent.picks2 = self.peaktreeToPicks(peaktree2)

		self.parent.onImportPicks(None, pixdiam, showmaps=True)
		apDisplay.printColor("Finished DoGPicker\n===================","cyan")

	#==================
	def peaktreeToPicks(self, peaktree):
		picks = []
		for p in peaktree:
			picks.append( (p['xcoord'], p['ycoord']) )
		npicks = numpy.asarray(picks, dtype=numpy.float32)
		return npicks

##
##
## View DoG Maps Frame
##
##

class viewDogMapsFrame(wx.Dialog):
	#==================
	def __init__(self, parent):
		self.parent = parent

		### check if images exist
		self.imgcount = len(glob.glob("maps/leftimage.dogmap*.jpg"))

		### create frame
		wx.Dialog.__init__(self, self.parent.frame, -1, "DoG Maps")
		self.sizer = wx.FlexGridSizer(2, 2, 15, 15)

		### set images
		result = self.onSetImages()
		if result is False:
			return

		### add left image
		self.leftsizer = wx.StaticBitmap(self, -1, self.leftbitmap)
		self.sizer.Add(self.leftsizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)

		### add right image
		self.rightsizer = wx.StaticBitmap(self, -1, self.rightbitmap)
		self.sizer.Add(self.rightsizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)

		### buttons
		if self.imgcount > 1:
			self.prevmap = wx.Button(self, wx.ID_BACKWARD, '&Previous')
			self.nextmap = wx.Button(self, wx.ID_FORWARD, '&Next')
			self.Bind(wx.EVT_BUTTON, self.onPrevMap, self.prevmap)
			self.Bind(wx.EVT_BUTTON, self.onNextMap, self.nextmap)
		self.okmap = wx.Button(self, wx.ID_OK, '&OK')
		self.Bind(wx.EVT_BUTTON, self.onClose, self.okmap)

		buttonrow = wx.GridSizer(1, 3)
		if self.imgcount > 1:
			buttonrow.Add(self.prevmap, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.okmap, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		if self.imgcount > 1:
			buttonrow.Add(self.nextmap, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)

		self.sizer.Add(buttonrow, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)

		#sizer.AddGrowableRow(0)
		#sizer.AddGrowableCol(0)
		#sizer.AddGrowableCol(1)
		self.SetSizerAndFit(self.sizer)

	#==================
	def onSetImages(self):
		self.leftmap = os.path.join(os.getcwd(), "maps/leftimage.dogmap%d.jpg"%(self.parent.dogimgnum))
		self.rightmap = os.path.join(os.getcwd(), "maps/rightimage.dogmap%d.jpg"%(self.parent.dogimgnum))

		if not os.path.isfile(self.leftmap) or not os.path.isfile(self.rightmap):
			print "failed to find DoG maps"
			return False

		### left image
		self.leftimg = wx.Image(self.leftmap, wx.BITMAP_TYPE_JPEG, -1)
		self.leftimg = self.leftimg.Scale(512, 512)
		self.leftbitmap = wx.BitmapFromImage(self.leftimg)

		### right image
		self.rightimg = wx.Image(self.rightmap, wx.BITMAP_TYPE_JPEG, -1)
		self.rightimg = self.rightimg.Scale(512, 512)
		self.rightbitmap = wx.BitmapFromImage(self.rightimg)

		return True

	#==================
	def onPrevMap(self, evt):
		self.parent.dogimgnum -= 1
		if self.parent.dogimgnum == 0:
			self.parent.dogimgnum = self.imgcount
		self.Destroy()
		self.parent.viewdogmaps_frame = viewDogMapsFrame(self.parent)
		self.parent.viewdogmaps_frame.Show()

	#==================
	def onNextMap(self, evt):
		self.parent.dogimgnum += 1
		if self.parent.dogimgnum > self.imgcount:
			self.parent.dogimgnum = 1
		self.Destroy()
		self.parent.viewdogmaps_frame = viewDogMapsFrame(self.parent)
		self.parent.viewdogmaps_frame.Show()

	#==================
	def onClose(self, evt):
		self.parent.dogimgnum = 0
		self.Destroy()

##
##
## Guess Shift Dialog
##
##

class GuessShiftDialog(wx.Dialog):
	#==================
	def __init__(self, parent):
		self.parent = parent
		wx.Dialog.__init__(self, self.parent.frame, -1, "Guess Initial Shift")

		inforow = wx.FlexGridSizer(3, 2, 15, 15)

		gammastr = "%3.3f" % self.parent.data['gamma']
		label = wx.StaticText(self, -1, "Tilt axis angle (degrees):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.tiltaxis = FloatEntry(self, -1, allownone=False, chars=5, value=gammastr)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.tiltaxis, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		label = wx.StaticText(self, -1, "Vertical is 0 degrees",
			style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add((1,1), 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		thetastr = "%3.3f" % self.parent.data['theta']
		label = wx.StaticText(self, -1, "Tilt angle:  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.tiltangle = FloatEntry(self, -1, allownone=False, chars=5, value=thetastr)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.tiltangle, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		label = wx.StaticText(self, -1, "negative tilted on left,  positive tilted or right",
			style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add((1,1), 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		self.cancelguess = wx.Button(self, wx.ID_CANCEL, '&Cancel')
		self.runguess = wx.Button(self, wx.ID_OK, '&Run')
		self.Bind(wx.EVT_BUTTON, self.onRunGuessShift, self.runguess)
		buttonrow = wx.GridSizer(1,2)
		buttonrow.Add(self.cancelguess, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.runguess, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)

		self.sizer = wx.FlexGridSizer(2,1)
		self.sizer.Add(inforow, 0, wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(buttonrow, 0, wx.EXPAND|wx.ALL, 5)
		self.SetSizerAndFit(self.sizer)

	#==================
	def onRunGuessShift(self, evt):
		tiltaxis  = self.tiltaxis.GetValue()
		tiltangle = self.tiltangle.GetValue()
		self.parent.data['theta'] = tiltangle
		self.parent.data['gamma'] = tiltaxis
		self.parent.data['phi']   = tiltaxis
		self.Close()
		self.parent.onGuessShift(evt)


##
##
## About TiltPicker Dialog
##
##

class AboutTiltPickerDialog(wx.Dialog):
	#==================
	def __init__(self, parent):
		self.parent = parent
		wx.Dialog.__init__(self, self.parent.frame, -1, "About TiltPicker")

		sizer = wx.FlexGridSizer(6, 1, 10, 0)

		logoimage = self.parent.logoimage
		if os.path.isfile(logoimage):
			#golden = (1+math.sqrt(5))/2.0
			#width = 480
			#height = int(width/golden)
			#logo = wx.EmptyBitmap(width, height)
			wxlogo = wx.Image(logoimage, wx.BITMAP_TYPE_PNG, -1)
			wxlogobit = wx.BitmapFromImage(wxlogo)
			#logosize = wx.Size(width, height) #golden ratio
			logosizer = wx.StaticBitmap(self, -1, wxlogobit)
			sizer.Add(logosizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, "TiltPicker, version "+self.parent.version)
		sizer.Add(label, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)

		release = wx.StaticText(self, -1, "Released on "+self.parent.releasedate)
		sizer.Add(release, 2, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)

		release = wx.StaticText(self, -1, "Please contact Neil Voss (vossman77@yahoo.com) for help")
		sizer.Add(release, 3, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)

		self.okbutton = wx.Button(self, wx.ID_OK, '&OK')
		sizer.Add(self.okbutton, 4, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)

		self.SetSizerAndFit(sizer)

