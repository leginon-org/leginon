#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import calibrationclient
import camerafuncs
import data
import event
import imagewatcher
import mosaic
import Mrc
import threading
import uidata

class TargetFinder(imagewatcher.ImageWatcher):
	eventoutputs = imagewatcher.ImageWatcher.eventoutputs + [
																							event.ImageTargetListPublishEvent]
	eventinputs = imagewatcher.ImageWatcher.eventinputs + [
																							event.TargetListDoneEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		self.targetlist = []
		self.targetlistevents = {}
		imagewatcher.ImageWatcher.__init__(self, id, session, nodelocations,
																				**kwargs)
		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)

	def researchImageTargets(self, imagedata):
		'''
		Get a list of all targets that have this image as their parent.
		'''
		targetquery = data.AcquisitionImageTargetData()
		imagequery = data.AcquisitionImageData(initializer=imagedata)
		imagequery['image'] = None
		targetquery['image'] = imagequery
		targets = self.research(datainstance=targetquery, fill=False)
		return targets

	def lastTargetIndex(self, imagedata):
		'''
		Returns the index of the last target associated with the given image data.
		'''
		targets = self.researchImageTargets(imagedata)
		maxindex = 0
		for target in targets:
			if target['index'] > maxindex:
				maxindex = target['index']
		return maxindex

	def findTargets(self, imdata):
		'''
		Virtual function, inherehiting classes implement building self.targetlist,
		a list of ImageTargetData items.
		'''
		raise NotImplementedError()

	def processImageData(self, imagedata):
		'''
		Gets and publishes target information of specified image data.
		'''
		if self.ignore_images.get():
			return
		self.findTargets(imagedata)
		self.publishTargetList()

	def publishTargetList(self):
		'''
		Updates and publishes the target list self.targetlist. Waits for target
		to be "done" if specified.
		'''
		index = 1
		for target in self.targetlist:
			# XXX this might not work for mosaic
			# XXX need to publish a mosaic image so this will work
			target['index'] = index
			index += 1
			print 'TARGET publishing %s' % (target['id'],)
			self.publish(target, database=True)

		if self.targetlist:
			targetlistdata = data.ImageTargetListData(id=self.ID(),
																								targets=self.targetlist)

			self.makeTargetListEvent(targetlistdata)

			self.publish(targetlistdata, pubevent=True)

			# wait for target list to be processed by other node
			if self.wait_for_done.get():
				self.waitForTargetListDone()

		self.targetlist = []

	def makeTargetListEvent(self, targetlistdata):
		'''
		Creates a threading event to be waited on for target list data.
		'''
		self.targetlistevents[targetlistdata['id']] = {}
		self.targetlistevents[targetlistdata['id']]['received'] = threading.Event()
		self.targetlistevents[targetlistdata['id']]['stats'] = 'waiting'

	def waitForTargetListDone(self):
		'''
		Waits until theading events of all target list data are cleared.
		'''
		for tid, teventinfo in self.targetlistevents.items():
			print '%s WAITING for %s' % (self.id,tid,)
			teventinfo['received'].wait()
			print '%s DONE WAITING for %s' % (self.id,tid,)
		self.targetlistevents.clear()
		print '%s DONE WAITING' % (self.id,)

	def passTargets(self, targetlistdata):
		'''
		???
		'''
		self.makeTargetListEvent(targetlistdata)
		self.publish(targetlistdata, pubevent=True)

	def handleTargetListDone(self, targetlistdoneevent):
		'''
		Receives a target list done event and sets the threading event.
		'''
		targetlistid = targetlistdoneevent['targetlistid']
		status = targetlistdoneevent['status']
		print 'got targetlistdone event, setting threading event', targetlistid
		if targetlistid in self.targetlistevents:
			self.targetlistevents[targetlistid]['status'] = status
			self.targetlistevents[targetlistid]['received'].set()
		self.confirmEvent(targetlistdoneevent)

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)

		# turn off data queuing by default
		self.uidataqueueflag.set(False)

		self.wait_for_done = uidata.Boolean('Wait for "Done"', True, 'rw', persist=True)
		self.ignore_images = uidata.Boolean('Ignore Images', False, 'rw', persist=True)

		container = uidata.LargeContainer('Target Finder')
		container.addObjects((self.wait_for_done,self.ignore_images))

		self.uiserver.addObject(container)

class ClickTargetFinder(TargetFinder):
	def __init__(self, id, session, nodelocations, **kwargs):
		TargetFinder.__init__(self, id, session, nodelocations, **kwargs)

		self.userpause = threading.Event()

		if self.__class__ == ClickTargetFinder:
			self.defineUserInterface()
			self.start()

	def findTargets(self, imdata):
		# display image
		self.clickimage.setTargets([])
		self.clickimage.setImage(imdata['image'])
		self.clickimage.imagedata = imdata

		# user now clicks on targets
		self.userpause.clear()
		self.userpause.wait()
		self.targetlist += self.getTargetDataList('focus')
		self.targetlist += self.getTargetDataList('acquisition')

	def submitTargets(self):
		self.userpause.set()

	def newTargetData(self, imagedata, type, drow, dcol):
		'''
		returns a new target data object with data filled in from the image data
		'''
		imagearray = imagedata['image']
		targetdata = data.AcquisitionImageTargetData(id=self.ID(), type=type, version=0)
		targetdata['image'] = imagedata
		targetdata['scope'] = imagedata['scope']
		targetdata['camera'] = imagedata['camera']
		targetdata['preset'] = imagedata['preset']
		targetdata['type'] = type
		targetdata['delta row'] = drow
		targetdata['delta column'] = dcol
		return targetdata

	def getTargetDataList(self, typename):
		targetlist = []
		for imagetarget in self.clickimage.getTargetType(typename):
			column, row = imagetarget
			imagedata = self.clickimage.imagedata
			imagearray = imagedata['image']
			drow = row - imagearray.shape[0]/2
			dcol = column - imagearray.shape[1]/2

			targetdata = self.newTargetData(imagedata, typename, drow, dcol)
			targetlist.append(targetdata)
		return targetlist

	def defineUserInterface(self):
		TargetFinder.defineUserInterface(self)

		self.clickimage = uidata.TargetImage('Clickable Image', None, 'rw')
		self.clickimage.addTargetType('acquisition')
		self.clickimage.addTargetType('focus')

		submitmethod = uidata.Method('Submit Targets', self.submitTargets)

		container = uidata.LargeContainer('Click Target Finder')
		container.addObjects((self.clickimage, submitmethod))

		self.uiserver.addObject(container)

class MosaicClickTargetFinder(ClickTargetFinder):
	eventoutputs = ClickTargetFinder.eventoutputs + [event.MosaicDoneEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		self.mosaicselectionmapping = {}
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

	# not complete
	def handleTargetListDone(self, targetlistdoneevent):
		self.setStatusMessage('Target list done')
		#ClickTargetFinder.handleTargetListDone(self, targetlistdoneevent)
		self.mosaicToDatabase()
		self.mosaicClear()
		self.outputEvent(event.MosaicDoneEvent())
		self.setStatusMessage('Mosaic is done, notification sent')

	def submitTargets(self):
		self.setStatusMessage('Sumbiting targets')
		targetlist = self.getTargetDataList('acquisition')
		self.targetlist.extend(targetlist)
		self.publishTargetList()
		self.setStatusMessage('Targets submitted')

	def processImageData(self, imagedata):
		'''
		different from ClickTargetFinder because findTargets is
		not per image, instead we have submitTargets.
		'''
		self.setStatusMessage('Processing inbound image data')
		#ClickTargetFinder.processImageData(self, imagedata)
		self.setStatusMessage('Adding image to mosaic')
		self.mosaic.addTile(imagedata)
		self.mosaicdata['data IDs'].append(imagedata['id'])
		self.setStatusMessage('Image added to mosaic')
		self.displayMosaic()
		self.setStatusMessage('Image data processed')

	def mosaicToDatabase(self):
		if not self.mosaicdata['data IDs']:
			self.setStatusMessage('Mosaic is empty')
			return

		if self.mosaicdata['session'] is not None:
			if self.mosaicdata['session']['name'] != self.session['name']:
				self.setStatusMessage(
											'Cannot publish a mosaic loaded from a different session')
				return

		self.setStatusMessage('Publishing mosaic data')

		mosaicdata = self.mosaicdata
		initializer = {'id': self.ID(), 'data IDs': list(mosaicdata['data IDs'])}
		self.mosaicdata = data.MosaicData(initializer=initializer)
		self.publish(mosaicdata, database=True)

		self.setStatusMessage('Publishing mosaic image data')

		mosaicimagedata = data.MosaicImageData()
		mosaicimagedata['id'] = self.ID()
		mosaicimagedata['mosaic'] = mosaicdata
		mosaicimagedata['image'] = self.getMosaicImage()
		mosaicimagedata['scale'] = self.mosaic.scale
		self.publish(mosaicimagedata, database=True)

		self.setStatusMessage('Mosaic published')

	def updateMosaicSelection(self):
		self.setStatusMessage('Updating mosaic selection')
		try:
			sessioninitializer = {'user': self.session['user'],
														'instrument': self.session['instrument']}
		except TypeError:
			self.mosaicselection.set([], 0)
			self.setStatusMessage(
												'No session availible to determine user and instrument')
			return
		session = data.SessionData(initializer=sessioninitializer)
		initializer = {'session': session}
		instance = data.MosaicData(initializer=initializer)
		self.setStatusMessage('Finding mosaics')
		mosaics = self.research(datainstance=instance)
		self.mosaicselectionmapping = {}
		for mosaic in mosaics:
			key = str(mosaic['session']['name']) + ' ' + str(mosaic['id'])
			self.mosaicselectionmapping[key] = mosaic
		self.mosaicselection.set(self.mosaicselectionmapping.keys(), 0)
		self.setStatusMessage('Mosaic selection updated')

	def mosaicFromDatabase(self):
		self.setStatusMessage('Loading mosaic')
		key = self.mosaicselection.getSelectedValue()
		try:
			mosaicdata = self.mosaicselectionmapping[key]
		except KeyError:
			self.setStatusMessage('Invalid mosaic selected')
			return
		self.setStatusMessage('Clearing mosaic')
		self.mosaic.clear()
		mosaicsession = mosaicdata['session']
		self.setStatusMessage('Finding mosaic images and data')
		n = len(mosaicdata['data IDs'])
		nloaded = 0
		for i, dataid in enumerate(mosaicdata['data IDs']):
			# create an instance model to query
			inst = data.AcquisitionImageData()
			# these are known:
			inst['id'] = dataid
			inst['session'] = mosaicsession
			# this are unknown, but we need them:
			inst['scope'] = data.ScopeEMData()
			inst['camera'] = data.CameraEMData()
			inst['preset'] = data.PresetData()
			self.setStatusMessage('Finding image %i of %i' % (i + 1, n))
			imagedatalist = self.research(datainstance=inst, fill=False)
			try:
				imagedata = imagedatalist[0]
			except IndexError:
				self.setStatusMessage('Cannot find image data referenced by mosaic')
			else:
				if imagedata['image'] is not None:
					self.mosaic.addTile(imagedata)
					nloaded += 1
		self.mosaicdata = mosaicdata
		self.displayMosaic()
		self.setStatusMessage('Mosaic loaded (%i of %i images loaded successfully)'
													% (nloaded, n))

	def getMosaicImage(self):
		if self.scaleimage.get():
			maxdim = self.maxdimension.get()
		else:
			maxdim = None
		return self.mosaic.getMosaicImage(maxdim)

	def displayMosaic(self):
		if self.displayimage.get():
			self.setStatusMessage('Displaying mosaic image')
			self.clickimage.setImage(self.getMosaicImage())
			## imagedata would be full mosaic image
			self.clickimage.imagedata = None
		else:
			self.setStatusMessage('Not diplaying mosaic image')
		self.clickimage.setTargets([])

	def mosaicToFile(self):
		self.setStatusMessage('Saving mosaic image to file')
		filename = self.uifilename.get()
		self.setStatusMessage('Creating mosaic image')
		mosaicnumericarray = self.getMosaicImage()
		self.setStatusMessage('Mosaic image created')
		if mosaicnumericarray is not None:
			try:
				Mrc.numeric_to_mrc(mosaicnumericarray, filename)
			except:
				self.setStatusMessage('Error saving mosaic image MRC to file')
			self.setStatusMessage('Mosaic image saved to file')
		else:
			self.setStatusMessage('Error saving mosaic image, no mosaic')

	def getTargetDataList(self, typename):
		targetlist = []
		for imagetarget in self.clickimage.getTargetType(typename):
			column, row = imagetarget
			target = self.mosaic.getTargetInfo(column, row)
			imagedata = target['imagedata']
			drow = target['delta row']
			dcol = target['delta column']
			targetdata = self.newTargetData(imagedata, typename, drow, dcol)
			targetlist.append(targetdata)
		return targetlist

	def mosaicClear(self):
		self.setStatusMessage('Clearing mosaic')
		self.mosaic.clear()
		initializer = {'id': self.ID(), 'data IDs': []}
		self.mosaicdata = data.MosaicData(initializer=initializer)
		self.clickimage.setImage(None)
		self.clickimage.imagedata = None
		self.setStatusMessage('Mosaic cleared')

	def uiSetCalibrationParameter(self, value):
		if not hasattr(self, 'uicalibrationparameter'):
			return value
		parameter = self.uicalibrationparameter.getSelectedValue(value)
		try:
			self.mosaic.setCalibrationParameter(parameter)
		except ValueError:
			self.setStatusMessage('invalid calibration parameter specified')
		return value

	def setStatusMessage(self, message):
		self.statusmessage.set(message)

	def defineUserInterface(self):
		ClickTargetFinder.defineUserInterface(self)

		self.statusmessage = uidata.String('Current status', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObjects((self.statusmessage,))

		parameters = self.mosaic.getCalibrationParameters()
		parameter = parameters.index(self.mosaic.getCalibrationParameter())
		self.uicalibrationparameter = uidata.SingleSelectFromList(
																			'Calibration Parameter', parameters,
																			parameter,
																			callback=self.uiSetCalibrationParameter,
																			persist=True)
		self.scaleimage = uidata.Boolean('Scale Image', True, 'rw')
		self.maxdimension = uidata.Integer('Maximum Dimension', 512, 'rw')
		self.displayimage = uidata.Boolean('Display Image', True, 'rw')
		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((self.uicalibrationparameter,
																	self.scaleimage, self.maxdimension,
																	self.displayimage))

		self.mosaicselection = uidata.SingleSelectFromList('Mosaic', [], 0)
		self.updateMosaicSelection()

		refreshmethod = uidata.Method('Refresh', self.updateMosaicSelection)

		loadmethod = uidata.Method('Load', self.mosaicFromDatabase)
		loadcontainer = uidata.Container('Load')
		loadcontainer.addObjects((self.mosaicselection, refreshmethod, loadmethod))

		publishmosaicmethod = uidata.Method('Publish Mosaic', self.mosaicToDatabase)


		self.uifilename = uidata.String('Filename', '', 'rw')
		saveimagemethod = uidata.Method('Save Image', self.mosaicToFile)
		filecontainer = uidata.Container('File')
		filecontainer.addObjects((self.uifilename, saveimagemethod)) 

		clearmethod = uidata.Method('Reset Mosaic', self.mosaicClear)

		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((clearmethod, publishmosaicmethod,
																	loadcontainer, filecontainer))

		container = uidata.LargeContainer('Mosaic Click Target Finder')
		container.addObjects((statuscontainer, settingscontainer, controlcontainer))
		self.uiserver.addObject(container)

