#!/usr/bin/env python

import threading
import imagewatcher
import node, event, data
import Queue
import Mrc
import uidata
import Numeric
import mosaic

import xmlrpclib
#import xmlrpclib2 as xmlbinlib
xmlbinlib = xmlrpclib

# TO DO:
#  - every TargetFinder should have optional target editing before publishing
#  - a lot of work to reorganize this class hierarchy
#       - everything to do with ImageTargetData should be in this module
#               (not in imagewatcher)

class TargetFinder(imagewatcher.ImageWatcher):
	def __init__(self, id, session, nodelocations, **kwargs):
		self.targetlist = []
		imagewatcher.ImageWatcher.__init__(self, id, session, nodelocations, **kwargs)

	def findTargets(self, numarray):
		'''
		this should build self.targetlist, a list of 
		ImageTargetData items.
		'''
		raise NotImplementedError()

	def processData(self, newdata):
		imagewatcher.ImageWatcher.processData(self, newdata)

		print 'findTargets'
		self.findTargets(newdata)
		print 'publishTargets'
		self.publishTargetList()
		print 'DONE'

	def publishTargetList(self):
		if self.targetlist:
			targetlistdata = data.ImageTargetListData(self.ID(), targets=self.targetlist)
			print 'TARGETLISTDATA'
			for targetdata in targetlistdata['targets']:
				print targetdata['id']
				
			self.publish(targetlistdata, pubevent=True)

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)
		# turn on data queue by default
		self.uidataqueueflag.set(True)

class ClickTargetFinder(TargetFinder):
	def __init__(self, id, session, nodelocations, **kwargs):
		TargetFinder.__init__(self, id, session, nodelocations, **kwargs)

		self.userbusy = threading.Condition()
		self.processlock = threading.Lock()
		self.currentimage = None

		self.defineUserInterface()
		self.start()

	def processData(self, newdata):
		'''
		redefined because this is manual target finding
		Instead of calling findTargets, let uiImage get the image
		Then call publishTargetList in another function
		'''
		imagewatcher.ImageWatcher.processData(self, newdata)
		
	def defineUserInterface(self):
		TargetFinder.defineUserInterface(self)
		self.clickimage = uidata.UITargetImage('Clickable Image', None, 'rw')
		self.clickimage.addTargetType('Imaging Target')
		self.clickimage.addTargetType('Focus Target')
		advancemethod = uidata.UIMethod('Advance Image', self.advanceImage)
		submitmethod = uidata.UIMethod('Submit Targets', self.submitTargets)
		container = uidata.UIMediumContainer('Click Target Finder')
		container.addUIObjects((advancemethod, submitmethod, self.clickimage))
		self.uiserver.addUIObject(container)

#		tfspec = TargetFinder.defineUserInterface(self)
#
#		clickimage = self.registerUIData('Clickable Image', 'binary', callback=self.uiImage, permissions='rw')
#		myspec = self.registerUISpec('Click Target Finder', (clickimage,))
#		myspec += tfspec
#		return myspec

#	def uiImage(self, value=None):
#		'''
#		get next image from queue
#		'''
#		if value is None:
#			### Get image from queue and set current image
#			if self.currentimage is None:
#				if self.processDataFromQueue():
#					self.currentimage = self.numarray
#				else:
#					self.currentimage = None
#
#			### return current image
#			if self.currentimage is None:
#				mrcstr = ''
#			else:
#				mrcstr = Mrc.numeric_to_mrcstr(self.currentimage)
#			return xmlbinlib.Binary(mrcstr)
#		else:
#			### submit targets from GUI
#			self.submitTargets(value)
#
#			## I don't think this is necessary
#			#return xmlbinlib.Binary('')

	def advanceImage(self):
		if self.processDataFromQueue():
			self.currentimage = self.numarray
		else:
			self.currentimage = None
		self.clickimage.setImage(self.currentimage)
		self.clickimage.setTargets([])

	def submitTargets(self):
		self.processTargets()
		self.clickimage.setTargets([])

	def processTargets(self):
		self.targetlist += self.getTargetDataList('Focus Target',
																							data.FocusTargetData)
		self.targetlist += self.getTargetDataList('Imaging Target',
																							data.ImageTargetData)
		self.publishTargetList()

	def getTargetDataList(self, typename, datatype):
		targetlist = []
		for imagetarget in self.clickimage.getTargetType(typename):
			column, row = imagetarget
			# using self.currentiamge.shape could be bad
			target = {'delta row': row - self.currentimage.shape/2,
								'delta column': column - self.currentimage.shape/2}
			imageinfo = self.imageInfo()
			target.update(imageinfo)
			targetdata = datatype(self.ID(), target)
			self.targetlist.append(targetdata)
		return targetlist

#	def submitTargets(self, targetlist):
#		self.targetlist = []
#		for target in targetlist:
#			### attach some image info about this one
#			imageinfo = self.imageInfo()
#			target.update(imageinfo)
#			# hopefully target matches ImageTargetData
#			print 'TARGET', target.keys()
#			print 'TARGET button', target['button']
#			b = target['button']
#			del target['button']
#			if b == 1:
#				targetdata = data.ImageTargetData(self.ID(), target)
#			elif b == 2:
#				targetdata = data.FocusTargetData(self.ID(), target)
#			else:
#				raise RuntimeError('unknown button %s' % (b,))
#
#			print 'TARGETDATA append', targetdata['id']
#			self.targetlist.append(targetdata)
#		for targetdata in self.targetlist:
#			print 'TARGETDATA later', targetdata['id']
#		self.publishTargetList()
#		self.currentimage = None

# perhaps this should be a 'mixin' class so it can work with any target finder
class MosaicClickTargetFinder(ClickTargetFinder):
	def __init__(self, id, session, nodelocations, **kwargs):
		ClickTargetFinder.__init__(self, id, session, nodelocations, **kwargs)
		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position':
												calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.mosaic = mosaic.EMMosaic(self.calclients)

	def processData(self, newdata):
		ClickTargetFinder.processData(self, newdata)
		self.mosaic.addTile(newdata['image'], newdata['scope'], newdata['camera'])
		self.clickimage.setImage(self.mosaic.getMosaicImage())
		# needs to update target positions
		self.clickimage.setTargets([])

	def getTargetDataList(self, typename, datatype):
		targetlist = []
		for imagetarget in self.clickimage.getTargetType(typename):
			x, y = imagetarget
			target = self.mosaic.getTargetInfo(x, y)
			imageinfo = self.imageInfo()
			target.update(imageinfo)
			targetdata = datatype(self.ID(), target)
			self.targetlist.append(targetdata)
		return targetlist

	def advanceImage(self):
		pass

	def defineUserInterface(self):
		ClickTargetFinder.defineUserInterface(self)
		clearmethod = uidata.UIMethod('Reset Mosaic', self.mosaic.clear)
		container = uidata.UIMediumContainer('Mosaic Click Target Finder')
		container.addUIObjects((clearmethod))
		self.uiserver.addUIObject(container)

