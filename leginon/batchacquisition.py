#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#
'''
BatchAcquire node is a TargetWatcher, so it receives either an ImageTargetData
or an ImageTargetListData.  The method processTargetData is called on each
ImageTargetData.
'''
import targetwatcher
import acquisition
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


class BatchAcquisition(acquisition.Acquisition):
	'''
	Fast beam-image shift only acquistion that sets beam-imageshift
	abberation without reset in between targets.  Pause/abort within
	the targetlist is not allowed. Only one preset can be in preset order.
	'''
	def batchMoveAndPreset0(self):
		# send preset to get 0 state
		# batchacquire only allow to have 1 preset
		presetname = self.settings['preset order'][0]
		presetdata = self.presetsclient.getPresetByName(presetname)
		self.setPresetMagProbeMode(presetdata,None)
		self.setComaStig0()
		self.defoc0 = presetdata['defocus']
	
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
		self.startTimer('position camera')
		t = threading.Thread(target=self.positionCamera)
		t.start()
		self.waitPositionCameraDone()
		self.stopTimer('position camera')

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
			except Exception, e:
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
				except PauseRepeatException, e:
					self.player.pause()
					self.logger.error(str(e) + '... Fix it, then press play to repeat target')
					condition_status = 'repeat'
				except Exception, e:
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
			# This will bright z to the value before reference targets and alignment
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
				except Exception, e:
					self.logger.exception('Process target failed: %s' % e)
					process_status = 'exception'
				self.stopTimer('processTargetData')

				if process_status == 'repeat':
					# Do not report targetstatus so that it can repeat even if
					# restart Leginon
					pass
				# end of target repeat loop
		# TODO reset coma correction at the end of good targets
		is_failed = self.resetComaCorrection()
		return targetliststatus

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
		### acquire CCD
		self.startTimer('acquire')
		ret = self.acquire(presetdata, emtarget, attempt=attempt, target=targetdata)
		self.stopTimer('acquire')
		self.reportStatus('processing', 'Processing complete')
		return ret

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
			self.correctImageShiftAbberations()
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

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		reduce_pause = self.onTarget
		status = self.moveAndPreset(presetdata, emtarget)
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this target')
			return status

		defaultchannel = self.preAcquire(presetdata, emtarget, channel, reduce_pause)
		args = (presetdata, emtarget, defaultchannel)
		try:
			self.acquirePublishDisplayWait(*args)
		except:
			raise
		return status
