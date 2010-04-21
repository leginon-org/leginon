#!/usr/bin/env python

import os
import sys
import wx
import time
from appionlib import apImage
import manualpicker
from PIL import Image
#import subprocess
from appionlib import appiondata
from appionlib import apParticle
from appionlib import apDatabase
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apMask
from appionlib import apCrud
from appionlib import apFindEM
from appionlib import filterLoop

#Leginon
import leginon.leginondata
import leginon.polygon
from leginon.gui.wx import ImagePanel, ImagePanelTools, TargetPanel, TargetPanelTools
import pyami
import numpy
import pyami.quietscipy
import scipy.ndimage as nd

class ManualMaskMakerPanel(manualpicker.ManualPickerPanel):
	def __init__(self, parent, id, callback=None, tool=True):
		manualpicker.ManualPickerPanel.__init__(self, parent, id, callback=callback, tool=tool)

	def openImageFile(self, filename):
		self.filename = filename
		print filename
		if filename is None:
			self.setImage(None)
		elif filename[-4:] == '.mrc':
			image = pyami.mrc.read(filename)
		else:
			image = Image.open(filename)
		if (filename):
			self.setImage(image.astype(numpy.float32))
			self.image = image
			self.maskimg =  numpy.zeros(self.image.shape)
##################################
##
##################################

class MaskApp(manualpicker.PickerApp):
	#def __init__(self,  shape='+', size=16, mask=True):
	def __init__(self):
		manualpicker.PickerApp.__init__(self, shape='+', size=16, mask=True)

	def OnInit(self):
		self.deselectcolor = wx.Color(240,240,240)

		self.frame = wx.Frame(None, -1, 'Manual Mask Maker')
		self.sizer = wx.FlexGridSizer(3,1)
		### VITAL STATS
		self.vitalstats = wx.StaticText(self.frame, -1, "Vital Stats:  ", style=wx.ALIGN_LEFT)
		#self.vitalstats.SetMinSize((100,40))
		self.sizer.Add(self.vitalstats, 1, wx.EXPAND|wx.ALL, 3)

		### BEGIN IMAGE PANEL
		self.panel = ManualMaskMakerPanel(self.frame, -1)

#		self.panel.addTypeTool('Select Particles', toolclass=TargetPanelTools.TargetTypeTool,
#			display=wx.Color(220,20,20), target=True, shape=self.shape, size=self.size)

#		self.panel.setTargets('Select Particles', [])
#		self.panel.selectiontool.setTargeting('Select Particles', True)

		self.panel.addTypeTool('Region to Remove', toolclass=TargetPanelTools.TargetTypeTool,
			display=wx.GREEN, target=True, shape='polygon')
		self.panel.setTargets('Region to Remove', [])
		self.panel.selectiontool.setTargeting('Region to Remove', True)


		self.panel.SetMinSize((300,300))
		self.sizer.Add(self.panel, 1, wx.EXPAND)
		### END IMAGE PANEL

		### BEGIN BUTTONS ROW
		self.buttonrow = wx.FlexGridSizer(1,7)

		self.next = wx.Button(self.frame, wx.ID_FORWARD, '&Forward')
		self.next.SetMinSize((200,40))
		self.Bind(wx.EVT_BUTTON, self.onNext, self.next)
		self.buttonrow.Add(self.next, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.add = wx.Button(self.frame, wx.ID_REMOVE, '&Add to Mask')
		self.add.SetMinSize((150,40))
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
		self.sizer.AddGrowableRow(1)
		self.sizer.AddGrowableCol(0)
		self.frame.SetSizerAndFit(self.sizer)
		self.SetTopWindow(self.frame)
		self.frame.Show(True)

		return True

	def onQuit(self, evt):
		wx.Exit()

	def onAdd(self, evt):
		vertices = []
		vertices = self.panel.getTargetPositions('Region to Remove')
		def reversexy(coord):
			clist=list(coord)
			clist.reverse()
			return tuple(clist)
		vertices = map(reversexy,vertices)

		polygonimg = leginon.polygon.filledPolygon(self.panel.imagedata.shape,vertices)
		type(polygonimg)
		self.panel.maskimg = self.panel.maskimg + polygonimg

		overlay = apMask.overlayMask(self.panel.image,self.panel.maskimg)
		self.panel.setImage(overlay.astype(numpy.float32))

		self.panel.setTargets('Region to Remove', [])

	def onNext(self, evt):
		#targets = self.panel.getTargets('Select Particles')
		#for target in targets:
		#	print '%s\t%s' % (target.x, target.y)
		self.appionloop.maskimg = self.panel.maskimg
		self.appionloop.image = self.panel.image
		self.appionloop.assess = self.finalAssessment()
		self.Exit()


	def onClear(self, evt):
		self.panel.setTargets('Region to Remove', [])
		self.panel.maskimg = numpy.zeros(self.panel.image.shape)
		self.panel.setImage(self.panel.image)

##################################
##################################
##################################
## APPION LOOP
##################################
##################################
##################################

class manualPicker(filterLoop.FilterLoop):
	def preLoopFunctions(self):
		apParam.createDirectory(os.path.join(self.params['rundir'], "masks"),warning=False)
		if self.params['sessionname'] is not None:
			self.processAndSaveAllImages()
		self.app = MaskApp()
		self.app.appionloop = self
		self.threadJpeg = True

	def postLoopFunctions(self):
		self.app.frame.Destroy()
		apDisplay.printMsg("Finishing up")
		time.sleep(10)
		apDisplay.printMsg("finished")
		wx.Exit()

	def processImage(self, imgdata,filterarray):
		if self.params['sessionname'] is not None:
			apFindEM.processAndSaveImage(imgdata, params=self.params)
		self.runManualPicker(imgdata)

	def commitToDatabase(self,imgdata):
		sessiondata = imgdata['session']
		rundir = self.params['rundir']
		maskname = self.params['runname']
		assessname = self.params['assessname']
		bin = self.params['bin']
		maskdir=os.path.join(rundir,"masks")
		maskrundata,maskparamsdata = apMask.getMaskParamsByRunName(maskname,sessiondata)
		if not maskrundata:
			apMask.insertManualMaskRun(sessiondata,rundir,maskname,bin)
			maskrundata,maskparamsdata = apMask.getMaskParamsByRunName(maskname,sessiondata)
			try:
				apParam.createDirectory(maskdir)
			except:
				apDisplay.printWarning('can not create mask directory')
		massessrundata,exist = apMask.insertMaskAssessmentRun(sessiondata,maskrundata,assessname)
		mask = self.maskimg
		image = self.image
		labeled_regions,clabels=nd.label(mask)
		testlog = [False,0,""]
		infos={}
		infos,testlog=apCrud.getLabeledInfo(image,mask,labeled_regions,range(1,clabels+1),False,infos,testlog)
		maskfilename = imgdata['filename']+'_mask.png'
		offset=1
		for l1 in range(0,len(infos)):

			l=l1+offset
			info=infos[l]
			info.append(l)
			regiondata= apMask.insertMaskRegion(maskrundata,imgdata,info)
		# PIL alpha channel read does not work
		#apImage.arrayMaskToPngAlpha(mask, os.path.join(maskdir,maskfilename))
		apImage.arrayMaskToPng(mask, os.path.join(maskdir,maskfilename))
		allregiondata = apMask.getMaskRegions(maskrundata,imgdata)
		for regiondata in allregiondata:
			apMask.insertMaskAssessment(massessrundata,regiondata,1)

		if self.assess != self.assessold and self.assess is not None:
			#imageaccessor run is always named run1
			apDatabase.insertImgAssessmentStatus(imgdata, 'run1', self.assess)
		return

	def specialCreateOutputDirs(self):
		self._createDirectory(os.path.join(self.params['rundir'], "masks"),warning=False)

	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --session <session name> --runame <new or maskrunname> [--pickrunid <id>]  \n\t ")
		self.parser.add_option("--assess", dest="assessname",
			help="New mask assessment run name", metavar="NAME")
		self.parser.add_option("--pickrunid", dest="pickrunid", type="int",
			help="id of the particle pick to be displayed", metavar="#")
		self.parser.add_option("--pickrunname", dest="pickrunname",
			help="Name of the particle pick to be displayed", metavar="NAME")
		self.parser.add_option("--checkmask", "--maskassess", dest="checkmask", default=False,
			action="store_true", help="Check mask")

	def checkConflicts(self):
		if self.params['commit'] and self.params['continue']==False:
			q = leginon.leginondata.SessionData(name=self.params['sessionname'])
			results = q.query(results=1)
			sessiondata = results[0]
			maskname = self.params['runname']
			maskrundata,maskparamsdata = apMask.getMaskParamsByRunName(maskname,sessiondata)
			if maskrundata:
				apDisplay.printWarning("Overwrite commited maskrun is not allowed")
				wx.Exit()

	###################################################
	##### END PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	###################################################


	def getParticlePicks(self, imgdata):
		return []


	def processAndSaveAllImages(self):
		sys.stderr.write("Pre-processing images before picking\n")
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

	def runManualPicker(self, imgdata):
		#reset targets
		self.targets = []

		#set the assessment status
		self.assessold = apDatabase.checkInspectDB(imgdata)
		self.assess = self.assessold
		self.app.setAssessStatus()

		#open new file
		imgname = imgdata['filename']+'.dwn.mrc'
		imgpath = os.path.join(self.params['rundir'],imgname)
		if not self.params['checkmask']:
			self.app.panel.openImageFile(imgpath)
		else:
			self.showAssessedMask(imgpath,imgdata)


		#set vital stats
		self.app.vitalstats.SetLabel(
			" image name: "+imgdata['filename'])
		#run the picker
		self.app.MainLoop()

		#targets are copied to self.targets by app
		#assessment is copied to self.assess by app
		self.app.panel.openImageFile(None)


if __name__ == '__main__':
	imgLoop = manualPicker()
	imgLoop.run()




