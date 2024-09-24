#!/usr/bin/env python
from leginon import acq as acquisition, singlefocuser, manualfocuschecker
import leginon.gui.wx.Focuser
from leginon import leginondata
from leginon import node, targetwatcher
import math

class Focuser(singlefocuser.SingleFocuser):
	panelclass = leginon.gui.wx.Focuser.Panel
	settingsclass = leginondata.FocuserSettingsData
	defaultsettings = dict(singlefocuser.SingleFocuser.defaultsettings)

	eventinputs = singlefocuser.SingleFocuser.eventinputs
	eventoutputs = singlefocuser.SingleFocuser.eventoutputs

	current_target = None
	current_focus_sequence_step = 0
	corrected_focus = []
	corrected_stagez = []
	delayed_targets = []

	def newSimulatedTarget(self, preset=None,grid=None):
		target = super(Focuser,self).newSimulatedTarget(preset,grid)
		self.current_target = target
		return target


	def simulateTarget(self):
		self.good_enough = False
		self.setStatus('processing')
		# no need to pause longer for simulateTarget
		self.is_firstimage = False
		# current preset is used to create a target for this node.
		currentpreset = self.presetsclient.getCurrentPreset()
		if currentpreset is None:
			# self.validatePresets() exception is caught by parent class of this.
			# it is not useful in this case.
			try:
				currentpreset = self.useFirstPresetOrderPreset()
			except acquisition.InvalidPresetsSequence:
				self.logger.error('Configure a valid preset in the settings to allow initialization')
				self.setStatus('idle')
				return
		targetdata = self.newSimulatedTarget(preset=currentpreset,grid=self.grid)
		self.publish(targetdata, database=True)
		## change to 'processing' just like targetwatcher does
		proctargetdata = self.reportTargetStatus(targetdata, 'processing')
		try:
			ret = self.processGoodTargets([proctargetdata,])
		except Exception as e:
			self.logger.error('processing simulated target failed: %s' %e)
			ret = 'aborted'
		self.reportTargetStatus(proctargetdata, 'done')
		self.logger.info('Done with simulated target, status: %s (repeat will not be honored)' % (ret,))
		self.setStatus('idle')

	def processGoodTargets(self, goodtargets):
		"""
		This overwrites TargetWatcher.processGoodTargets.
		It loops through goodtargets before looping focus sequence.
		The correction result are kept and at the end of target loop
		an average of the correction is applied.
		"""
		if self.getIsResetTiltInList() and goodtargets:
			# ? Do we need to reset on every target ?
			self.logger.info('Tilting to %.2f degrees on first good target.' % (self.targetlist_reset_tilt*180.0/math.pi))
			self.instrument.tem.setDirectStagePosition({'a':self.targetlist_reset_tilt})
		# initialize
		self.current_target = None
		self.current_focus_sequence_step = 0
		self.delayed_targets = []
		self.is_last_target_and_focus_step = False
		self.good_enough = False

		for j, setting in enumerate(self.focus_sequence):
			self.corrected_focus = []
			self.corrected_stagez = []
			self.current_focus_sequence_step = j
			if self.good_enough == True:
				break
			for i, target in enumerate(goodtargets):
				self.logger.debug('Step %d of target %d' % (j,i))
				if j == len(self.focus_sequence)-1 and i == len(goodtargets)-1:
					self.is_last_target_and_focus_step = True
				self.goodnumber = i
				self.logger.debug('target %s status %s' % (i, target['status'],))
				# ...
				if self.player.state() == 'pause':
					self.setStatus('user input')
				state = self.clearBeamPath()
				self.setStatus('processing')
				# abort
				if state in ('stop', 'stopqueue'):
					self.logger.info('Aborting current target list')
					targetliststatus = 'aborted'
					self.reportTargetStatus(target, 'aborted')
					## continue so that remaining targets are marked as done also
					continue

				# if this target is done, skip it
				if target['status'] in ('done', 'aborted'):
					self.logger.info('Target has been done, processing next target')
					continue

				adjustedtarget = self.reportTargetStatus(target, 'processing')

				# this while loop allows target to repeat
				process_status = 'repeat'
				attempt = 0
				while process_status == 'repeat':
					attempt += 1

					# now have processTargetData work on it
					self.startTimer('processTargetData')
					try:
						process_status = self.processTargetData(adjustedtarget, attempt=attempt)
					except targetwatcher.PauseRepeatException as e:
						self.player.pause()
						self.logger.error(str(e) + '... Fix it, then press play to repeat target')
						self.beep()
						process_status = 'repeat'
					except node.PublishError as e:
						self.player.pause()
						self.logger.exception('Saving image failed: %s' % e)
						process_status = 'repeat'
					except Exception as e:
						self.logger.exception('Process target failed: %s' % e)
						process_status = 'exception'
						
					self.stopTimer('processTargetData')

					if process_status != 'exception':
						self.delayReportTargetStatusDone(adjustedtarget)
					else:
						# set targetlist status to abort if exception not user fixable
						targetliststatus = 'aborted'
						self.reportTargetStatus(adjustedtarget, 'aborted')

					# pause check after a good target processing
					state =  self.pauseCheck('paused after processTargetData')
					self.setStatus('processing')
					if state in ('stop', 'stopqueue'):
						self.logger.info('Aborted')
						break
					# end of target repeat loop
				# next target is not a first-image
				self.is_firstimage = False
				# end of target loop
	
			self.applyAverageCorrection(setting)
			if self.good_enough and not self.is_last_target_and_focus_step:
				self.logger.info('Skipping the rest of focus sequence. Defocus accuracy better than %.2f um.' % (self.settings['accuracy limit']*1e6,))
				if self.settings['acquire final']:
					presetdata = self.useFirstPresetOrderPreset()
					self.acquireFinal(presetdata, self.last_emtarget)
			# end of focus sequence loop

	def applyAverageCorrection(self, setting):
		if not setting['switch']:
			return
		# average the results for current
		#print(self.corrected_focus)
		if setting['correction type'] == 'Defocus' and len(self.corrected_focus) > 0:
			defocus0 = self.instrument.tem.Defocus
			avg_focus = sum(self.corrected_focus) / len(self.corrected_focus)
			self.instrument.tem.Focus = avg_focus
			defocus1 = self.instrument.tem.Defocus
			delta = defocus1 - defocus0
			# individual may be good enough but not collectively.
			if delta > abs(self.settings['accuracy limit']):
				self.good_enough = False
			self.logger.info('Corrected defocus to target average by %.3e' % (delta,))
			self.resetDefocus()
		elif setting['correction type'] == 'Stage Z' and len(self.corrected_stagez) > 0:
			stage0 = self.instrument.tem.StagePosition
			avg_stagez = sum(self.corrected_stagez) / len(self.corrected_stagez)
			self.instrument.tem.StagePosition = {'z':avg_stagez}
			delta = avg_stagez - stage0['z']
			# individual may be good enough but not collectively.
			if abs(delta) > abs(self.settings['accuracy limit']):
				self.good_enough = False
			self.logger.info('Corrected stage z to target average by %.3e' % (delta,))
		self.reportDelayedTargetStatusToDone()

	def avoidTargetAdjustment(self,target_to_adjust,recent_target):
		if self.current_focus_sequence_step > 0 or not self.is_firstimage:
			return True
		else:
			return super(Focuser,self).avoidTargetAdjustment(target_to_adjust,recent_target)

	def delayReportTargetStatusDone(self, target):
		self.delayed_targets.append(target)

	def reportDelayedTargetStatusToDone(self):
		for target in self.delayed_targets:
			self.reportTargetStatus(target, 'done')
		self.delayed_targets = []

	def getFocusBeamTilt(self):
		for setting in self.focus_sequence:
			if setting['switch'] and setting['focus method']=='Beam Tilt':
				return setting['tilt']
		return 0.0

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None):
		'''
		this replaces singlefocuser.Focuser.acquire()
		Instead of doing all sequence of autofocus, we do the one set by
		self.current_focus_sequence_step each time this is called.
		'''
		self.new_acquire = True

		## sometimes have to apply or un-apply deltaz if image shifted on
		## tilted specimen
		if emtarget is None:
			self.deltaz = 0
		else:
			self.deltaz = emtarget['delta z']

		# melt only on the first focus sequence
		if self.current_focus_sequence_step == 0:
			self.setEMtargetAndMeltIce(emtarget, attempt)

		status = 'unknown'

		self.last_emtarget = emtarget
		if self.good_enough:
			message = 'Skipping the rest because it is good enough in focuser.acquire'
			self.logger.info(message)
			self.current_focus_sequence_step = len(self.focus_sequence)
			status = 'ok'
		if self.current_focus_sequence_step in range(len(self.focus_sequence)):
			setting = self.focus_sequence[self.current_focus_sequence_step]
			if not setting['switch']:
				message = 'Skipping focus setting \'%s\'...' % setting['name']
				self.logger.info(message)
				status = 'ok'
			else:
				message = 'Processing focus setting \'%s\'...' % setting['name']
				self.logger.info(message)
				self.startTimer('processFocusSetting')
				self.clearBeamPath()
				status = self.processFocusSetting(setting, emtarget=emtarget)
				self.stopTimer('processFocusSetting')
				#Focuser loops every targets for each focus_step
				# Therefore, needs reset after each time processFocusSetting is done.
				is_failed = self.resetComaCorrection()
				## TEST ME
				## repeat status means give up and do the what over ???


		# aquire and save the focus image
		# only done at the last target
		if status != 'repeat' and self.settings['acquire final'] and self.is_last_target_and_focus_step:
			# if autofocus is good enough before reaching last focus_step,
			# this part is not reached.
			self.acquireFinal(presetdata, emtarget)
		return status

	def acquireFinal(self, presetdata, emtarget):
		self.clearBeamPath()
		manualfocuschecker.ManualFocusChecker.acquire(self, presetdata, emtarget)

	def processFocusSetting(self, setting, emtarget=None):
		"""
		Go through one Focus Setting on one emtarget
		"""
		resultdata = leginondata.FocuserResultData(session=self.session)
		resultdata['target'] = emtarget['target']
		resultdata['preset'] = emtarget['preset']
		resultdata['method'] = setting['focus method']
		status = 'unknown'
		# measuremrnt
		try:
			measuretype = setting['focus method']
			meth = self.focus_methods[measuretype]
		except (IndexError, KeyError):
			self.logger.warning('No method selected for correcting defocus')
		else:
			self.startTimer(measuretype)
			status = meth(setting, emtarget, resultdata)
			self.stopTimer(measuretype)
		if status == 'ok' and measuretype != 'Manual':
			# validation
			status = self.validateMeasurementResult(setting, resultdata)
			if status == 'ok':
				# correction of the measure defocus
				self.defocusCorrection(setting, resultdata)
		resultdata['status'] = status
		scopedata = self.instrument.getData(leginondata.ScopeEMData)
		scopedata.insert(force=True)
		resultdata['scope'] = scopedata
		self.publish(resultdata, database=True, dbforce=True)
		stagenow = self.instrument.tem.StagePosition
		self.logger.debug('z after step %s %.2f um' % (setting['name'], stagenow['z']*1e6))
		# record the result for averaging
		correcttype = setting['correction type']
		if correcttype == 'Defocus':
				self.corrected_focus.append(scopedata['focus'])
		if correcttype == 'Stage Z':
				self.corrected_stagez.append(scopedata['stage position']['z'])

		return status

	def defocusCorrection(self,setting, resultdata):
		""" 
		Correct measured defocus. Method of correction depends
		on the correction type.
		"""
		try:
			correcttype = setting['correction type']
			correctmethod = self.correction_types[correcttype]
		except (IndexError, KeyError):
			self.logger.warning('No method selected for correcting defocus')
		else:
			correctmethod(setting, resultdata)
