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
import presets
import copy
import threading
import node
import instrument
import imagefun
import gui.wx.Acquisition
import gui.wx.Presets
import newdict
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
	panelclass = gui.wx.Acquisition.Panel
	settingsclass = data.AcquisitionSettingsData
	# maybe not a class attribute
	defaultsettings = {
		'pause time': 2.5,
		'move type': 'image shift',
		'preset order': [],
		'correct image': True,
		'display image': True,
		'save image': True,
		'wait for process': False,
		'wait for rejects': False,
		'duplicate targets': False,
		'duplicate target type': 'focus',
		'iterations': 1,
		'wait time': 0,
		'adjust for drift': False,
	}
	eventinputs = targetwatcher.TargetWatcher.eventinputs \
								+ [event.DriftDoneEvent,
										event.ImageProcessDoneEvent, event.AcquisitionImageDriftPublishEvent] \
								+ presets.PresetsClient.eventinputs
	eventoutputs = targetwatcher.TargetWatcher.eventoutputs \
									+ [event.LockEvent,
											event.UnlockEvent,
											event.AcquisitionImagePublishEvent,
											event.NeedTargetShiftEvent,
										
	event.ChangePresetEvent, event.PresetLockEvent, event.PresetUnlockEvent,
											event.DriftDetectedEvent, 
											event.ImageListPublishEvent]

	def __init__(self, id, session, managerlocation, target_types=('acquisition',), **kwargs):

		targetwatcher.TargetWatcher.__init__(self, id, session, managerlocation, target_types=target_types, **kwargs)

		self.addEventInput(event.DriftDoneEvent, self.handleDriftDone)
		self.addEventInput(event.ImageProcessDoneEvent, self.handleImageProcessDone)
		self.addEventInput(event.AcquisitionImageDriftPublishEvent,
												self.handleImageDrift)
		self.driftdone = threading.Event()
		self.instrument = instrument.Proxy(self.objectservice, self.session)

		self.calclients = newdict.OrderedDict()
		self.calclients['image shift'] = calibrationclient.ImageShiftCalibrationClient(self)
		self.calclients['stage position'] = calibrationclient.StageCalibrationClient(self)
		self.calclients['modeled stage position'] = calibrationclient.ModeledStageCalibrationClient(self)
		self.calclients['image beam shift'] = calibrationclient.ImageBeamShiftCalibrationClient(self)

		self.presetsclient = presets.PresetsClient(self)
		self.doneevents = {}
		self.imagelistdata = None
		self.simloopstop = threading.Event()
		self.received_image_drift = threading.Event()
		self.requested_drift = None

		self.duplicatetypes = ['acquisition', 'focus']
		self.presetlocktypes = ['acquisition', 'target', 'target list']

		self.start()

	def onPresetPublished(self, evt):
		evt = gui.wx.Presets.NewPresetEvent()
		self.panel.GetEventHandler().AddPendingEvent(evt)

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
		if isinstance(newdata, data.QueueData):
			self.processTargetListQueue(newdata)
			return
		self.logger.debug('Acquisition.processData')
		self.imagelistdata = data.ImageListData(session=self.session,
																						targets=newdata)
		self.publish(self.imagelistdata, database=True)
		targetwatcher.TargetWatcher.processData(self, newdata)
		self.publish(self.imagelistdata, pubevent=True)
		self.presetsclient.unlock()
		self.logger.debug('Acquisition.processData done')

	def validateStagePosition(self, stageposition):
		## check for out of stage range target
		stagelimits = {
			'x': (-9.9e-4, 9.9e-4),
			'y': (-9.9e-4, 9.9e-4),
		}
		for axis, limits in stagelimits.items():
			if stageposition[axis] < limits[0] or stageposition[axis] > limits[1]:
				pstr = '%s: %g' % (axis, stageposition[axis])
				messagestr = 'Aborting target: stage position %s out of range' % pstr
				self.logger.error(messagestr)
				raise InvalidStagePosition(messagestr)

	def validatePresets(self):
		presetorder = self.settings['preset order']
		if not presetorder:
			raise InvalidPresetsSequence()
		availablepresets = self.getPresetNames()
		for presetname in presetorder:
			if presetname not in availablepresets:
				raise InvalidPresetsSequence()
		return list(presetorder)

	def processTargetData(self, targetdata, attempt=None):
		'''
		This is called by TargetWatcher.processData when targets available
		If called with targetdata=None, this simulates what occurs at
		a target (going to presets, acquiring images, etc.)
		'''
		try:
			presetnames = self.validatePresets()
		except InvalidPresetsSequence:
			estr = 'Presets sequence is invalid, please correct it'
			if targetdata is None or targetdata['type'] == 'simulated':
				self.logger.error(estr + ' and try again')
				return 'aborted'
			else:
				## if there was a targetdata, then 
				## we assume we are in a target list loop
				self.player.pause()
				self.logger.error(estr + ' and press continue')
				self.beep()
				return 'repeat'

		ret = 'ok'
		for newpresetname in presetnames:
			if self.alreadyAcquired(targetdata, newpresetname):
				continue

			if self.settings['adjust for drift']:
				targetdata = self.adjustTargetForDrift(targetdata)

			try:
				emtarget = self.targetToEMTargetData(targetdata)
			except InvalidStagePosition:
				return 'invalid'
			except NoMoveCalibration:
				self.player.pause()
				self.logger.error('Calibrate this move type, then continue')
				self.beep()
				return 'repeat'

			self.presetsclient.toScope(newpresetname, emtarget)
			self.reportStatus('processing', 'Determining current preset')
			p = self.presetsclient.getCurrentPreset()
			if p['name'] != newpresetname:
				self.logger.error('failed to set preset %s' % (newpresetname,))
				continue
			if p is not None:
				self.reportStatus('processing', 'Current preset is "%s"' % p['name'])
			pausetime = self.settings['pause time']
			self.reportStatus('processing',
												'Pausing for %s seconds before acquiring' % pausetime)
			time.sleep(pausetime)

			if p['film']:
				self.reportStatus('acquisition', 'Acquiring film...')
				try:
					self.acquireFilm(p, target=targetdata, emtarget=emtarget)
					self.reportStatus('acquisition', 'film acquired')
				except:
					self.logger.exception('film acquisition')
			else:
				ret = self.acquire(p, target=targetdata, emtarget=emtarget, attempt=attempt)
				# in these cases, return immediately
				if ret in ('aborted', 'repeat'):
					self.reportStatus('acquisition', 'Acquisition state is "%s"' % ret)
					break

		self.reportStatus('processing', 'Processing complete')

		return ret

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
		## don't care if drift correction was done on target after image was
		## acquired, so ignore version, delta row/col
		targetquery = data.AcquisitionImageTargetData(initializer=targetdata)
		targetquery['version'] = None
		targetquery['delta row'] = None
		targetquery['delta column'] = None
		imagequery = data.AcquisitionImageData(target=targetquery, preset=presetquery)
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
		emtargetdata = data.EMTargetData()
		if targetdata is not None:
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

			movetype = self.settings['move type']
			oldpreset = targetdata['preset']

			### simulated target does not require transform
			if targetdata['type'] == 'simulated':
				newscope = origscope
			else:
				targetcamera = targetdata['camera']
		
				## to shift targeted point to center...
				deltarow = -targetdeltarow
				deltacol = -targetdeltacolumn
		
				pixelshift = {'row':deltarow, 'col':deltacol}
		
				## figure out scope state that gets to the target
				calclient = self.calclients[movetype]
				try:
					newscope = calclient.transform(pixelshift, targetscope, targetcamera)
				except calibrationclient.NoMatrixCalibrationError:
					message = 'No calibration for acquisition move to target'
					self.logger.error(message)
					raise NoMoveCalibration(message)
	
			### check if stage position is valid
			if newscope['stage position']:
				self.validateStagePosition(newscope['stage position'])
	
			emtargetdata['preset'] = oldpreset
			emtargetdata['movetype'] = movetype
			emtargetdata['image shift'] = dict(newscope['image shift'])
			emtargetdata['beam shift'] = dict(newscope['beam shift'])
			emtargetdata['stage position'] = dict(newscope['stage position'])

		emtargetdata['target'] = targetdata

		## publish in DB because it will likely be needed later
		## when returning to the same target,
		## even after it is removed from memory
		self.publish(emtargetdata, database=True)
		return emtargetdata

	def acquireFilm(self, presetdata, target=None, emtarget=None):
		## get current film parameters
		stock = self.instrument.tem.FilmStock
		if stock < 1:
			self.logger.error('Film stock = %s. Film exposure failed' % (stock,))
			return

		## create FilmData(AcquisitionImageData) which 
		## will be used to store info about this exposure
		filmdata = data.FilmData(session=self.session, preset=presetdata, label=self.name, target=target, emtarget=emtarget)
		## no image to store in file, but this provides 'filename' for 
		## film text
		self.setImageFilename(filmdata)

		## first three of user name
		self.instrument.tem.FilmUserCode = self.session['user']['name'][:3]
		## like filename in regular acquisition (limit 96 chars)
		self.instrument.tem.FilmText = str(filmdata['filename'])
		self.instrument.tem.FilmDateType = 'YY.MM.DD'

		## get scope for database
		scopebefore = self.instrument.getData(data.ScopeEMData)
		filmdata['scope'] = scopebefore

		## insert film
		self.instrument.tem.preFilmExposure()

		# expose film
		self.instrument.ccdcamera.getImage()

		## take out film
		self.instrument.tem.postFilmExposure()

		## record in database
		self.publish(filmdata, pubevent=True, database=self.settings['save image'])

	def acquire(self, presetdata, target=None, emtarget=None, attempt=None):
		### corrected or not??

		## acquire image
		self.reportStatus('acquisition', 'acquiring image...')
		imagedata = None
		correctimage = self.settings['correct image']
		try:
			if correctimage:
				dataclass = data.CorrectedCameraImageData
			else:
				dataclass = data.CameraImageData
			imagedata = self.instrument.getData(dataclass)
		except:
			self.logger.error('Cannot access instrument')
		if imagedata is None:
			return 'fail'

		self.reportStatus('acquisition', 'image acquired')

		## store EMData to DB to prevent referencing errors
		self.publish(imagedata['scope'], database=True)
		self.publish(imagedata['camera'], database=True)

		## convert CameraImageData to AcquisitionImageData
		imagedata = data.AcquisitionImageData(initializer=imagedata, preset=presetdata, label=self.name, target=target, list=self.imagelistdata, emtarget=emtarget)
		if target is not None and 'grid' in target and target['grid'] is not None:
			imagedata['grid'] = target['grid']

		self.publishDisplayWait(imagedata)

	def retrieveImagesFromDB(self):
		imagequery = data.AcquisitionImageData()
		imagequery['session'] = self.session
		imagequery['label'] = self.name
		## don't read images because we only need the id
		images = self.research(datainstance=imagequery, readimages=False)
		imageids = [x.dbid for x in images]
		return imageids

	def publishDisplayWait(self, imagedata):
		'''
		publish image data, display it, then wait for something to 
		process it
		'''
		## set the 'filename' value
		self.setImageFilename(imagedata)

		self.reportStatus('output', 'Publishing image...')
		self.publish(imagedata, pubevent=True, database=self.settings['save image'])
		self.reportStatus('output', 'Image published')
		self.reportStatus('output', 'Publishing stats...')
		self.publishStats(imagedata)
		self.reportStatus('output', 'Stats published...')

		## set up to handle done events
		dataid = imagedata.dbid
		self.doneevents[dataid] = {}
		self.doneevents[dataid]['received'] = threading.Event()
		self.doneevents[dataid]['status'] = 'waiting'
		if self.settings['display image']:
			self.reportStatus('output', 'Displaying image...')
			self.setImage(imagedata['image'].astype(Numeric.Float32), 'Image')
			self.reportStatus('output', 'Image displayed')

		if self.settings['wait for process']:
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

	def publishImage(self, imdata):
		self.publish(imdata, pubevent=True)

	def setImageFilename(self, imagedata):
		if imagedata['filename']:
			return
		parts = []
		rootname = self.getRootName(imagedata)
		parts.append(rootname)

		if 'grid' in imagedata and imagedata['grid'] is not None:
			if imagedata['grid']['grid ID'] is not None:
				grididstr = '%05d' % (imagedata['grid']['grid ID'],)
				parts.append(grididstr)

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
			parts.append(listlabel)
		parts.append(mystr)

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

	def waitForImageProcessDone(self):
		imageids = self.doneevents.keys()
		imageidstrs = map(str, imageids)
		# wait for image processing nodes to complete
		for id, eventinfo in self.doneevents.items():
			self.reportStatus('processing', 'Waiting for %s to be processed' % (id,))
			eventinfo['received'].wait()
			idstr = str(id)
			imageidstrs.remove(idstr)
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

	def getPresetNames(self):
		presetnames = self.presetsclient.getPresetNames()
		return presetnames

	def declareDrift(self, type):
		## declare drift manually
		declared = data.DriftDeclaredData()
		declared['system time'] = self.instrument.tem.SystemTime
		declared['type'] = type
		self.publish(declared, database=True, dbforce=True)

	def driftDetected(self, presetname, emtarget):
		'''
		notify DriftManager of drifting
		'''
		driftdetecteddata = data.DriftDetectedData(presetname=presetname, emtarget=emtarget)
		self.driftdone.clear()
		self.publish(driftdetecteddata, pubevent=True)
		self.reportStatus('acquisition', 'Waiting for DriftManager...')
		self.driftdone.wait()

	def reportStatus(self, type, message):
		self.logger.info('%s: %s' % (type, message))

	def simulateTarget(self):
		currentpreset = self.presetsclient.getCurrentPreset()
		if currentpreset is None:
			self.logger.warning('No preset currently on instrument. Targeting may fail.')
		targetdata = self.newSimulatedTarget(preset=currentpreset)
		self.publish(targetdata, database=True)
		## change to 'processing' just like targetwatcher does
		proctargetdata = data.AcquisitionImageTargetData(initializer=targetdata, status='processing')
		ret = self.processTargetData(targetdata=proctargetdata, attempt=1)
		self.logger.info('Done with simulated target, status: %s (repeat will not be honored)' % (ret,))

	def simulateTargetLoop(self):
		iterations = self.settings['iterations']
		self.logger.info('begin simulated target loop of %s iterations' % (iterations,))
		self.simloopstop.clear()
		for i in range(iterations):
			self.logger.info('iteration %s of %s' % (i+1, iterations,))
			self.simulateTarget()
			if self.simloopstop.isSet():
				self.logger.info('User stopped loop')
				break
			waittime = self.settings['wait time']
			time.sleep(waittime)
		self.logger.info('Simulated Target Loop Done')
	

	def simulateTargetLoopStop(self):
		self.logger.info('Simulated Target Loop will stop after next iteration')
		self.simloopstop.set()

	def loadImage(self, imagedata):
			try:
				num = imagedata['image'].read()
			except AttributeError:
				pass
			else:
				imagedata.__setitem__('image', num, force=True)
			self.setImage(imagedata['image'].astype(Numeric.Float32), 'Image')

	def adjustTargetForDrift(self, oldtarget):
		if oldtarget['image'] is None:
			return oldtarget
		## check if drift has occurred since target's parent image was acquired
		# hack to be sure image data is not read, since it's not needed
		imageref = oldtarget.special_getitem('image', dereference=False)
		imageid = imageref.dbid
		self.logger.debug('ADJUSTTARGET, imageid: %s' % (imageid,))
		imagedata = self.researchDBID(data.AcquisitionImageData, imageid, readimages=False)
		# image time
		imagetime = imagedata['scope']['system time']
		self.logger.debug('ADJUSTTARGET, imagetime: %s' % (imagetime,))
		# last declared drift
		lastdeclared = self.research(data.DriftDeclaredData(), results=1)
		self.logger.debug('ADJUSTTARGET, lastdeclared: %s' % (lastdeclared,))
		if not lastdeclared:
			## no drift declared, no adjustment needed
			return oldtarget
		# last declared drift time
		lastdeclared = lastdeclared[0]
		lastdeclaredtime = lastdeclared['system time']
		# has drift occurred?
		if imagetime < lastdeclaredtime:
			self.logger.info('target needs shift')
			# yes, now we need a recent image drift for this image
			query = data.AcquisitionImageDriftData()
			query['image'] = imagedata
			imagedrift = self.research(query, results=1)
			# was image drift already measured for this image?
			if not imagedrift:
				self.logger.info('need to request image drift')
				# no, request measurement now
				imagedrift = self.requestImageDrift(imagedata)
			else:
				# yes, but was it measured after declared drift?
				imagedrift = imagedrift[0]
				if imagedrift['system time'] < lastdeclaredtime:
					self.logger.info('existing image drift, but too old, requesting new one')
					# too old, need to measure it again
					imagedrift = self.requestImageDrift(imagedata)

			## create new adjusted target from old adjusted target and original target
			originaltargetquery = data.AcquisitionImageTargetData(initializer=oldtarget)
			originaltargetquery['version'] = 0
			originaltargetquery['delta row'] = None
			originaltargetquery['delta column'] = None
			results = self.research(datainstance=originaltargetquery, results=1)
			originaltarget = results[0]
			dr = originaltarget['delta row']
			dc = originaltarget['delta column']
			self.logger.info('original target:  %s, %s' % (dr, dc))

			newtarget = data.AcquisitionImageTargetData(initializer=oldtarget)
			newtarget['version'] += 1
			newtarget['delta row'] = originaltarget['delta row'] + imagedrift['rows']
			newtarget['delta column'] = originaltarget['delta column'] + imagedrift['columns']
			dr = newtarget['delta row']
			dc = newtarget['delta column']
			self.logger.info('new target:  %s, %s' % (dr, dc))
			self.publish(newtarget, database=True, dbforce=True)
			return newtarget
		else:
			self.logger.info('target does not need shift')
			return oldtarget

	def requestImageDrift(self, imagedata):
		# need to have drift manager do it
		self.received_image_drift.clear()
		ev = event.NeedTargetShiftEvent(image=imagedata)
		imageid = imagedata.dbid
		## set requested_drift to the reply can be recognized
		self.requested_drift = imageid
		self.logger.debug('Sending NeedTargetShiftEvent and waiting, imageid = %s' % (imageid,))
		self.outputEvent(ev)
		self.setStatus('waiting')
		self.received_image_drift.wait()
		self.setStatus('processing')
		self.logger.debug('Done waiting for NeedTargetShiftEvent')
		return self.requested_drift

	def handleImageDrift(self, ev):
		self.logger.debug('HANDLING IMAGE DRIFT')
		driftdata = ev['data']
		imageid = driftdata.special_getitem('image', dereference=False).dbid
		## only continue if this was one that I requested
		if imageid == self.requested_drift:
			self.requested_drift = driftdata
			self.received_image_drift.set()
