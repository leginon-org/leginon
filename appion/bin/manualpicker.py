#!/usr/bin/python -O

import os
import sys
import wx
import time
import particleLoop
import apImage
#import subprocess
import apFindEM
import appionData
import apParticle
import apDatabase
import apDisplay
import apMask

#Leginon
import polygon
try:
	from gui.wx import ImagePanel, ImagePanelTools, TargetPanel, TargetPanelTools
except ImportError:
	from  gui.wx import ImageViewer
	ImagePanel = ImageViewer
	ImagePanelTools = ImageViewer
	TargetPanel = ImageViewer
	TargetPanelTools = ImageViewer
import pyami
import numpy

class ManualPickerPanel(TargetPanel.TargetImagePanel):
	def __init__(self, parent, id, callback=None, tool=True):
		TargetPanel.TargetImagePanel.__init__(self, parent, id, callback=callback, tool=tool)

	def openImageFile(self, filename):
		self.filename = filename
		if filename is None:
			self.setImage(None)
		elif filename[-4:] == '.mrc':
			image = pyami.mrc.read(filename)
			self.setImage(image.astype(numpy.float32))
		else:
			self.setImage(Image.open(filename))

##################################
##
##################################

class PickerApp(wx.App):
	def OnInit(self):
		self.deselectcolor = wx.Color(240,240,240)

		self.frame = wx.Frame(None, -1, 'Manual Particle Picker')
		self.sizer = wx.FlexGridSizer(2,1)

		### BEGIN IMAGE PANEL
		self.panel = ManualPickerPanel(self.frame, -1)
		self.target = 'x'
		if self.target =='o':
			#	circle target for seeing particle in the middle
			self.panel.addTypeTool('Select Particles', toolclass=TargetPanelTools.TargetTypeTool,
				display=wx.RED, target=True, shape='o', size=25)
		else:
			self.panel.addTypeTool('Select Particles', toolclass=TargetPanelTools.TargetTypeTool,
				display=wx.RED, target=True, numbers=True, shape='x')
		self.panel.setTargets('Select Particles', [])
		self.panel.selectiontool.setTargeting('Select Particles', True)

		self.panel.addTypeTool('Particle Mask', toolclass=TargetPanelTools.TargetTypeTool,
			display=wx.GREEN, target=True, shape='polygon')
		self.panel.setTargets('Particle Mask', [])
		self.panel.selectiontool.setTargeting('Particle Mask', True)

		self.panel.SetMinSize((300,300))
		self.sizer.Add(self.panel, 1, wx.EXPAND)
		### END IMAGE PANEL

		### BEGIN BUTTONS ROW
		self.buttonrow = wx.FlexGridSizer(1,7)

		self.next = wx.Button(self.frame, wx.ID_FORWARD, '&Forward')
		self.next.SetMinSize((200,40))
		self.Bind(wx.EVT_BUTTON, self.onNext, self.next)
		self.buttonrow.Add(self.next, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.add = wx.Button(self.frame, wx.ID_REMOVE, '&Remove Region')
		self.add.SetMinSize((100,40))
		self.Bind(wx.EVT_BUTTON, self.onAdd, self.add)
		self.buttonrow.Add(self.add, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.clear = wx.Button(self.frame, wx.ID_CLEAR, '&Clear')
		self.clear.SetMinSize((100,40))
		self.Bind(wx.EVT_BUTTON, self.onClear, self.clear)
		self.buttonrow.Add(self.clear, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "Image Assessment:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.assessnone = wx.ToggleButton(self.frame, -1, "&None")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleNone, self.assessnone)
		self.assessnone.SetValue(0)
		#self.assessnone.SetBackgroundColour(self.selectcolor)
		self.assessnone.SetMinSize((100,40))
		self.buttonrow.Add(self.assessnone, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.assesskeep = wx.ToggleButton(self.frame, -1, "&Keep")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleKeep, self.assesskeep)
		self.assesskeep.SetValue(0)
		self.assesskeep.SetMinSize((100,40))
		self.buttonrow.Add(self.assesskeep, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.assessreject = wx.ToggleButton(self.frame, -1, "&Reject")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleReject, self.assessreject)
		self.assessreject.SetValue(0)
		self.assessreject.SetMinSize((100,40))
		self.buttonrow.Add(self.assessreject, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
		### END BUTTONS ROW

		self.sizer.Add(self.buttonrow, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
		self.sizer.AddGrowableRow(0)
		self.sizer.AddGrowableCol(0)
		self.frame.SetSizerAndFit(self.sizer)
		self.SetTopWindow(self.frame)
		self.frame.Show(True)
		return True

	def onQuit(self, evt):
		targets = self.panel.getTargets('Select Particles')
		for target in targets:
			print '%s\t%s' % (target.x, target.y)
		wx.Exit()

	def onAdd(self, evt):
		vertices = []
		vertices = self.panel.getTargetPositions('Particle Mask')
		def reversexy(coord):
			clist=list(coord)
			clist.reverse()
			return tuple(clist)
		vertices = map(reversexy,vertices)
		maskimg = polygon.filledPolygon(self.shape,vertices)
		type(maskimg)
		targets = self.panel.getTargets('Select Particles')
		eliminated = 0
		newparticles = []
		for target in targets:
			coord = (target.y,target.x)
			if maskimg[coord] != 0:
				eliminated += 1
			else:
				newparticles.append(target)
		print eliminated,"particle(s) eliminated due to masking"
		self.panel.setTargets('Select Particles',newparticles)
		self.panel.setTargets('Particle Mask', [])
		
	def onNext(self, evt):
		#targets = self.panel.getTargets('Select Particles')
		#for target in targets:
		#	print '%s\t%s' % (target.x, target.y)
		self.appionloop.targets = self.panel.getTargets('Select Particles')
		self.appionloop.assess = self.finalAssessment()
		self.Exit()

	def finalAssessment(self):
		if self.assessnone.GetValue() is True:
			return None
		elif self.assesskeep.GetValue() is True:
			return True
		elif self.assessreject.GetValue() is True:
			return False
		return None

	def setAssessStatus(self):
		if self.appionloop.assess is True:
			self.onToggleKeep(None)
		elif self.appionloop.assess is False:
			self.onToggleReject(None)
		else:
			self.onToggleNone(None)

	def onToggleNone(self, evt):
		self.assessnone.SetValue(1)
		self.assessnone.SetBackgroundColour(wx.Color(200,200,0))
		self.assesskeep.SetValue(0)
		self.assesskeep.SetBackgroundColour(self.deselectcolor)
		self.assessreject.SetValue(0)
		self.assessreject.SetBackgroundColour(self.deselectcolor)
		self.assess = None

	def onToggleKeep(self, evt):
		self.assessnone.SetValue(0)
		self.assessnone.SetBackgroundColour(self.deselectcolor)
		self.assesskeep.SetValue(1)
		self.assesskeep.SetBackgroundColour(wx.Color(0,200,0))
		self.assessreject.SetValue(0)
		self.assessreject.SetBackgroundColour(self.deselectcolor)
		self.assess = True


	def onToggleReject(self, evt):
		self.assessnone.SetValue(0)
		self.assessnone.SetBackgroundColour(self.deselectcolor)
		self.assesskeep.SetValue(0)
		self.assesskeep.SetBackgroundColour(self.deselectcolor)
		self.assessreject.SetValue(1)
		self.assessreject.SetBackgroundColour(wx.Color(200,0,0))
		self.assess = False

	def onClear(self, evt):
		self.panel.setTargets('Select Particles', [])


##################################
##
##################################

class manualPicker(particleLoop.ParticleLoop):
	def preLoopFunctions(self):
		if self.params['dbimages'] or self.params['alldbimages']:
			self.processAndSaveAllImages()
		self.app = PickerApp()
		self.app.appionloop = self
		self.threadJpeg = True

	def postLoopFunctions(self):
		self.app.frame.Destroy()
		apDisplay.printMsg("Finishing up")
		time.sleep(20)
		apDisplay.printMsg("finished")
		wx.Exit()

	def particleProcessImage(self, imgdata):
		if not self.params['dbimages'] and not self.params['alldbimages']:
			apFindEM.processAndSaveImage(imgdata, params=self.params)
		peaktree = self.runManualPicker(imgdata)
		#peaktree = self.runManualPickerOld(imgdata)
		return peaktree

	def getParticleParamsData(self):
		manparamsq=appionData.ApManualParamsData()
		if self.params['pickrunid'] is not None:
			manparamsq['oldselectionrun'] = apParticle.getSelectionRunDataFromID(self.params['pickrunid'])
		return manparamsq

	def particleCommitToDatabase(self, imgdata):
		if self.assess != self.assessold and self.assess is not None:
			#imageaccessor run is always named run1
			apDatabase.insertImgAssessmentStatus(imgdata, 'run1', self.assess)
		return

	def particleDefaultParams(self):
		self.params['mapdir']="manualmaps"
		self.params['pickrunname'] = None
		self.params['pickrunid'] = None

	def particleCreateOutputDirs(self):
		self._createDirectory(os.path.join(self.params['rundir'], "pikfiles"),warning=False)

	def particleParseParams(self, args):
		for arg in args:
			elements = arg.split('=')
			elements[0] = elements[0].lower()
			if (elements[0]=='pickrunid'):
				self.params['pickrunid']=int(elements[1])
			elif (elements[0]=='pickrunname'):
				self.params['pickrunname']=str(elements[1])
			else:
				apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

	###################################################
	##### END PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	###################################################

	def getParticlePicks(self, imgdata):
		if not self.params['pickrunid']:
			if not self.params['pickrunname']:
				return []
			self.params['pickrunid'] = apParticle.getSelectionRun(imgdata, self.params['pickrunname'])
			#particles = apParticle.getParticlesForImageFromRunName(imgdata, self.params['pickrunname'])
		particles = apParticle.getParticles(imgdata, self.params['pickrunid'])
		targets = self.particlesToTargets(particles)
		return targets

	def particlesToTargets(self, particles):
		targets = []
		for p in particles:
			targets.append( (p['xcoord']/self.params['bin'], p['ycoord']/self.params['bin']) )
		return targets

	def processAndSaveAllImages(self):
		sys.stderr.write("Pre-processing images before picking\n")
		#print self.params
		count = 0
		total = len(self.imgtree)
		for imgdata in self.imgtree:
			count += 1
			imgpath = os.path.join(self.params['rundir'], imgdata['filename']+'.dwn.mrc')
			if self.params['continue'] == False:
				if os.path.isfile(imgpath):
					os.remove(imgpath)
				apFindEM.processAndSaveImage(imgdata, params=self.params)
			else:
				if os.path.isfile(imgpath):
					sys.stderr.write(".")
					#print "already processed: ",apDisplay.short(imgdata['filename'])
				else:
					sys.stderr.write("#")
					apFindEM.processAndSaveImage(imgdata, params=self.params)

			if count % 60 == 0:
				sys.stderr.write(" %d left\n" % (total-count))

	def showMask(self,imgfile,imgdata):
		self.filename = imgfile
		image = pyami.mrc.read(imgfile)
		sessiondata = self.params['session']
		maskassessname = self.params['checkMask']
		mask,maskbin = apMask.makeInspectedMask(sessiondata,maskassessname,imgdata)
		overlay = apMask.overlayMask(image,mask)
		self.app.panel.setImage(overlay.astype(numpy.float32))
		self.app.shape = overlay.shape

	
	def runManualPicker(self, imgdata):
		#reset targets
		self.app.panel.setTargets('Select Particles', [])
		self.targets = []

		#set the assessment status
		self.assessold = apDatabase.getImgAssessmentStatus(imgdata)
		self.assess = self.assessold
		self.app.setAssessStatus()
					
		#open new file
		imgname = imgdata['filename']+'.dwn.mrc'
		imgpath = os.path.join(self.params['rundir'],imgname)
		if not self.params['checkMask']:
			self.app.panel.openImageFile(imgpath)
		else:
			self.showMask(imgpath,imgdata)

		targets = self.getParticlePicks(imgdata)
		if targets:
			print "inserting ",len(targets)," targets"
			self.app.panel.setTargets('Select Particles', targets)

		#run the picker
		self.app.MainLoop()

		#targets are copied to self.targets by app
		#assessment is copied to self.assess by app
		#parse and return the targets in peaktree form
		self.app.panel.openImageFile(None)
		peaktree=[]
		for target in self.targets:
			peaktree.append(self.XY2particle(target.x, target.y))
		return peaktree

	def runManualPickerOld(self, imgdata):
		#use ImageViewer to pick particles
		#this is a total hack but an idea that can be expanded on
		imgname = imgdata['filename']+'.dwn.mrc'
		imgpath = os.path.join(self.params['rundir'],imgname)
		commandlst = ['ApImageViewer.py',imgpath]
		manpicker = subprocess.Popen(commandlst,stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		outstring = manpicker.stdout.read()
		words = outstring.split()
		peaktree=[]
		#print outstring
		#print words
		for xy in range(0,len(words)/2):
			binx = int(words[2*xy])
			biny = int(words[2*xy+1])
			peaktree.append(self.XY2particle(binx, biny))
		#print peaktree
		return peaktree

	def XY2particle(self, binx, biny):
		peak={}
		peak['xcoord'] = binx*self.params['bin']
		peak['ycoord'] = biny*self.params['bin']
		peak['correlation'] = None
		peak['peakmoment'] = None
		peak['peakstddev'] = None
		peak['peakarea'] = 1
		peak['tmplnum'] = None
		peak['template'] = None
		return peak

	def deleteOldPicks(self, imgdata):
		particles=apParticle.getParticlesForImageFromRunName(imgdata, self.params['runid'])
		count=0
		if particles:
			print "Deleting old picks"
			for particle in particles:
				#print particle
				count+=1
				#print count,
				self.appiondb.remove(particle)
		return

if __name__ == '__main__':
	imgLoop = manualPicker()
	imgLoop.run()



