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
try:
	import numarray as Numeric
except:
	import Numeric

class NoMoveCalibration(Exception):
	pass

class InvalidStagePosition(Exception):
	pass

class InvalidPresetsSequence(Exception):
	pass

class Acquisition(targetwatcher.TargetWatcher):

	eventinputs = targetwatcher.TargetWatcher.eventinputs \
								+ [event.DriftDoneEvent,
										event.ImageProcessDoneEvent] \
								+ EM.EMClient.eventinputs
	eventoutputs = targetwatcher.TargetWatcher.eventoutputs \
									+ [event.LockEvent,
											event.UnlockEvent,
											event.AcquisitionImagePublishEvent,
										
	event.ChangePresetEvent,
											event.DriftDetectedEvent,
											event.ImageListPublishEvent, event.DriftWatchEvent] \
									+ EM.EMClient.eventoutputs

	def __init__(self, id, session, managerlocation, target_types=('acquisition',), **kwargs):

		targetwatcher.TargetWatcher.__init__(self, id, session, managerlocation, target_types=target_types, **kwargs)
		self.addEventInput(event.DriftDoneEvent, self.handleDriftDone)
		self.addEventInput(event.ImageProcessDoneEvent, self.handleImageProcessDone)
		self.driftdone = threading.Event()
		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)

		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'image beam shift': calibrationclient.ImageBeamShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.presetsclient = presets.PresetsClient(self)
		self.doneevents = {}
		self.imagelistdata = None

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
		self.logger.debug('Acquisition.processData')
		self.imagelistdata = data.ImageListData(session=self.session, targets=newdata)
		self.publish(self.imagelistdata, database=True)
		targetwatcher.TargetWatcher.processData(self, newdata)
		self.publish(self.imagelistdata, pubevent=True)

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

	def processTargetData(self, targetdata, force=False, attempt=None):
		'''
		This is called by TargetWatcher.processData when targets available
		If called with targetdata=None, this simulates what occurs at
		a target (going to presets, acquiring images, etc.)
		'''
		if targetdata is None or targetdata['type'] == 'simulated':
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
			if targetdata is None or targetdata['type'] == 'simulated':
				self.acquisitionlog.error('correct the invalid presets sequence, then try again')
				return
			else:
				## if there was a targetdata, then 
				## we assume we are in a target list loop
				self.acquisitionlog.error('Paused... correct the invalid presets sequence, then continue')
				node.beep()
				self.pause.set()
				return 'repeat'

		for newpresetname in presetnames:
			presettarget = data.PresetTargetData(emtarget=emtarget, preset=newpresetname)
			#self.publish(presettarget, database=True)
			if force == False:
				if self.alreadyAcquired(targetdata, presettarget):
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
				ret = self.acquire(p, target=targetdata, presettarget=presettarget, attempt=attempt)
				# in these cases, return immediately
				if ret in ('aborted', 'repeat'):
					self.reportStatus('acquisition', 'Acquisition state is "%s"' % ret)
					return ret

		self.reportStatus('processing', 'Processing complete')

		return 'ok'

	def alreadyAcquired(self, targetdata, presettarget):
		'''
		determines if image already acquired using targetdata and presetname
		'''
		## if image exists with targetdata and presetdata, no acquire
		## we expect target to be exact, however, presetdata may have
		## changed so we only query on preset name

		# seems to have trouple with using original targetdata as
		# a query, so use a copy with only some of the fields
		presetquery = data.PresetData(name=presettarget['preset'])
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
			self.publishDisplayWait(imagedata, presettarget)
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
		origscope = targetdata['scope']
		targetscope = data.ScopeEMData(initializer=origscope)
		## copy these because they are dictionaries that could
		## otherwise be shared (although transform() should be
		## smart enough to create copies as well)
		targetscope['stage position'] = dict(origscope['stage position'])
		targetscope['image shift'] = dict(origscope['image shift'])
		targetscope['beam shift'] = dict(origscope['beam shift'])
		targetcamera = targetdata['camera']

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

		### check if stage position is valid
		if newscope['stage position']:
			self.validateStagePosition(newscope['stage position'])

		oldpreset = targetdata['preset']
		# now make EMTargetData to hold all this
		emtargetdata = data.EMTargetData(preset=oldpreset, movetype=movetype)
		emtargetdata['image shift'] = dict(newscope['image shift'])
		emtargetdata['beam shift'] = dict(newscope['beam shift'])
		emtargetdata['stage position'] = dict(newscope['stage position'])

		## publish in DB because it will likely be needed later
		## when returning to the same target,
		## even after it is removed from memory
		self.publish(emtargetdata, database=True)
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
		filmdata = data.FilmData(session=self.session, preset=presetdata, label=self.name, target=target)
		## no image to store in file, but this provides 'filename' for 
		## film text
		self.setImageFilename(filmdata)

		## set film parameters
		request = data.ScopeEMData()
		## first three of user name
		request['film user code'] = self.session['user']['name'][:3]
		## like filename in regular acquisition (limit 96 chars)
		request['film text'] = str(filmdata['filename'])
		request['film date type'] = 'YY.MM.DD'
		self.emclient.setScope(request)

		## get scope for database
		scopebefore = self.emclient.getScope()
		filmdata['scope'] = scopebefore

		## insert film
		request = data.ScopeEMData()
		request['pre film exposure'] = True
		self.emclient.setScope(request)

		# expose film
		self.emclient.getImage()

		## take out film
		request = data.ScopeEMData()
		request['post film exposure'] = True
		self.emclient.setScope(request)

		## record in database
		self.publish(filmdata, pubevent=True, database=self.databaseflag.get())

	def acquire(self, presetdata, target=None, presettarget=None, attempt=None):
		### corrected or not??
		cor = self.uicorrectimage.get()

		## acquire image
		self.reportStatus('acquisition', 'acquiring image...')
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

		self.reportStatus('acquisition', 'image acquired')

		## store EMData to DB to prevent referencing errors
		self.publish(imagedata['scope'], database=True)
		self.publish(imagedata['camera'], database=True)

		## convert CameraImageData to AcquisitionImageData
		imagedata = data.AcquisitionImageData(initializer=imagedata, preset=presetdata, label=self.name, target=target, list=self.imagelistdata)
		if target is not None and 'grid' in target and target['grid'] is not None:
			imagedata['grid'] = target['grid']

		self.publishDisplayWait(imagedata, presettarget)

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
			print 'HOW TO GET PRESETTARGET?????'
			presettarget = None
			self.publishDisplayWait(imagedata, presettarget)

	def uiAcquireTargetAgain(self):
		dbid = self.dbimages.getSelectedValue()
		imagedata = self.researchDBID(data.AcquisitionImageData, dbid)
		## should be one result only
		if imagedata is not None:
			targetdata = imagedata['target']
			self.processTargetData(targetdata, force=True)

	def publishDisplayWait(self, imagedata, presettarget=None):
		'''
		publish image data, display it, then wait for something to 
		process it
		'''
		## set the 'filename' value
		self.setImageFilename(imagedata)

		self.reportStatus('output', 'Publishing image...')
		self.publish(imagedata, pubevent=True, database=self.databaseflag.get())
		self.reportStatus('output', 'Image published')

		ev = event.DriftWatchEvent(image=imagedata, presettarget=presettarget)
		self.outputEvent(ev)
		## set up to handle done events
		dataid = imagedata.dbid
		self.doneevents[dataid] = {}
		self.doneevents[dataid]['received'] = threading.Event()
		self.doneevents[dataid]['status'] = 'waiting'
		if self.displayimageflag.get():
			self.reportStatus('output', 'Displaying image...')
			self.ui_image.set(imagedata['image'].astype(Numeric.Float32))
			self.reportStatus('output', 'Image displayed')

		if self.waitfordone.get():
			self.waitForImageProcessDone()
		return 'ok'

	def publishStats(self, imagedata):
		im = imagedata['image']
		mn,mx = imagefun.minmax(im)
		mean = imagefun.mean(im)
		std = imagefun.stdev(im, mean)
		statsdata = data.AcquisitionImageStatsData()
		statsdata['min'] = mn
		statsdata['max'] = mx
		statsdata['mean'] = mean
		statsdata['stdev'] = std
		statsdata['image'] = imagedata
		self.publish(statsdata, database=True)

	def setImageFilename(self, imagedata):
		if imagedata['filename']:
			return
		rootname = self.getRootName(imagedata)
		listlabel = ''

		## use either data id or target number
		if imagedata['target'] is None or imagedata['target']['number'] is None:
			print 'This image does not have a target number, it would be nice to have an alternative to target number, like an image number.  for now we will use dmid'
			numberstr = '%05d' % (imagedata.dmid[-1],)
		else:
			numberstr = '%05d' % (imagedata['target']['number'],)
			if imagedata['target']['list'] is not None:
				listlabel = imagedata['target']['list']['label']
		if imagedata['preset'] is None:
			presetstr = ''
		else:
			presetstr = imagedata['preset']['name']
		mystr = numberstr + presetstr
		sep = '_'
		if listlabel:
			parts = (rootname, listlabel, mystr)
		else:
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

	def uiSimulateTarget(self):
		targetdata = self.newSimulatedTarget()
		self.publish(targetdata, database=True)
		## change to 'processing' just like targetwatcher does
		proctargetdata = data.AcquisitionImageTargetData(initializer=targetdata, status='processing')
		ret = self.processTargetData(targetdata=proctargetdata, attempt=1)
		self.logger.info('Done with simulated target, status: %s (repeat will not be honored)' % (ret,))

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

	def driftDetected(self, presettarget):
		'''
		notify DriftManager of drifting
		'''
		driftdetecteddata = data.DriftDetectedData(initializer=presettarget)
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

		presetscontainer = uidata.Container('Presets Sequence')

		refreshpresetnames = uidata.Method('Show Presets', self.uiRefreshPresetNames)
		self.uiavailablepresetnames = uidata.String('Preset names', '', 'r')
		self.uipresetnames = uidata.Sequence('Presets Sequence', [], 'rw', persist=True)
		presetscontainer.addObject(refreshpresetnames, position={'position':(0,0)})
		presetscontainer.addObject(self.uiavailablepresetnames, position={'position':(0,1)})
		presetscontainer.addObject(self.uipresetnames, position={'position':(1,0), 'span':(1,2)})


		self.uimovetype = uidata.SingleSelectFromList('Move Type',
																									self.calclients.keys(),
																									0, persist=True)
		self.uidelay = uidata.Float('Delay (sec)', 2.5, 'rw', persist=True,
																	size=(5, 1))
		self.uicorrectimage = uidata.Boolean('Correct image', True, 'rw',
																			persist=True)

		self.waitfordone = uidata.Boolean('Wait for another node to process each published image', True, 'rw', persist=True)
		acquirecontainer = uidata.Container('Acquisition')
		acquirecontainer.addObject(self.uicorrectimage, position={'position':(0,0)})
		acquirecontainer.addObject(self.displayimageflag, position={'position':(0,1)})
		acquirecontainer.addObject(self.uimovetype, position={'position':(1,0)})
		acquirecontainer.addObject(self.uidelay, position={'position':(1,1)})
		acquirecontainer.addObject(self.waitfordone, position={'position':(2,0), 'span':(1,2)})

		self.databaseflag = uidata.Boolean('Save images in database', True, 'rw')
		self.dbimages = uidata.SingleSelectFromList('Image', [], 0)
		updatedbimages = uidata.Method('Refresh', self.uiUpdateDBImages)
		self.pretendfromdb = uidata.Method('Simulate Acquistion from DB (broken for now)',
																				self.uiPretendAcquire,
					tooltip='Pretend image selected from the database was just acquired')
		self.reacquirefromdb = uidata.Method('Reacquire',
																					self.uiAcquireTargetAgain,
					tooltip='Acquire the image selected from the database again')
		self.pretendfromdb.disable()
		self.reacquirefromdb.disable()

		databasecontainer = uidata.Container('Database')
		databasecontainer.addObject(self.databaseflag, position={'position': (0, 0), 'span': (1, 4)})
		databasecontainer.addObject(updatedbimages, position={'position': (1, 0)})
		databasecontainer.addObject(self.dbimages, position={'position': (1, 1)})
		databasecontainer.addObject(self.pretendfromdb, position={'position': (1, 2)})
		databasecontainer.addObject(self.reacquirefromdb, position={'position': (1, 3)})

		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObject(presetscontainer, position={'expand': 'all'})
		settingscontainer.addObject(acquirecontainer, position={'expand': 'all'})
		settingscontainer.addObject(databasecontainer, position={'expand': 'all'})

		trialmethod = uidata.Method('Acquire Simulated Target', self.uiSimulateTarget)
		self.waitingforimages = uidata.SingleSelectFromList('Waiting For', [], 0)
		self.stopwaiting = uidata.Method('Stop Waiting', self.stopWaitingForImage)
		self.stopwaiting.disable()

		controlcontainer = uidata.Container('Control')
		controlcontainer.addObject(self.waitingforimages,
																position={'position': (0, 0)})
		controlcontainer.addObject(self.stopwaiting, position={'position': (0, 1)})
		controlcontainer.addObject(trialmethod, position={'position':(1,0)})

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

