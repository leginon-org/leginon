#!/usr/bin/python -O

import sys
import wx
import re
import os
import math
import numpy
import pyami
import Image
import ImageDraw
import apImage
from gui.wx import ImageViewer
import radermacher
from scipy import ndimage,optimize
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

ImageViewer.penwidth=2

class TiltTargetPanel(ImageViewer.TargetImagePanel):
	def __init__(self, parent, id, callback=None, tool=True, name=None):
		ImageViewer.TargetImagePanel.__init__(self, parent, id, callback=callback, tool=tool, mode="vertical")
		#self.button_1.SetValue(1)
		if name is not None:
			self.outname = name
		else:
			self.outname="unknown"

	#---------------------------------------
	def setOtherPanel(self, panel):
		self.other = panel

	#---------------------------------------
	def addTarget(self, name, x, y):
		#sys.stderr.write("%s: (%4d,%4d),\n" % (self.outname,x,y))
		return self._getSelectionTool().addTarget(name, x, y)

	#---------------------------------------
	def deleteTarget(self, target):
		return self._getSelectionTool().deleteTarget(target)

	#---------------------------------------
	def openImageFile(self, filename):
		self.filename = filename
		if filename is None:
			self.setImage(None)
		elif filename[-4:] == '.mrc':
			image = pyami.mrc.read(filename)
			self.setImage(image.astype(numpy.float32))
		else:
			self.setImage(Image.open(filename))

#---------------------------------------
class MyApp(wx.App):
	def OnInit(self):
		self.arealim = 50000.0
		self.theta = 0
		self.gamma = 0
		self.phi = 0
		self.shiftx = 0
		self.shifty = 0
		self.filename = ""
		self.dirname = ""

		self.frame = wx.Frame(None, -1, 'Image Viewer')
		splitter = wx.SplitterWindow(self.frame)

		self.panel1 = TiltTargetPanel(splitter, -1, name="untilt")
		self.panel1.addTargetTool('PickedParticles', color=wx.RED, shape='x', target=True)
		self.panel1.setTargets('PickedParticles', [])
		self.panel1.addTargetTool('AlignedParticles', color=wx.BLUE, shape='o')
		self.panel1.setTargets('AlignedParticles', [])
		#self.panel1.SetMinSize((512,700))
		#self.panel1.SetBackgroundColour("sky blue")

		self.panel2 = TiltTargetPanel(splitter, -1, name="tilt")
		self.panel2.addTargetTool('PickedParticles', color=wx.BLUE, shape='x', target=True)
		self.panel2.setTargets('PickedParticles', [])
		self.panel2.addTargetTool('AlignedParticles', color=wx.RED, shape='o', target=None)
		self.panel2.setTargets('AlignedParticles', [])
		#self.panel2.SetMinSize((512,700))
		#self.panel2.SetBackgroundColour("pink")

		self.panel1.setOtherPanel(self.panel2)
		self.panel2.setOtherPanel(self.panel1)

		self.bsizer = wx.FlexGridSizer(1,12)

		self.theta_dialog = tiltDialog.FitThetaDialog(self)
		self.fittheta = wx.Button(self.frame, -1, 'Find &Theta')
		self.frame.Bind(wx.EVT_BUTTON, self.onFitTheta, self.fittheta)
		self.bsizer.Add(self.fittheta, 0, wx.ALL, 1)

		self.fitall_dialog = tiltDialog.FitAllDialog(self)
		self.fitall = wx.Button(self.frame, -1, '&Optimize Angles')
		self.frame.Bind(wx.EVT_BUTTON, self.onFitAll, self.fitall)
		self.bsizer.Add(self.fitall, 0, wx.ALL, 1)

		self.update = wx.Button(self.frame, wx.ID_APPLY, '&Apply')
		self.frame.Bind(wx.EVT_BUTTON, self.onUpdate, self.update)
		self.bsizer.Add(self.update, 0, wx.ALL, 1)

		self.maskregion = wx.Button(self.frame, -1, '&Mask Region')
		self.frame.Bind(wx.EVT_BUTTON, self.onMaskRegion, self.maskregion)
		self.bsizer.Add(self.maskregion, 0, wx.ALL, 1)

		self.bsizer.Add((100,10), 0, wx.ALL, 1)

		self.clear = wx.Button(self.frame, wx.ID_CLEAR, '&Clear')
		self.frame.Bind(wx.EVT_BUTTON, self.onClear, self.clear)
		self.bsizer.Add(self.clear, 0, wx.ALL, 1)

		self.load = wx.Button(self.frame, wx.ID_OPEN, '&Open')
		self.frame.Bind(wx.EVT_BUTTON, self.onFileOpen, self.load)
		self.bsizer.Add(self.load, 0, wx.ALL, 1)

		self.save = wx.Button(self.frame, wx.ID_SAVE, '&Save')
		self.frame.Bind(wx.EVT_BUTTON, self.onFileSave, self.save)
		self.bsizer.Add(self.save, 0, wx.ALL, 1)

		self.saveas = wx.Button(self.frame, wx.ID_SAVEAS, 'Save &As...')
		self.frame.Bind(wx.EVT_BUTTON, self.onFileSaveAs, self.saveas)
		self.bsizer.Add(self.saveas, 0, wx.ALL, 1)

		self.quit = wx.Button(self.frame, wx.ID_EXIT, '&Quit')
		self.frame.Bind(wx.EVT_BUTTON, self.onQuit, self.quit)
		self.bsizer.Add(self.quit, 0, wx.ALL, 1)

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

		self.statbar = self.frame.CreateStatusBar(3)
		self.statbar.SetStatusWidths([-1, 65, 150])
		self.statbar.PushStatusText("Ready", 0)

		self.frame.SetSizer(self.sizer)
		self.SetTopWindow(self.frame)
		self.frame.Show(True)
		return True

	#---------------------------------------
	def onMaskRegion(self, evt):
		targets1 = self.panel1.getTargets('PickedParticles')
		targets2 = self.panel2.getTargets('PickedParticles')
		#GET IMAGES
		self.panel1.openImageFile(self.panel1.filename)
		self.panel2.openImageFile(self.panel2.filename)
		image1 = numpy.asarray(self.panel1.imagedata, dtype=numpy.float32)
		image2 = numpy.asarray(self.panel2.imagedata, dtype=numpy.float32)
		#SET IMAGE LIMITS
		gap = 16
		xm = image1.shape[0]+gap
		ym = image1.shape[1]+gap
		a1 = numpy.array([ [targets1[0].x, targets1[0].y], [-gap,-gap], [-gap,ym], [xm,ym], [xm,-gap], ])
		xm = image2.shape[0]+gap
		ym = image2.shape[1]+gap
		a2 = numpy.array([ [targets2[0].x, targets2[0].y], [-gap,-gap], [-gap,ym], [xm,ym], [xm,-gap], ])
		#print "a1=",numpy.asarray(a1, dtype=numpy.int32)
		#print "a2=",numpy.asarray(a2, dtype=numpy.int32)
		#SET PARAMETERS
		thetarad = self.theta*math.pi/180.0
		gammarad = self.gamma*math.pi/180.0
		phirad = self.phi*math.pi/180.0
		#CALCULATE TRANSFORM LIMITS
		a1b = tiltDialog.a1Toa2(a1,a2,thetarad,gammarad,phirad,self.shiftx,self.shifty)
		a2b = tiltDialog.a2Toa1(a1,a2,thetarad,gammarad,phirad,self.shiftx,self.shifty)
		#print "a1b=",numpy.asarray(a1b, dtype=numpy.int32)
		#print "a2b=",numpy.asarray(a2b, dtype=numpy.int32)
		#DRAW A POLYGON FROM THE LIMITS
		a1blist = []
		for j in range(4):
			for i in range(2):
				#if a1b[j+1,i] < 0: 
				#	a1b[j+1,i] = 0
				#if a1b[j+1,i] > image2.shape[i]: 
				#	a1b[j+1,i] = image2.shape[i]
				item = int(a1b[j+1,i])
				a1blist.append(item)
		#print "a1b=",numpy.asarray(a1b, dtype=numpy.int32)
		#print "a1blist=",a1blist
		mask2 = numpy.zeros(shape=image2.shape, dtype=numpy.bool_)
		mask2b = apImage.arrayToImage(mask2, normalize=False)
		mask2b = mask2b.convert("L")
		draw2 = ImageDraw.Draw(mask2b)
		draw2.polygon(a1blist, fill="white")
		mask2b.save("mask2b.png", "PNG")
		mask2 = apImage.imageToArray(mask2b, dtype=numpy.float32)
		immin2 = ndimage.minimum(image2)+1.0
		image2 = (image2+immin2)*mask2
		immax2 = ndimage.maximum(image2)
		image2 = numpy.where(image2==0,immax2,image2)
		#DRAW A POLYGON FROM THE LIMITS
		a2blist = []
		for j in range(4):
			for i in range(2):
				#if a2b[j+1,i] < 0: 
				#	a2b[j+1,i] = 0
				#if a2b[j+1,i] > image1.shape[i]: 
				#	a2b[j+1,i] = image1.shape[i]
				item = int(a2b[j+1,i])
				a2blist.append(item)
		#print "a1b=",numpy.asarray(a1b, dtype=numpy.int32)
		#print "a1blist=",a1blist
		mask1 = numpy.zeros(shape=image1.shape, dtype=numpy.bool_)
		mask1b = apImage.arrayToImage(mask1, normalize=False)
		mask1b = mask1b.convert("L")
		draw1 = ImageDraw.Draw(mask1b)
		draw1.polygon(a2blist, fill="white")
		mask1b.save("mask1b.png", "PNG")
		mask1 = apImage.imageToArray(mask1b, dtype=numpy.float32)
		immin1 = ndimage.minimum(image1)+1.0
		image1 = (image1+immin1)*mask1
		immax1 = ndimage.maximum(image1)
		image1 = numpy.where(image1==0,immax1,image1)
		"""
		#CONVERT LIMITS TO A RECTANGLE
		limits2 = numpy.array(
			[[ndimage.minimum(a1b[:,0]), ndimage.minimum(a1b[:,1])],
			[ndimage.maximum(a1b[:,0]), ndimage.maximum(a1b[:,1])]],
			dtype=numpy.int32,
		)
		limits1 = numpy.array( 
			[[ndimage.minimum(a2b[:,0]), ndimage.minimum(a2b[:,1])],
			[ndimage.maximum(a2b[:,0]), ndimage.maximum(a2b[:,1])]],
			dtype=numpy.int32,
		)
		for i in range(2):
			if limits1[0,i] < 0: 
				limits1[0,i] = 0
			if limits2[0,i] < 0: 
				limits2[0,i] = 0
			if limits1[1,i] > image1.shape[i]: 
				limits1[1,i] = image1.shape[i]
			if limits2[1,i] > image2.shape[i]: 
				limits2[1,i] = image2.shape[i]
		#MASK OUT IMAGES
		print "lim1=",limits1[0,0],":",limits1[1,0],",",limits1[0,1],":",limits1[1,1]
		print "lim2=",limits2[0,0],":",limits2[1,0],",",limits2[0,1],":",limits2[1,1]
		image1[0:limits1[0,0]] = 0
		self.panel1.setImage(image1)
		#image2 = image2[limits2[0,0]:limits2[1,0],limits2[0,1]:limits2[1,1]]
		mean2 = ndimage.mean(image2)
		image2[0:limits2[0,0]] = mean2
		image2[0:limits2[0,1]] = mean2
		image2[limits2[1,0]:image2.shape[0]] = mean2
		image2[limits2[1,1]:image2.shape[1]] = mean2
		"""
		self.panel1.setImage(image1)
		self.panel2.setImage(image2)
		#REFRESH SCREEN
		self.panel1.setBitmap()
		self.panel1.setVirtualSize()
		self.panel1.setBuffer()
		self.panel1.UpdateDrawing()
		self.panel2.setBitmap()
		self.panel2.setVirtualSize()
		self.panel2.setBuffer()
		self.panel2.UpdateDrawing()

	#---------------------------------------
	def onUpdate(self, evt):
		#align first
		targets1 = self.panel1.getTargets('PickedParticles')
		a1 = self.targetsToArray(targets1)
		targets2 = self.panel2.getTargets('PickedParticles')
		a2 = self.targetsToArray(targets2)

		thetarad = self.theta*math.pi/180.0
		gammarad = self.gamma*math.pi/180.0
		phirad = self.phi*math.pi/180.0

		#aligned1 = radermacher.transform(a1, a2, self.theta, 0.0, 0.0)
		#x1 = numpy.asarray(a1[:,0] - a1[0,0] + a2[0,0], dtype=numpy.float32)
		#y1 = numpy.asarray(a1[:,1], dtype=numpy.float32)
		#y1 = (y1-y1[0]) * math.cos(self.theta*math.pi/180.0) + float(a2[0,1])
		#a1b = numpy.column_stack((x1,y1))
		#print a1[0:10,:]
		#print a1b[0:10,:]
		a1b = tiltDialog.a1Toa2(a1,a2,thetarad,gammarad,phirad,self.shiftx,self.shifty)
		self.panel2.setTargets('AlignedParticles', a1b)
		
		#align second
		#aligned1 = radermacher.transform(a1, a2, self.theta, 0.0, 0.0)
		#x2 = numpy.asarray(a2[:,0] - a2[0,0] + a1[0,0], dtype=numpy.float32)
		#y2 = numpy.asarray(a2[:,1], dtype=numpy.float32)
		#y2 = (y2-y2[0]) / math.cos(self.theta*math.pi/180.0) + float(a1[0,1])
		#a2b = numpy.column_stack((x2,y2))
		#print a2[0:10,:]
		#print a2b[0:10,:]
		a2b = tiltDialog.a2Toa1(a1,a2,thetarad,gammarad,phirad,self.shiftx,self.shifty)
		self.panel1.setTargets('AlignedParticles', a2b)

	#---------------------------------------
	def targetsToArray(self, targets):
		i = 0
		count = len(targets)
		a = numpy.zeros((count,2), dtype=numpy.int32)
		for t in targets:
			a[i,0] = int(t.x)
			a[i,1] = int(t.y)
			i += 1
		return a

	#---------------------------------------
	def onFitTheta(self, evt):
		if len(self.panel1.getTargets('PickedParticles')) > 3 and len(self.panel2.getTargets('PickedParticles')) > 3:
			self.theta_dialog.tiltvalue.SetLabel(label=("       %3.3f       " % self.theta))
			self.theta_dialog.Show()

	#---------------------------------------
	def onFitAll(self, evt):
		if len(self.panel1.getTargets('PickedParticles')) > 3 and len(self.panel2.getTargets('PickedParticles')) > 3:
			self.fitall_dialog.thetavalue.SetValue(round(self.theta,4))
			self.fitall_dialog.gammavalue.SetValue(round(self.gamma,4))
			self.fitall_dialog.phivalue.SetValue(round(self.phi,4))
			self.fitall_dialog.Show()

	#---------------------------------------
	def onClear(self, evt):
		self.panel1.setTargets('PickedParticles', [])
		self.panel1.setTargets('AlignedParticles', [])
		self.panel2.setTargets('PickedParticles', [])
		self.panel2.setTargets('AlignedParticles', [])

	#---------------------------------------
	def onFileOpen(self, evt):
		dlg = wx.FileDialog(self.frame, "Choose a pick file to open", self.dirname, "", \
			"Text Files (*.txt)|*.txt|All Files|*.*", wx.OPEN)
		if dlg.ShowModal() == wx.ID_OK:
			self.filename = dlg.GetFilename()
			self.dirname  = dlg.GetDirectory()
			try:
				self.openPicksFromFile()
			except:
				self.statbar.PushStatusText("ERROR: Opening file "+self.filename+" failed", 0)
		dlg.Destroy()
 
	#---------------------------------------
	def onFileSave(self, evt):
		if self.filename == "" or self.dirname == "":
			#First Save, Run SaveAs...
			return self.onFileSaveAs(evt)
		self.savePicksToFile()

	#---------------------------------------
	def onFileSaveAs(self, evt):
		dlg = wx.FileDialog(self.frame, "Choose a pick file to save as", self.dirname, "", \
			"Text Files (*.txt)|*.txt|All Files|*.*", wx.SAVE|wx.OVERWRITE_PROMPT)
		#alt1 = "*.[a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9]"
		#alt2 = "Text Files (*.txt)|*.txt|All Files|*.*"
		if dlg.ShowModal() == wx.ID_OK:
			self.filename = dlg.GetFilename()
			self.dirname  = dlg.GetDirectory()
			try:
				self.savePicksToFile()
			except:
				self.statbar.PushStatusText("ERROR: Saving to file "+self.filename+" failed", 0)		
		dlg.Destroy()

	#---------------------------------------
	def savePicksToFile(self):
		targets1 = self.panel1.getTargets('PickedParticles')
		targets2 = self.panel2.getTargets('PickedParticles')
		if len(targets1) < 4 or len(targets2) < 4:
			self.statbar.PushStatusText("ERROR: Cannot save file. Not enough picks", 0)
			return False
		f = open(os.path.join(self.dirname, self.filename),"w")
		f.write( "image 1: "+self.panel1.filename+"\n" )
		for target in targets1:
			f.write( '%d,%d\n' % (target.x, target.y) )
		f.write( "image 2: "+self.panel2.filename+"\n" )
		for target in targets2:
			f.write( '%d,%d\n' % (target.x, target.y) )
		f.close()
		self.statbar.PushStatusText("Saved "+str(len(targets1))+" particles and parameters to "+self.filename, 0)
		return True

	#---------------------------------------
	def openPicksFromFile(self):
		filepath = os.path.join(self.dirname, self.filename)
		f = open(filepath,"r")
		size = int(len(f.readlines())/2-1)
		f.close()
		f = open(filepath,"r")
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
				self.statbar.PushStatusText("Reading picks for image "+str(i),0)
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
		self.statbar.PushStatusText("Read "+str(len(a1))+" particles and parameters from file "+self.filename, 0)

	#---------------------------------------
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



