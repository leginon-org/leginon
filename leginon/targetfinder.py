#!/usr/bin/env python

import threading
import imagewatcher
import node, event, data
import Queue
import Mrc
import uidata
import Numeric
import mosaic
import calibrationclient
import camerafuncs

import xmlrpclib
#import xmlrpclib2 as xmlbinlib
xmlbinlib = xmlrpclib

# TO DO:
#  - every TargetFinder should have optional target editing before publishing
#  - a lot of work to reorganize this class hierarchy
#       - everything to do with ImageTargetData should be in this module
#               (not in imagewatcher)

class TargetFinder(imagewatcher.ImageWatcher):
	eventoutputs = imagewatcher.ImageWatcher.eventoutputs + [event.ImageTargetListPublishEvent]
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

		self.findTargets(newdata)
		self.publishTargetList()

	def publishTargetList(self):
		if self.targetlist:
			targetlistdata = data.ImageTargetListData(id=self.ID(), targets=self.targetlist)
			for targetdata in targetlistdata['targets']:
				targetdata['image id'] = self.imagedata['id']
				
			self.publish(targetlistdata, pubevent=True)

		self.targetsToDatabase()
		self.targetlist = []

	def targetsToDatabase(self):
		for target in self.targetlist:
			self.publish(target, database=True)

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

		if self.__class__ == ClickTargetFinder:
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
		self.clickimage = uidata.TargetImage('Clickable Image', None, 'rw')
		self.clickimage.addTargetType('Imaging Target')
		self.clickimage.addTargetType('Focus Target')
		advancemethod = uidata.Method('Advance Image', self.advanceImage)
		submitmethod = uidata.Method('Submit Targets', self.submitTargets)
		container = uidata.MediumContainer('Click Target Finder')
		container.addObjects((advancemethod, submitmethod, self.clickimage))
		self.uiserver.addObject(container)

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
			target = {'delta row': row - self.currentimage.shape[0]/2,
								'delta column': column - self.currentimage.shape[1]/2}
			imageinfo = self.imageInfo()
			target.update(imageinfo)
			targetdata = datatype(id=self.ID())
			targetdata.friendly_update(target)
			self.targetlist.append(targetdata)
		return targetlist

# perhaps this should be a 'mixin' class so it can work with any target finder
class MosaicClickTargetFinder(ClickTargetFinder):
	def __init__(self, id, session, nodelocations, **kwargs):
		ClickTargetFinder.__init__(self, id, session, nodelocations, **kwargs)
		self.cam = camerafuncs.CameraFuncs(self)
		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position':
												calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.mosaic = mosaic.EMMosaic(self.calclients)
		if self.__class__ == MosaicClickTargetFinder:
			self.defineUserInterface()
			self.start()

	def processData(self, newdata):
		ClickTargetFinder.processData(self, newdata)
		self.mosaic.addTile(newdata)
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
			targetdata = datatype(id=self.ID())
			targetdata.friendly_update(target)
			self.targetlist.append(targetdata)
		return targetlist

	#def advanceImage(self):
	#	pass

	def mosaicClear(self):
		self.mosaic.clear()
		self.clickimage.setImage(None)

	def uiSetCalibrationParameter(self, value):
		if not hasattr(self, 'uicalibrationparameter'):
			return value
		parameter = self.uicalibrationparameter.getSelectedValue(value)
		try:
			self.mosaic.setCalibrationParameter(parameter)
		except ValueError:
			self.printerror('invalid calibration parameter specified')
		return value

	def defineUserInterface(self):
		ClickTargetFinder.defineUserInterface(self)
		parameters = self.mosaic.getCalibrationParameters()
		parameter = parameters.index(self.mosaic.getCalibrationParameter())
		self.uicalibrationparameter = uidata.SingleSelectFromList(
																'Calibration Parameter', parameters, parameter,
																callback=self.uiSetCalibrationParameter)
		clearmethod = uidata.Method('Reset Mosaic', self.mosaicClear)
		container = uidata.MediumContainer('Mosaic Click Target Finder')
		container.addObjects((clearmethod, self.uicalibrationparameter))
		self.uiserver.addObject(container)

