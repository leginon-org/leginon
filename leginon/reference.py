# $Source: /ami/sw/cvsroot/pyleginon/reference.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2006-10-13 04:13:07 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import threading
import time
import data
import calibrationclient
import event
import instrument
import presets
import targethandler
import watcher
import gui.wx.Reference

class MoveError(Exception):
	pass

class Reference(watcher.Watcher, targethandler.TargetHandler):
	panelclass = gui.wx.Reference.ReferencePanel
	settingsclass = data.ReferenceSettingsData
	eventinputs = watcher.Watcher.eventinputs + \
				  presets.PresetsClient.eventinputs + \
				  [event.ReferenceTargetPublishEvent]
	eventoutputs = watcher.Watcher.eventoutputs + \
					presets.PresetsClient.eventoutputs

	defaultsettings = {
		'move type': 'stage position',
		'pause time': 3.0,
		'interval time': 0.0,
	}

	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.ReferenceTargetPublishEvent]
		watcher.Watcher.__init__(self, *args, **kwargs)
		targethandler.TargetHandler.__init__(self)

		self.instrument = instrument.Proxy(self.objectservice, self.session)

		self.calibration_clients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self),
			'image beam shift': calibrationclient.ImageBeamShiftCalibrationClient(self),
		}

		self.presets_client = presets.PresetsClient(self)

		self.lock = threading.RLock()
		self.reference_target = self.getReferenceTarget()

		self.last_processed = None

		self.start()

	def processData(self, incoming_data):
		if isinstance(incoming_data, data.ReferenceTargetData):
			self.processReferenceTarget(incoming_data)

	def processReferenceTarget(self, target_data):
		self.lock.acquire()
		self.reference_target = target_data
		self.lock.release()

	def getEMTargetData(self):
		target_data = self.reference_target
		if target_data is None:
			raise MoveError('no reference target available')
		move_type = self.settings['move type']
		calibration_client = self.calibration_clients[move_type]

		target_delta_row = target_data['delta row']
		target_delta_column = target_data['delta column']
		pixel_shift = {'row': -target_delta_row, 'col': -target_delta_column}

		target_scope = data.ScopeEMData(initializer=target_data['scope'])
		for i in ['image shift', 'beam shift', 'stage position']:
			target_scope[i] = dict(target_data['scope'][i])

		target_camera = target_data['camera']

		args = (pixel_shift, target_scope, target_camera)
		try:
			scope = calibration_client.transform(*args)
		except calibrationclient.NoMatrixCalibrationError, e:
			message = 'no %s calibration to move to reference target: %s'
			raise MoveError(message % (move_type, e))

		em_target_data = data.EMTargetData()

		em_target_data['preset'] = target_data['preset']
		em_target_data['movetype'] = move_type
		for i in ['image shift', 'beam shift', 'stage position']:
			em_target_data[i] = dict(scope[i])
		em_target_data['target'] = data.AcquisitionImageTargetData(initializer=target_data)

		return em_target_data

	def moveToTarget(self, preset_name):
		em_target_data = self.getEMTargetData()

		self.publish(em_target_data, database=True)

		self.presets_client.toScope(preset_name, em_target_data)
		preset = self.presets_client.getCurrentPreset()
		if preset['name'] != preset_name:
			message = 'failed to set preset \'%s\'' % preset_name
			raise MoveError(message)

	def _processRequest(self, request_data):
		preset_name = request_data['preset']
		pause_time = self.settings['pause time']
		interval_time = self.settings['interval time']

		if interval_time is not None and self.last_processed is not None:
			interval = time.time() - self.last_processed
			if interval < interval_time:
				message = '%d second(s) since last request, ignoring request'
				self.logger.info(message % interval)
				return

		try:
			self.moveToTarget(preset_name)
		except Exception, e:
			self.logger.error('Error moving to target, %s' % e)
			return

		if pause_time is not None:
			time.sleep(pause_time)

		try:
			self.execute(request_data)
		except Exception, e:
			self.logger.error('Error executing request, %s' % e)
			return

		self.last_processed = time.time()

	def processRequest(self, request_data):
		self.lock.acquire()
		try:
			self._processRequest(request_data)
		finally:
			self.lock.release()

	def execute(self, request_data):
		pass

class AlignZeroLossPeak(Reference):
	defaultsettings = {
		'move type': 'stage position',
		'pause time': 3.0,
		'interval time': 900.0,
	}
	eventinputs = Reference.eventinputs + [event.AlignZeroLossPeakPublishEvent]
	panelclass = gui.wx.Reference.AlignZeroLossPeakPanel
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.AlignZeroLossPeakPublishEvent]
		Reference.__init__(self, *args, **kwargs)

	def processData(self, incoming_data):
		Reference.processData(self, incoming_data)
		if isinstance(incoming_data, data.AlignZeroLossPeakData):
			self.processRequest(incoming_data)

	def execute(self, request_data):
		ccd_camera = self.instrument.ccdcamera
		if not ccd_camera.EnergyFiltered:
			self.logger.warning('No energy filter on this instrument.')
			return
		before_shift = None
		after_shift = None
		try:
			if not ccd_camera.EnergyFilter:
				self.logger.warning('Energy filtering is not enabled.')
				return
			before_shift = ccd_camera.getInternalEnergyShift()
			m = 'Energy filter internal shift: %g.' % before_shift
			self.logger.info(m)
		except AttributeError:
			m = 'Energy filter methods are not available on this instrument.'
			self.logger.warning(m)
		except Exception, e:
			s = 'Energy internal shift query failed: %s.'
			self.logger.error(s % e)

		try:
			if not ccd_camera.EnergyFilter:
				self.logger.warning('Energy filtering is not enabled.')
				return
			ccd_camera.alignEnergyFilterZeroLossPeak()
			m = 'Energy filter zero loss peak aligned.'
			self.logger.info(m)
		except AttributeError:
			m = 'Energy filter methods are not available on this instrument.'
			self.logger.warning(m)
		except Exception, e:
			s = 'Energy filter align zero loss peak failed: %s.'
			self.logger.error(s % e)

		try:
			if not ccd_camera.EnergyFilter:
				self.logger.warning('Energy filtering is not enabled.')
				return
			after_shift = ccd_camera.getInternalEnergyShift()
			m = 'Energy filter internal shift: %g.' % after_shift
			self.logger.info(m)
		except AttributeError:
			m = 'Energy filter methods are not available on this instrument.'
			self.logger.warning(m)
		except Exception, e:
			s = 'Energy internal shift query failed: %s.'
			self.logger.error(s % e)

		shift_data = data.InternalEnergyShiftData(session=self.session, before=before_shift, after=after_shift)
		self.publish(shift_data, database=True, dbforce=True)

class MeasureDose(Reference):
	defaultsettings = {
		'move type': 'stage position',
		'pause time': 3.0,
		'interval time': 900.0,
	}
	# relay measure does events
	eventinputs = Reference.eventinputs + [event.MeasureDosePublishEvent]
	eventoutputs = Reference.eventoutputs
	panelclass = gui.wx.Reference.MeasureDosePanel
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.MeasureDosePublishEvent]
		Reference.__init__(self, *args, **kwargs)

	def processData(self, incoming_data):
		Reference.processData(self, incoming_data)
		if isinstance(incoming_data, data.MeasureDoseData):
			self.processRequest(incoming_data)

	# override move to measure dose...
	def moveToTarget(self, preset_name):
		em_target_data = self.getEMTargetData()

		self.publish(em_target_data, database=True)

		self.presets_client.measureDose(preset_name, em_target_data)

	def execute(self, request_data):
		preset_name = request_data['preset']
		preset = self.presets_client.getPresetByName(preset_name)
		dose = preset['dose']/1e20
		exposure_time = preset['exposure time']/1000.0
		try:
			dose_rate = dose/exposure_time
		except ZeroDivisionError:
			dose_rate = 0
		self.logger.info('Measured dose for preset \'%s\'' % preset_name)
		self.logger.info('Dose: %g e-/A^2, rate: %g e-/A^2/s' % (dose, dose_rate))

