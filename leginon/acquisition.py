#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
'''
Acquisition node is a TargetWatcher, so it receives either an ImageTargetData
or an ImageTargetListData.  The method processTargetData is called on each
ImageTargetData.
'''
import targetwatcher
import time
import data, event
import calibrationclient
import camerafuncs
import presets
import copy
import threading
import uidata
import node
import EM

class NoMoveCalibration(Exception):
	pass

class InvalidStagePosition(Exception):
	pass

class InvalidPresetsSequence(Exception):
	pass

class Acquisition(targetwatcher.TargetWatcher):

	eventinputs = targetwatcher.TargetWatcher.eventinputs \
								+ [event.ImageClickEvent,
										event.DriftDoneEvent,
										event.ImageProcessDoneEvent] \
								+ EM.EMClient.eventinputs
	eventoutputs = targetwatcher.TargetWatcher.eventoutputs \
									+ [event.LockEvent,
											event.UnlockEvent,
											event.AcquisitionImagePublishEvent,
											event.TrialImagePublishEvent,
											event.ChangePresetEvent,
											event.DriftDetectedEvent,
											event.AcquisitionImageListPublishEvent] \
									+ EM.EMClient.eventoutputs

	def __init__(self, id, session, managerlocation, target_type='acquisition', **kwargs):

		targetwatcher.TargetWatcher.__init__(self, id, session, managerlocation, target_type, **kwargs)
		self.addEventInput(event.DriftDoneEvent, self.handleDriftDone)
		self.addEventInput(event.ImageProcessDoneEvent, self.handleImageProcessDone)
		self.driftdone = threading.Event()
		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)

		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.presetsclient = presets.PresetsClient(self)
		self.doneevents = {}
		self.imagelist = []

		self.defineUserInterface()
		self.presetsclient.uistatus = self.uiacquisitionstatus
		self.start()

	def handleDriftDone(self, ev):
		self.reportStatus('acquisition', 'Received notification drift done')
		self.driftdonestatus = ev['status']
		self.driftdone.set()

	def handleImageProcessDone(self, ev):
		imageid = ev['imageid']
		status = ev['status']
		if imageid in self.doneevents:
			self.doneevents[imageid]['status'] = status
			self.doneevents[imageid]['received'].set()

	def processData(self, newdata):
		self.imagelist = []
		targetwatcher.TargetWatcher.processData(self, newdata)
		print 'IMAGE LIST SHOULD NOT ACTUALLY CONTAIN A LIST'
		print 'INSTEAD, IMAGEDATA SHOULD LINK TO IMAGELISTDATA'
		print 'for now we will make it a list of references'
		imagelistdata = data.AcquisitionImageListData(images=self.imagelist)
		print 'cannot publish to database for now because how do data references go in there'
		print 'this is another reason this should be done differently'
		self.publish(imagelistdata, pubevent=True)
		self.imagelist = []

	def validateStagePosition(self, stageposition):
		## check for out of stage range target
		stagelimits = {
			'x': (-9.9e-4, 9.9e-4),
			'y': (-9.9e-4, 9.9e-4),
		}
		for axis, limits in stagelimits.items():
			if stageposition[axis] < limits[0] or stageposition[axis] > limits[1]:
				messagestr = 'target stage position %s out of range... target aborting' % (stageposition,)
				self.acquisitionlog.error(messagestr)
				raise InvalidStagePosition(messagestr)

	def validatePresets(self):
		presetnames = self.uipresetnames.get()
		if not presetnames:
			raise InvalidPresetsSequence()
		availablepresets = self.getPresetNames()
		for presetname in presetnames:
			if presetname not in availablepresets:
				raise InvalidPresetsSequence()
		return presetnames

	def processTargetData(self, targetdata, force=False):
		'''
		This is called by TargetWatcher.processData when targets available
		If called with targetdata=None, this simulates what occurs at
		a target (going to presets, acquiring images, etc.)
		'''
		if targetdata is None:
			emtarget = None
		else:
			try:
				emtarget = self.targetToEMTargetData(targetdata)
			except InvalidStagePosition:
				return 'invalid'
			except NoMoveCalibration:
				self.acquisitionlog.error('calibrate this move type, then continue')
				node.beep()
				self.pause.set()
				return 'repeat'

		try:
			presetnames = self.validatePresets()
		except InvalidPresetsSequence:
			self.acquisitionlog.error('correct the invalid presets sequence, then continue')
			node.beep()
			self.pause.set()
			return 'repeat'

		for newpresetname in presetnames:
			if force == False:
				if self.alreadyAcquired(targetdata, newpresetname):
					continue

			self.presetsclient.toScope(newpresetname, emtarget)
			self.reportStatus('processing', 'Determining current preset')
			p = self.presetsclient.getCurrentPreset()
			if p['name'] != newpresetname:
				self.logger.error('failed to set preset %s' % (newpresetname,))
				continue
			if p is not None:
				self.reportStatus('processing', 'Current preset is "%s"' % p['name'])
			delay = self.uidelay.get()
			self.reportStatus('processing', 'Pausing for %s seconds before acquiring' % (delay,))
			time.sleep(delay)

			if p['film']:
				self.reportStatus('acquisition', 'Acquiring film...')
				try:
					self.acquireFilm(p, target=targetdata, emtarget=emtarget)
					self.reportStatus('acquisition', 'film acquired')
				except:
					self.logger.exception('film acquisition')
			else:
				self.reportStatus('acquisition', 'Acquiring image...')
				ret = self.acquire(p, target=targetdata, emtarget=emtarget)
				# in these cases, return immediately
				if ret in ('aborted', 'repeat'):
					self.reportStatus('acquisition', 'Acquition state is "%s"' % ret)
					return ret
				self.reportStatus('acquisition', 'Image acquired')


		self.reportStatus('processing', 'Processing complete')

		return 'ok'

	def alreadyAcquired(self, targetdata, presetname):
		'''
		determines if image already acquired using targetdata and presetname
		'''
		## if image exists with targetdata and presetdata, no acquire
		## we expect target to be exact, however, presetdata may have
		## changed so we only query on preset name

		# seems to have trouple with using original targetdata as
		# a query, so use a copy with only some of the fields
		presetquery = data.PresetData(name=presetname)
		imagequery = data.AcquisitionImageData(target=targetdata, preset=presetquery)
		## other things to fill in
		imagequery['scope'] = data.ScopeEMData()
		imagequery['camera'] = data.CameraEMData()
		imagequery['session'] = data.SessionData()

		datalist = self.research(datainstance=imagequery)
		if datalist:
			## no need to acquire again, but need to republish
			self.reportStatus('output', 'Image was acquired previously, republishing')
			imagedata = datalist[0]
			self.publishDisplayWait(imagedata)
			return True
		else:
			return False

	def targetToEMTargetData(self, targetdata):
		'''
		convert an ImageTargetData to an EMTargetData object
		using chosen move type.
		The result is a valid scope state that will center
		the target on the camera, but not necessarily at the
		desired preset.  It is shifted from the preset of the 
		original targetdata.

		Certain fields are reset to None becuase they are not
		necessary, and cause problems if used between different
		magnification modes (LM, M, SA).
		'''
		originalpreset = targetdata['preset']

		# get relevant info from target data
		targetdeltarow = targetdata['delta row']
		targetdeltacolumn = targetdata['delta column']
		targetscope = targetdata['scope']
		targetscope = data.ScopeEMData(initializer=targetscope)
		targetcamera = targetdata['camera']

		## ignore these fields:
		ignore = ('beam tilt', 'stigmator', 'holder type', 'holder status', 'stage status', 'vacuum status', 'column valves', 'turbo pump')
		for key in ignore:
			targetscope[key] = None

		## to shift targeted point to center...
		deltarow = -targetdeltarow
		deltacol = -targetdeltacolumn

		pixelshift = {'row':deltarow, 'col':deltacol}

		## figure out scope state that gets to the target
		movetype = self.uimovetype.getSelectedValue()
		calclient = self.calclients[movetype]
		try:
			newscope = calclient.transform(pixelshift, targetscope, targetcamera)
		except calibrationclient.NoMatrixCalibrationError:
			message = 'No calibration for acquisition move to target'
			self.acquisitionlog.error(message)
			raise NoMoveCalibration(message)

		### remove stage position if this is not a stage move
		### (unless requested to always move stage)
		if movetype == 'image shift':
			if not self.alwaysmovestage.get():
				newscope['stage position'] = None

		### check if stage position is valid
		if newscope['stage position']:
			self.validateStagePosition(newscope['stage position'])

		# create new EMData object to hold this
		emdata = data.ScopeEMData(initializer=newscope)

		oldpreset = targetdata['preset']
		# now make EMTargetData to hold all this
		emtargetdata = data.EMTargetData(scope=emdata, preset=oldpreset)
		return emtargetdata

	def acquireFilm(self, presetdata, target=None, emtarget=None):
		## get current film parameters
		scopebefore = self.emclient.getScope()
		stock = scopebefore['film stock']
		if stock < 1:
			self.logger.error('Film stock = %s. Film exposure failed' % (stock,))
			return

		## create FilmData(AcquisitionImageData) which 
		## will be used to store info about this exposure
		filmdata = data.FilmData(scope=scopebefore, preset=presetdata, label=self.name, target=target)
		## no image to store in file, but this provides 'filename' for 
		## film text
		self.setImageFilename(filmdata)

		## create a film exposure request
		request = data.ScopeEMData()
		request['film exposure'] = True
		request['film exposure type'] = 'manual'
		## convert from ms to s
		filmtime = presetdata['exposure time'] / 1000.0
		request['film manual exposure time'] = filmtime
		## first three of user name
		request['film user code'] = self.session['user']['name'][:3]
		## like filename in regular acquisition (limit 96 chars)
		request['film text'] = str(imdata['filename'])
		request['film data type'] = 'YY.MM.DD'

		## do exposure
		self.emclient.setScope(request)

		## record in database
		self.publish(filmdata, pubevent=True, database=self.databaseflag.get())

	def acquire(self, presetdata, target=None, emtarget=None):
		### corrected or not??
		cor = self.uicorrectimage.get()

		## acquire image
		imagedata = None
		try:
			try:
				imagedata = self.cam.acquireCameraImageData(correction=cor)
			except node.ResearchError:
				self.acquisitionlog.error('Cannot access EM node to acquire image')
		except camerafuncs.NoCorrectorError:
			self.acquisitionlog.error('Cannot access Corrector node to correct image')
		if imagedata is None:
			return 'fail'

		## convert CameraImageData to AcquisitionImageData
		imagedata = data.AcquisitionImageData(initializer=imagedata, preset=presetdata, label=self.name, target=target)

		self.publishDisplayWait(imagedata)
		self.imagelist.append(imagedata.reference())

	def retrieveImagesFromDB(self):
		imagequery = data.AcquisitionImageData()
		imagequery['session'] = self.session
		imagequery['label'] = self.name
		## don't read images because we only need the id
		images = self.research(datainstance=imagequery, readimages=False)
		imageids = [x.dbid for x in images]
		return imageids

	def uiUpdateDBImages(self):
		imageids = self.retrieveImagesFromDB()
		if imageids:
			self.pretendfromdb.enable()
			self.reacquirefromdb.enable()
		else:
			self.pretendfromdb.disable()
			self.reacquirefromdb.disable()
		self.dbimages.setList(imageids)

	def uiPretendAcquire(self):
		dbid = self.dbimages.getSelectedValue()
		imagedata = self.researchDBID(data.AcquisitionImageData, dbid)
		## should be one result only
		if imagedata is not None:
			self.publishDisplayWait(imagedata)

	def uiAcquireTargetAgain(self):
		dbid = self.dbimages.getSelectedValue()
		imagedata = self.researchDBID(data.AcquisitionImageData, dbid)
		## should be one result only
		if imagedata is not None:
			targetdata = imagedata['target']
			self.processTargetData(targetdata, force=True)

	def publishDisplayWait(self, imagedata):
		'''
		publish image data, display it, then wait for something to 
		process it
		'''
		## set up to handle done events
		dataid = imagedata.dmid
		self.doneevents[dataid] = {}
		self.doneevents[dataid]['received'] = threading.Event()
		self.doneevents[dataid]['status'] = 'waiting'

		## set the 'filename' value
		self.setImageFilename(imagedata)

		self.reportStatus('output', 'Publishing image...')
		self.publish(imagedata, pubevent=True, database=self.databaseflag.get())
		self.reportStatus('output', 'Image published')
		if self.displayimageflag.get():
			self.reportStatus('output', 'Displaying image...')
			self.ui_image.set(imagedata['image'])
			self.reportStatus('output', 'Image displayed')

		if self.waitfordone.get():
			self.waitForImageProcessDone()
		self.reportStatus('output', 'Image published')
		return 'ok'

	def setImageFilename(self, imagedata):
		if imagedata['filename']:
			return
		rootname = self.getRootName(imagedata)
		## use either data id or target number
		if imagedata['target'] is None or imagedata['target']['number'] is None:
			print 'This image does not have a target number, it would be nice to have an alternative to target number, like an image number.  for now we will use dmid'
			numberstr = '%05d' % (imagedata.dmid[-1],)
		else:
			numberstr = '%05d' % (imagedata['target']['number'],)
		if imagedata['preset'] is None:
			presetstr = ''
		else:
			presetstr = imagedata['preset']['name']
		mystr = numberstr + presetstr
		sep = '_'
		parts = (rootname, mystr)
		filename = sep.join(parts)
		self.reportStatus('output', 'Using filename "%s"' % filename)
		imagedata['filename'] = filename

	def getRootName(self, imagedata):
		'''
		get the root name of an image from its parent
		'''
		parent_target = imagedata['target']
		if parent_target is None:
			## there is no parent target
			## create my own root name
			return self.newRootName()

		parent_image = parent_target['image']
		if parent_image is None:
			## there is no parent image
			return self.newRootName()

		## use root name from parent image
		parent_root = parent_image['filename']
		if parent_root:
			return parent_root
		else:
			return self.newRootName()

	def newRootName(self):
		name = self.session['name']
		return name

	def updateWaitingForImages(self, imageidstrs):
		self.waitingforimages.setList(imageidstrs)
		if imageidstrs:
			self.stopwaiting.enable()
		else:
			self.stopwaiting.disable()

	def waitForImageProcessDone(self):
		imageids = self.doneevents.keys()
		imageidstrs = map(str, imageids)
		self.updateWaitingForImages(imageidstrs)
		# wait for image processing nodes to complete
		for id, eventinfo in self.doneevents.items():
			self.reportStatus('processing', 'Waiting for %s to be processed' % (id,))
			eventinfo['received'].wait()
			idstr = str(id)
			imageidstrs.remove(idstr)
			self.updateWaitingForImages(imageidstrs)
			self.reportStatus('processing', 'Done waiting for %s to be processed' % (id,))
		self.doneevents.clear()
		self.reportStatus('processing', 'Done waiting for images to be processed')

	def stopWaitingForImage(self):
		imageidstr = self.waitingforimages.getSelectedValue()
		try:
			imageid = eval(imageidstr)
		except TypeError:
			return
		if imageid in self.doneevents:
			self.doneevents[imageid]['received'].set()
			self.doneevents[imageid]['status'] = 'forced'

	def uiToScope(self):
		presetname = self.presetsclient.uiGetSelectedName()
		self.reportStatus('acquisition', 'Going to preset "%s"' % (presetname,))
		self.presetsclient.toScope(presetname)
		self.reportStatus('acquisition', 'At preset "%s"' % (presetname,))

	def uiToScopeAcquire(self):
		presetname = self.presetsclient.uiGetSelectedName()
		## acquire a trial image
		self.reportStatus('acquisition', 'Going to preset "%s"' % (presetname,))
		self.presetsclient.toScope(presetname)
		self.reportStatus('acquisition', 'At preset "%s", checking preset' % (presetname,))
		p = self.presetsclient.getCurrentPreset()
		self.reportStatus('acquisition', 'Current preset is "%s"' % (p['name'],))
		# trial image
		self.reportStatus('acquisition', 'Acquiring image...')
		self.acquire(p, target=None)
		self.reportStatus('acquisition', 'Image acquired...')

	def uiTrial(self):
		self.processTargetData(targetdata=None)

	def getPresetNames(self):
		presetnames = self.presetsclient.getPresetNames()
		return presetnames

	def setDisplayImage(self, value):
		if not value:
			self.ui_image.set(None)
		return value

	def uiRefreshPresetNames(self):
		pnames = self.getPresetNames()
		pnamestr = '  '.join(pnames)
		self.uiavailablepresetnames.set(pnamestr)

	def driftDetected(self):
		'''
		notify DriftManager of drifting
		'''
		scope = self.emclient.getScope()
		camera = self.emclient.getCamera()
		driftdetecteddata = data.DriftDetectedData(scope=scope, camera=camera)
		self.reportStatus('acquisition', 'Passing beam tilt %s' % str(allemdata['scope']['beam tilt']))
		self.driftdone.clear()
		self.publish(driftdetecteddata, pubevent=True)
		self.reportStatus('acquisition', 'Waiting for DriftManager...')
		self.driftdone.wait()

	def reportStatus(self, type, message):
		self.logger.info('%s:  %s' % (type, message))
		if type == 'processing':
			self.uiprocessingstatus.set(message)
		elif type == 'output':
			self.uioutputstatus.set(message)
		elif type == 'acquisition':
			self.uiacquisitionstatus.set(message)

	def defineUserInterface(self):
		targetwatcher.TargetWatcher.defineUserInterface(self)

		self.acquisitionlog = uidata.MessageLog('Messages')

		self.uiprocessingstatus = uidata.String('Processing', '', 'r')
		self.uioutputstatus = uidata.String('Output', '', 'r')
		self.uiacquisitionstatus = uidata.String('Acquisition', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObject(self.uiprocessingstatus,
															position={'expand': 'all'})
		statuscontainer.addObject(self.uioutputstatus,
															position={'expand': 'all'})
		statuscontainer.addObject(self.uiacquisitionstatus,
															position={'expand': 'all'})

		self.ui_image = uidata.Image('Image', None, 'rw')

		self.displayimageflag = uidata.Boolean('Display Image', True, 'rw',
																						persist=True)
		uicontainer = uidata.Container('User Interface')
		uicontainer.addObjects((self.displayimageflag,))

		presetscontainer = uidata.Container('Presets Sequence')

		self.uiavailablepresetnames = uidata.String('Preset names', '', 'r')
		self.uipresetnames = uidata.Sequence('Presets Sequence', [], 'rw', persist=True)
		refreshpresetnames = uidata.Method('Show Presets', self.uiRefreshPresetNames)
		presetscontainer.addObject(self.uiavailablepresetnames)
		presetscontainer.addObject(refreshpresetnames,
																position={'justify': 'right'})
		presetscontainer.addObject(self.uipresetnames)

		self.uimovetype = uidata.SingleSelectFromList('Move Type',
																									self.calclients.keys(),
																									0, persist=True)
		self.alwaysmovestage = uidata.Boolean('Reset stage position even when move type is image shift', False, 'rw', persist=True)
		self.uidelay = uidata.Float('Delay (sec)', 2.5, 'rw', persist=True,
																	size=(5, 1))
		self.uicorrectimage = uidata.Boolean('Correct image', True, 'rw',
																			persist=True)

		self.waitfordone = uidata.Boolean('Wait for another node to process each published image', True, 'rw',
																				persist=True)

		acquirecontainer = uidata.Container('Acquisition')
		acquirecontainer.addObjects((self.uicorrectimage, self.uimovetype,
																	self.alwaysmovestage, self.uidelay,
																	self.waitfordone))

		self.databaseflag = uidata.Boolean('Save images in database', True, 'rw')
		self.dbimages = uidata.SingleSelectFromList('Image', [], 0)
		updatedbimages = uidata.Method('Refresh', self.uiUpdateDBImages)
		self.pretendfromdb = uidata.Method('Simulate',
																				self.uiPretendAcquire,
					tooltip='Pretend image selected from the database was just acquired')
		self.reacquirefromdb = uidata.Method('Reacquire',
																					self.uiAcquireTargetAgain,
					tooltip='Acquire the image selected from the database again')
		self.pretendfromdb.disable()
		self.reacquirefromdb.disable()

		databasecontainer = uidata.Container('Database')
		databasecontainer.addObject(self.databaseflag,
																position={'position': (0, 0), 'span': (1, 2)})
		databasecontainer.addObject(self.dbimages,
																position={'position': (1, 0)})
		databasecontainer.addObject(updatedbimages,
																position={'position': (1, 1)})
		databasecontainer.addObject(self.pretendfromdb,
																position={'position': (2, 1)})
		databasecontainer.addObject(self.reacquirefromdb,
																position={'position': (3, 1)})

		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObject(uicontainer, position={'expand': 'all'})
		settingscontainer.addObject(presetscontainer, position={'expand': 'all'})
		settingscontainer.addObject(acquirecontainer, position={'expand': 'all'})
		settingscontainer.addObject(databasecontainer, position={'expand': 'all'})

		trialmethod = uidata.Method('Trial Image', self.uiTrial)
		self.waitingforimages = uidata.SingleSelectFromList('Waiting For', [], 0)
		self.stopwaiting = uidata.Method('Stop Waiting', self.stopWaitingForImage)
		self.stopwaiting.disable()

		controlcontainer = uidata.Container('Control')
		controlcontainer.addObject(self.waitingforimages,
																position={'position': (0, 0)})
		controlcontainer.addObject(self.stopwaiting, position={'position': (0, 1)})
		#controlcontainer.addObject(trialmethod)

		container = uidata.LargeContainer('Acquisition')
		container.addObject(self.acquisitionlog, position={'position': (0, 0),
																												'span': (1, 2),
																												'expand': 'all'})
		container.addObject(statuscontainer, position={'position': (1, 0),
																										'span': (1, 2),
																										'expand': 'all'})
		container.addObject(settingscontainer, position={'position': (2, 0)})
		container.addObject(controlcontainer, position={'position': (3, 0)})
		container.addObject(self.ui_image, position={'position': (2, 1),
																									'span': (2, 1)})

		self.uicontainer.addObject(container)

