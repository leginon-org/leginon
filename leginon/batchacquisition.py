#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#
'''
BatchAcquisition node is a subclass of Acquisition.
The method processTargetData is called on each ImageTargetData.
'''
from leginon import targetwatcher
from leginon import acq as acquisition
import time
from leginon import leginondata
from leginon import event
from leginon import calibrationclient
from leginon import presets
import copy
import threading
from leginon import node
from leginon import instrument
import leginon.gui.wx.BatchAcquisition
import numpy
import math
from pyami import arraystats, imagefun

debug = False

class NoMoveCalibration(targetwatcher.PauseRepeatException):
	pass

class InvalidPresetsSequence(targetwatcher.PauseRepeatException):
	pass

class InvalidSettings(targetwatcher.PauseRepeatException):
	pass

class BadImageAcquirePause(targetwatcher.PauseRestartException):
	pass

class InvalidStagePosition(targetwatcher.BypassWarningException):
	pass


class BatchAcquisition(acquisition.Acquisition):
	'''
	Fast beam-image shift only acquistion that sets beam-imageshift
	abberation without reset in between targets.  Pause/abort within
	the targetlist is not allowed. Only one preset can be in preset order.
	'''
	panelclass = leginon.gui.wx.BatchAcquisition.Panel
	settingsclass = leginondata.BatchAcquisitionSettingsData
	# maybe not a class attribute
	defaultsettings = dict(acquisition.Acquisition.defaultsettings)
	defaultsettings['shutter delay'] = 0.0

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		# first fake array for publishThread
		self.image_array = numpy.ones((8,8),dtype=numpy.uint8)

	def batchMoveAndPreset0(self):
		# send preset to get 0 state
		# batchacquire only allow to have 1 preset
		presetname = self.settings['preset order'][0]
		presetdata = self.presetsclient.getPresetByName(presetname)
		self.batch_preset = presetdata
		self.setPresetMagProbeMode(presetdata,None)
		self.setComaStig0()
		self.defoc0 = presetdata['defocus']
	
	def validatePresets(self):
		super(BatchAcquisition, self).validatePresets()
		presetorder = self.settings['preset order']
		if len(presetorder) > 1:
			raise InvalidPresetsSequence('this node can only acquire with one preset')

	def validateTarget(self, targetdata):
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

	def setupFirstGoodTarget(self,targetdata):
		self.validateTarget(targetdata)
		self.batchMoveAndPreset0()
		# set stage z first before move
		z = self.moveToLastFocusedStageZ(targetdata)
		self.targetlist_z = z
		self.testprint('preset manager moved to LastFocusedStageZ %s' % (z,))
		self._setCameraAndCorrection()
		self.logger.info('setting first target camera state with preset %s:%d' % (self.batch_preset['name'],self.batch_preset.dbid))
		# wait for it ready before setting
		self.instrument.ccdcamera.waitForCameraReady()
		self.instrument.setData(self.batch_preset['ccdcamera'])
		self.logger.info('first good target mag and stage and camera set done')

	def _setCameraAndCorrection(self):
		self.startTimer('position camera')
		t = threading.Thread(target=self.positionCamera)
		t.start()
		self.waitPositionCameraDone()
		self.stopTimer('position camera')
		self.channel = 0
		scopedict = {'high tension': self.instrument.tem.HighTension,'tem':self.batch_preset['tem']}
		cameradict = dict(self.batch_preset)
		cameradict['ccdcamera'] = self.batch_preset['ccdcamera']
		cameradict['gain index'] = None
		self.norm = self.retrieveCorrectorImageData('norm', scopedict, cameradict, self.channel)
		if self.norm:
			self.bright = self.norm['bright']
			self.dark = self.norm['dark']
		else:
			self.bright = None
			self.dark = None
		plan, plandata = self.retrieveCorrectorPlan(cameradict)
		self.plan = plandata

	def processTargetList(self, newdata):
		if self.settings['limit image']:
			if self.isAboveImageNumberLimit():
				self.logger.info('Image number limit reached. Stop processing TargetList')
				self.setStatus('idle')
				return
		self.setStatus('processing')
		mytargettype = self.settings['process target type']
		### get targets that belong to this target list
		targetlist = self.researchTargets(list=newdata)
		listid = newdata.dbid
		self.logger.debug('TargetWatcher will process %s targets in list %s' % (len(targetlist), listid))
		completed_targets, good_targets, rejects = self.sortTargetsByType(targetlist, mytargettype)

		# There may not be good targets but only rejected
		# or reference targets causing self.targetlist_reset_tilt undefined.
		# define it now regardless.
		original_position = self.instrument.tem.getStagePosition()
		self.targetlist_z = original_position['z']
		self.targetlist_reset_tilt = original_position['a']
		if self.settings['set aperture']:
			# get aperture selection only if need to avoid error in accessing info.
			try:
				self.logger.info('Getting current aperture selection so we can restore....')
				self.obj_aperture_reset_value = self.instrument.tem.getApertureSelection('objective')
				self.c2_aperture_reset_value = self.instrument.tem.getApertureSelection('condenser')
			except Exception as e:
				self.logger.error(e)
				self.logger.error('Please set aperture manually and continue')
				self.player.pause()
				self.obj_aperture_reset_value = 'unknown'
				self.c2_aperture_reset_value = 'unknown'
			
		if good_targets:
			# Things to do before reject targets are published.
			# pause and abort check before reference and rejected targets are sent away
			state = self.pauseCheck('paused before reject targets are published')
			self.setStatus('processing')
			if state in ('stop', 'stopqueue'):			# When user stops at this node
				targetliststatus = 'aborted'
				# If I report targets done then rejected target are also done.  Which make
				# them unrestartable What to do???????
				self.reportTargetListDone(newdata, targetliststatus)
				self.setStatus('idle')
				return

			# initialize is_first-image
			self.is_firstimage = True
			self.targetlist_reset_tilt = self.getTiltForList(newdata)
			# There was a set self.targetlist_reset_tilt in the old code.
			# start conditioner
			condition_status = 'repeat'					# don't need a target
			while condition_status == 'repeat':
				if self.remote_pmlock:
					self.remote_pmlock.setLock()
				try:
					self.setStatus('waiting')
					self.fixCondition()
					self.setStatus('processing')
					condition_status = 'success'
				except targetwatcher.PauseRepeatException as e:
					self.player.pause()
					self.logger.error(str(e) + '... Fix it, then press play to repeat target')
					condition_status = 'repeat'
				except Exception as e:
					self.logger.error('Conditioning failed. Continue without it')
					condition_status = 'abort'
				self.beep()
				if self.remote_pmlock:
					self.remote_pmlock.setUnlock()
			# pause but not stop
			state = self.pauseCheck('paused after fix condition')

			# processReference.  FIX ME, when it comes back, need to move more
			# accurately than just send the position.
			if self.settings['wait for reference']:				#For example ZLP alignment
				self.setStatus('waiting')
				if self.remote_pmlock:
					self.remote_pmlock.setLock()
				self.processReferenceTarget()
				if self.remote_pmlock:
					self.remote_pmlock.setUnlock()
				self.setStatus('processing')
			# pause but not stop
			state = self.pauseCheck('paused after reference processing')
			# start alignment manager.  May replace reference in the future
			self.setStatus('waiting')
			if self.remote_pmlock:
				self.remote_pmlock.setLock()
			self.fixAlignment()
			if self.remote_pmlock:
				self.remote_pmlock.setUnlock()
			self.setStatus('processing')
			# pause but not stop
			state = self.pauseCheck('paused after fix alignment')
			# This will bring z to the value before reference targets and alignment
			# fixing.
			self.logger.info('Setting z to original z of %.2f um' % (original_position['z']*1e6))
			try:
				self.setStatus('processing')
				self.instrument.tem.setStagePosition({'z':original_position['z']})
			except Exception as e:
				self.logger.error('Failed to return z position %s' % str(e))
				self.logger.error('Please check tem')
			self.logger.info('Processing %d %s targets...' % (len(good_targets), mytargettype))
		# republish the rejects and wait for them to complete
		
		waitrejects = rejects and self.settings['wait for rejects']
		if waitrejects:

			# FIX ME: If autofocus involves stage tilt and self.targetlist_reset_tilt
			# is at high tilt, it is better not to tilt first but if autofocus does
			# not involve that, it needs to be tilted now.
			if self.remote_pmlock:
				self.remote_pmlock.setLock()
			rejectstatus = self.rejectTargets(newdata) # will stay until node gives back a done
			if self.remote_pmlock:
				self.remote_pmlock.setUnlock()
			if rejectstatus != 'success':
				## report my status as reject status may not be a good idea
				## all the time. This means if rejects were aborted
				## then this whole target list was aborted
				self.logger.debug('Passed targets not processed, aborting current target list')
				self.reportTargetListDone(newdata, rejectstatus)
				self.setStatus('idle')
				# Anchi, at focus node, if it fails, I think it still reports success since 
				# line ~ 324 is always true. This is a bit dangerous for tomo.
				# If focusing fails, there is not reason to move on, since tracking with likely
				# be very off. 
				if rejectstatus != 'aborted':	 
					return
			self.logger.info('Passed targets processed, processing current target list')
			# pause but not stop
			state = self.pauseCheck('paused after waiting for processing rejected targets')

		self.logger.info('Original tilt %.2f degrees.' % (original_position['a']*180.0/math.pi))
		self.logger.info('Parent tilt %.2f degrees.' % (self.targetlist_reset_tilt*180.0/math.pi))
		# process the good ones
		retract_successful = False
		if self.isNeedSetApertures(good_targets):
			retract_successful = self.setApertures()

		targetliststatus = 'success'
		if good_targets:
			targetdata0 = good_targets[0]
			if targetdata0 is not None and targetdata0['type'] != 'simulated' and self.settings['adjust for transform'] != 'no':
				# This gives back adjusted targets
				targetlist = self.researchTargets(list=newdata)
				listid = newdata.dbid
				self.logger.debug('Got %s adjusted targets in list %s' % (len(targetlist), listid))
				completed_targets, good_targets, rejects = self.sortTargetsByType(targetlist, mytargettype)

			# processing
			self.setupFirstGoodTarget(good_targets[0])
			targetliststatus = self.processGoodTargets(good_targets)
		# reset abberation correction
		if self.settings['correct image shift coma']:
			self.resetComaCorrection()
		self.reportTargetListDone(newdata, targetliststatus)
		if retract_successful:
			self.putBackApertures()

		if self.settings['park after list']:
			self.park()
		self.setStatus('idle')

	def makeTargetIndexOrder(self, good_targets):
		'''
		Return the order of the good_targets within a targetlist
		expressed in its target numbers. Use database values if present.
		'''
		if not good_targets:
			return [] # nothing to reorder
		index_order = list(range(len((remaining_targets))))

	def processGoodTargets(self, good_targets):
		# Approach 1: order targets 
		remaining_targets = list(good_targets)
		targetliststatus = 'success'
		# Things to do before start
		if remaining_targets and self.getIsResetTiltInList():
			self.logger.info('Tilting to %.2f degrees on first good target.' % (self.targetlist_reset_tilt*180.0/math.pi))
			self.instrument.tem.setDirectStagePosition({'a':self.targetlist_reset_tilt})
			state = self.clearBeamPath()
			self.setStatus('processing')
		for i,target in enumerate(remaining_targets):
			self.is_firstimage = i==0
			is_from_mosaic=False
			# abort if image number limit reached
			if self.settings['limit image']:
				if self.isAboveImageNumberLimit():
					self.logger.info('Image number limit reached. Stop processing good targets')
					break
			# get back new targetdata in processing status
			adjustedtarget = self.reportTargetStatus(target, 'processing')

			# this while loop allows target to repeat
			process_status = 'repeat'
			attempt = 0
			while process_status == 'repeat':
				attempt += 1

				# now have processTargetData work on it
				self.startTimer('processTargetData')
				try:
					self.logger.info('Processing target id %d' % adjustedtarget.dbid)
					process_status = self.processTargetData(adjustedtarget, attempt=attempt)
				except Exception as e:
					self.logger.exception('Process target failed: %s' % e)
					process_status = 'exception'
				self.stopTimer('processTargetData')

				if process_status == 'repeat':
					# Do not report targetstatus so that it can repeat even if
					# restart Leginon
					pass
				# end of target repeat loop
		if not self.is_firstimage:
			self.acquire_thread.join()
		self.instrument.ccdcamera.unsetNextRawFramesName()
		# TODO reset coma correction at the end of good targets
		is_failed = self.resetComaCorrection()
		return targetliststatus

	def simulateTarget(self):
		self.setStatus('processing')
		# need follow firstimage rule so it does not multi-thread.
		self.is_firstimage = True
		self.batchMoveAndPreset0()
		self._setCameraAndCorrection()
		return self._simulateTarget()

	def processTargetData(self, targetdata, attempt=None):
		'''
		This is called by TargetWatcher.processData when targets available
		If called with targetdata=None, this simulates what occurs at
		a target (going to presets, acquiring images, etc.)
		'''

		self.preTargetSetup()
		# process target begins
		newpresetname = self.settings['preset order'][0]
		ret = 'ok'
		self.onTarget = True
		### determine how to move to target
		try:
			emtarget = self.targetToEMTargetData(targetdata, self.targetlist_z)
		except InvalidStagePosition as e:
			raise
		presetdata = self.presetsclient.getPresetByName(newpresetname)
		if not self.is_firstimage:
			delta_time = time.time()-self.tp0
			pause_time = self.settings['pause time']
			min_acquire_time = presetdata['exposure time']/1000.0+pause_time+self.settings['shutter delay']
			if delta_time < min_acquire_time:
				extra_wait = min_acquire_time-delta_time
				self.logger.info('wait for %.2f seconds for camera shutter before new move' % extra_wait)
				time.sleep(extra_wait)
		status = self.moveAndPreset(presetdata, emtarget)
		if not self.is_firstimage:
			self.acquire_thread.join()
			self.logger.info('image acquired from last target')
		# make frames name to use during acquire
		if presetdata['save frames']:
			self.instrument.ccdcamera.makeNextRawFramesName()
		# get scope and camera state before acquiring because Falcon camera locks get properties
		# during acquiring
		scopeclass = leginondata.ScopeEMData
		cameraclass = leginondata.CameraEMData
		scopedata = self.instrument.getData(scopeclass)
		cameradata = self.instrument.getData(cameraclass)
		### make acquire CCD a thread and continue with publishThread
		self.clearCameraEvents()
		args = (presetdata, emtarget)
		self.acquire_thread = threading.Thread(target=self.acquireThread, args=args)
		self.acquire_thread.start()
		self.tp0 = time.time()
		if self.is_firstimage:
			# wait for thread to complete so it has self.image_array
			self.acquire_thread.join()
		ret = self.publishThread(presetdata, scopedata, cameradata, emtarget=emtarget, attempt=attempt, target=targetdata)
		self.reportStatus('processing', 'Processing complete')
		return ret

		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this target')
			return status

	def moveAndPreset(self, presetdata, emtarget):
			'''
			Move xy to emtarget position with its mover and set preset
			'''
			status = 'ok'
			presetname = presetdata['name']
			targetdata = emtarget['target']
			keep_shift = False
			#### move and change preset
			movetype = self.settings['move type']
			movefunction = self.settings['mover']
			if 'shift' not in movetype:
				raise ValueError('Bad settings: BatchAcquisition can not be used for moving %s' % movetype)
			if movefunction == 'navigator':
				self.logger.warning('Navigator cannot be used for %s, using Presets Manager instead' % movetype)
				movefunction = 'presets manager'
			self.setStatus('waiting')
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
			self.setDefocus0()
			self.correctImageShiftAbberations(presetdata['ccdcamera'])
			self.adjustTiltExposure(presetdata)
			self.setStatus('processing')
			return status

	def preAcquire(self, presetdata, emtarget=None, channel=None, reduce_pause=False):
		'''
		Things to do after moved to preset.
		'''
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
		time.sleep(pausetime)

		# the next image will not be first even if repeated
		self.is_firstimage = False
		## pre-exposure
		pretime = presetdata['pre exposure']
		if pretime:
			self.exposeSpecimen(pretime)
		defaultchannel = int(presetdata['alt channel'])
		return defaultchannel

	def publishThread(self, presetdata, scopedata, cameradata, emtarget=None, attempt=None, target=None, channel=None):
		'''
		Publish AcquisitionImageData while acquiring thread is running.  Use the previous image array
		as place holder.  Most of these are copied from acquisition.py
		'''
		targetdata = emtarget['target']
		imagedata = leginondata.AcquisitionImageData(
					session=self.session,
					scope=scopedata,
					camera=cameradata,
					bright=self.bright,
					norm=self.norm,
					dark=self.dark,
					#....
		)
		imagedata['corrector plan']=self.plan
		imagedata['correction channel']=self.channel
		dim = imagedata['camera']['dimension']
		pixels = dim['x'] * dim['y']
		# Use last image array to publish
		imagedata['image'] = self.image_array
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
		# grid info
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

	def acquireThread(self, presetdata, emtarget=None):
		'''
		Do image acquire without publishing.
		'''
		channel = 0
		reduce_pause = self.onTarget
		defaultchannel = self.preAcquire(presetdata, emtarget, channel, reduce_pause)
		imagedata = self.acquireCameraImageData()
		## convert float to uint16
		if self.settings['save integer']:
			imagedata['image'] = numpy.clip(imagedata['image'], 0, 2**16-1)
			imagedata['image'] = numpy.asarray(imagedata['image'], numpy.uint16)
		# self.image_array can be used for display and for next image saving.
		self.image_array=imagedata['image']
		return

	def getMoveTypes(self):
		return ['image shift', 'image-beam shift']
