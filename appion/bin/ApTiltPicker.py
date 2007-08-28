#!/usr/bin/python -O

import sys
import wx
import re
import math
import numpy
import pyami
from gui.wx import ImageViewer
import radermacher
from scipy import optimize
import tiltDialog

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
	def __init__(self, parent, id, callback=None, tool=True, name=None):
		ImageViewer.TargetImagePanel.__init__(self, parent, id, callback=callback, tool=tool, imagesize=(520,700))
		#self.button_1.SetValue(1)
		if name is not None:
			self.outname = name
		else:
			self.outname="unknown"

	def setOtherPanel(self, panel):
		self.other = panel

	def addTarget(self, name, x, y):
		sys.stderr.write("%s: (%4d,%4d),\n" % (self.outname,x,y))
		return self._getSelectionTool().addTarget(name, x, y)

	def deleteTarget(self, target):
		return self._getSelectionTool().deleteTarget(target)

	def openImageFile(self, filename):
		self.filename = filename
		if filename is None:
			self.setImage(None)
		elif filename[-4:] == '.mrc':
			image = pyami.mrc.read(filename)
			self.setImage(image.astype(numpy.float32))
		else:
			self.setImage(Image.open(filename))

class MyApp(wx.App):
	def OnInit(self):
		self.arealim = 50000.0
		self.theta = 0
		self.gamma = 0
		self.phi = 0

		self.frame = wx.Frame(None, -1, 'Image Viewer')
		splitter = wx.SplitterWindow(self.frame)

		self.panel1 = TiltTargetPanel(splitter, -1, name="untilt")
		self.panel1.addTargetTool('PickedParticles', color=wx.RED, shape='x', target=True)
		self.panel1.setTargets('PickedParticles', [])
		self.panel1.addTargetTool('AlignedParticles', color=wx.BLUE, shape='o')
		self.panel1.setTargets('AlignedParticles', [])
		self.panel1.SetMinSize((512,700))
		self.panel1.SetBackgroundColour("sky blue")

		self.panel2 = TiltTargetPanel(splitter, -1, name="tilt")
		self.panel2.addTargetTool('PickedParticles', color=wx.BLUE, shape='x', target=True)
		self.panel2.setTargets('PickedParticles', [])
		self.panel2.addTargetTool('AlignedParticles', color=wx.RED, shape='o')
		self.panel2.setTargets('AlignedParticles', [])
		self.panel2.SetMinSize((512,700))
		self.panel2.SetBackgroundColour("pink")

		self.panel1.setOtherPanel(self.panel2)
		self.panel2.setOtherPanel(self.panel1)

		self.bsizer = wx.FlexGridSizer(1,10)

		self.quit = wx.Button(self.frame, wx.ID_EXIT, '&Quit')
		self.frame.Bind(wx.EVT_BUTTON, self.onQuit, self.quit)
		self.bsizer.Add(self.quit, 0, wx.ALL, 1)

		self.update = wx.Button(self.frame, wx.ID_APPLY, '&Update')
		self.frame.Bind(wx.EVT_BUTTON, self.onUpdate, self.update)
		self.bsizer.Add(self.update, 0, wx.ALL, 1)

		self.theta_dialog = tiltDialog.FitThetaDialog(self)
		self.fittheta = wx.Button(self.frame, -1, 'Fit &Theta')
		self.frame.Bind(wx.EVT_BUTTON, self.onFitTheta, self.fittheta)
		self.bsizer.Add(self.fittheta, 0, wx.ALL, 1)

		self.fitall_dialog = tiltDialog.FitAllDialog(self)
		self.fitall = wx.Button(self.frame, -1, 'Fit &All')
		self.frame.Bind(wx.EVT_BUTTON, self.onFitAll, self.fitall)
		self.bsizer.Add(self.fitall, 0, wx.ALL, 1)

		self.clear = wx.Button(self.frame, wx.ID_CLEAR, '&Clear')
		self.frame.Bind(wx.EVT_BUTTON, self.onClear, self.clear)
		self.bsizer.Add(self.clear, 0, wx.ALL, 1)

		self.save = wx.Button(self.frame, wx.ID_SAVE, '&Save')
		self.frame.Bind(wx.EVT_BUTTON, self.onSave, self.save)
		self.bsizer.Add(self.save, 0, wx.ALL, 1)

		self.load = wx.Button(self.frame, wx.ID_OPEN, '&Load Picks')
		self.frame.Bind(wx.EVT_BUTTON, self.onLoad, self.load)
		self.bsizer.Add(self.load, 0, wx.ALL, 1)

		self.sizer = wx.GridBagSizer(2,2)

		#splitter.Initialize(self.panel1)
		splitter.SplitVertically(self.panel1, self.panel2)
		splitter.SetMinimumPaneSize(10)
		self.sizer.Add(splitter, (0,0), (1,2), wx.EXPAND|wx.ALL, 3)
		#self.sizer.Add(self.panel1, (0,0), (1,1), wx.EXPAND|wx.ALL, 3)
		#self.sizer.Add(self.panel2, (0,1), (1,1), wx.EXPAND|wx.ALL, 3)
		self.sizer.Add(self.bsizer, (1,0), (1,2), wx.EXPAND|wx.ALL|wx.CENTER, 3)
		self.sizer.AddGrowableRow(0)
		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableCol(1)

		self.frame.SetSizer(self.sizer)
		self.SetTopWindow(self.frame)
		self.frame.Show(True)
		return True

	def onQuit(self, evt):
		print "First"
		targets = self.panel1.getTargets('PickedParticles')
		for target in targets:
			print '(%d,%d),' % (target.x, target.y)
		print "Second"
		targets = self.panel2.getTargets('PickedParticles')
		for target in targets:
			print '(%d,%d),' % (target.x, target.y)
		wx.Exit()

	def onUpdate(self, evt):
		#align first
		targets1 = self.panel1.getTargets('PickedParticles')
		a1 = self.targetsToArray(targets1)
		targets2 = self.panel2.getTargets('PickedParticles')
		a2 = self.targetsToArray(targets2)
		#aligned1 = radermacher.transform(a1, a2, self.theta, 0.0, 0.0)
		x1 = numpy.asarray(a1[:,0] - a1[0,0] + a2[0,0], dtype=numpy.float32)
		y1 = numpy.asarray(a1[:,1], dtype=numpy.float32)
		y1 = (y1-y1[0]) * math.cos(self.theta*math.pi/180.0) + float(a2[0,1])
		a1b = numpy.column_stack((x1,y1))
		#print a1[0:10,:]
		#print a1b[0:10,:]
		self.panel2.setTargets('AlignedParticles', a1b)
		
		#align second
		#aligned1 = radermacher.transform(a1, a2, self.theta, 0.0, 0.0)
		x2 = numpy.asarray(a2[:,0] - a2[0,0] + a1[0,0], dtype=numpy.float32)
		y2 = numpy.asarray(a2[:,1], dtype=numpy.float32)
		y2 = (y2-y2[0]) / math.cos(self.theta*math.pi/180.0) + float(a1[0,1])
		a2b = numpy.column_stack((x2,y2))
		#print a2[0:10,:]
		#print a2b[0:10,:]
		self.panel1.setTargets('AlignedParticles', a2b)

	def targetsToArray(self, targets):
		i = 0
		count = len(targets)
		a = numpy.zeros((count,2), dtype=numpy.int32)
		for t in targets:
			a[i,0] = int(t.x)
			a[i,1] = int(t.y)
			i += 1
		return a

	def onFitTheta(self, evt):
		if len(self.panel1.getTargets('PickedParticles')) > 3 and len(self.panel2.getTargets('PickedParticles')) > 3:
			self.theta_dialog.tiltvalue.SetLabel(label=("%3.3f" % self.theta))
			self.theta_dialog.Show()

	def onFitAll(self, evt):
		if len(self.panel1.getTargets('PickedParticles')) > 3 and len(self.panel2.getTargets('PickedParticles')) > 3:
			self.fitall_dialog.thetavalue.SetValue(round(self.theta,4))
			self.fitall_dialog.gammavalue.SetValue(round(self.gamma,4))
			self.fitall_dialog.phivalue.SetValue(round(self.phi,4))
			self.fitall_dialog.Show()

	def onClear(self, evt):
		self.panel1.setTargets('PickedParticles', [])
		self.panel1.setTargets('AlignedParticles', [])
		self.panel2.setTargets('PickedParticles', [])
		self.panel2.setTargets('AlignedParticles', [])

	def onSave(self, evt):
		targets1 = self.panel1.getTargets('PickedParticles')
		targets2 = self.panel2.getTargets('PickedParticles')
		if len(targets1) > 4 and len(targets2) > 4:
			f = open("savedpicks.txt","w")
			f.write( "image 1: "+self.panel1.filename+"\n" )
			for target in targets1:
				f.write( '%d,%d\n' % (target.x, target.y) )
			f.write( "image 2: "+self.panel2.filename+"\n" )
			for target in targets2:
				f.write( '%d,%d\n' % (target.x, target.y) )
			f.close()

	def onLoad(self, evt):
		f = open("savedpicks.txt","r")
		size = int(len(f.readlines())/2-1)
		f.close()
		f = open("savedpicks.txt","r")
		strarrays = ["","",""]
		arrays = [
			numpy.zeros((size,2), dtype=numpy.int32),
			numpy.zeros((size,2), dtype=numpy.int32),
			numpy.zeros((size,2), dtype=numpy.int32),
		]
		i = 0
		for line in f:
			if line[:5] == "image":
				i += 1
				j = 0
				print("reading picks for image "+str(i));
			else:
				line = line.strip()
				seps = line.split(",")
				for k in range(len(seps)):
					#print "'"+seps[k]+"'"
					if seps[k]:
						arrays[i][j,k] = int(seps[k])
				j += 1
		#print arrays[1]
		f.close()
		#sys.exit(1)
		a1 = arrays[1]
		a2 = arrays[2]
		self.panel1.setTargets('PickedParticles', a1)
		self.panel2.setTargets('PickedParticles', a2)

if __name__ == '__main__':
	try:
		filename1 = sys.argv[1]
		filename2 = sys.argv[2]
	except IndexError:
		filename1 = None
		filename2 = None

	app = MyApp(0)
	app.panel1.openImageFile(filename1)
	app.panel2.openImageFile(filename2)

	app.MainLoop()



