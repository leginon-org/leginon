#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#
'''
Acquisition node is a TargetWatcher, so it receives either an ImageTargetData
or an ImageTargetListData.  The method processTargetData is called on each
ImageTargetData.
'''
import targetwatcher
import time
from leginon import leginondata
import event
import calibrationclient
import presets
import copy
import threading
import node
import instrument
import gui.wx.Acquisition
import gui.wx.Presets
import navigator
import appclient
import numpy
import numpy.linalg
import math
from pyami import arraystats, imagefun, ordereddict, moduleconfig
import smtplib
import emailnotification
import leginonconfig
import gridlabeler
import itertools
import re       # wjr for getting rid of gr in filename

debug = False

class NoMoveCalibration(targetwatcher.PauseRepeatException):
	pass

class InvalidPresetsSequence(targetwatcher.PauseRepeatException):
	pass

class InvalidSettings(targetwatcher.PauseRepeatException):
	pass

class BadImageStatsPause(targetwatcher.PauseRepeatException):
	pass

class BadImageAcquirePause(targetwatcher.PauseRestartException):
	pass

class BadImageAcquireBypass(targetwatcher.BypassException):
	pass

class BadImageStatsAbort(Exception):
	pass

class InvalidStagePosition(targetwatcher.BypassWarningException):
	pass

def setImageFilename(imagedata):
	if imagedata['filename'] is not None:
		return
	listlabel = ''
	numberstr = '%05d' % (imagedata['target']['number'],)
	if imagedata['target']['list'] is not None:
		listlabel = imagedata['target']['list']['label']
	if imagedata['preset'] is None:
		presetstr = ''
	else:
		presetstr = imagedata['preset']['name']
	mystr = numberstr + presetstr
	rootname = getRootName(imagedata, listlabel)
	parts = []
	parts.append(rootname)
	if listlabel:
		parts.append(listlabel)
	parts.append(mystr)
	if imagedata['version']:
		vstr = 'v%02d' % (imagedata['version'],)
		parts.append(vstr)

	filename = '_'.join(parts)
	imagedata['filename'] = filename

def isSkipGrTileId():
	is_skip = False
	try:
		is_skip = moduleconfig.getConfigured('leginon_session.cfg', 'leginon')['filename']['skip_gr_tile_id']
	except IOError as e:
		pass
	except KeyError:
		pass
	return is_skip

def getRootName(imagedata, listlabel=False):
	'''
	get the root name of an image from its parent
	'''
	parent_target = imagedata['target']
	usegridlabel = not listlabel
	if parent_target is None:
		## there is no parent target
		## create my own root name
		return newRootName(imagedata, usegridlabel)

	parent_image = parent_target['image']
	if parent_image is None:
		## there is no parent image
		return newRootName(imagedata, usegridlabel)

	## use root name from parent image
	parent_root = parent_image['filename']
	if parent_root:
		if isSkipGrTileId():
			parent_root = re.sub(r'_\d+gr','',parent_root)    # wjr eliminate grid number and grid label
		if parent_target['spotmap'] and not parent_image['spotmap']:
			# target only has spotmap if from MosaicSpotFinder
			parent_root += '_%s' % (parent_target['spotmap']['name'])
		return parent_root
	else:
		return newRootName(imagedata, usegridlabel)

def newRootName(imagedata, usegridlabel):
	parts = []
	sessionstr = imagedata['session']['name']
	parts.append(sessionstr)
	if usegridlabel:
		if 'grid' in imagedata and imagedata['grid'] is not None:
			gridlabel = gridlabeler.getGridLabel(imagedata['grid'])
			parts.append(gridlabel)
	sep = '_'
	name = sep.join(parts)
	return name


class Acquisition(targetwatcher.TargetWatcher):
	panelclass = gui.wx.Acquisition.Panel
	settingsclass = leginondata.AcquisitionSettingsData
	# maybe not a class attribute
	defaultsettings = dict(targetwatcher.TargetWatcher.defaultsettings)
	defaultsettings.update({
		'pause time': 2.5,
		'first pause time': 0,
		'pause between time': 0,
		'move type': 'image shift',
		'preset order': [],
		'correct image': True,
		'display image': True,
		'save image': True,
		'wait for process': False,
		'wait for rejects': False,
		'wait for reference': False,
		#'duplicate targets': False,
		#'duplicate target type': 'focus',
		'iterations': 1,
		'wait time': 0,
		'loop delay time': 0,
		'adjust for transform': 'no',
		'use parent mover': False,
		'drift between': False,
		'mover': 'presets manager',
		'move precision': 0.0,
		'accept precision': 1e-3,
		'process target type': 'acquisition',
		'save integer': False,
		'background': False,
		'use parent tilt': False,
		'adjust time by tilt': False,
		'reset tilt': False,
		'high mean': 2**16,
		'low mean': 50,
		'bad stats response': 'Continue',
		'bad stats type': 'Mean',
		'reacquire when failed': False,
		'recheck pause time': 10,
		'target offset row': 0,
		'target offset col': 0,
		'correct image shift coma': False,
		'park after target': False,
		'set aperture': False,
		'objective aperture': 'open',
		'c2 aperture': '150',
	})
	eventinputs = targetwatcher.TargetWatcher.eventinputs \
								+ [event.DriftMonitorResultEvent,
										event.MakeTargetListEvent,
										event.ImageProcessDoneEvent,
										event.AcquisitionImagePublishEvent,
										event.PhasePlateUsagePublishEvent,
										event.PauseEvent,
										event.ContinueEvent,
									] \
								+ presets.PresetsClient.eventinputs \
								+ navigator.NavigatorClient.eventinputs
	eventoutputs = targetwatcher.TargetWatcher.eventoutputs \
									+ [event.LockEvent,
											event.UnlockEvent,
											event.AcquisitionImagePublishEvent,
	event.ChangePresetEvent, event.PresetLockEvent, event.PresetUnlockEvent,
											event.DriftMonitorRequestEvent, 
											event.FixBeamEvent,
											event.FixAlignmentEvent,
											event.FixConditionEvent,
											event.AlignZeroLossPeakPublishEvent,
											event.ScreenCurrentLoggerPublishEvent,
											event.PhasePlatePublishEvent,
											event.NodeBusyNotificationEvent,
											event.ManagerPauseAvailableEvent,
											event.ManagerPauseNotAvailableEvent,
											event.ManagerContinueAvailableEvent,
											event.ImageListPublishEvent, event.ReferenceTargetPublishEvent] \
											+ navigator.NavigatorClient.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		targetwatcher.TargetWatcher.__init__(self, id, session, managerlocation, **kwargs)

		self.addEventInput(event.AcquisitionImagePublishEvent, self.handleDriftImage)
		self.addEventInput(event.DriftMonitorResultEvent, self.handleDriftResult)
		self.addEventInput(event.ImageProcessDoneEvent, self.handleImageProcessDone)
		self.addEventInput(event.MakeTargetListEvent, self.setGrid)
		self.addEventInput(event.PhasePlateUsagePublishEvent, self.handlePhasePlateUsage)
		self.addEventInput(event.PauseEvent, self.handlePause)
		self.addEventInput(event.ContinueEvent, self.handleContinue
)
		self.driftdone = threading.Event()
		self.driftimagedone = threading.Event()
		self.instrument = instrument.Proxy(self.objectservice, self.session)

		self.calclients = ordereddict.OrderedDict()
		self.calclients['image shift'] = calibrationclient.ImageShiftCalibrationClient(self)
		self.calclients['stage position'] = calibrationclient.StageCalibrationClient(self)
		self.calclients['modeled stage position'] = calibrationclient.ModeledStageCalibrationClient(self)
		self.calclients['image beam shift'] = calibrationclient.ImageBeamShiftCalibrationClient(self)
		self.calclients['beam shift'] = calibrationclient.BeamShiftCalibrationClient(self)
		self.calclients['beam tilt'] = calibrationclient.BeamTiltCalibrationClient(self)

		self.presetsclient = presets.PresetsClient(self)
		self.navclient = navigator.NavigatorClient(self)
		self.doneevents = {}
		self.onTarget = False
		self.imagelistdata = None
		self.simloopstop = threading.Event()
		self.received_image_drift = threading.Event()
		self.requested_drift = None
		self.grid = None
		self.pp_used = None
		self.acq_counter = itertools.cycle(range(0,5))
		self.time0 = time.time()
		self.times = []
		self.intensities = []
		self.targetfinder_from = False
		self.alignzlp_bound = False
		self.phaseplate_bound = False
		self.screencurrent_bound = False
		self.alignzlp_warned = False
		self.beamtilt0 = None
		self.paused_by_gui = False
		self.retry_count = 0

		self.duplicatetypes = ['acquisition', 'focus']
		self.presetlocktypes = ['acquisition', 'target', 'target list']

		if debug:
			self.timedebug = {}

		self.start()

	def setStatus(self, status):
		'''
		Modify Node setStatus to allow manager to pause or continue.
		'''
		if status == 'user input':
			self.notifyManagerContinueAvailable()
		else:
			self.notifyManagerPauseAvailable()
		super(Acquisition, self).setStatus(status)

	def handleApplicationEvent(self,evt):
		'''
		Find Reference class or its subclass instance bound
		to this node upon application loading.
		'''
		super(Acquisition, self).handleApplicationEvent(evt)
		app = evt['application']
		self.targetfinder_from = appclient.getLastNodeThruBinding(app,self.name,'ImageTargetListPublishEvent','TargetFinder')
		self.alignzlp_bound = appclient.getNextNodeThruBinding(app,self.name,'AlignZeroLossPeakPublishEvent','AlignZeroLossPeak')
		self.phaseplate_bound = appclient.getNextNodeThruBinding(app,self.name,'PhasePlatePublishEvent','PhasePlateAligner')
		self.screencurrent_bound = appclient.getNextNodeThruBinding(app,self.name,'ScreenCurrentLoggerPublishEvent','ScreenCurrentLogger')

	def checkSettings(self, settings):
		problems = []
		return problems
		presetnames = settings['preset order']
		for presetname in presetnames:
			try:
				self.presetsclient.getPresetFromDB(presetname)
			except:
				problems.append(('error','Preset "%s" does not exist.  Create it, or import from a previous session' % (presetname,)))
				continue
			for type in ('dark', 'norm'):
				for channel in (0,1):
					exists = self.presetsclient.correctorImageExists(presetname, type, channel)
					if not exists:
						problems.append(('error','Preset "%s" Missing %s CCD image, channel %s' % (presetname, type, channel)))

		return problems

	def onPresetPublished(self, evt):
		evt = gui.wx.Presets.NewPresetEvent()
		self.panel.GetEventHandler().AddPendingEvent(evt)

	def handleDriftResult(self, ev):
		driftresult = ev['data']
		status = driftresult['status']
		final = driftresult['final']
		drift = numpy.hypot(final['rowmeters'],final['colmeters']) / final['interval']
		self.reportStatus('acquisition', 'Received drift result status "%s", final drift: %.3e' % (status, drift))
		self.driftresult = driftresult
		self.driftdone.set()

	def handleDriftImage(self, ev):
		driftimage = ev['data']
		self.reportStatus('acquisition', 'Received drift image')
		self.driftimage = driftimage
		self.driftimagedone.set()

	def handleImageProcessDone(self, ev):
		imageid = ev['imageid']
		status = ev['status']
		if imageid in self.doneevents:
			self.doneevents[imageid]['status'] = status
			self.doneevents[imageid]['received'].set()

	def handlePhasePlateUsage(self, ev):
		pp_used = ev['data']
		if pp_used:
			self.reportStatus('acquisition', 'Received phase plate patch assignment')
			self.pp_used = pp_used

	def processData(self, newdata):
		if isinstance(newdata, leginondata.QueueData):
			self.processTargetListQueue(newdata)
			return
		self.logger.info('Acquisition.processData')
		self.imagelistdata = leginondata.ImageListData(session=self.session,
																						targets=newdata)
		self.publish(self.imagelistdata, database=True)
		listid = newdata.dbid
		if self.inDoneTargetList(newdata):
			# most likely aborted from myamiweb
			self.logger.info('target list ID: %d found in DoneImageTargetList' % (listid,))
			# send event so waiting stops.
			status='success'
			e = event.TargetListDoneEvent(targetlistid=listid, status=status, targetlist=newdata)
			self.outputEvent(e)
			self.logger.info('TargetListDoneEvent sent')
			return
		targetwatcher.TargetWatcher.processData(self, newdata)
		self.publish(self.imagelistdata, pubevent=True)
		self.logger.info('Acquisition.processData done')

	def validateStagePosition(self, stageposition):
		## check for out of stage range target
		stagelimits = self.instrument.tem.StageLimits
		for axis, limits in stagelimits.items():
			if stageposition[axis] < limits[0] or stageposition[axis] > limits[1]:
				pstr = '%s: %g' % (axis, stageposition[axis])
				messagestr = 'Stage position %s out of range' % pstr
				raise InvalidStagePosition(messagestr)

	def validatePresets(self):
		presetorder = self.settings['preset order']
		if not presetorder:
			raise InvalidPresetsSequence('no presets configured')
		availablepresets = self.getPresetNames()
		for presetname in presetorder:
			if presetname not in availablepresets:
				raise InvalidPresetsSequence('bad preset %s in presets order' % (presetname,))

	def makeOffsetTarget(self, target, offset):
		newtarget = leginondata.AcquisitionImageTargetData(initializer=target)
		# Fix here about version
		newtarget['delta row'] = target['delta row'] + offset['y']
		newtarget['delta column'] = target['delta column'] + offset['x']
		newtarget['fromtarget'] = target
		newtarget.insert(force=True)
		self.logger.info('target offset by (%.1f,%.1f) (column, row)' % (offset['x'],offset['y']))
		return newtarget

	def avoidTargetAdjustment(self,target_to_adjust,recent_target):
		'''
		Determine if target adjustment should be avoided.
		'''
		return False

	def adjustTargetForTransform(self, targetdata):
		## look up most recent version of this target
		targetlist = targetdata['list']
		targetnumber = targetdata['number']
		newtargetdata = self.researchTargets(session=self.session, number=targetnumber, list=targetlist)
		newtargetdata = newtargetdata[0]

		if self.avoidTargetAdjustment(targetdata,newtargetdata):
			return newtargetdata

		## look up all transforms declared for this session
		decq = leginondata.TransformDeclaredData(session=self.session)
		transformsdeclared = decq.query()

		## if no transforms declared, return recent target
		if not transformsdeclared:
			return newtargetdata

		## if recent target after transforms declared, return recent target
		if newtargetdata['image'] is None:
			# simulated target
			newtargettime = newtargetdata.timestamp
		else:
			# need to compare when the parent image is acquired not when target is
			# selected
			try:
				# newtargetdata['image'] does not always has timestamp attribute. 
				# Do direct query
				parentid = newtargetdata['image'].dbid
				q = leginondata.AcquisitionImageData
				parentdata = q.direct_query(parentid, readimages=False)
				newtargettime = parentdata.timestamp
			except:
				self.logger.warning("Could not find parent image (ID: %d) timestamp,use targetinstead" % parentdata.dbid)
				newtargettime = newtargetdata.timestamp
		declaredtime = transformsdeclared[0].timestamp
		if newtargettime > declaredtime:
			return newtargetdata

		## if transform declared after most recent target, need new transformed	target
		newtargetdata = self.requestTransformTarget(newtargetdata)
			
		## make sure we move to new target
		self.onTarget = False
		return newtargetdata

	def tunePhasePlate(self, presetname):
		# TO DO: need some way to check if there is a phase plate
		presetdata = self.presetsclient.getPresetByName(presetname)
		if type(self.phaseplate_bound)==type({}) and self.phaseplate_bound['is_direct_bound']:
				self.nextPhasePlate(presetname)

	def tuneEnergyFilter(self, presetname):
		presetdata = self.presetsclient.getPresetByName(presetname)
		if not presetdata:
			return
		if presetdata['energy filter'] or presetdata['tem energy filter']:
			if type(self.alignzlp_bound)==type({}) and self.alignzlp_bound['is_direct_bound']:
				self.alignZeroLossPeak(presetname)
			else:
				if False:
					self.logger.warning('Energy filter activated but can not tune without binding to Align ZLP')
					self.alignzlp_warned = True	

	def monitorScreenCurrent(self, presetname):
		presetdata = self.presetsclient.getPresetByName(presetname)
		if not presetdata:
			return
		if type(self.screencurrent_bound) == dict({}) and self.screencurrent_bound['is_direct_bound']==True:
			self.measureScreenCurrent(presetname)

	def nextPhasePlate(self, preset_name):
		'''
		Send Phase Plate Advancement  request
		'''
		request_data = leginondata.PhasePlateData()
		request_data['session'] = self.session
		request_data['preset'] = preset_name
		self.publish(request_data, database=True, pubevent=True, wait=True)

	def alignZeroLossPeak(self, preset_name):
		'''
		Send align ZLP  request
		'''
		self.setStatus('waiting')
		request_data = leginondata.AlignZeroLossPeakData()
		request_data['session'] = self.session
		request_data['preset'] = preset_name
		self.publish(request_data, database=True, pubevent=True, wait=True)
		self.setStatus('processing')

	def measureScreenCurrent(self, preset_name): 
		'''
		Send screen current measurement request
		'''
		request_data = leginondata.ScreenCurrentLoggerData()
		request_data['session'] = self.session
		request_data['preset'] = preset_name
		self.publish(request_data, database=True, pubevent=True, wait=True)

	def preTargetSetup(self):
		'''
		Things to do before moving to each target and set preset
		'''
		zlp_preset_name = self.settings['preset order'][-1]
		self.logger.info('Tuning before processing a target')
		self.tuneEnergyFilter(zlp_preset_name)
		self.monitorScreenCurrent(zlp_preset_name)

	def validateSettings(self):
		'''
		A chance for subclass to abort processTargetData.
		'''
		pass

	def processTargetData(self, targetdata, attempt=None):
		'''
		This is called by TargetWatcher.processData when targets available
		If called with targetdata=None, this simulates what occurs at
		a target (going to presets, acquiring images, etc.)
		'''
		# validate any bad settings that requires aborting now.
		try:
			self.validateSettings()
		except Exception as e:
			self.logger.error(str(e))
			raise
		# need to validate presets before preTargetSetup because they need
		# to use preset, too, even though not the same target.
		try:
			self.validatePresets()
		except InvalidPresetsSequence as e:
			if targetdata is None or targetdata['type'] == 'simulated':
				## don't want to repeat in this case
				self.logger.error(str(e))
				return 'aborted'
			else:
				raise
		except Exception as e:
			self.logger.error(str(e))
			raise

		self.preTargetSetup()
		# process target begins
		presetnames = self.settings['preset order']
		ret = 'ok'
		self.onTarget = False
		for preset_index, newpresetname in enumerate(presetnames):
			if self.alreadyAcquired(targetdata, newpresetname):
				continue

			if targetdata is not None and targetdata['type'] != 'simulated' and self.settings['adjust for transform'] != 'no':
				if self.settings['drift between'] and self.goodnumber > 0:
						self.declareDrift('between targets')
				targetonimage = targetdata['delta column'],targetdata['delta row']
				targetdata = self.adjustTargetForTransform(targetdata)
				self.logger.info('target adjusted by (%.1f,%.1f) (column, row)' % (targetdata['delta column']-targetonimage[0],targetdata['delta row']-targetonimage[1]))
			offset = {'x':self.settings['target offset col'],'y':self.settings['target offset row']}
			if offset['x'] or offset['y']:
				targetdata = self.makeOffsetTarget(targetdata,offset)

			# set stage z first before move
			z = self.moveToLastFocusedStageZ(targetdata)
			self.testprint('preset manager moved to LastFocusedStageZ %s' % (z,))

			### determine how to move to target
			try:
				emtarget = self.targetToEMTargetData(targetdata, z)
			except InvalidStagePosition as e:
				raise

			presetdata = self.presetsclient.getPresetByName(newpresetname)

			pause_between_time = self.settings['pause between time']
			if preset_index > 0 and pause_between_time > 0.0:
				self.logger.info('Pausing for extra %.1f before acquisition with %s' % (pause_between_time,newpresetname))
				time.sleep(pause_between_time)
			### acquire CCD
			self.startTimer('acquire')
			ret = self.acquire(presetdata, emtarget, attempt=attempt, target=targetdata)
			self.stopTimer('acquire')
			# in these cases, return immediately
			if ret in ('aborted', 'repeat'):
				self.reportStatus('acquisition', 'Acquisition state is "%s"' % ret)
				break
			if ret == 'repeat':
				return repeat

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
		presetquery = leginondata.PresetData(name=presetname)
		targetquery = leginondata.AcquisitionImageTargetData(initializer=targetdata)
		## don't care if drift correction was done on target after image was
		## acquired, so ignore version, delta row/col, parentimage, and fromtarget
		targetquery['version'] = None
		targetquery['delta row'] = None
		targetquery['delta column'] = None
		targetquery['image'] = None
		targetquery['fromtarget'] = None
		imagequery = leginondata.AcquisitionImageData(target=targetquery, preset=presetquery)
		## other things to fill in
		imagequery['scope'] = leginondata.ScopeEMData()
		imagequery['camera'] = leginondata.CameraEMData()
		imagequery['session'] = leginondata.SessionData()
		datalist = self.research(datainstance=imagequery)
		if datalist:
			## no need to acquire again, but need to republish
			self.reportStatus('output', 'Image was acquired previously, republishing')
			imagedata = datalist[0]
			self.publishDisplayWait(imagedata)
			return True
		else:
			return False

	def targetToEMTargetData(self, targetdata, z=None):
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
		emtargetdata = leginondata.EMTargetData()
		if targetdata is not None:
			# get relevant info from target data
			targetdeltarow = targetdata['delta row']
			targetdeltacolumn = targetdata['delta column']
			origscope = targetdata['scope']
			# printing parent scope parameters for debugging
			if targetdata['image']:
				parentscope = targetdata['image']['scope']
			else:
				parentscope = None
			if hasattr(origscope,'dbid'):
				self.logger.info('Using ScopeEMData  id %d for emscope calculation' % origscope.dbid)
			if hasattr(parentscope,'dbid'):
				self.logger.info('Parent ScopeEMData id %d' % parentscope.dbid)
				self.logger.info('target parent image stage position (%.2f, %.2f) um' % (parentscope['stage position']['x']*1e6, parentscope['stage position']['y']*1e6)) 
			self.logger.info('origscope stage position (%.2f, %.2f) um' % (origscope['stage position']['x']*1e6, origscope['stage position']['y']*1e6)) 
			# Initialize targetscope
			targetscope = leginondata.ScopeEMData(initializer=origscope)
			## copy these because they are dictionaries that could
			## otherwise be shared (although transform() should be
			## smart enough to create copies as well)
			targetscope['stage position'] = dict(origscope['stage position'])
			targetscope['image shift'] = dict(origscope['image shift'])
			targetscope['beam shift'] = dict(origscope['beam shift'])

			if z is not None:
				# since presetsmanager settings 'only xy' is always True, this
				# is only good for database record
				targetscope['stage position']['z'] = z

			movetype = self.settings['move type']
			oldpreset = targetdata['preset']

			zdiff = 0.0
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
				except calibrationclient.NoMatrixCalibrationError as e:
					raise NoMoveCalibration(e)

				## if stage is tilted and moving by image shift,
				## calculate z offset between center of image and target
				if movetype in ('image shift','image beam shift','beam shift') and abs(targetscope['stage position']['a']) > 0.02:
					calclient = self.calclients['stage position']
					try:
						tmpscope = calclient.transform(pixelshift, targetscope, targetcamera)
					except calibrationclient.NoMatrixCalibrationError as e:
						raise NoMoveCalibration(e)
					ydiff = tmpscope['stage position']['y'] - targetscope['stage position']['y']
					zdiff = ydiff * numpy.sin(targetscope['stage position']['a'])
	
			### check if stage position is valid
			if newscope['stage position']:
				self.validateStagePosition(newscope['stage position'])

			emtargetdata['preset'] = oldpreset
			emtargetdata['movetype'] = movetype
			emtargetdata['image shift'] = dict(newscope['image shift'])
			emtargetdata['beam shift'] = dict(newscope['beam shift'])
			emtargetdata['stage position'] = dict(newscope['stage position'])
			emtargetdata['delta z'] = zdiff

		emtargetdata['target'] = targetdata
		## publish in DB because it will likely be needed later
		## when returning to the same target,
		## even after it is removed from memory
		# This may be a problem for focus target when used to return to it.
		self.publish(emtargetdata, database=True)
		return emtargetdata

	def setImageFilename(self, imagedata):
		setImageFilename(imagedata)

	def exposeSpecimen(self, seconds):
		self.exposeSpecimenWithShutterOverride(seconds)
		#self.exposeSpecimenWithScreenDown(seconds)

	def getImageShiftOffset(self):
		pimageshift = self.presetsclient.currentpreset['image shift']
		simageshift = self.instrument.tem.ImageShift
		offsetx = simageshift['x'] - pimageshift['x']
		offsety = simageshift['y'] - pimageshift['y']
		return {'x': offsetx, 'y': offsety}

	def setImageShiftOffset(self, imageshift):
		simageshift = self.instrument.tem.ImageShift
		x = simageshift['x'] + imageshift['x']
		y = simageshift['y'] + imageshift['y']
		self.instrument.tem.ImageShift = {'x':x, 'y':y}

	def setPresetMagProbeMode(self, presetdata,emtarget):
		'''
		Set magnification and probe mode according to presetdata.
		This is required before setting beam tilt or other projection
		submode dependent values.
		'''
		if not presetdata:
			return
		tem = presetdata['tem']
		current_tem = self.instrument.getTEMData()
		if not tem or current_tem.dbid != tem.dbid:
			self.instrument.setTEM(tem['name'])
		# magnification check
		preset_mag = presetdata['magnification']
		current_mag = self.instrument.tem.Magnification
		# probe mode
		current_probe = self.instrument.tem.getProbeMode()
		preset_probe = presetdata['probe mode']
		if preset_mag != current_mag or preset_probe != current_probe:
			presetname = presetdata['name']
			self.logger.info('Setting Preset and emtarget to %s to get zero beam tilt and stig' % (presetname))
			self.presetsclient.toScope(presetname, emtarget, keep_shift=False)
		
	def setComaStig0(self):
		mag = self.instrument.tem.Magnification
		self.logger.info('Set zero beam tilt and stig at %d mag' % (int(mag)))
		self.beamtilt0 = self.instrument.tem.getBeamTilt()
		self.stig0 = self.instrument.tem.getStigmator()['objective']
		self.defoc0 = self.instrument.tem.getDefocus()
		self.probe0 = self.instrument.tem.getProbeMode()

	def moveAndPreset(self, presetdata, emtarget):
			'''
			Move xy to emtarget position with its mover and set preset
			'''
			status = 'ok'
			presetname = presetdata['name']
			targetdata = emtarget['target']
			#### move and change preset
			movetype = self.settings['move type']
			movefunction = self.settings['mover']
			keep_shift = False
			if 'shift' in movetype and movefunction == 'navigator':
				self.logger.warning('Navigator cannot be used for %s, using Presets Manager instead' % movetype)
				movefunction = 'presets manager'
			self.setStatus('waiting')
			if movefunction == 'navigator':
				emtarget = None
				if not self.onTarget and targetdata['type'] != 'simulated':
					precision = self.settings['move precision']
					accept_precision = self.settings['accept precision']
					final_imageshift = self.settings['final image shift']
					if final_imageshift:
						keep_shift = True
					status = self.navclient.moveToTarget(targetdata, movetype, precision, accept_precision, final_imageshift=final_imageshift, use_current_z=True)
					if status == 'error':
						return status
					# Give presetsclient time to unlock navigator changePreset request
					time.sleep(0.5)
			self.presetsclient.toScope(presetname, emtarget, keep_shift=keep_shift)
			if self.presetsclient.stage_targeting_failed:
				self.setStatus('idle')
				return 'error'
			try:
				# Random defocus is set in presetsclient.  This is the easiestt
				# way to get it.  Could be better.
				self.intended_defocus = self.instrument.tem.Defocus - emtarget['delta z']
			except:
				self.intended_defocus = self.instrument.tem.Defocus
			# DO this the second time give an effect of normalization. Removed defocus and beam shift hysteresis on Talos
			if presetdata['tem']['hostname'] == 'talos-20taf2c':
				self.presetsclient.toScope(presetname, emtarget, keep_shift=keep_shift)
			stageposition = self.instrument.tem.getStagePosition()
			stagea = stageposition['a']
			if self.settings['correct image shift coma']:
				## beam tilt correction induced by image shift
				beamtiltclient = self.calclients['beam tilt']
				tem = self.instrument.getTEMData()
				cam = self.instrument.getCCDCameraData()
				ht = self.instrument.tem.HighTension
				mag = self.instrument.tem.Magnification
				self.setComaStig0()
				imageshift = self.instrument.tem.getImageShift()
				try:
					beamtilt = beamtiltclient.transformImageShiftToBeamTilt(imageshift, tem, cam, ht, self.beamtilt0, mag)
					self.instrument.tem.BeamTilt = beamtilt
					self.logger.info("beam tilt for image acquired (%.4f,%.4f)" % (self.instrument.tem.BeamTilt['x'],self.instrument.tem.BeamTilt['y']))
				except Exception as e:
					self.resetComaCorrection()
					raise NoMoveCalibration(e)
				try:
					stig = beamtiltclient.transformImageShiftToObjStig(imageshift, tem, cam, ht, self.stig0, mag)
					self.instrument.tem.Stigmator = {'objective':stig}
					stig1 = self.instrument.tem.getStigmator()['objective']
					self.logger.info("objective stig for image acquired (%.4f,%.4f)" % (stig1['x']-self.stig0['x'],stig1['y']-self.stig0['y']))
				except Exception as e:
					self.resetComaCorrection()
					raise NoMoveCalibration(e)
				try:
					defoc = beamtiltclient.transformImageShiftToDefocus(imageshift, tem, cam, ht, self.defoc0, mag)
					self.instrument.tem.Defocus = defoc
					defoc1 = self.instrument.tem.getDefocus()
					self.logger.info("correcting defocus for image acquired by (%.4f) (um)" % ((defoc1-self.defoc0)*1e6))
				except Exception as e:
					self.resetComaCorrection()
					raise NoMoveCalibration(e)

			if self.settings['adjust time by tilt'] and abs(stagea) > 10 * 3.14159 / 180:
				camdata = leginondata.CameraEMData()
				camdata.friendly_update(presetdata)
				old_time = camdata['exposure time']
				new_time = old_time / math.cos(stagea)
				if new_time > 5000 or new_time <= 1:
					self.logger.warning('Ignore unreasonable exposure time at %d ms' % new_time)
					new_time = old_time
				camdata['exposure time'] = new_time
				self.logger.info('scale exposure time from %d to %d by cos(%d)' % (old_time,new_time,int(stagea*180/3.14159)))
				self.instrument.setData(camdata)
			self.onTarget = True
			self.setStatus('processing')
			return status

	def acquireCCD(self, presetdata, emtarget=None,channel=None):
		targetdata = emtarget['target']
		## set correction channel
		## in the future, may want this based on preset or something
		if channel is None:
			channel = 0
		else:
			channel = channel
		## acquire image
		self.reportStatus('acquisition', 'acquiring image...')
		self.startTimer('acquire getData')
		correctimage = self.settings['correct image']
		imagedata = self._acquireCameraImage(correctimage, channel)
		self.reportStatus('acquisition', 'image acquired')
		self.stopTimer('acquire getData')
		retry_limit = 3
		while self.settings['reacquire when failed'] and (imagedata is None or imagedata['image'] is None) and self.retry_count < retry_limit:
			self.retry_count += 1
			self.logger.info('pause %d seconds before retry' % self.settings['recheck pause time'])
			time.sleep(self.settings['recheck pause time'])
			self.logger.warning('reaquiring image trial %d' % self.retry_count)
			imagedata = self._acquireCameraImage(correctimage, channel)
		if imagedata is None:
			raise BadImageAcquirePause('failed acquire camera image')
		if imagedata['image'] is None:
			raise BadImageAcquirePause('Acquired array is None. Possible camera problem')

		if self.settings['bad stats response'] != 'Continue':
			self.recheck_counter = itertools.count()
			# For ring collapse testing
			#c = self.acq_counter.next()
			#imagearray = imagedata['image'] - c*c
			imagearray = imagedata['image']
			self.evaluateStats(imagearray)

		## convert float to uint16
		if self.settings['save integer']:
			imagedata['image'] = numpy.clip(imagedata['image'], 0, 2**16-1)
			imagedata['image'] = numpy.asarray(imagedata['image'], numpy.uint16)

		## convert CameraImageData to AcquisitionImageData
		dim = imagedata['camera']['dimension']
		pixels = dim['x'] * dim['y']
		try:
			pixeltype = str(imagedata['image'].dtype)
		except:
			self.logger.error('array not returned from camera')
			is_failed = self.resetComaCorrection()
			if is_failed:
				raise BadImageAcquirePause('Failed reset coma correction. Not safe to continue automatically')
			return
		imagedata = leginondata.AcquisitionImageData(initializer=imagedata, preset=presetdata, label=self.name, target=targetdata, list=self.imagelistdata, emtarget=emtarget, pixels=pixels, pixeltype=pixeltype)
		imagedata['phase plate'] = self.pp_used
		imagedata['version'] = 0
		## store EMData to DB to prevent referencing errors
		self.publish(imagedata['scope'], database=True)
		self.publish(imagedata['camera'], database=True)
		return imagedata

	def _acquireCameraImage(self, correctimage, channel):
		if correctimage:
			imagedata = self.acquireCorrectedCameraImageData(channel=channel)
		else:
			imagedata = self.acquireCameraImageData()
		return imagedata

	def preAcquire(self, presetdata, emtarget=None, channel=None, reduce_pause=False):
		'''
		Things to do after moved to preset.
		'''
		if debug:
			try:
				tnum = emtarget['target']['number']
				tkey = emtarget.dbid
			except:
				tnum = None
				tkey = None
			print tnum, 'MOVEANDPRESETPAUSE START'
			t0 = time.time()
			self.timedebug[tkey] = t0
			if 'consecutive' in self.timedebug:
				print tnum, '************************************* CONSECUTIVE', t0 - self.timedebug['consecutive']
			self.timedebug['consecutive'] = t0

		pausetime = self.settings['pause time']
		if reduce_pause:
			pausetime = min(pausetime, 2.5)
		elif self.is_firstimage and self.settings['first pause time'] > 0.1:
			# pause longer for the first image of the first target
			# this is used for the first image taken that touches the edge of the hole
			# in a multiple high mag target in a c-flat or quantifoil hole
			extra_pausetime = self.settings['first pause time']
			self.logger.info('Pause extra %s s for first image' % extra_pausetime)
			pausetime += extra_pausetime

		self.logger.info('pausing for %s s' % (pausetime,))

		self.startTimer('pause')
		t = threading.Thread(target=self.positionCamera)
		t.start()
		time.sleep(pausetime)
		self.waitPositionCameraDone()
		self.stopTimer('pause')
		# the next image will not be first even if repeated
		self.is_firstimage = False

		if debug:
			print tnum, 'MOVEANDPRESETPAUSE DONE', time.time() - t0

		## pre-exposure
		pretime = presetdata['pre exposure']
		if pretime:
			self.exposeSpecimen(pretime)
		if channel is None:
			try:
				defaultchannel = int(presetdata['alt channel'])
			except:
				# back compatible since imported old presetdata would have value if
				# database column is not yet created by sinedon
				defaultchannel = None
		else:
			defaultchannel = channel

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		reduce_pause = self.onTarget
		status = self.moveAndPreset(presetdata, emtarget)
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this target')
			return status

		defaultchannel = self.preAcquire(presetdata, emtarget, channel, reduce_pause)
		args = (presetdata, emtarget, defaultchannel)
		try:
			if self.settings['background']:
				self.clearCameraEvents()
				t = threading.Thread(target=self.acquirePublishDisplayWait, args=args)
				t.start()
				self.waitExposureDone()
			else:
				self.acquirePublishDisplayWait(*args)
		except:
			self.resetComaCorrection()
			raise
		finally:
			is_failed = self.resetComaCorrection()
			if is_failed:
				self.player.pause()
		return status

	def acquirePublishDisplayWait(self, presetdata, emtarget, channel):
		if debug:
			try:
				tnum = emtarget['target']['number']
				tkey = emtarget.dbid
			except:
				tnum = None
				tkey = None
			print tnum, 'APDW START'
			t0 = time.time()

		self.retry_count = 0
		imagedata = self.acquireCCD(presetdata, emtarget, channel=channel)

		self.imagedata = imagedata
		targetdata = emtarget['target']
		if targetdata is not None:
			if 'grid' in targetdata and targetdata['grid'] is not None:
				imagedata['grid'] = targetdata['grid']
			if 'spotmap' in targetdata:
				# if in targetdata, get spotmap from it
				imagedata['spotmap'] = targetdata['spotmap']
			if not targetdata['spotmap']:
				if targetdata['image']:
					# get spotmap from parent image
					imagedata['spotmap'] = targetdata['image']['spotmap']
		else:
			if self.grid:
				imagedata['grid'] = self.grid
		self.publishDisplayWait(imagedata)

		if debug:
			print tnum, 'APDW DONE', time.time() - t0
			ttt = time.time() - self.timedebug[tkey]
			del self.timedebug[tkey]
			print tnum, '************* TOTAL ***', ttt

	def resetComaCorrection(self):
		'''
		Reset aberration correction values if possible.  This does not
		raise error when failed but return is_failed boolean because it
		is typically used as escape route for other failure during target
		processing.
		'''
		# projection submode and probe mode must be the same as beamtilt0
		# and stig0 when calling thisi.
		# Only need this if it is image shift.
		# TODO: check projection submode and probe mode.
		#Navigator move or target adjustment may make the these incorrect.
		if 'shift' in self.settings['move type'] and self.settings['correct image shift coma']:
			if self.beamtilt0 is None:
				# Exception during pre-acquire target processing may call this function.
				# before the real reset values are set
				self.logger.warning("Calling resetComaCorrection before it is known is not possible. No reset is done")
				return False
			if self.probe0 != self.instrument.tem.getProbeMode():
				mag = self.instrument.tem.getMagnification()
				self.logger.error("Attempting to resetComaCorrection at %dx on a different probe mode is not doable." % mag)
				return False
			try:
				self.instrument.tem.BeamTilt = self.beamtilt0
				self.instrument.tem.Stigmator = {'objective':self.stig0}
				self.instrument.tem.Defocus = self.defoc0
				self.logger.info("reset beam tilt to (%.4f,%.4f)" % (self.instrument.tem.BeamTilt['x'],self.instrument.tem.BeamTilt['y']))
				stig1 = self.instrument.tem.getStigmator()['objective']
				self.logger.info("reset object stig to (%.4f,%.4f)" % (stig1['x'],stig1['y']))
				defoc1 = self.instrument.tem.getDefocus()
				self.logger.info("reset defocus to (%.4f) um" % (defoc1*1e6))
			except Exception as e:
				# Don't raise, just report because this function is the escape route
				# for other failures.
				self.logger.exception('Reset coma correction failed. Beam tilt and objective stig may be wrong')
				self.logger.error(e)
				# Fail to reset
				return True

	def parkAtHighMag(self):
		# wait for at least for 30 seconds
		self.logger.info('wait 30 seconds before parking')
		time.sleep(max(self.settings['pause time'],30))
		# send a preset at the highest magnification to keep the lens warm
		park_presetname = self.presetsclient.getHighestMagPresetName()
		self.logger.info('parking the scope to preset %s' % (park_presetname,))
		self.presetsclient.toScope(park_presetname, None, False)
		self.logger.info('scope parked at preset %s' % (park_presetname,))

	def park(self):
		# also go to highest mag.
		self.parkAtHighMag()
		super(Acquisition,self).park()
		
	def notifyNodeBusy(self):
			'''
			Notify Manager that the node is doing something so it does not timeout.
			'''
			self.outputEvent(event.NodeBusyNotificationEvent())

	def notifyManagerPauseAvailable(self):
		'''
		Notify Manager that the node is doing something so it does not timeout.
		'''
		self.outputEvent(event.ManagerPauseAvailableEvent())

	def notifyManagerPauseNotAvailable(self):
		'''
		Notify Manager that the node is doing something so it does not timeout.
		'''
		self.outputEvent(event.ManagerPauseNotAvailableEvent())

	def notifyManagerContinueAvailable(self):
		'''
		Notify Manager that the node is doing something so it does not timeout.
		'''
		self.outputEvent(event.ManagerContinueAvailableEvent())

	def handlePause(self, evt):
		'''
		Manager doing the pause
		'''
		#self.panel.playerEvent('pause')
		self.player.pause()
		self.setStatus('user input')

	def handleContinue(self, evt):
		'''
		Manager continues the paused status
		'''
		if self.paused_by_gui:
			self.logger.info('Paused through local gui, skip workflow continuing')
			return
		# Only continue that was paused by Manager. This way, local expert user can still
		# pause intentionally at a place.
		#self.panel.playerEvent('play')
		self.player.play()
		self.setStatus(self.before_pause_node_status)

	def publishDisplayWait(self, imagedata):
		'''
		publish image data, display it, then wait for something to 
		process it
		'''
		## set the 'filename' value
		self.setImageFilename(imagedata)

		## set pixel size so mrc file will have it in header
		if imagedata.__class__ is leginondata.AcquisitionImageData:
			imagedata.attachPixelSize()

		if self.settings['park after target']:
			self.parkAtHighMag()

		self.reportStatus('output', 'Publishing image...')
		self.startTimer('publish image')
		if self.settings['save image']:
			if not imagedata['mover']:
				moverq = leginondata.MoverParamsData(mover=self.settings['mover'])
				moverq['move precision'] = self.settings['move precision']
				moverq['accept precision'] = self.settings['accept precision']
				imagedata['mover'] = moverq
			imagedata.insert(force=True)
		self.publish(imagedata, pubevent=True)
		self.notifyNodeBusy()

		## set up to handle done events
		dataid = imagedata.dbid
		doneevent = {}
		doneevent['received'] = threading.Event()
		doneevent['status'] = 'waiting'
		self.doneevents[dataid] = doneevent

		self.stopTimer('publish image')
		self.reportStatus('output', 'Image published')
		self.reportStatus('output', 'Publishing stats...')
		self.startTimer('publish stats')
		self.publishStats(imagedata)
		self.stopTimer('publish stats')
		self.reportStatus('output', 'Stats published...')
		if self.retry_count >= 1:
			self.logger.error('image %s was acquired %d times.' % (imagedata['filename'], self.retry_count+1))

		image_array = imagedata['image']
		if isinstance(image_array, numpy.ndarray):
			if self.settings['display image']:
				self.reportStatus('output', 'Displaying image...')
				self.startTimer('display')
				self.setImage(numpy.asarray(image_array, numpy.float32), 'Image')
				self.stopTimer('display')
				self.reportStatus('output', 'Image displayed')
			self.finalizeImageProcess()
		return 'ok'

	def finalizeImageProcess(self):
		if self.settings['wait for process']:
			self.setStatus('waiting')
			self.startTimer('waitForImageProcess')
			self.waitForImageProcessDone()
			self.stopTimer('waitForImageProcess')
			if not self.settings['background']:
				self.setStatus('processing')
			else:
				self.setStatus('idle')

	def publishStats(self, imagedata):
		im = imagedata['image']
		if im is None:
			return
		allstats = arraystats.all(im)
		statsdata = leginondata.AcquisitionImageStatsData()
		statsdata['session'] = self.session
		statsdata['min'] = allstats['min']
		statsdata['max'] = allstats['max']
		statsdata['mean'] = allstats['mean']
		statsdata['stdev'] = allstats['std']
		statsdata['image'] = imagedata
		self.publish(statsdata, database=True)

	def setEmailPassword(self, password):
		self.emailpassword = password

	def emailBadImageStats(self, stats):
		s = smtplib.SMTP()
		s.connect(leginonconfig.emailhost)
		s.login(leginonconfig.emailuser, self.emailpassword)

		subject = 'LEGINON: bad image stats'
		responsetext = self.settings['bad stats response'].replace('Abort','aborted')
		responsetext = responsetext.replace('Pause','paused at current')
		text = 'Your Leginon session has '+ responsetext + ' target list(s) at \n\n'+time.ctime() + '\n\n due to bad image mean value of %.2f' %stats
		mes = emailnotification.makeMessage(leginonconfig.emailfrom, leginonconfig.emailto, subject, text)
		s.sendmail(leginonconfig.emailfrom, leginonconfig.emailto, mes.as_string())

	def pauseAndRecheck(self,pausetime):
		recheck_count = self.recheck_counter.next()
		self.logger.info('Pausing for %d s before checking again at %d' % (pausetime,recheck_count))
		time.sleep(pausetime)
		## acquire image
		self.reportStatus('acquisition', 'acquiring image...')
		self.startTimer('acquire getData')
		correctimage = self.settings['correct image']
		# Switch frame saving if available
		try:
			isSaveRawFrames = self.instrument.ccdcamera.SaveRawFrames
			self.instrument.ccdcamera.SaveRawFrames = False
		except:
			isSaveRawFrames = False
		imagedata = self._acquireCameraImage(correctimage, 0)
		# Restore frame saving
		try:
			self.instrument.ccdcamera.SaveRawFrames = isSaveRawFrames
		except:
			pass
		self.reportStatus('acquisition', 'image acquired')
		self.stopTimer('acquire getData')
		# failed acquireCCD returns None
		if imagedata is None:
			raise BadImageAcquirePause('failed acquire')
		imagearray = imagedata['image']
		if imagearray is None:
			raise BadImageAcquirePause('image array is None. Possible camera problem')
		if recheck_count == 0:
			# Restrict recover mean value with this too if slope is used
			self.recover_mean = imagearray.mean() * 0.8
		'''
		Simulator testing ring collapse	
		if recheck_count > 5:
			imagearray = numpy.ones(imagearray.shape)*2800
		else:
			imagearray += 20 * recheck_count
		'''
		self.recheckEvaluateStats(imagearray)
		return

	def respondBadImageStats(self, badstate=''):
			if self.settings['bad stats response'] == 'Abort all':
				self.player.stopqueue()
				self.logger.info('Stopping all targets in queue')
				raise BadImageStatsAbort('image mean too '+badstate)
			elif self.settings['bad stats response'] == 'Abort one':
				self.player.stop()
				self.logger.info('Skiping targets in this target list')
				raise BadImageStatsAbort('image mean too '+badstate)
			elif self.settings['bad stats response'] == 'Recheck':
				self.pauseAndRecheck(self.settings['recheck pause time'])
			elif self.settings['bad stats response'] == 'Pause':
				raise BadImageStatsPause('image mean too '+badstate)

	def evaluateStats(self, imagearray):
		mean = arraystats.mean(imagearray)
		if self.settings['bad stats type'] == 'Slope':
			mean = self.runningSlope(time.time() - self.time0,mean)
			self.logger.info('current slope %s' % (mean,))
			if mean is None:
				return
		if mean > self.settings['high mean']:
			try:
				self.emailBadImageStats(mean)
			except:
				self.logger.info('could not email')
			self.respondBadImageStats('high')
		if mean < self.settings['low mean']:
			try:
				self.emailBadImageStats(mean)
			except:
				self.logger.info('could not email')
			if mean is not None:
				self.logger.info('mean lower than settings %6.0f' % (mean))
			self.respondBadImageStats('low')

	def recheckEvaluateStats(self,imagearray):
		'''
		Stats evaluation in recheck.
		This is mainly based on the slope.
		'''
		mean = arraystats.mean(imagearray)
		if self.settings['bad stats type'] is None or self.settings['bad stats type'] == 'Mean':
			return self.evaluateStats(imagearray)
		# Evaluate with slope.  Always rejects None (no slope calculated)
		slope = self.runningSlope(time.time() - self.time0,mean)
		self.logger.info('current slope %s' % (slope,))
		if slope is not None and mean > self.recover_mean and slope <= self.settings['high mean'] and slope >=self.settings['low mean']:
			return
		else:
			self.respondBadImageStats('low')

	def runningSlope(self,time,intensity):
		if len(self.times) == 5:
			self.times = self.times[1:]
			self.intensities = self.intensities[1:]
		self.times.append(time)
		self.intensities.append(intensity)
		if len(self.times) < 3:
			return None
		slope, intercept = self.linearFitData(self.times,self.intensities)
		return slope

	def linearFitData(self,xlist,ylist):
		'''
		Fit data with a line.
		dataxy is a dictionary of x values in a list and y values in a list.
		returned result is a tuple of (slope, intercept).
		'''
		x = numpy.array(xlist)
		y = numpy.array(ylist)
		A = numpy.vstack([x,numpy.ones(len(x))]).T
		return numpy.linalg.lstsq(A,y, rcond=-1)[0]

	def publishImage(self, imdata):
		self.publish(imdata, pubevent=True)

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

	def checkDrift(self, presetname, emtarget, threshold, apply_beamtilt = {'x':0.0,'y':0.0}):
		'''
		request DriftManager to monitor drift
		'''
		driftdata = leginondata.DriftMonitorRequestData(session=self.session, presetname=presetname, emtarget=emtarget, threshold=threshold, beamtilt=apply_beamtilt)
		self.driftdone.clear()
		self.driftimagedone.clear()
		self.publish(driftdata, pubevent=True, database=True, dbforce=True)
		self.reportStatus('acquisition', 'Waiting for DriftManager to check drift...')
		self.driftimagedone.wait()
		self.driftdone.wait()
		return self.driftresult

	def reportStatus(self, type, message):
		self.logger.info('%s: %s' % (type, message))

	def useFirstPresetOrderPreset(self):
			presetnames = self.settings['preset order']
			currentpreset = self.presetsclient.getPresetByName(presetnames[0])
			if not currentpreset:
				raise InvalidPresetsSequence('selected preset name %s not found in presets manager')
			return currentpreset

	def simulateTarget(self):
		self.setStatus('processing')
		# no need to pause longer for simulateTarget
		self.is_firstimage = False
		# current preset is used to create a target for this node.
		currentpreset = self.presetsclient.getCurrentPreset()
		if currentpreset is None:
			try:
				self.validatePresets()
			except InvalidPresetsSequence as e:
				self.logger.error(e)
				self.setStatus('idle')
				return
			# use first preset in preset order to initialize
			try:
				currentpreset = self.useFirstPresetOrderPreset()
			except InvalidPresetsSequence as e:
				self.logger.error(e)
				self.logger.error('Configure a valid preset to allow initialization')
				self.setStatus('idle')
				return
		targetdata = self.newSimulatedTarget(preset=currentpreset,grid=self.grid)
		self.publish(targetdata, database=True)
		## change to 'processing' just like targetwatcher does
		proctargetdata = self.reportTargetStatus(targetdata, 'processing')
		try:
			ret = self.processTargetData(targetdata=proctargetdata, attempt=1)
		except BadImageStatsPause as e:
			self.logger.error('processing target failed: %s' %e)
			ret = 'aborted'
		except BadImageAcquirePause as e:
			self.logger.error('processing target failed: %s' %e)
			ret = 'aborted'
		except BadImageAcquireBypass as e:
			self.logger.error('processing target failed: %s' %e)
			ret = 'aborted'
		except BadImageStatsAbort as e:
			self.logger.error('processing target failed: %s' %e)
			ret = 'aborted'
		except Exception as e:
			self.logger.error('processing target failed: %s' %e)
			ret = 'aborted'
		self.reportTargetStatus(proctargetdata, 'done')
		self.logger.info('Done with simulated target, status: %s (repeat will not be honored)' % (ret,))
		self.setStatus('idle')

	def simulateTargetLoop(self):
		self.setStatus('processing')
		self.simloopstop.clear()
		if self.settings['loop delay time'] > 0:
			self.logger.info('delay the loop by %.1f mins' % (self.settings['loop delay time']/60.0))
			self.setStatus('processing')
			time0 = time.time()
			blocktime = 20.0
			num_block = int(self.settings['loop delay time']/blocktime)
			while num_block > 0:
				if self.simloopstop.isSet():
					self.logger.info('User stopped loop')
					self.setStatus('idle')
					return
				time.sleep(blocktime)
				time1 = time.time() - time0
				num_block = int(time1/blocktime)
			# remaining time
			if self.simloopstop.isSet():
				self.logger.info('User stopped loop')
				self.setStatus('idle')
				return
			time1 = time.time() - time0
			if time1 > 1.0:
				time.sleep(time1)
		iterations = self.settings['iterations']
		self.logger.info('begin simulated target loop of %s iterations' % (iterations,))
		for i in range(iterations):
			self.logger.info('iteration %s of %s' % (i+1, iterations,))
			self.simulateTarget()
			self.setStatus('processing')
			if self.simloopstop.isSet():
				self.logger.info('User stopped loop')
				break
			waittime = self.settings['wait time']
			self.setStatus('waiting')
			time.sleep(waittime)
			self.setStatus('processing')
		self.logger.info('Simulated Target Loop Done')
		self.setStatus('idle')

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
			self.setImage(numpy.asarray(imagedata['image'], numpy.float32), 'Image')

	def processReferenceTarget(self):
		# This happens after fixCondition
		refq = leginondata.ReferenceTargetData(session=self.session)
		results = refq.query(results=1, readimages=False)
		if not results:
			return
		# This really does not need data but beamfixer and other presetadjusters
		# currently are subclass of targetwatcher and only watch for PublishEvent
		# This can all be changed once alignment manager can handle different
		# target types differently.
		request_data = leginondata.FixBeamData()
		request_data['session'] = self.session
		try:
			original_position = self.instrument.tem.getStagePosition()
			self.publish(request_data, database=True, pubevent=True, wait=True)
			self.instrument.tem.setStagePosition({'z':original_position['z']})
		except node.ConfirmationNoBinding as e:
			self.logger.debug(e)
		except Exception as e:
			self.logger.error(e)

	def fixAlignment(self):
		# This happens after processReferenceTarget
		# start alignment manager.  May replace reference in the future
		evt = event.FixAlignmentEvent()
		try:
			original_position = self.instrument.tem.getStagePosition()
			status = self.outputEvent(evt, wait=True)
			self.instrument.tem.setStagePosition({'z':original_position['z']})
		except node.ConfirmationNoBinding as e:
			self.logger.debug(e)
		except Exception as e:
			self.logger.error(e)

	def fixCondition(self):
		# This is done before any targets are rejected and processed in the targetlist.
		# First part is for conditions to be fixed don't involve presets,
		# such as buffer cycling or nitrogen filler
		evt = event.FixConditionEvent()
		try:
			self.logger.info('Condition fixing before processing a target')
			status = self.outputEvent(evt, wait=True)
		except node.ConfirmationNoBinding as e:
			self.logger.debug(e)
		except Exception as e:
			self.logger.error(e)

		# Second part: Preset-required tuning before rejected targets.
		try:
			self.validatePresets()
		except InvalidPresetsSequence:
			self.logger.error('Configure at least one preset in the settings for this node.')
			self.player.pause()
			self.setStatus('user input')
		preset_name = self.settings['preset order'][-1]
		# Phase Plate stuff
		self.tunePhasePlate(preset_name)

	def getMoveTypes(self):
		movetypes = []
		for key, value in self.calclients.items():
			if value.mover:
				movetypes.append(key)
		return movetypes
	def setGrid(self,evt):
		if evt['grid'] is None:
			self.grid = None
			self.logger.info('Remove filename grid prefix')
			return
		grid = evt['grid']
		self.grid = grid
		label = gridlabeler.getGridLabel(grid)
		self.logger.info('Add grid prefix as '+label)
