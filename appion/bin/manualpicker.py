#!/usr/bin/env python

import os
import sys
import wx
import time
import particleLoop2
import apImage
#import subprocess
import apFindEM
import appiondata
import apParticle
import apDatabase
import apDisplay
import apMask
import apImage
import apParam

#Leginon
import polygon
from gui.wx import ImagePanel, ImagePanelTools, TargetPanel, TargetPanelTools
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
	def __init__(self, shape='+', size=16, mask=False):
		self.shape = shape
		self.size = size
		self.mask = mask
		wx.App.__init__(self)

	def OnInit(self):
		self.deselectcolor = wx.Color(240,240,240)

		self.frame = wx.Frame(None, -1, 'Manual Particle Picker')
		self.sizer = wx.FlexGridSizer(3,1)

		### VITAL STATS
		self.vitalstats = wx.StaticText(self.frame, -1, "Vital Stats:  ", style=wx.ALIGN_LEFT)
		#self.vitalstats.SetMinSize((100,40))
		self.sizer.Add(self.vitalstats, 1, wx.EXPAND|wx.ALL, 3)

		### BEGIN IMAGE PANEL
		self.panel = ManualPickerPanel(self.frame, -1)

		self.panel.addTargetTool('Select Particles', color=wx.Color(220,20,20),
			target=True, shape=self.shape, size=self.size)
		self.panel.setTargets('Select Particles', [])
		self.panel.selectiontool.setTargeting('Select Particles', True)

		self.panel.addTargetTool('Region to Remove', color=wx.Color(20,220,20),
			target=True, shape='polygon')
		self.panel.setTargets('Region to Remove', [])
		self.panel.selectiontool.setDisplayed('Region to Remove', True)

		#make 'Select Particles' the initial targeting selection
		self.panel.selectiontool.setTargeting('Select Particles', True)

		self.panel.SetMinSize((300,300))
		self.sizer.Add(self.panel, 1, wx.EXPAND)
		### END IMAGE PANEL

		### BEGIN BUTTONS ROW
		self.buttonrow = wx.FlexGridSizer(1,8)

		self.next = wx.Button(self.frame, wx.ID_FORWARD, '&Forward')
		self.next.SetMinSize((200,40))
		self.Bind(wx.EVT_BUTTON, self.onNext, self.next)
		self.buttonrow.Add(self.next, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.add = wx.Button(self.frame, wx.ID_REMOVE, '&Remove Region')
		self.add.SetMinSize((150,40))
		self.Bind(wx.EVT_BUTTON, self.onAdd, self.add)
		self.buttonrow.Add(self.add, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.clear = wx.Button(self.frame, wx.ID_CLEAR, '&Clear')
		self.clear.SetMinSize((100,40))
		self.Bind(wx.EVT_BUTTON, self.onClear, self.clear)
		self.buttonrow.Add(self.clear, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.revert= wx.Button(self.frame, wx.ID_REVERT_TO_SAVED, 'Revert to Saved')
		self.revert.SetMinSize((80,40))
		self.Bind(wx.EVT_BUTTON, self.onRevert, self.revert)
		self.buttonrow.Add(self.revert, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

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
		self.sizer.AddGrowableRow(1)
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
		vertices = self.panel.getTargetPositions('Region to Remove')
		def reversexy(coord):
			clist=list(coord)
			clist.reverse()
			return tuple(clist)
		vertices = map(reversexy,vertices)

		maskimg = polygon.filledPolygon(self.panel.imagedata.shape,vertices)
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
		self.panel.setTargets('Region to Remove', [])

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

	def onRevert(self, evt):
		self.panel.setTargets('Select Particles', self.panel.originaltargets)


##################################
##################################
##################################
## APPION LOOP
##################################
##################################
##################################

class manualPicker(particleLoop2.ParticleLoop):
	##=======================
	def preLoopFunctions(self):
		apParam.createDirectory(os.path.join(self.params['rundir'], "pikfiles"),warning=False)
		if self.params['sessionname'] is not None:
			self.processAndSaveAllImages()

		self.app = PickerApp(
			shape = self.canonicalShape(self.params['shape']),
			size =  self.params['shapesize'], )
		self.app.appionloop = self
		self.threadJpeg = True

	##=======================
	def postLoopFunctions(self):
		self.app.frame.Destroy()
		apDisplay.printMsg("Finishing up")
		time.sleep(20)
		apDisplay.printMsg("finished")
		wx.Exit()

	##=======================
	def processImage(self, imgdata, filtarray):
		filtfile = os.path.join(self.params['rundir'], imgdata['filename']+".dwn.mrc")
		if not os.path.isfile(filtfile):
			apImage.arrayToMrc(filtarray, filtfile, msg=False)
		peaktree = self.runManualPicker(imgdata)
		return peaktree

	##=======================
	def getParticleParamsData(self):
		manparamsq=appiondata.ApManualParamsData()
		if self.params['pickrunid'] is not None:
			manparamsq['oldselectionrun'] = apParticle.getSelectionRunDataFromID(self.params['pickrunid'])
		return manparamsq

	##=======================
	def commitToDatabase(self, imgdata, rundata):
		if self.assess != self.assessold and self.assess is not None:
			#imageaccessor run is always named run1
			apDatabase.insertImgAssessmentStatus(imgdata, 'run1', self.assess)
		return

	##=======================
	def setupParserOptions(self):
		### Input value options
		self.outtypes = ['text','xml','spider','pickle']
		self.parser.add_option("--outtype", dest="outtype", default="spider",
			help="file output type: "+str(self.outtypes), metavar="TYPE")
		self.parser.add_option("--pickrunid", dest="pickrunid", type="int",
			help="selection run id for previous automated picking run", metavar="#")
		self.parser.add_option("--pickrunname", dest="pickrunname", type="str",
			help="previous selection run name, e.g. --pickrunname=dogrun1", metavar="NAME")
		self.parser.add_option("--shape", dest="shape", default='+',
			help="pick shape")
		self.parser.add_option("--shapesize", dest="shapesize", type="int", default=16,
			help="shape size")
		self.parser.add_option("--mask", dest="checkMask", default=False,
			action="store_true", help="check mask")

	##=======================
	def checkConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		for i,v in enumerate(self.outtypes):
			if self.params['outtype'] == v:
				self.params['outtypeindex'] = i
		if self.params['outtypeindex'] is None:
			apDisplay.printError("outtype must be one of: "+str(self.outtypes)+"; NOT "+str(self.params['outtype']))
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
			if self.params['continue'] is True and os.path.isfile(imgpath):
				sys.stderr.write(".")
				#print "already processed: ",apDisplay.short(imgdata['filename'])
			else:
				if os.path.isfile(imgpath):
					os.remove(imgpath)
				sys.stderr.write("#")
				apFindEM.processAndSaveImage(imgdata, params=self.params)

			if count % 60 == 0:
				sys.stderr.write(" %d left\n" % (total-count))

	def showAssessedMask(self,imgfile,imgdata):
		self.filename = imgfile
		image = pyami.mrc.read(imgfile)
		sessiondata = self.params['session']
		maskassessname = self.params['checkMask']
		mask,maskbin = apMask.makeInspectedMask(sessiondata,maskassessname,imgdata)
		overlay = apMask.overlayMask(image,mask)
		self.app.panel.setImage(overlay.astype(numpy.float32))


	def runManualPicker(self, imgdata):
		#reset targets
		self.app.panel.setTargets('Select Particles', [])
		self.targets = []

		#set the assessment and viewer status
		self.assessold = apDatabase.checkInspectDB(imgdata)
		self.assess = self.assessold
		self.app.setAssessStatus()

		#open new file
		imgname = imgdata['filename']+'.dwn.mrc'
		imgpath = os.path.join(self.params['rundir'],imgname)
		if not self.params['checkMask']:
			self.app.panel.openImageFile(imgpath)
		else:
			self.showAssessedMask(imgpath,imgdata)

		targets = self.getParticlePicks(imgdata)
		if targets:
			print "inserting ",len(targets)," targets"
			self.app.panel.setTargets('Select Particles', targets)
			self.app.panel.originaltargets = targets

		#set vital stats
		self.app.vitalstats.SetLabel("Vital Stats: Image "+str(self.stats['count'])
			+" of "+str(self.stats['imagecount'])+", inserted "+str(len(targets))+" picks, "
			+" image name: "+imgdata['filename'])
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
		apDisplay.printError("This is a dead function")
		particles=apParticle.getParticlesForImageFromRunName(imgdata, self.params['runname'])
		count=0
		if particles:
			print "Deleting old picks"
			for particle in particles:
				#print particle
				count+=1
				#print count,
				particle.remove()
		return

if __name__ == '__main__':
	imgLoop = manualPicker()
	imgLoop.run()




