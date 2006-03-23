# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/beamtiltcalibrator.py,v $
# $Revision: 1.70 $
# $Name: not supported by cvs2svn $
# $Date: 2006-03-23 01:59:03 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import numarray
import threading
import calibrator
import calibrationclient
import data
import gui.wx.BeamTiltCalibrator

class Abort(Exception):
	pass

class BeamTiltCalibrator(calibrator.Calibrator):
	panelclass = gui.wx.BeamTiltCalibrator.Panel
	settingsclass = data.BeamTiltCalibratorSettingsData
	defaultsettings = calibrator.Calibrator.defaultsettings
	defaultsettings.update({
		'defocus beam tilt': 0.01,
		'first defocus': -2e-6,
		'second defocus': -4e-6,
		'stig beam tilt': 0.01,
		'stig delta': 0.2,
		'stig lens': 'objective',
		'measure beam tilt': 0.01,
		'measure lens': 'objective',
		'correct tilt': True,
		'settling time': 0.5,
	})

	def __init__(self, *args, **kwargs):
		calibrator.Calibrator.__init__(self, *args, **kwargs)

		self.abort = threading.Event()

		self.measurement = {}

		self.calibration_clients = {
			'beam tilt': calibrationclient.BeamTiltCalibrationClient(self),
			'eucentric focus': calibrationclient.EucentricFocusClient(self),
		}

		self.start()

	def _rotationCenterToScope(self):
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		calibration_client = self.calibration_clients['beam tilt']
		beam_tilt = calibration_client.retreiveRotationCenter(tem, cam, ht, mag)
		if not beam_tilt:
			raise RuntimeError('no rotation center for %geV, %gX' % (ht, mag))
		self.instrument.tem.BeamTilt = beam_tilt

	def rotationCenterToScope(self):
		try:
			self._rotationCenterToScope()
		except Exception, e:
			self.logger.error('Unable to set rotation center: %s' % e)
		else:
			self.logger.info('Set instrument rotation center')
		self.panel.setInstrumentDone()

	def _rotationCenterFromScope(self):
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		beam_tilt = self.instrument.tem.BeamTilt
		calibration_client = self.calibration_clients['beam tilt']
		calibration_client.storeRotationCenter(tem, cam, ht, mag, beam_tilt)

	def rotationCenterFromScope(self):
		try:
			self._rotationCenterFromScope()
		except Exception, e:
			self.logger.error('Unable to get rotation center: %s' % e)
		else:
			self.logger.info('Saved instrument rotation center')
		self.panel.setInstrumentDone()

	def FUTUREcalibrateRotationCenter(self, tilt_value):
		if self.initInstruments():
			raise RuntimeError('cannot initialize instrument')

		calibration_client = self.calibration_clients['beam tilt']

		state1 = {'beam tilt': tilt_value}
		state2 = {'beam tilt': -tilt_value}

		matdict = {}

		for axis in ('x','y'):
			self.logger.info('Measuring %s tilt' % (axis,))

			diff1 = calibration_client.measureDispDiff(axis, tilt_value, tilt_value, correct_tilt=self.settings['correct tilt'])
			diff2 = calibration_client.measureDispDiff(axis, -tilt_value, tilt_value, correct_tilt=self.settings['correct tilt'])

			matcol = calibration_client.eq11((diff1, diff2), (0, 0), tilt_value)
			matdict[axis] = matcol

		self.logger.debug('Making matrix...')
		matrix = numarray.zeros((2,2), numarray.Float)
		self.logger.debug('Matrix type %s, matrix dict type %s'
											% (matrix.type(), matdict['x'].type()))
		matrix[:,0] = matdict['x']
		matrix[:,1] = matdict['y']

		# store calibration
		self.logger.info('Storing calibration...')
		mag = self.instrument.tem.Magnification
		ht = self.instrument.tem.HighTension
		calibration_client = self.calibration_clients['beam tilt']
		calibration_client.storeMatrix(ht, mag, 'coma-free', matrix)
		self.logger.info('Calibration stored')

	def __calibrateDefocus(self, beam_tilt, defocii):
		if self.initInstruments():
			raise RuntimeError('cannot initialize instrument')

		calibration_client = self.calibration_clients['beam tilt']

		axes = ('x', 'y')
		states = ({'defocus': defocii[0]}, {'defocus': defocii[1]})
		matrix = numarray.identity(2, numarray.Float)
		for i, axis in enumerate(axes):
			self.logger.info('Calibrating on %s-axis...' % axis)
			args = (axis, beam_tilt, states)
			kwargs = {
				'correct_tilt': self.settings['correct tilt'],
				'settle': self.settings['settling time'],
			}
			shifts = calibration_client.measureDisplacements(*args, **kwargs)
			matrix[:, i] = calibration_client.eq11(shifts, defocii, beam_tilt)
			self.checkAbort()

		# store calibration
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		calibration_client.storeMatrix(ht, mag, 'defocus', matrix)

	def _calibrateDefocus(self, beam_tilt, defocii):
		rotation_center = self.instrument.tem.BeamTilt
		defocus = self.instrument.tem.Defocus
		try:
			self.__calibrateDefocus(beam_tilt, defocii)
		finally:
			self.instrument.tem.BeamTilt = rotation_center
			self.instrument.tem.Defocus = defocus

	def calibrateDefocus(self):
		beam_tilt = self.settings['defocus beam tilt']
		defocii = []
		defocii.append(self.settings['first defocus'])
		defocii.append(self.settings['second defocus'])

		self.logger.info('Calibrating defocus...')
		try:
			self._calibrateDefocus(beam_tilt, defocii)
		except Exception, e:
			self.logger.error('Calibration failed: %s' % e)
		else:
			self.logger.info('Calibration completed')

		self.panel.calibrationDone()

	def __calibrateStigmator(self, lens, beam_tilt, delta, stigmator):
		if self.initInstruments():
			raise RuntimeError('cannot initialize instrument')

		calibration_client = self.calibration_clients['beam tilt']

		magnification = self.instrument.tem.Magnification
		high_tension = self.instrument.tem.HighTension

		# set up the stigmator states
		axes = ('x', 'y')
		deltas = (delta/2.0, -delta/2.0)
		for stig_axis in axes:
			self.logger.info('Calibrating stig. %s-axis...' % stig_axis)
			parameters = []
			states = []
			for delta in deltas:
				v = dict(stigmator)
				v[stig_axis] += delta
				parameters.append(v[stig_axis])
				s = data.ScopeEMData(stigmator={lens: v})
				states.append(s)

			matrix = numarray.identity(2, numarray.Float)
			for i, tilt_axis in enumerate(axes):
				self.logger.info('Calibrating on %s-axis...' % tilt_axis)
				args = (tilt_axis, beam_tilt, states)
				kwargs = {
					'correct_tilt': self.settings['correct tilt'],
					'settle': self.settings['settling time'],
				}
				shifts = calibration_client.measureDisplacements(*args, **kwargs)
				args = (shifts, parameters, beam_tilt)
				matrix[:, i] = calibration_client.eq11(*args)
				self.checkAbort()

			# store calibration
			type = lens + stig_axis
			args = (high_tension, magnification, type, matrix)
			calibration_client.storeMatrix(*args)

	def _calibrateStigmator(self, lens, beam_tilt, delta):
		rotation_center = self.instrument.tem.BeamTilt
		stigmator = self.instrument.tem.Stigmator[lens]
		try:
			self.__calibrateStigmator(lens, beam_tilt, delta, stigmator)
		finally:
			self.instrument.tem.BeamTilt = rotation_center
			self.instrument.tem.Stigmator = {lens: stigmator}

	def calibrateStigmator(self):
		lens = self.settings['stig lens']
		beam_tilt = self.settings['stig beam tilt']
		delta = self.settings['stig delta']

		self.logger.info('Calibrating %s stigmator...' % lens)
		try:
			self._calibrateStigmator(lens, beam_tilt, delta)
		except Exception, e:
			self.logger.error('Calibration failed: %s' % e)
		else:
			self.logger.info('Calibration completed')

		self.panel.calibrationDone()

	def _measure(self, beam_tilt, lens, correct_tilt):
		if self.initInstruments():
			raise RuntimeError('cannot initialize instrument')

		calibration_client = self.calibration_clients['beam tilt']

		args = (beam_tilt,)
		kwargs = {
			'stig': lens,
			'correct_tilt': self.settings['correct tilt'],
			'settle': self.settings['settling time'],
		}
		result = calibration_client.measureDefocusStig(*args, **kwargs)

		try:
			defocus = result['defocus']
			self.measurement['defocus'] = result['defocus']
		except KeyError:
			defocus = None

		self.measurement[lens] = {}
		stig = {}
		for axis in ('x', 'y'):
			try:
				stig[axis] = result['stig' + axis]
				self.measurement[lens][axis] = result['stig' + axis]
			except KeyError:
				pass

		return defocus, stig

	def measure(self):
		beam_tilt = self.settings['measure beam tilt']
		lens = self.settings['measure lens']
		correct_tilt = self.settings['correct tilt']

		self.logger.info('Measuring defocus and %s stigmator...' % lens)
		try:
			args = self._measure(beam_tilt, lens, correct_tilt)
		except Exception, e:
			args = (None, {})
			self.logger.exception('Measurement failed: %s' % e)
		else:
			self.logger.info('Measurement completed')
		self.panel.measurementDone(*args)

	def _correctDefocus(self):
		try:
			measurement = self.measurement['defocus']
		except:
			raise RuntimeError('no measurment')
		defocus = self.instrument.tem.Defocus
		self.instrument.tem.Defocus = defocus + measurement

	def correctDefocus(self):
		self.logger.info('Correcting defocus...')
		try:
			self._correctDefocus()
		except Exception, e:
			self.logger.exception('Correction failed: %s' % e)
		else:
			self.logger.info('Correction completed')

		self.panel.setInstrumentDone()

	def _correctStigmator(self, lens):
		stigmator = self.instrument.tem.Stigmator[lens]
		try:
			for axis in ('x', 'y'):
				stigmator[axis] += self.measurement[lens][axis]
		except:
			raise RuntimeError('no measurment')
		self.instrument.tem.Stigmator = {lens: stigmator}

	def correctStigmator(self):
		lens = self.settings['stig lens']

		self.logger.info('Correcting %s stigmator...' % lens)
		try:
			self._correctStigmator(lens)
		except Exception, e:
			self.logger.exception('Correction failed: %s' % e)
		else:
			self.logger.info('Correction completed')

		self.panel.setInstrumentDone()

	def resetDefocus(self):
		try:
			self.instrument.tem.resetDefocus(True)
		except Exception, e:
			self.logger.error('Reset defocus failed: %s' % e)
		else:
			self.logger.info('Defocus reset')

		self.panel.setInstrumentDone()

	def _eucentricFocusToScope(self):
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		
		calibration_client = self.calibration_clients['eucentric focus']
		eucentric = calibration_client.researchEucentricFocus(ht, mag)
		if not eucentric:
			raise RuntimeError('no eucentric focus for %geV, %gX' % (ht, mag))

		self.instrument.tem.Focus = eucentric['focus']

	def eucentricFocusToScope(self):
		try:
			self._eucentricFocusToScope()
		except Exception, e:
			self.logger.error('Set eucentric focus failed: %s' % e)
		else:
			self.logger.info('Set eucentric focus')

		self.panel.setInstrumentDone()

	def _eucentricFocusFromScope(self):
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		focus = self.instrument.tem.Focus

		calibration_client = self.calibration_clients['eucentric focus']
		calibration_client.publishEucentricFocus(ht, mag, focus)

	def eucentricFocusFromScope(self):
		try:
			self._eucentricFocusFromScope()
		except Exception, e:
			self.logger.error('Unable to get eucentric focus: %s' % e)
		else:
			self.logger.info('Saved eucentric focus')

		self.panel.getInstrumentDone()

	def checkAbort(self):
		if not self.abort.isSet():
			return
		self.abort.clear()
		raise Abort('operation aborted')

	def abortCalibration(self):
		self.abort.set()

