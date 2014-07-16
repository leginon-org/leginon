#!/usr/bin/env python

import os
import sys
import operator
import wx
import time
import math
import numpy
#import subprocess
from appionlib import particleLoop2
from appionlib import apFindEM
from appionlib import appiondata
from appionlib import apParticle
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib import apMask
from appionlib import apImage
from appionlib import apParam

#Leginon
import leginon.polygon
from leginon.gui.wx import ImagePanel, ImagePanelTools, TargetPanel, TargetPanelTools
import pyami.mrc


## need better way to generate a list of easy to distinguish colors
pick_colors = [
	(255,0,0),
	(0,255,0),
	(0,0,255),
	(255,255,0),
	(255,0,255),
	(0,255,255),
	(128,128,0),
	(128,0,128),
	(0,128,128),
	(255,128,128),
	(128,255,128),
	(128,128,255),
]

class ManualPickerPanel(TargetPanel.TargetImagePanel):
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
	def __init__(self, shape='+', size=16, usehelix=False, mask=False, labels=[]):
		self.shape = shape
		self.size = size
		self.usehelix = usehelix
		self.mask = mask
		self.pick_colors = iter(pick_colors)
		self.labels = labels
		wx.App.__init__(self)

	def OnInit(self):
		self.deselectcolor = wx.Colour(240,240,240)

		self.frame = wx.Frame(None, -1, 'Manual Particle Picker')
		self.sizer = wx.FlexGridSizer(3,1)

		### VITAL STATS
		self.vitalstats = wx.StaticText(self.frame, -1, "Vital Stats:  ", style=wx.ALIGN_LEFT)
		#self.vitalstats.SetMinSize((100,40))
		self.sizer.Add(self.vitalstats, 1, wx.EXPAND|wx.ALL, 3)

		### BEGIN IMAGE PANEL
		self.panel = ManualPickerPanel(self.frame, -1)
		self.panel.originaltargets = {}

		if self.usehelix is True:
			self.panel.addTargetTool('Add Helix', color=wx.Colour(20,220,20),
				target=True, shape='spline')
			self.panel.setTargets('Add Helix', [])
			self.panel.selectiontool.setDisplayed('Add Helix', True)
			self.panel.addTargetTool('Stored Helices', color=wx.Colour(200,0,0),
				target=True, shape='spline')
			self.panel.setTargets('Stored Helices', [])
			self.panel.selectiontool.setDisplayed('Stored Helices', True)
		else:
			self.panel.addTargetTool('Region to Remove', color=wx.Colour(20,220,20),
				target=True, shape='polygon')
			self.panel.setTargets('Region to Remove', [])
			self.panel.selectiontool.setDisplayed('Region to Remove', True)

			for label in self.labels:
				self.addLabelPicker(label)

		# make first target type the initial targeting selection
		if self.labels:
			self.panel.selectiontool.setTargeting(self.labels[0], True)

		self.panel.SetMinSize((300,300))
		self.sizer.Add(self.panel, 1, wx.EXPAND)
		### END IMAGE PANEL

		### BEGIN BUTTONS ROW
		self.buttonrow = wx.FlexGridSizer(1,9)

		self.next = wx.Button(self.frame, wx.ID_FORWARD, '&Forward')
		self.next.SetMinSize((200,40))
		self.Bind(wx.EVT_BUTTON, self.onNext, self.next)
		self.buttonrow.Add(self.next, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		### Helix picker doesn't have 'remove region'
		if self.usehelix is False:
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

		if self.usehelix is True:
			self.helicalinsert = wx.Button(self.frame, -1, '&Add Helix')
			self.helicalinsert.SetMinSize((120,40))
			self.Bind(wx.EVT_BUTTON, self.addHelix, self.helicalinsert)
			#self.helicalinsert = wx.Button(self.frame, -1, '&Helical insert')
			#self.helicalinsert.SetMinSize((120,40))
			#self.Bind(wx.EVT_BUTTON, self.onHelicalInsert, self.helicalinsert)
			self.buttonrow.Add(self.helicalinsert, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

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

		self.assessreject = wx.ToggleButton(self.frame, -1, "Re&ject")
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

	def addLabelPicker(self, label):
		rgb = self.pick_colors.next()
		self.panel.addTargetTool(label, color=wx.Colour(*rgb),
			target=True, shape=self.shape, size=self.size)
		self.panel.setTargets(label, [])
		self.panel.selectiontool.setTargeting(label, True)

	def onQuit(self, evt):
		for label in self.labels:
			targets = self.panel.getTargets(label)
			for target in targets:
				print '%s\t%s\t%s' % (label, target.x, target.y)
		wx.Exit()

	def onAdd(self, evt):
		vertices = []
		vertices = self.panel.getTargetPositions('Region to Remove')
		apDisplay.printMsg("Removing region contained in %d polygon vertices"%(len(vertices)))
		def reversexy(coord):
			clist=list(coord)
			clist.reverse()
			return tuple(clist)
		vertices = map(reversexy,vertices)

		maskimg = leginon.polygon.filledPolygon(self.panel.imagedata.shape,vertices)
		type(maskimg)
		for label in self.labels:
			targets = self.panel.getTargets(label)
			eliminated = 0
			newparticles = []
			for target in targets:
				coord = (target.y,target.x)
				if maskimg[coord] != 0:
					eliminated += 1
				else:
					newparticles.append(target)
			apDisplay.printMsg("%d particle(s) eliminated due to masking"%(eliminated))
			self.panel.setTargets(label,newparticles)

		self.panel.setTargets('Region to Remove', [])

	def onNext(self, evt):
		#targets = self.panel.getTargets('Select Particles')
		#for target in targets:
		#	print '%s\t%s' % (target.x, target.y)
		if self.usehelix is False:
			vertices = self.panel.getTargetPositions('Region to Remove')
			if len(vertices) > 0:
				apDisplay.printMsg("Clearing %d polygon vertices"%(len(vertices)))
				self.panel.setTargets('Region to Remove', [])
		## add any green particle picks to 'Stored Helices'
		else:
			self.addHelix(evt)
		self.appionloop.targets = {}
		for label in self.labels:
			self.appionloop.targets[label] = self.panel.getTargets(label)
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
		self.assessnone.SetBackgroundColour(wx.Colour(200,200,0))
		self.assesskeep.SetValue(0)
		self.assesskeep.SetBackgroundColour(self.deselectcolor)
		self.assessreject.SetValue(0)
		self.assessreject.SetBackgroundColour(self.deselectcolor)
		self.assess = None

	def onToggleKeep(self, evt):
		self.assessnone.SetValue(0)
		self.assessnone.SetBackgroundColour(self.deselectcolor)
		self.assesskeep.SetValue(1)
		self.assesskeep.SetBackgroundColour(wx.Colour(0,200,0))
		self.assessreject.SetValue(0)
		self.assessreject.SetBackgroundColour(self.deselectcolor)
		self.assess = True


	def onToggleReject(self, evt):
		self.assessnone.SetValue(0)
		self.assessnone.SetBackgroundColour(self.deselectcolor)
		self.assesskeep.SetValue(0)
		self.assesskeep.SetBackgroundColour(self.deselectcolor)
		self.assessreject.SetValue(1)
		self.assessreject.SetBackgroundColour(wx.Colour(200,0,0))
		self.assess = False

	def onClear(self, evt):
		for label in self.labels:
			self.panel.setTargets(label, [])
		self.panel.setTargets('Region to Remove', [])

	def onRevert(self, evt):
		if self.panel.originaltargets:
			for label,targets in self.panel.originaltargets.items():
				self.panel.setTargets(label, targets)

	def targetsToArray(self, targets):
		a = []
		for t in targets:
			if t.x and t.y:
				a.append([ int(t.x), int(t.y) ])
				
		na = numpy.array(a, dtype=numpy.int32)
		return na

	def addHelix(self,evt):
		"""
		store list of points as a new helix, and add
		to list of helices
		"""
		### determine which particle label to operate on
		userlabel = 'Add Helix'
		helicallabel = 'Stored Helices'
		### get the selected user targets
		usertargets = self.panel.getTargets(userlabel)
		helicaltargets = self.panel.getTargets(helicallabel)

		if len(usertargets) < 2:
			apDisplay.printWarning("not enough targets")
			return
		userarray = self.targetsToArray(usertargets)
		helicalarray = self.targetsToArray(helicaltargets)
		if len(helicalarray)==0:
			self.hnums={}
			hnum=1
		else:
			hnum = helicaltargets[-1].stats['helixnum']+1
		## set the helix number for these new coordinates
		helicalpoints = list(helicalarray)
		for c in userarray:
			x = c[0]
			y = c[1]
			helicalpoints.append((x,y))
			try:
				self.hnums[x,y]
			except:
				self.hnums[x,y]=hnum
		newhelicalpoints = []
		for point in helicalpoints:
			x = point[0]
			y = point[1]
			h = {'helixnum':self.hnums[x,y]}
			newhelicalpoints.append({'x':x,'y':y,'stats':h})
		self.panel.setTargets(helicallabel, newhelicalpoints)
		self.panel.setTargets(userlabel, [])

	def onHelicalInsert(self, evt):
		"""
		connect the last two targets by filling inbetween
		copied from EMAN1 boxer
		"""
		### determine which particle label to operate on
		userlabel = 'User'
		helicallabel = 'Helical'
		### get last two user targets
		usertargets = self.panel.getTargets(userlabel)
		helicaltargets = self.panel.getTargets(helicallabel)
		if len(usertargets) == 2:
			self.angles = {}
		if len(usertargets) < 2:
			apDisplay.printWarning("not enough targets")
			return
		if len(usertargets) > 2 and not helicaltargets:
			apDisplay.printWarning("too many targets")
			return
		userarray = self.targetsToArray(usertargets)
		helicalarray = self.targetsToArray(helicaltargets)
		### get pixelsize
		apix = self.appionloop.params['apix']
		if not apix or apix == 0.0:
			apDisplay.printWarning("unknown pixel size")
			return
		### get helicalstep
		ovrlp = 1 - (self.appionloop.params['ovrlp']/100.00)
		if ovrlp == 0:
			helicalstep = self.appionloop.params['helicalstep']
		else:
			helicalstep = int(self.appionloop.params['helicalstep']*ovrlp)
		if not helicalstep:
			apDisplay.printWarning("unknown helical step size")
			return

		first = userarray[-2]
		last = userarray[-1]
		### Do tan(y,x) to be consistent with ruler tool, convert to x,y in makestack
		angle = math.degrees(math.atan2((last[1]*1.0 - first[1]),(last[0] - first[0])))
		stats = {'angle': angle}	
		pixeldistance = math.hypot(first[0] - last[0], first[1] - last[1])
		if pixeldistance == 0:
			### this will probably never happen since mouse does not let you click same point twice
			apDisplay.printWarning("points have zero distance")
			return
		stepsize = helicalstep/(pixeldistance*apix*self.appionloop.params['bin'])
		### parameterization of a line btw points (x1,y1) and (x2,y2):
		# x = (1 - t)*x1 + t*x2,
		# y = (1 - t)*y1 + t*y2,
		# t { [0,1] ; t is a real number btw 0 and 1
		helicalpoints = list(helicalarray)
		t = 0.0
		while t < 1.0:
			x = int(round( (1.0 - t)*first[0] + t*last[0], 0))
			y = int(round( (1.0 - t)*first[1] + t*last[1], 0))
			helicalpoints.append((x,y))
			self.angles[x,y] = angle
			t += stepsize
		newhelicalpoints = []
		for point in helicalpoints:
			x = point[0]
			y = point[1]
			stats = {'angle': self.angles[x,y]}
			newhelicalpoints.append({'x': x, 'y': y, 'stats': stats})	

		self.panel.setTargets(helicallabel, newhelicalpoints)
		
		
		
		


##################################
##################################
##################################
## APPION LOOP
##################################
##################################
##################################

class ManualPicker(particleLoop2.ParticleLoop):
	def onInit(self):
		super(ManualPicker,self).onInit()
		self.trace = False
		
	def setApp(self):
		self.app = PickerApp(
			shape = self.canonicalShape(self.params['shape']),
			size =  self.params['shapesize'],
			usehelix =  self.params['helix'],
			labels = self.labels,
		)

	##=======================
	def preLoopFunctions(self):
		apParam.createDirectory(os.path.join(self.params['rundir'], "pikfiles"),warning=False)
		if self.params['sessionname'] is not None:
			self.processAndSaveAllImages()

		## use labels from params if specified
		if self.params['labels']:
			self.labels = self.params['labels']
		else:
			self.labels = []

		### this is confusing and needs someone to look at it.
		if self.params['helicalstep']:
			self.labels = ['User', 'Helical']
		if self.params['helix'] is True:
			self.labels = ['Add Helix', 'Stored Helices']
		## If no labels specified or previous picks to get labels from,
		##   then use default label 'particle'.
		if not self.labels:
			self.labels = ['particle_w/o_label']

		self.setApp()
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
		manparamsq['trace'] = self.trace
		if self.params['helicalstep'] is not None:
			manparamsq['helicalstep'] = self.params['helicalstep']
		manparamsq['diam'] = self.params['diam']
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
		self.parser.add_option("--helicalstep", dest="helicalstep", type="float",
			help="helical step size (in Angstroms)")
		self.parser.add_option("--helix", dest="helix", default=False, action="store_true",
			help="draw lines along helices instead of particles")
		self.parser.add_option("--ovrlp", dest="ovrlp", type="int",
			help="percent overlap")
		self.parser.add_option("--mask", dest="checkMask", default=False,
			action="store_true", help="check mask")
		self.parser.add_option("--label", dest="labels", action="append", help="Add a label. All labels will be availabe for picking.")

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
		# reserve 'fromtrace' for particles created from center of the traced results
		# self.params['labels'] default is None, not []
		if self.params['labels'] and 'fromtrace' in self.params['labels']:
			apDisplay.printError('"fromtrace" is a reserved label. Use another name')
		if self.params['labels'] and '_trace' in self.params['labels']:
			apDisplay.printError('"_trace" is a reserved label for centers created from traced object. You can cause confusion if you mean other things')
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
		if not self.params['pickrunname']:
			rundata = apParticle.getSelectionRunDataFromID(self.params['pickrunid'])
			self.params['pickrunname'] = rundata['name']
		particles = apParticle.getParticles(imgdata, self.params['pickrunid'])
		targets = self.particlesToTargets(particles)
		return targets

	def particlesToTargets(self, particles):
		targets = {}
		for p in particles:
			label = p['label']
			if label is None:
				# if there is no label, it adopts the pickrunname if new label is specified or a dummy "particle_w/o_label"
				if self.params['labels']:
					label = self.params['pickrunname']
					i = 0
					while label in self.params['labels']:
						label = self.params['pickrunname']+'_orig%d' % i
						i += 1
				else:
					label = 'particle_w/o_label'
			else:
				if self.params['labels'] is not None and label not in self.params['labels']:
					print "ERROR: It is too late to add old labels to the gui"
			if label not in targets:
				targets[label] = []
			targets[label].append( (p['xcoord']/self.params['bin'], p['ycoord']/self.params['bin']) )
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
		sessiondata = self.params['sessionname']
		maskassessname = self.params['checkMask']
		mask,maskbin = apMask.makeInspectedMask(sessiondata,maskassessname,imgdata)
		overlay = apMask.overlayMask(image,mask)
		self.app.panel.setImage(overlay.astype(numpy.float32))

	def runManualPicker(self, imgdata):
		#reset targets
		self.targets = {}
		for label in self.labels:
			self.app.panel.setTargets(label, [])
			self.targets[label] = []

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
			for label in targets.keys():
				if label not in self.labels:
					self.labels.append(label)
					self.app.addLabelPicker(label)
			for label in self.labels:
				if label not in targets:
					targets[label] = []
				print "inserting ",len(targets[label]),"%s targets" % (label,)
				self.app.panel.setTargets(label, targets[label])
				self.app.panel.originaltargets[label] = targets[label]
		# labels may have changed, default selection is the first one
		if self.labels:
			self.app.panel.selectiontool.setTargeting(self.labels[0], True)

		#set vital stats
		self.app.vitalstats.SetLabel("Vital Stats: Image "+str(self.stats['count'])
			+" of "+str(self.stats['imagecount'])+", inserted "+str(self.stats['peaksum'])+" picks, "
			+" image name: "+imgdata['filename'])
		#run the picker
		self.app.MainLoop()

		#targets are copied to self.targets by app
		#assessment is copied to self.assess by app
		#parse and return the targets in peaktree form
		self.app.panel.openImageFile(None)
		peaktree=[]
		for label,targets in self.targets.items():
			for target in targets:	
				angle=None
				helixnum=None
				if isinstance(target, leginon.gui.wx.TargetPanelTools.StatsTarget):
					t = target.stats
					if t.has_key('angle'):
						angle = target.stats['angle']
					if t.has_key('helixnum'):
						helixnum = target.stats['helixnum']
				peaktree.append(self.XY2particle(target.x, target.y, angle, helixnum, label))

		# if any peak has an angle, then remove all peaks that do not have an angle
		#if peaktree:
		#	def hasangle(x):
		#		try:
		#			return 'angle' in x
		#		except:
		#			return False
		#	haveangles = map(hasangle, peaktree)
		#	anyangles = reduce(operator.or_, haveangles)
		#	if anyangles:	
		#		before = len(peaktree)	
		#		peaktree = filter(hasangle, peaktree)
		#		after = len(peaktree)
		#		diff = before - after
		#		apDisplay.printWarning("Removed %d particles with no angle"%(diff))

		return peaktree

	def XY2particle(self, binx, biny, angle=None, helixnum=None, label=None):
		peak={}
		peak['xcoord'] = binx*self.params['bin']
		peak['ycoord'] = biny*self.params['bin']
		if angle is not None:
			peak['angle'] = angle
		if helixnum is not None:
			peak['helixnum'] = helixnum
		peak['correlation'] = None
		peak['peakmoment'] = None
		peak['peakstddev'] = None
		peak['peakarea'] = 1
		peak['tmplnum'] = None
		peak['template'] = None
		if label != 'particle_w/o_label':
			peak['label'] = label
		return peak

if __name__ == '__main__':
	imgLoop = ManualPicker()
	imgLoop.run()




