import sys
import wx
import re
import math
from gui.wx.Entry import FloatEntry, IntEntry, EVT_ENTRY
import radermacher

FitThetaEventType = wx.NewEventType()
EVT_FIT_THETA = wx.PyEventBinder(FitThetaEventType)

class FitThetaDialog(wx.Dialog):
	def __init__(self, parent):
		self.parent = parent
		self.theta = self.parent.theta
		wx.Dialog.__init__(self, self.parent.frame, -1, "Measure Tilt Angle, Theta")

		inforow = wx.FlexGridSizer(2, 3, 15, 15)
		thetastr = str(self.theta)
		label = wx.StaticText(self, -1, "Current tilt angle:  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.tiltvalue = wx.StaticText(self, -1, thetastr, style=wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)
		#self.tiltvalue = FloatEntry(self, -1, allownone=True, chars=5, value=thetastr)
		label3 = wx.StaticText(self, -1, "degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.tiltvalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		inforow.Add(label3, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		arealimstr = str(int(self.parent.arealim))
		label = wx.StaticText(self, -1, "Minimum Triangle Area:  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.arealimit = IntEntry(self, -1, allownone=False, chars=8, value=arealimstr)
		label2 = wx.StaticText(self, -1, "square pixels", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.arealimit, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

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
		targets1 = self.parent.panel1.getTargets('PickedParticles')
		a1 = self.parent.targetsToArray(targets1)
		targets2 = self.parent.panel2.getTargets('PickedParticles')
		a2 = self.parent.targetsToArray(targets2)
		fittheta = radermacher.tiltang(a1, a2, arealim)
		print fittheta
		if 'wtheta' in fittheta:
			self.theta = fittheta['wtheta']
			thetastr = "%3.3f" % fittheta['wtheta']
			self.tiltvalue.SetLabel(label=thetastr)

	def onApplyTiltAng(self, evt):
		self.Close()
		self.parent.theta = self.theta

class FitAllDialog(wx.Dialog):
	def __init__(self, parent):
		self.parent = parent
		wx.Dialog.__init__(self, self.parent.frame, -1, "Least Squares Optimization")

		inforow = wx.FlexGridSizer(4, 3, 15, 15)

		thetastr = "%3.3f" % self.parent.theta
		label = wx.StaticText(self, -1, "Tilt angle (theta):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		#self.tiltvalue = wx.StaticText(self, -1, thetastr, style=wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)
		self.thetavalue = FloatEntry(self, -1, allownone=False, chars=8, value=thetastr)
		label2 = wx.StaticText(self, -1, "degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.thetavalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		gammastr = "%3.3f" % self.parent.gamma
		label = wx.StaticText(self, -1, "Image 1 Rotation (gamma):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.gammavalue = FloatEntry(self, -1, allownone=False, chars=8, value=gammastr)
		label2 = wx.StaticText(self, -1, "degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.gammavalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		phistr = "%3.3f" % self.parent.phi
		label = wx.StaticText(self, -1, "Image 2 Rotation (phi):  ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.phivalue = FloatEntry(self, -1, allownone=False, chars=8, value=phistr)
		label2 = wx.StaticText(self, -1, "degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(self.phivalue, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		inforow.Add(label2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		self.cancelfitall = wx.Button(self, wx.ID_CANCEL, '&Cancel')
		self.applyfitall = wx.Button(self,  wx.ID_APPLY, '&Apply')
		self.runfitall = wx.Button(self, -1, '&Run')
		self.Bind(wx.EVT_BUTTON, self.onRunLeastSquares, self.runfitall)
		self.Bind(wx.EVT_BUTTON, self.onApplyLeastSquares, self.applyfitall)
		buttonrow = wx.GridSizer(1,3)
		buttonrow.Add(self.cancelfitall, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.applyfitall, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.runfitall, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)

		self.sizer = wx.FlexGridSizer(2,1)
		self.sizer.Add(inforow, 0, wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(buttonrow, 0, wx.EXPAND|wx.ALL, 5)
		self.SetSizerAndFit(self.sizer)

	def onRunLeastSquares(self, evt):
		#self.Close()
		theta  = self.thetavalue.GetValue()
		gamma  = self.gammavalue.GetValue()
		phi    = self.phivalue.GetValue()
		targets1 = self.parent.panel1.getTargets('PickedParticles')
		a1 = self.parent.targetsToArray(targets1)
		targets2 = self.parent.panel2.getTargets('PickedParticles')
		a2 = self.parent.targetsToArray(targets2)
		#fit = willsq(a1, a2, theta, gamma, phi)
		#self.thetavalue.SetValue(round(fit['theta'],4))
		#self.gammavalue.SetValue(round(fit['theta'],4))
		#self.phivalue.SetValue(round(fit['theta'],4))

	def onApplyLeastSquares(self, evt):
		self.Close()
		self.parent.theta = self.thetavalue.GetValue()
		self.parent.gamma = self.gammavalue.GetValue()
		self.parent.phi = self.phivalue.GetValue()

##
##
## Fit All Least Squares Routine
##
##


def willsq(a1, a2, theta0, gamma0=0.0, phi0=0.0, shiftx0=0.0, shifty0=0.0):
	"""
	given two sets of particles; find the tilt, and twist of them
	"""	
	#x0 initial values
	x0 = numpy.array((
		theta0 * math.pi/180.0,
		gamma0 * math.pi/180.0,
		phi0   * math.pi/180.0,
		shiftx0,
		shifty0,
	))
	#x1 delta values
	x1 = numpy.zeros(5, dtype=float32)
	#xscale scaling values
	xscale = numpy.ones(5, dtype=float32)

	print "optimizing angles and shift..."
	x2 = optimize.fmin(_diffParticles, x1, args=(x0, xscale, a1, a2), xtol=0.01, ftol=0.01, maxiter=1000)
	err = _diffParticles(x2, x0, xscale, a1, a2)
	print "complete"

	#x3 final values
	x3 = scaleParams(x2,xscale)+x0
	theta  = x3[0]*180.0/math.pi
	gamma  = x3[1]*180.0/math.pi
	phi    = x3[2]*180.0/math.pi
	shiftx = x3[3]
	shifty = x3[4]

	prob = math.exp(-1.0*math.sqrt(abs(err)))**2
	return theta,gamma,phi,shiftx,shifty,prob

def scaleParams(x1,xscale):
	nump = len(x1)
	x2 = numpy.zeros(nump, dtype=float32)
	for i in range(nump):
		x2[i] = x1[i]*xscale[i]
	return x2

def _diffParticles(x1, x0, xscale, a1, a2):
	x2 = scaleParams(x1,xscale) + x0
	theta  = x2[0]
	gamma  = x2[1]
	phi    = x2[2]
	shiftx = x2[3]
	shifty = x2[4]

	

	return
