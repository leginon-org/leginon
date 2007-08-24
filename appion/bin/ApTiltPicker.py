#!/usr/bin/python -O

import sys
from gui.wx import ImageViewer
import wx
import pyami
import numpy
import radermacher
from scipy import optimize

wx.InitAllImageHandlers()

ImageClickedEventType = wx.NewEventType()
ImageClickDoneEventType = wx.NewEventType()
MeasurementEventType = wx.NewEventType()
DisplayEventType = wx.NewEventType()
TargetingEventType = wx.NewEventType()
SettingsEventType = wx.NewEventType()

EVT_IMAGE_CLICKED = wx.PyEventBinder(ImageClickedEventType)
EVT_IMAGE_CLICK_DONE = wx.PyEventBinder(ImageClickDoneEventType)
EVT_MEASUREMENT = wx.PyEventBinder(MeasurementEventType)
EVT_DISPLAY = wx.PyEventBinder(DisplayEventType)
EVT_TARGETING = wx.PyEventBinder(TargetingEventType)
EVT_SETTINGS = wx.PyEventBinder(SettingsEventType)

class TiltTargetPanel(ImageViewer.TargetImagePanel):
	def __init__(self, parent, id, callback=None, tool=True):
		ImageViewer.TargetImagePanel.__init__(self, parent, id, callback=callback, tool=tool)

		self.bsizer = wx.GridBagSizer(5,5)

		self.quit = wx.Button(self, -1, 'Next')
		self.Bind(wx.EVT_BUTTON, self.onQuit, self.quit)
		self.bsizer.Add(self.quit, (0, 0), (1, 1), wx.ALL)

		self.update = wx.Button(self, -1, 'Update')
		self.Bind(wx.EVT_BUTTON, self.onUpdate, self.update)
		self.bsizer.Add(self.update, (1, 0), (1, 1), wx.ALL)

		self.fit = wx.Button(self, -1, 'Fit')
		self.Bind(wx.EVT_BUTTON, self.onFit, self.fit)
		self.bsizer.Add(self.fit, (0, 1), (1, 1), wx.ALL)

		self.clear = wx.Button(self, -1, 'Clear')
		self.Bind(wx.EVT_BUTTON, self.onClear, self.clear)
		self.bsizer.Add(self.clear, (1, 1), (1, 1), wx.ALL)

		self.sizer.Add(self.bsizer, (0, 0), (1, 1), wx.EXPAND|wx.ALL)

	def onQuit(self, evt):
		print "First"
		targets = self.getTargets('PickedParticles')
		for target in targets:
			print '(%d,%d),' % (target.x, target.y)
		print "Second"
		targets = self.other.getTargets('PickedParticles')
		for target in targets:
			print '(%d,%d),' % (target.x, target.y)
		wx.Exit()

	def onUpdate(self, evt):
		targets = self.other.getTargets('PickedParticles')
		self.setTargets('AlignedParticles', targets)

	def targetsToArray(self, targets):
		i = 0
		count = len(targets)
		a = numpy.zeros((count,2), dtype=numpy.int32)
		for t in targets:
			a[i,0] = int(t.x)
			a[i,1] = int(t.y)
			i += 1
		return a

	def onFit(self, evt):
		targets = self.getTargets('PickedParticles')
		a1 = self.targetsToArray(targets)
		targets = self.other.getTargets('PickedParticles')
		a2 = self.targetsToArray(targets)
		j = 0
		for i in a1,a2:
			j+=1
			print j,i
		fit = radermacher.tiltang(a1,a2,5000.0)
		print fit

	def onClear(self, evt):
		self.setTargets('PickedParticles', [])
		self.setTargets('AlignedParticles', [])

	def setOtherPanel(self, panel):
		self.other = panel

if __name__ == '__main__':
	try:
		filename = sys.argv[1]
		filename2 = sys.argv[2]
	except IndexError:
		filename = None
		filename2 = None

	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Viewer')
			self.sizer = wx.GridBagSizer(5,5)

			self.panel = TiltTargetPanel(frame, -1)
			self.panel.addTargetTool('PickedParticles', color=wx.RED, shape='x', target=True)
			self.panel.setTargets('PickedParticles', [])
			self.panel.addTargetTool('AlignedParticles', color=wx.BLUE, shape='o')
			self.panel.setTargets('AlignedParticles', [])

			self.panel2 = TiltTargetPanel(frame, -1)
			self.panel2.addTargetTool('PickedParticles', color=wx.BLUE, shape='x', target=True)
			self.panel2.setTargets('PickedParticles', [])
			self.panel2.addTargetTool('AlignedParticles', color=wx.RED, shape='o')
			self.panel2.setTargets('AlignedParticles', [])

			self.panel.setOtherPanel(self.panel2)
			self.panel2.setOtherPanel(self.panel)

			self.sizer.Add(self.panel, (1, 0), (1,1), wx.EXPAND|wx.ALL)
			self.sizer.Add(self.panel2, (1, 1), (1,1), wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.Show(True)
			return True

	app = MyApp(0)
	if filename is None:
		app.panel.setImage(None)
	elif filename[-4:] == '.mrc':
		image = pyami.mrc.read(filename)
		app.panel.setImage(image.astype(numpy.float32))
	else:
		app.panel.setImage(Image.open(filename))

	if filename2 is None:
		app.panel2.setImage(None)
	elif filename2[-4:] == '.mrc':
		image2 = pyami.mrc.read(filename2)
		app.panel2.setImage(image2.astype(numpy.float32))
	else:
		app.panel2.setImage(Image.open(filename2))
	app.MainLoop()


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

