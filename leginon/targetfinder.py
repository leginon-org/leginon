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
	eventinputs = imagewatcher.ImageWatcher.eventinputs + [event.TargetListDoneEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		self.targetlist = []
		imagewatcher.ImageWatcher.__init__(self, id, session, nodelocations, **kwargs)
		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)
		self.targetlistevents = {}

	def findTargets(self, imdata):
		'''
		this should build self.targetlist, a list of 
		ImageTargetData items.
		'''
		raise NotImplementedError()

	def processImageData(self, imagedata):
		self.findTargets(imagedata)
		self.publishTargetList()

	def publishTargetList(self):


		self.targetsToDatabase()
		if self.targetlist:
			targetlistdata = data.ImageTargetListData(id=self.ID(), targets=self.targetlist)
			## XXX this might not work for mosaic
			## XXX need to publish a mosaic image so this will work
			for targetdata in targetlistdata['targets']:
				targetdata['image'] = self.imagedata

			self.targetlistevents[targetlistdata['id']] = {}
			self.targetlistevents[targetlistdata['id']]['received'] = threading.Event()
			self.targetlistevents[targetlistdata['id']]['stats'] = 'waiting'

			self.publish(targetlistdata, pubevent=True)

			# wait for target list to be processed by other node
			if self.wait_for_done.get():
				self.waitForTargetListDone()

		self.targetlist = []


	def waitForTargetListDone(self):
		for tid, teventinfo in self.targetlistevents.items():
			print 'waiting for target list %s to complete' % (tid,)
			teventinfo['received'].wait()
		self.targetlistevents.clear()

	def passTargets(self, targetlistdata):
		## create an event watcher for each target we pass
		#for target in targetlistdata['targets']:
		#	targetid = target['id']
		#	## maybe should check if already waiting on this target?
		#	self.targetevents[targetid] = {}
		#	self.targetevents[targetid]['received'] = threading.Event()
		#	self.targetevents[targetid]['status'] = 'waiting'

		self.targetlistevents[targetlistdata['id']] = {}
		self.targetlistevents[targetlistdata['id']]['received'] = threading.Event()
		self.targetlistevents[targetlistdata['id']]['stats'] = 'waiting'

		self.publish(targetlistdata, pubevent=True)



	def handleTargetListDone(self, targetlistdoneevent):
		targetlistid = targetlistdoneevent['targetlistid']
		status = targetlistdoneevent['status']
		print 'got targetlistdone event, setting threading event', targetlistid
		if targetlistid in self.targetlistevents:
			self.targetlistevents[targetlistid]['status'] = status
			self.targetlistevents[targetlistid]['received'].set()
		self.confirmEvent(targetlistdoneevent)

	def targetsToDatabase(self):
		for target in self.targetlist:
			self.publish(target, database=True)

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)
		# turn off data queue by default
		self.uidataqueueflag.set(False)

		self.wait_for_done = uidata.Boolean('Wait for "Done"', True, 'rw', persist=True)

		container = uidata.MediumContainer('Target Finder')
		container.addObjects((self.wait_for_done,))

		self.uiserver.addObject(container)


class ClickTargetFinder(TargetFinder):
	def __init__(self, id, session, nodelocations, **kwargs):
		TargetFinder.__init__(self, id, session, nodelocations, **kwargs)

		self.userpause = threading.Event()

		if self.__class__ == ClickTargetFinder:
			self.defineUserInterface()
			self.start()

	def OLDprocessImageData(self, imagedata):
		'''
		redefined because this is manual target finding
		We don't want to call findTargets because it is not
		implemented.  Instead, let user select targets, then
		publish targets as a user activated step.
		'''
		pass

	def findTargets(self, imdata):
		## display image
		self.clickimage.setTargets([])
		self.clickimage.setImage(imdata['image'])

		## user now clicks on targets
		self.userpause.clear()
		self.userpause.wait()
		self.getTargetDataList('Focus Target', data.FocusTargetData)
		self.getTargetDataList('Imaging Target', data.AcquisitionImageTargetData)

	def submitTargets(self):
		self.userpause.set()

	def defineUserInterface(self):
		TargetFinder.defineUserInterface(self)
		self.clickimage = uidata.TargetImage('Clickable Image', None, 'rw')
		self.clickimage.addTargetType('Imaging Target')
		self.clickimage.addTargetType('Focus Target')
		#advancemethod = uidata.Method('Advance Image', self.advanceImage)
		submitmethod = uidata.Method('Submit Targets', self.submitTargets)
		container = uidata.MediumContainer('Click Target Finder')
		container.addObjects((submitmethod, self.clickimage))
		self.uiserver.addObject(container)

	def OLDadvanceImage(self):
		if self.processDataFromQueue():
			self.currentimage = self.numarray
		else:
			self.currentimage = None
		self.clickimage.setImage(self.currentimage)
		self.clickimage.setTargets([])

	def OLDsubmitTargets(self):
		self.processTargets()
		self.clickimage.setTargets([])

	def OLDprocessTargets(self):
		self.getTargetDataList('Focus Target', data.FocusTargetData)
		self.getTargetDataList('Imaging Target', data.AcquisitionImageTargetData)
		self.publishTargetList()

	def getTargetDataList(self, typename, datatype):
		for imagetarget in self.clickimage.getTargetType(typename):
			column, row = imagetarget
			# using self.currentiamge.shape could be bad
			target = {'delta row': row - self.numarray.shape[0]/2,
								'delta column': column - self.numarray.shape[1]/2}
			imageinfo = self.imageInfo()
			target.update(imageinfo)
			targetdata = datatype(id=self.ID())
			targetdata.friendly_update(target)
			self.targetlist.append(targetdata)

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
		initializer = {'id': self.ID(), 'data IDs': []}
		self.mosaicdata = data.MosaicData(initializer=initializer)
		if self.__class__ == MosaicClickTargetFinder:
			self.defineUserInterface()
			self.start()

	def processImageData(self, imagedata):
		ClickTargetFinder.processImageData(self, imagedata)
		self.mosaic.addTile(imagedata)
		self.mosaicdata['data IDs'].append(imagedata['id'])
		self.clickimage.setImage(self.mosaic.getMosaicImage())
		# needs to update target positions
		self.clickimage.setTargets([])

	def mosaicToDatabase(self):
		if self.mosaicdata['session'] is not None:
			if self.mosaicdata['session']['name'] != self.session['name']:
				self.outputError('Cannot save loaded mosaic.')
				return
		mosaicdata = self.mosaicdata
		initializer = {'id': self.ID(), 'data IDs': list(mosaicdata['data IDs'])}
		self.mosaicdata = data.MosaicData(initializer=initializer)
		self.publish(mosaicdata, database=True)

	def updateMosaicSelection(self):
		sessioninitializer = {'user': self.session['user'],
													'instrument': self.session['instrument']}
		session = data.SessionData(initializer=sessioninitializer)
		initializer = {'session': session}
		instance = data.MosaicData(initializer=initializer)
		mosaics = self.research(datainstance=instance)
		self.mosaicselectionmapping = {}
		for mosaic in mosaics:
			key = str(mosaic['session']['name']) + ' ' + str(mosaic['id'])
			self.mosaicselectionmapping[key] = mosaic
		self.mosaicselection.set(self.mosaicselectionmapping.keys(), 0)

	def mosaicFromDatabase(self):
		key = self.mosaicselection.getSelectedValue()
		try:
			mosaicdata = self.mosaicselectionmapping[key]
		except KeyError:
			self.outputError('Invalid mosaic selected.')
			return
		self.mosaic.clear()
		mosaicsession = mosaicdata['session']
		print 'mosaicsession =', mosaicsession
		for dataid in mosaicdata['data IDs']:
			initializer = {'id': dataid, 'session': mosaicsession}
			print 'initializer =', initializer
			instance = data.AcquisitionImageData(initializer=initializer)
			imagedatalist = self.research(datainstance=instance) #, results=1)
			try:
				imagedata = imagedatalist[0]
			except IndexError:
				#self.outputWarning('Cannot find image data referenced by mosaic')
				print 'Cannot find image data referenced by mosaic'
			else:
				self.mosaic.addTile(imagedata)
		self.mosaicdata = mosaicdata
		self.clickimage.setImage(self.mosaic.getMosaicImage())
		self.clickimage.setTargets([])

	def getTargetDataList(self, typename, datatype):
		for imagetarget in self.clickimage.getTargetType(typename):
			x, y = imagetarget
			target = self.mosaic.getTargetInfo(x, y)
			imageinfo = self.imageInfo()
			### just need preset, everythin else is there already
			target['preset'] = imageinfo['preset']

			targetdata = datatype(id=self.ID())
			targetdata.friendly_update(target)
			self.targetlist.append(targetdata)

	#def advanceImage(self):
	#	pass

	def mosaicClear(self):
		self.mosaic.clear()
		initializer = {'id': self.ID(), 'data IDs': []}
		self.mosaicdata = data.MosaicData(initializer=initializer)
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
		# turn queue off by default
		self.uidataqueueflag.set(False)

		self.mosaicselection = uidata.SingleSelectFromList('Mosaic', [], 0)
		self.updateMosaicSelection()
		refreshmethod = uidata.Method('Refresh', self.updateMosaicSelection)
		loadmethod = uidata.Method('Load', self.mosaicFromDatabase)
		loadcontainer = uidata.Container('Load')
		loadcontainer.addObjects((self.mosaicselection, refreshmethod,
																											loadmethod))
		savecurrentmethod = uidata.Method('Save Current', self.mosaicToDatabase)
		savecontainer = uidata.Container('Save')
		savecontainer.addObjects((savecurrentmethod,))
		databasecontainer = uidata.Container('Database')
		databasecontainer.addObjects((loadcontainer, savecontainer))

		parameters = self.mosaic.getCalibrationParameters()
		parameter = parameters.index(self.mosaic.getCalibrationParameter())
		self.uicalibrationparameter = uidata.SingleSelectFromList(
																			'Calibration Parameter', parameters,
																			parameter,
																			callback=self.uiSetCalibrationParameter,
																			persist=True)
		clearmethod = uidata.Method('Reset Mosaic', self.mosaicClear)
		container = uidata.MediumContainer('Mosaic Click Target Finder')
		container.addObjects((databasecontainer, clearmethod,
													self.uicalibrationparameter))
		self.uiserver.addObject(container)

