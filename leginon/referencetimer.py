
import threading
import time
from leginon import leginondata
import calibrationclient
import event
import instrument
import reference
import gui.wx.ReferenceTimer
import gui.wx.AlignZLP

class ReferenceTimer(reference.Reference):
	panelclass = gui.wx.ReferenceTimer.ReferenceTimerPanel
	settingsclass = leginondata.ReferenceTimerSettingsData
	eventinputs = reference.Reference.eventinputs
	eventoutputs = reference.Reference.eventoutputs

	defaultsettings = dict(reference.Reference.defaultsettings)
	defaultsettings.update (
		{'interval time': 0.0}
	)
	requestdata = None

	def __init__(self, *args, **kwargs):
		super(ReferenceTimer,self).__init__(*args, **kwargs)
		#self.last_processed = time.time()

		if self.__class__ == ReferenceTimer:
			self.start()

	def _processRequest(self, request_data):
		# This is the function that would be different between Timer and Counter
		interval_time = self.settings['interval time']
		if interval_time is not None and self.last_processed is not None:
			interval = time.time() - self.last_processed
			if interval < interval_time:
				message = '%d second(s) since last request, ignoring request'
				self.logger.info(message % interval)
				return
		self.moveAndExecute(request_data)

	def onTest(self):
		super(ReferenceTimer,self).onTest()

	def uiResetTimer(self):
		self.resetProcess()

	def resetProcess(self):
		# reset timer
		self.logger.info('Reset Request Process Timer')
		self.last_processed = time.time()


class AlignZeroLossPeak(ReferenceTimer):
	settingsclass = leginondata.AlignZLPSettingsData
	# defaultsettings are not the same as the parent class.  Therefore redefined.
	defaultsettings = dict(reference.Reference.defaultsettings)
	defaultsettings.update (
		{'interval time': 900.0,
		'check preset': '',
		'threshold': 0.0,
		}
	)
	eventinputs = ReferenceTimer.eventinputs + [event.AlignZeroLossPeakPublishEvent, event.FixAlignmentEvent]
	panelclass = gui.wx.AlignZLP.AlignZeroLossPeakPanel
	requestdata = leginondata.AlignZeroLossPeakData

	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.AlignZeroLossPeakPublishEvent]
		ReferenceTimer.__init__(self, *args, **kwargs)
		self.addEventInput(event.FixAlignmentEvent, self.handleFixAlignmentEvent)
		self.proceed_threshold = None
		self.ref_position = None
		self.start()

	def handleFixAlignmentEvent(self, evt):
		# called from another Reference Class to execute after target move
		# but before execution.
		self.logger.info('handling request to execute alignment in place')
		if self.settings['bypass']:
			self.logger.info('Bypass alignment fixing')
			status = 'bypass'
			self.confirmEvent(evt, status=status)
			return
		self.setStatus('processing')
		self.panel.playerEvent('play')
		status = self.alignZLP(None)
		self.confirmEvent(evt, status=status)
		self.setStatus('idle')
		self.panel.playerEvent('stop')

	def setCheckPreset(self):
		# set check preset and send to scope
		check_preset_name = self.settings['check preset']
		self.checkpreset = self.presets_client.getPresetFromDB(check_preset_name)
		self.logger.info('Check preset is %s' % self.checkpreset['name'])

	def needChecking(self):
		return self.settings['threshold'] >= 0.1

	def moveAndExecute(self, request_data):
		'''
		Overwrite base class moveAndExecute from AlignZeroLossPeak.
		It needs to check shift threshold, and take test image.
		'''
		request_preset_name = request_data['preset']
		self.logger.info('request preset: %s' % request_preset_name)
		pause_time = self.settings['pause time']
		position0 = self.instrument.tem.StagePosition
		goto_preset = request_preset_name
		if self.needChecking():
			if self.settings['check preset'] == request_preset_name:
				self.logger.warning('check preset %s is normally different from request preset %s' % (self.settings['check preset'], request_preset_name))
			goto_preset = self.settings['check preset']
		try:
			self.moveToTarget(goto_preset)
			self.declareDrift('stage')
		except Exception, e:
			self.logger.error('Error moving to target, %s' % e)
			self.moveBack(position0)
			return
		if pause_time is not None:
			self.logger.info('waiting for %.2f seconds' % (pause_time))
			time.sleep(pause_time)
		# threshold check and shift check only for AlignZLP
		if self.needChecking():
			self.logger.info('Checking energy shift....')
			need_align = self.checkShift()
		else:
			# if threshold is zero, always execute
			need_align = True
		# whether need_align or not always reset timer once the shift is checked.
		self.resetProcess()

		if need_align:
			# now ready to do it.
			try:
				self._setRequestPreset(request_preset_name)
			except:
				self.moveBack(position0)
				return
			try:
				self.at_reference_target = True
				self.execute(request_data)
			except Exception, e:
				self.logger.error('Error executing request, %s' % e)
				self._setRequestPreset(request_preset_name)
				self.moveBack(position0)
				return
			# got here if successful
			if self.needChecking():
				# need to record current zero loss intensity if checking shift, 
				self.resetZeroLossCheck()
		# set preset back to avoid confusion
		self._setRequestPreset(request_preset_name)
		self.moveBack(position0)

	def _setRequestPreset(self, request_preset_name):
		preset = self.presets_client.getCurrentPreset()
		if preset['name'] != request_preset_name:
			self.logger.info('Change preset to requested %s' % request_preset_name)
			self.presets_client.toScope(request_preset_name)

	def alignZLP(self, ccd_camera=None):
		if not ccd_camera:
			ccd_camera = self.instrument.ccdcamera
		ccd_name = ccd_camera._name
		if not ccd_camera.EnergyFiltered:
			self.logger.warning('No energy filter on this instrument.')
			return
		try:
			if not ccd_camera.EnergyFilter:
				self.logger.warning('Energy filtering is not enabled.')
				return 'bypass'
			self.positionCamera(camera_name=ccd_name)
			self.openColumnValveBeforeExposure()
			self.logger.info('Aligning ZLP with %s camera' % ccd_name)
			ccd_camera.alignEnergyFilterZeroLossPeak()
			m = 'Energy filter zero loss peak aligned.'
			self.logger.info(m)
		except AttributeError:
			m = 'Energy filter methods are not available on this instrument.'
			self.logger.warning(m)
		except Exception, e:
			raise
			s = 'Energy filter align zero loss peak failed: %s.'
			self.logger.error(s % e)

	def getShift(self,ccd_camera):
		shift = None
		# Can not find any reference to this function in recent code. Disabled.
		return shift
		try:
			shift = ccd_camera.getInternalEnergyShift()
			m = 'Energy filter internal shift: %g.' % shift
			self.logger.info(m)
		except AttributeError, e:
			m = 'Energy filter method not available %s' % e
			self.logger.warning(m)
		except Exception, e:
			s = 'Energy internal shift query failed: %s.'
			self.logger.error(s % e)
		return shift

	def execute(self, request_data=None):
		'''
		Execute without moving. Used in testing and handling the
		request after moving and set preset.
		'''
		ccd_camera = self.instrument.ccdcamera
		try:
			if not ccd_camera.EnergyFiltered:
				self.logger.warning('No energy filter on this instrument.')
				return
			if not ccd_camera.EnergyFilter:
				self.logger.warning('Energy filtering is not enabled.')
				return
		except AttributeError:
			m = 'Energy filter methods are not available on this instrument.'
			self.logger.warning(m)
		except Exception, e:
			s = 'EnergyFilter query failed: %s.'
			self.logger.error(s % e)

		try:
			if request_data:
				preset_name = request_data['preset']
				self.checkIntensityRange(preset_name)
		except Exception as e:
			self.logger.error('Failed intensity test: %s' % e)
			self.logger.error('Reference position is probably blocked.  Aborting.')
			return

		before_shift = self.getShift(ccd_camera)
		self.alignZLP(ccd_camera)
		after_shift = self.getShift(ccd_camera)

		shift_data = leginondata.InternalEnergyShiftData(session=self.session, before=before_shift, after=after_shift)
		self.publish(shift_data, database=True, dbforce=True)
		return 'ok'

	def checkIntensityRange(self, preset_name):
		'''
		check image mean value at the reference target. Failure of this
		function means the reference target is not suitable for ZLP
		alignment.  An error is thrown and process aborted.
		'''
		# corresponds to 0.5% of 1 electron count in counting camera.
		threshold_min = 0.05
		self.logger.info('Acquiring test image....')
		imagedata = self.acquireCorrectedCameraImageData(force_no_frames=True)
		this_mean = imagedata['image'].mean()
		ref_position = self.instrument.tem.StagePosition
		has_new_position = self.ref_position == None or abs(ref_position['x']-self.ref_position['x'])+abs(ref_position['y']-self.ref_position['y']) > 2e-6
		if has_new_position:
			self.logger.info('reference position has changed by at least 2 um')
		if not self.proceed_threshold or has_new_position:
			# use the first test image since start of the program as threshold.
			threshold = 0.05 * this_mean
			if threshold < threshold_min:
				raise ValueError('Mean %.2f is too low to set future threshold' % (this_mean,))
			self.ref_position = ref_position
			self.proceed_threshold = threshold
			self.logger.info('Set future threshold to %.2f' % self.proceed_threshold)
		else:
			threshold = self.proceed_threshold
		if threshold < threshold_min:
			self.logger.info('limit threshold to %.2f' % threshold_min)
			threshold = threshold_min
		if this_mean >= threshold:
			self.logger.info('Mean %.2f larger or equal to threshold %.2f. Proceed' % (this_mean, threshold))
			return		
		else:
			raise ValueError('Mean %.2f less than %.2f' % (this_mean, threshold))

	def checkShift(self):
		'''
		Check if alignment is needed.  This is typically done at a
		lower magnification where misaligned slit can be seen in the
		image as dark area when it is still minimally misaligned.
		'''
		self.setCheckPreset()
		ccd_camera = self.instrument.ccdcamera
		if not ccd_camera.EnergyFiltered:
			self.logger.warning('No energy filter on this instrument.')
			return False
		imagedata = self.acquireCorrectedCameraImageData(force_no_frames=True)
		if imagedata is None:
			return False
		image = imagedata['image']
		stageposition = imagedata['scope']['stage position']
		lastresetq = leginondata.ZeroLossCheckData(session=self.session, preset=self.checkpreset)
		result = lastresetq.query(readimages=False, results=1)

		if result is None:
			self.publishZeroLossCheck(image)
		else:
			if result:
				self.logger.info('Image standard deviation changed from %.2f to %.2f' % (result[0]['std'], image.std()))
				# compare the standard deviation with that from last alignment
				# standard deviation goes up when the slit is interfering it.
				if result[0]['std'] * self.settings['threshold'] > image.std():
					self.logger.info('Energy filter slit has not shifted significantly')
					return False
		self.logger.info('Need energy filter slit alignment')
		return True

	def publishZeroLossCheck(self,image):
		resetdata = leginondata.ZeroLossCheckData()
		resetdata['session'] = self.session
		resetdata['reference'] = self.reference_target
		resetdata['preset'] = self.checkpreset
		resetdata['mean'] = image.mean()
		self.logger.info('published zero-loss check data')
		resetdata['std'] = image.std()
		self.publish(resetdata, database=True, dbforce=True)

	def resetZeroLossCheck(self):
		try:
			self.at_reference_target = True
			self.moveToTarget(self.checkpreset['name'])
			self.declareDrift('stage')
		except Exception, e:
			self.logger.error('Error moving to target, %s' % e)
			return
		self.logger.info('reset zero-loss check data with a new image')
		imagedata = self.acquireCorrectedCameraImageData(force_no_frames=True)
		if imagedata is None:
			return
		stageposition = imagedata['scope']['stage position']
		image = imagedata['image']
		self.publishZeroLossCheck(image)

class MeasureDose(ReferenceTimer):
	defaultsettings = dict(reference.Reference.defaultsettings)
	defaultsettings.update (
		{'interval time': 900.0,
		}
	)
	# relay measure does events
	eventinputs = ReferenceTimer.eventinputs + [event.MeasureDosePublishEvent]
	eventoutputs = ReferenceTimer.eventoutputs
	panelclass = gui.wx.ReferenceTimer.MeasureDosePanel
	requestdata = leginondata.MeasureDoseData
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.MeasureDosePublishEvent]
		ReferenceTimer.__init__(self, *args, **kwargs)
		self.start()

	# override move to measure dose...
	def moveToTarget(self, preset_name):
		em_target_data = self.getEMTargetData(preset_name)

		self.publish(em_target_data, database=True)

		self.presets_client.measureDose(preset_name, em_target_data)

	def execute(self, request_data=None):
		if request_data:
			preset_name = request_data['preset']
			preset = self.presets_client.getPresetByName(preset_name)
		else:
			preset = self.presets_client.getCurrentPreset()
			if preset is None:
				return
			preset_name = preset['name']
		if preset['dose'] is None:
			self.logger.warning('Failed measuring dose for preset \'%s\'' % preset_name)
			return
		dose = preset['dose']/1e20
		exposure_time = preset['exposure time']/1000.0
		try:
			dose_rate = dose/exposure_time
		except ZeroDivisionError:
			dose_rate = 0
		self.logger.info('Measured dose for preset \'%s\'' % preset_name)
		self.logger.info('Dose: %g e-/A^2, rate: %g e-/A^2/s' % (dose, dose_rate))

