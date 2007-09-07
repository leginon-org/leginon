import wx
import numpy
import pprint
from gui.wx.Entry import FloatEntry, IntEntry, EVT_ENTRY
import radermacher
import apTiltTransform

##
##
## Fit Theta Dialog
##
##

class FitThetaDialog(wx.Dialog):
	def __init__(self, parent):
		self.parent = parent
		self.theta = self.parent.theta
		wx.Dialog.__init__(self, self.parent.frame, -1, "Measure Tilt Angle, Theta")

		inforow = wx.FlexGridSizer(2, 3, 15, 15)
		thetastr = ("***** %3.3f *****" % self.theta)
		label = wx.StaticText(self, -1, "Current tilt angle:  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.tiltvalue = wx.StaticText(self, -1, thetastr, style=wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)
		#self.tiltvalue = FloatEntry(self, -1, allownone=True, chars=5, value=thetastr)
		label3 = wx.StaticText(self, -1, "degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.tiltvalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		inforow.Add(label3, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		arealimstr = str(int(self.parent.arealim))
		label = wx.StaticText(self, -1, "Minimum Triangle Area:  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.arealimit = IntEntry(self, -1, allownone=False, chars=8, value=arealimstr)
		label2 = wx.StaticText(self, -1, "square pixels", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.arealimit, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

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

	def onRunTiltAng(self, evt):
		arealim  = self.arealimit.GetValue()
		self.parent.arealim = arealim
		targets1 = self.parent.panel1.getTargets('Picked')
		a1 = self.parent.targetsToArray(targets1)
		targets2 = self.parent.panel2.getTargets('Picked')
		a2 = self.parent.targetsToArray(targets2)
		fittheta = radermacher.tiltang(a1, a2, arealim)
		pprint.pprint(fittheta)
		if 'wtheta' in fittheta:
			self.theta = fittheta['wtheta']
			self.thetadev = fittheta['wthetadev']
			thetastr = ("%3.3f +/- %2.2f" % (self.theta, self.thetadev))
			self.tiltvalue.SetLabel(label=thetastr)

	def onApplyTiltAng(self, evt):
		self.Close()
		self.parent.theta = self.theta
		self.parent.onUpdate(evt)

##
##
## Fit All Least Squares Dialog
##
##

class FitAllDialog(wx.Dialog):
	def __init__(self, parent):
		self.parent = parent
		wx.Dialog.__init__(self, self.parent.frame, -1, "Least Squares Optimization")

		inforow = wx.FlexGridSizer(5, 4, 15, 15)

		thetastr = "%3.3f" % self.parent.theta
		label = wx.StaticText(self, -1, "Tilt angle (theta):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		#self.tiltvalue = wx.StaticText(self, -1, thetastr, style=wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)
		self.thetavalue = FloatEntry(self, -1, allownone=False, chars=8, value=thetastr)
		label2 = wx.StaticText(self, -1, "degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.thetatog = wx.ToggleButton(self, -1, "Refine")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleTheta, self.thetatog)
		self.thetavalue.Enable(False)
		self.thetatog.SetValue(1)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.thetavalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.thetatog, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		gammastr = "%3.3f" % self.parent.gamma
		label = wx.StaticText(self, -1, "Image 1 Rotation (gamma):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.gammavalue = FloatEntry(self, -1, allownone=False, chars=8, value=gammastr)
		label2 = wx.StaticText(self, -1, "degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.gammatog = wx.ToggleButton(self, -1, "Refine")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleGamma, self.gammatog)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.gammavalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.gammatog, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		phistr = "%3.3f" % self.parent.phi
		label = wx.StaticText(self, -1, "Image 2 Rotation (phi):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.phivalue = FloatEntry(self, -1, allownone=False, chars=8, value=phistr)
		label2 = wx.StaticText(self, -1, "degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.phitog = wx.ToggleButton(self, -1, "Refine")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onTogglePhi, self.phitog)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.phivalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.phitog, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		scalestr = "%3.3f" % self.parent.scale
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

		shiftxstr = "%3.3f" % self.parent.shiftx
		shiftystr = "%3.3f" % self.parent.shifty
		label = wx.StaticText(self, -1, "Shift (x,y) pixels:  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.shiftxvalue = FloatEntry(self, -1, allownone=False, chars=8, value=shiftxstr)
		self.shiftyvalue = FloatEntry(self, -1, allownone=False, chars=8, value=shiftystr)
		self.shifttog = wx.ToggleButton(self, -1, "Locked")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleShift, self.shifttog)
		self.shiftxvalue.Enable(False)
		self.shiftyvalue.Enable(False)
		self.shifttog.SetValue(1)
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

	def onToggleTheta(self, evt):
		if self.thetatog.GetValue() is True:
			self.thetavalue.Enable(False)
			self.thetatog.SetLabel("Locked")
		else:
			self.thetavalue.Enable(True)
			self.thetatog.SetLabel("Refine")

	def onToggleGamma(self, evt):
		if self.gammatog.GetValue() is True:
			self.gammavalue.Enable(False)
			self.gammatog.SetLabel("Locked")
		else:
			self.gammavalue.Enable(True)
			self.gammatog.SetLabel("Refine")

	def onTogglePhi(self, evt):
		if self.phitog.GetValue() is True:
			self.phivalue.Enable(False)
			self.phitog.SetLabel("Locked")
		else:
			self.phivalue.Enable(True)
			self.phitog.SetLabel("Refine")

	def onTogglePhi(self, evt):
		if self.phitog.GetValue() is True:
			self.phivalue.Enable(False)
			self.phitog.SetLabel("Locked")
		else:
			self.phivalue.Enable(True)
			self.phitog.SetLabel("Refine")

	def onToggleScale(self, evt):
		if self.scaletog.GetValue() is True:
			self.scalevalue.Enable(False)
			self.scaletog.SetLabel("Locked")
		else:
			self.scalevalue.Enable(True)
			self.scaletog.SetLabel("Refine")

	def onToggleShift(self, evt):
		if self.shifttog.GetValue() is True:
			self.shiftxvalue.Enable(False)
			self.shiftyvalue.Enable(False)
			self.shifttog.SetLabel("Locked")
		else:
			self.shiftxvalue.Enable(True)
			self.shiftyvalue.Enable(True)
			self.shifttog.SetLabel("Refine")

	def onRunLeastSquares(self, evt):
		theta  = self.thetavalue.GetValue()
		gamma  = self.gammavalue.GetValue()
		phi    = self.phivalue.GetValue()
		scale  = self.scalevalue.GetValue()
		shiftx = self.shiftxvalue.GetValue()
		shifty = self.shiftyvalue.GetValue()
		targets1 = self.parent.panel1.getTargets('Picked')
		a1 = self.parent.targetsToArray(targets1)
		targets2 = self.parent.panel2.getTargets('Picked')
		a2 = self.parent.targetsToArray(targets2)
		xscale = numpy.array((
			not self.thetatog.GetValue(),
			not self.gammatog.GetValue(),
			not self.phitog.GetValue(),
			not self.scaletog.GetValue(),
			not self.shifttog.GetValue(),
			not self.shifttog.GetValue(),
			), dtype=numpy.float32)
		print xscale
		fit = apTiltTransform.willsq(a1, a2, theta, gamma, phi, scale, shiftx, shifty, xscale)
		pprint.pprint(fit)
		self.thetavalue.SetValue(round(fit['theta'],5))
		self.gammavalue.SetValue(round(fit['gamma'],5))
		self.phivalue.SetValue(round(fit['phi'],5))
		self.scalevalue.SetValue(round(fit['scale'],5))
		self.shiftxvalue.SetValue(round(fit['shiftx'],5))
		self.shiftyvalue.SetValue(round(fit['shifty'],5))
		self.rmsdlabel.SetLabel(str(round(fit['rmsd'],5)))
		self.iterlabel.SetLabel(str(fit['iter']))

	def onApplyLeastSquares(self, evt):
		self.Close()
		self.parent.theta  = self.thetavalue.GetValue()
		self.parent.gamma  = self.gammavalue.GetValue()
		self.parent.phi    = self.phivalue.GetValue()
		self.parent.scale  = self.scalevalue.GetValue()
		self.parent.shiftx = self.shiftxvalue.GetValue()
		self.parent.shifty = self.shiftyvalue.GetValue()
		self.parent.onUpdate(evt)



