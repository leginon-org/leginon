# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/beamtiltcalibrator.py,v $
# $Revision: 1.82 $
# $Name: not supported by cvs2svn $
# $Date: 2007-08-13 23:58:28 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import numpy
import threading
import calibrator
import calibrationclient
from leginon import leginondata
import gui.wx.BeamTiltCalibrator
import time

class Abort(Exception):
	pass

class BeamTiltCalibrator(calibrator.Calibrator):
	panelclass = gui.wx.BeamTiltCalibrator.Panel
	settingsclass = leginondata.BeamTiltCalibratorSettingsData
	defaultsettings = calibrator.Calibrator.defaultsettings
	defaultsettings.update({
		'defocus beam tilt': 0.01,
		'first defocus': -2e-6,
		'second defocus': -4e-6,
		'stig beam tilt': 0.01,
		'stig delta': 0.2,
		'measure beam tilt': 0.01,
		'correct tilt': True,
		'settling time': 0.5,
		'comafree beam tilt': 0.005,
		'comafree misalign': 0.002,
		'imageshift coma tilt': 0.005,
		'imageshift coma step': -1e-6,
		'imageshift coma number': 1,
		'imageshift coma repeat': 1,
	})

	def __init__(self, *args, **kwargs):
		calibrator.Calibrator.__init__(self, *args, **kwargs)

		self.abort = threading.Event()

		self.measurement = {}
		self.comameasurement = {}

		self.calibration_clients = {
			'beam tilt': calibrationclient.BeamTiltCalibrationClient(self),
			'eucentric focus': calibrationclient.EucentricFocusClient(self),
		}
		self.btcalclient = self.calibration_clients['beam tilt']

		self.start()

	def alignRotationCenter(self, defocus1, defocus2):
		cal = self.calibration_clients['beam tilt']
		bt = cal.alignRotationCenter(defocus1, defocus2)

	def rotationCenterToScope(self):
		self.calibration_clients['beam tilt'].rotationCenterToScope()
		self.panel.setInstrumentDone()

	def rotationCenterFromScope(self):
		self.calibration_clients['beam tilt'].rotationCenterFromScope()
		self.panel.setInstrumentDone()

	def calibrateComaFree(self):
		'''determine the calibration matrix for coma-free alignment'''
		calibration_client = self.calibration_clients['beam tilt']
		try:
			if self.initInstruments():
				raise RuntimeError('cannot initialize instrument')
			tilt_value = self.settings['comafree beam tilt']
			m_value = self.settings['comafree misalign']
			matrix = calibration_client.measureMatrixC(m_value, tilt_value, settle=self.settings['settling time'])
		except Exception, e:
			self.logger.error('Calibration failed: %s' % e)
			matrix = None
		else:
			self.logger.info('Calibration completed')
		# store calibration
		if matrix is not None:
			self.logger.info('Storing calibration...')
			mag = self.instrument.tem.Magnification
			ht = self.instrument.tem.HighTension
			probe = self.instrument.tem.ProbeMode
			calibration_client.storeMatrix(ht, mag, 'beam-tilt coma', matrix, probe=probe)
			self.logger.info('Calibration stored')
		self.panel.calibrationDone()

	def calibrateImageShiftComa(self):
		'''determine the calibration matrix for image shift induced coma'''
		calibration_client = self.calibration_clients['beam tilt']
		try:
			if self.initInstruments():
				raise RuntimeError('cannot initialize instrument')
			tilt_value = self.settings['imageshift coma tilt']
			shift_step = self.settings['imageshift coma step']
			shift_n = self.settings['imageshift coma number']
			repeat = self.settings['imageshift coma repeat']
			matrix,coma0 = self.measureImageShiftComaMatrix(shift_n,shift_step,repeat, tilt_value, settle=self.settings['settling time'])
		except Exception, e:
			self.logger.error('Calibration failed: %s' % e)
			matrix = None
		else:
			self.logger.info('Calibration completed')
		# store calibration
		if matrix is not None:
			self.logger.info('Storing calibration...')
			mag = self.instrument.tem.Magnification
			ht = self.instrument.tem.HighTension
			probe = self.instrument.tem.ProbeMode
			calibration_client.storeMatrix(ht, mag, 'image-shift coma', matrix, probe=probe)
			self.logger.info('Calibration stored')
		self.panel.calibrationDone()

	def measureImageShiftComaMatrix(self, shift_n, shift_step, repeat, tilt_value, settle):
		''' Measure coma for a range of image shift and fit the results 
				to a straight line on individual axis.  Strickly speaking should
				use orthogonal distance regression.''' 
		calibration_client = self.calibration_clients['beam tilt']
		f = open(self.session['name']+'tilt.dat','w')
		tem = self.instrument.getTEMData()
		shift0 = self.instrument.tem.ImageShift
		state = leginondata.ScopeEMData()
		tilt0 = self.instrument.tem.BeamTilt
		state['image shift'] = shift0
		state['beam tilt'] = tilt0
		coma0 = tilt0
		tdict = {}
		xydict = {}
		ordered_axes = ['x','y']
		debug = False
		try:
			for axis in ordered_axes:
				tdata = []
				data = {'x':[],'y':[]}
				for i in range(0,2*shift_n+1):
					shift = (i - shift_n) * shift_step
					tdata.append(shift)
					state['image shift'][axis] = shift0[axis] + shift
					self.instrument.setData(state)
					newshift = self.instrument.tem.ImageShift
					self.logger.info('Image Shift ( %5.2f, %5.2f)' % (newshift['x']*1e6,newshift['y']*1e6))
					text = '%5.2f %5.2f ' % (newshift['x']*1e6,newshift['y']*1e6)
					xarray,yarray = calibration_client.repeatMeasureComaFree(tilt_value,settle,repeat)
					xmean = xarray.mean()
					ymean = yarray.mean()
					text = text + "%5.2f %5.2f %5.2f %5.2f" %(xmean*1000,xarray.std()*1000,ymean*1000,yarray.std()*1000) + '\n'
					f.write(text)
					state['image shift'] = shift0
					state['beam tilt'] = tilt0
					self.instrument.setData(state)
					comatilt = {'x':xmean,'y':ymean}
					data['x'].append(xmean)
					data['y'].append(ymean)
					self.checkAbort()
				tdict[axis] = tdata
				xydict[axis] = data
			matrix, coma0 = calibration_client.calculateImageShiftComaMatrix(tdict,xydict)
		except:
			raise
			matrix = None
		f.close()
		return matrix, coma0

	def measureComaFree(self, tilt_value, correctshift=False):
		tilt0 = self.instrument.tem.BeamTilt
		calibration_client = self.calibration_clients['beam tilt']
		if correctshift:
			try:
				calibration_client.correctImageShiftComa()
			except Exception, e:
				self.logger.error('Correction failed: %s' % e)
				self.panel.comaMeasurementDone(self.comameasurement)
				return
		try:
			cftiltsx,cftiltsy = calibration_client.repeatMeasureComaFree(tilt_value, settle=self.settings['settling time'], repeat=1)
			comatilt = {'x':cftiltsx.mean(),'y':cftiltsy.mean()}
			self.comameasurement = comatilt
		except Exception, e:
			self.logger.error('ComaFree Measurement failed: %s' % e)
		self.instrument.tem.BeamTilt = tilt0
		self.panel.comaMeasurementDone(self.comameasurement)

	def _correctComaTilt(self):
		bt = self.comameasurement
		oldbt = self.instrument.tem.BeamTilt
		self.logger.info('Old beam tilt: %.4f, %.4f' % (oldbt['x'],oldbt['y'],))
		newbt = {'x': oldbt['x'] + bt['x'], 'y': oldbt['y'] + bt['y']}
		self.instrument.tem.BeamTilt = newbt
		self.logger.info('New beam tilt: %.4f, %.4f' % (newbt['x'],newbt['y'],))

	def correctComaTilt(self):
		self.logger.info('Correcting beam tilt...')
		try:
			self._correctComaTilt()
		except Exception, e:
			self.logger.exception('Correction failed: %s' % e)
		else:
			self.logger.info('Correction completed')

		self.panel.setInstrumentDone()

	def __calibrateDefocus(self, beam_tilt, defocii):
		if self.initInstruments():
			raise RuntimeError('cannot initialize instrument')

		calibration_client = self.calibration_clients['beam tilt']

		axes = ('x', 'y')
		states = ({'defocus': defocii[0]}, {'defocus': defocii[1]})
		matrix = numpy.identity(2, numpy.float)
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
		probe = self.instrument.tem.ProbeMode
		calibration_client.storeMatrix(ht, mag, 'defocus', matrix, probe=probe)

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

	def __calibrateStigmator(self, beam_tilt, delta, stigmator):
		if self.initInstruments():
			raise RuntimeError('cannot initialize instrument')

		calibration_client = self.calibration_clients['beam tilt']

		magnification = self.instrument.tem.Magnification
		high_tension = self.instrument.tem.HighTension
		probe = self.instrument.tem.ProbeMode

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
				s = leginondata.ScopeEMData(stigmator={'objective': v})
				states.append(s)

			matrix = numpy.identity(2, numpy.float)
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
			type = 'stig' + stig_axis
			args = (high_tension, magnification, type, matrix)
			kwargs = {'probe':probe}
			calibration_client.storeMatrix(*args,**kwargs)

	def _calibrateStigmator(self, beam_tilt, delta):
		rotation_center = self.instrument.tem.BeamTilt
		stigmator = self.instrument.tem.Stigmator['objective']
		try:
			self.__calibrateStigmator(beam_tilt, delta, stigmator)
		finally:
			self.instrument.tem.BeamTilt = rotation_center
			self.instrument.tem.Stigmator = {'objective': stigmator}

	def calibrateStigmator(self):
		beam_tilt = self.settings['stig beam tilt']
		delta = self.settings['stig delta']

		self.logger.info('Calibrating objective stigmator...')
		try:
			self._calibrateStigmator(beam_tilt, delta)
		except Exception, e:
			self.logger.error('Calibration failed: %s' % e)
		else:
			self.logger.info('Calibration completed')

		self.panel.calibrationDone()

	def _measure(self, beam_tilt, correct_tilt):
		if self.initInstruments():
			raise RuntimeError('cannot initialize instrument')

		calibration_client = self.calibration_clients['beam tilt']

		args = (beam_tilt,)
		kwargs = {
			'stig': True,
			'correct_tilt': self.settings['correct tilt'],
			'settle': self.settings['settling time'],
		}
		result = calibration_client.measureDefocusStig(*args, **kwargs)
		self.measurement = {}

		try:
			defocus = result['defocus']
			self.measurement['defocus'] = result['defocus']
		except KeyError:
			defocus = None

		stig = {}
		for axis in ('x', 'y'):
			try:
				stig[axis] = result['stig' + axis]
				self.measurement[axis] = result['stig' + axis]
			except KeyError:
				pass

		return defocus, stig

	def measure(self):
		beam_tilt = self.settings['measure beam tilt']
		if not beam_tilt > 0:
			self.logger.error('measure beam tilt must be greater than 0...')
			args = (None, {})
			self.panel.measurementDone(*args)
			return

		correct_tilt = self.settings['correct tilt']

		self.logger.info('Measuring defocus and objective stigmator...')
		try:
			args = self._measure(beam_tilt, correct_tilt)
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
			raise RuntimeError('no measurement')
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

	def _correctStigmator(self):
		stigmator = self.instrument.tem.Stigmator['objective']
		try:
			for axis in ('x', 'y'):
				stigmator[axis] += self.measurement[axis]
		except:
			raise RuntimeError('no measurement')
		self.instrument.tem.Stigmator = {'objective': stigmator}

	def correctStigmator(self):
		self.logger.info('Correcting objective stigmator...')
		try:
			self._correctStigmator()
		except Exception, e:
			self.logger.exception('Correction failed: %s' % e)
		else:
			self.logger.info('Correction completed')

		self.panel.setInstrumentDone()

	def resetDefocus(self):
		try:
			self.instrument.tem.resetDefocus()
		except Exception, e:
			self.logger.error('Reset defocus failed: %s' % e)
		else:
			self.logger.info('Defocus reset')

		self.panel.setInstrumentDone()

	def _eucentricFocusToScope(self):
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		probe = self.instrument.tem.ProbeMode
		
		calibration_client = self.calibration_clients['eucentric focus']
		eucentric = calibration_client.researchEucentricFocus(ht, mag, probe)
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
		probe = self.instrument.tem.ProbeMode
		focus = self.instrument.tem.Focus

		calibration_client = self.calibration_clients['eucentric focus']
		calibration_client.publishEucentricFocus(ht, mag, probe, focus)

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

	def editCurrentCalibration(self):
		try:
			kwargs = self.getCurrentCalibration()
			self.panel.editCalibration(**kwargs)
		except Exception, e:
			self.logger.error('Calibration edit failed: %s' % e)
			return

	def getCurrentCalibration(self):
		tem = self.instrument.getTEMData()
		if tem is None:
			raise RuntimerError('no TEM selected')
		ccd_camera = self.instrument.getCCDCameraData()
		if ccd_camera is None:
			raise RuntimerError('no CCD camera selected')
		high_tension = self.instrument.tem.HighTension
		if high_tension is None:
			raise RuntimerError('cannot get high tension')
		magnification = self.instrument.tem.Magnification
		if magnification is None:
			raise RuntimerError('cannot get magnification')
		probe = self.instrument.tem.ProbeMode
		if probe is None:
			raise RuntimerError('cannot get beam probe mode')
		parameter = 'defocus'
		client = self.calibration_clients['beam tilt']
		m = 'Get %s calibration failed: %s'
		try:
			matrix_data = client.researchMatrix(tem, ccd_camera, parameter, high_tension, magnification, probe)
			matrix = matrix_data['matrix']
		except Exception, e:
			self.logger.warning(m % ('focus', e))
			matrix = None
		try:
			rotation_center = client.retrieveRotationCenter(tem, high_tension, magnification, probe)
		except Exception, e:
			self.logger.warning(m % ('rotation center', e))
			rotation_center = None
		client = self.calibration_clients['eucentric focus']
		try:
			eucentric_focus_data = client.researchEucentricFocus(high_tension, magnification, probe, tem=tem, ccdcamera=ccd_camera)
			eucentric_focus = eucentric_focus_data['focus']
		except Exception, e:
			self.logger.warning(m % ('eucentric focus', e))
			eucentric_focus = None
		kwargs = {
			'tem': tem,
			'ccd_camera': ccd_camera,
			'high_tension': high_tension,
			'magnification': magnification,
			'probe': probe,
			'parameter': parameter,
			'matrix': matrix,
			'rotation_center': rotation_center,
			'eucentric_focus': eucentric_focus,
		}
		return kwargs

	def saveCalibration(self, calibration, parameter, high_tension, magnification, tem, ccd_camera, probe):
		matrix, rotation_center, eucentric_focus = calibration
		client = self.calibration_clients['beam tilt']
		client.storeMatrix(high_tension, magnification, parameter, matrix, tem, ccd_camera, probe)
		client.storeRotationCenter(tem, high_tension, magnification, probe, rotation_center)
		client = self.calibration_clients['eucentric focus']
		client.publishEucentricFocus(high_tension, magnification, probe, eucentric_focus)

