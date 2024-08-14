# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#
# $Source: /ami/sw/cvsroot/pyleginon/beamtiltcalibrator.py,v $
# $Revision: 1.82 $
# $Name: not supported by cvs2svn $
# $Date: 2007-08-13 23:58:28 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $


import numpy
import math
import threading
from leginon import calibrator
from leginon import calibrationclient
from leginon import leginondata
from pyami import imagefun
from leginon import tableau
from leginon import player
import leginon.gui.wx.BeamTiltCalibrator
import time

class Abort(Exception):
	pass

class BeamTiltCalibrator(calibrator.Calibrator):
	panelclass = leginon.gui.wx.BeamTiltCalibrator.Panel
	settingsclass = leginondata.BeamTiltCalibratorSettingsData
	defaultsettings = dict(calibrator.Calibrator.defaultsettings)
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
		'imageshift coma tilt': 0.01,
		'imageshift coma step': -5e-6,
		'imageshift coma number': 2,
		'imageshift coma repeat': 1,
	})

	def __init__(self, *args, **kwargs):
		calibrator.Calibrator.__init__(self, *args, **kwargs)

		self.abort = threading.Event()

		self.measurement = {}
		self.comameasurement = {}
		self.parameter = 'defocus'
		self.dialog_done = threading.Event()
		self.ab_types = ['beam tilt','stig','defocus']
		self.sites = 4
		self.manualplayer = player.Player()

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
		except Exception as e:
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
			matrices = self.measureImageShiftAberrationMatrices(shift_n,shift_step,repeat, tilt_value, settle=self.settings['settling time'])
		except Exception as e:
			self.logger.error('Calibration failed: %s' % e)
			matrices = None
		else:
			self.logger.info('Calibration completed')
		# store calibration
		if matrices is not None:
			self.logger.info('Storing calibration...')
			mag = self.instrument.tem.Magnification
			ht = self.instrument.tem.HighTension
			probe = self.instrument.tem.ProbeMode
			for key in list(matrices.keys()):
				matrix = matrices[key]
				self.logger.info('Storing image-shift %s calibration' % (key,))
				calibration_client.storeMatrix(ht, mag, 'image-shift %s' % (key,), matrix, probe=probe)
			self.logger.info('Calibrations stored')
		self.panel.calibrationDone()

	def getFakeValues(self, axis, index):
		'''
		get fake values for testing. Set shift to -10e-6 and number of steps to 1.
		'''
		newstate = {}
		fake = {}
		fake['beam tilt'] = {'x':[(0.00355495,-0.0236784),(0.00590004,-0.0213854),(0.00808952,-0.0189389)],'y':[(0.00329904,-0.0192235),(0.00585431,-0.0213466),(0.00822038,-0.023757)]}
		fake['stig'] = {'x':[(-0.0047448,-0.0031997),(-0.012963,-0.0113492),(-0.0225249,-0.0163792)],'y':[(-0.0111456, -0.0247119),(-0.0131071,-0.0115893),(-0.0147681, 0.00236871)]}
		fake['defocus'] = {'x':[3.14407e-6*2.429,2.358393e-6*2.429,1.64571e-6*2.429],'y':[2.00239e-6*2.429,2.33574e-6*2.429,2.90392e-6*2.429]}
		for ab_type in list(fake.keys()):
			if type(fake[ab_type][axis][index]) == type(()):
				newstate[ab_type] = {'x':fake[ab_type][axis][index][0],'y':fake[ab_type][axis][index][1]}
			else:
				newstate[ab_type] = fake[ab_type][axis][index]
		return newstate

	def measureImageShiftAberrationMatrices(self, shift_n, shift_step, repeat, tilt_value, settle):
		''' Measure various aberration for a range of image shift and fit the results 
				to a straight line on individual axis.  Strickly speaking should
				use orthogonal distance regression.''' 
		calibration_client = self.calibration_clients['beam tilt']
		tem = self.instrument.getTEMData()
		shift0 = self.instrument.tem.ImageShift
		state = leginondata.ScopeEMData()
		state['image shift'] = shift0
		tdict = {}
		xydict = {}
		ordered_axes = ['x','y']
		debug = False
		try:
			for axis in ordered_axes:
				tdata = []
				data = {}
				for ab_type in self.ab_types:
					data[ab_type] = {'x':[],'y':[]}
				for i in range(0,2*shift_n+1):
					shift = (i - shift_n) * shift_step
					tdata.append(shift)
					# set to shift0 so that the other axis is reset.
					state['image shift'] = shift0
					state['image shift'][axis] = shift0[axis] + shift
					# all values are at original except image shift
					self.instrument.setData(state)
					newshift = self.instrument.tem.ImageShift
					self.logger.info('Image Shift ( %5.2f, %5.2f)' % (newshift['x']*1e6,newshift['y']*1e6))
					# memorize the aberration state0
					self.setPreMeasureState()
					try:
						last_calibration = self.getCurrentNoMagCalibration()
					except calibrationclient.NoMatrixCalibrationError as e:
						pass
					try:
						self.btcalclient.correctImageShiftComa()
						self.logger.warning('Apply beam tilt delta from last image-shift coma calibration to start')
						no_cal = False
					except:
						self.logger.warning('use original beam tilt to start')
						no_cal = True
					try:
						if no_cal == False:
							self.btcalclient.correctImageShiftObjStig()
							self.logger.warning('Apply obj stig delta from last image-shift stig calibration to start')
					except:
						self.logger.warning('use original stig to start')
					try:
						if no_cal == False:
							self.btcalclient.correctImageShiftDefocus()
							self.logger.warning('Apply defocus delta from last image-shift defocus calibration to start')
					except:
						self.logger.warning('use original defocus to start')
					# For TESTING ---START HERE
					'''
					newstate = self.getFakeValues(axis, i)
					self.instrument.tem.BeamTilt = newstate['beam tilt']
					self.instrument.tem.Defocus = newstate['defocus']
					self.instrument.tem.Stigmator = {'objective':newstate['stig']}
					'''
					# For TESTING ---END HERE
					newstate = self.readAbFree(state['image shift'])
					if abs(shift) > 1e-7:
						while no_cal and abs(newstate['beam tilt']['x']-self.state0['beam tilt']['x']) < 1e-5 or abs(newstate['beam tilt']['y']-self.state0['beam tilt']['y']) < 1e-5:
							self.logger.error('Beam tilt has not changed. Will cause calibration failure.')
							self.logger.info('Please repeat the measurement or Cancel in the dialog....')
							newstate = self.readAbFree(state['image shift'])
					# reset to original state for the original shift to be consistent.
					self.resetState()
					self.instrument.tem.ImageShift = shift0
					# measured value is the correction needed to remove coma.
					for ab_type in list(newstate.keys()):
						value = newstate[ab_type]
						if ab_type == 'defocus':
							data[ab_type]['x'].append(-value)
							data[ab_type]['y'].append(-value)
						else:
							data[ab_type]['x'].append(-value['x'])
							data[ab_type]['y'].append(-value['y'])
					self.checkAbort()
				tdict[axis] = tdata
				xydict[axis] = data
			matrices, ab0s = self.calculateImageShiftAberrationMatrix(tdict,xydict)
		except ValueError as e:
			self.logger.warning('Aborting calibration....')
			self.resetState()
			self.instrument.tem.ImageShift = shift0
			matrices = None
		return matrices

	def calculateImageShiftAberrationMatrix(self, tdict, xydict):
		'''
		Calculate the aberration matrix.  Requires input of
		tdict = {'x': [shiftx1,....],'y':[shifty1,....]}
		xydict ={'x':{aberration_type: [aberration_value_dictx1,....],
		         'y':{aberration_type: [aberration_value_dictx1,....],
						}
		aberration_value_dicts are in the form of {'x':valuex, 'y':valuey}
		'''
		matrices = {}
		ab0s = {}
		for ab_type in self.ab_types:
			this_xydict = {'x':xydict['x'][ab_type],'y':xydict['y'][ab_type]}
			matrix, ab0 = self.btcalclient.calculateImageShiftAberrationMatrix(tdict,this_xydict)
			if ab_type == 'beam tilt':
				matrices['coma'] = matrix
				ab0s['coma'] = ab0
			else:
				matrices[ab_type] = matrix
				ab0s[ab_type] = ab0
		return matrices, ab0s

	def readComaFree(self):
		newstate = self.readAbFree()
		return newstate['beam tilt']['x'], newstate['beam tilt']['y']

	def readAbFree(self, imageshift=None):
		# trigger opening dialog. Let it fail and caught by the caller
		self.dialog_done.clear()
		self.panel.readAbFreeState(imageshift)
		# wait for dialog to close
		self.dialog_done.wait()
		if not self.value_accepted:
			self.resetState()
			raise ValueError('Abort calibration')
		newstate = self.getState()
		return newstate

	def guiReadAbFreeStateDone(self,is_ok):
		self.value_accepted = is_ok
		self.dialog_done.set()

	def getState(self):
		state = {}
		state['beam tilt'] = self.instrument.tem.BeamTilt
		state['defocus'] = self.instrument.tem.Defocus
		state['stig'] = self.instrument.tem.Stigmator['objective']
		return state

	def readState(self):
		state = self.getState()
		self.panel.readStateDone(state)
		return

	def resetState(self):
		self.instrument.tem.BeamTilt = self.state0['beam tilt']
		self.instrument.tem.Defocus = self.state0['defocus']
		self.instrument.tem.Stigmator = {'objective':self.state0['stig']}
		self.logger.info('Reset to uncorrected state at current image shift')
		self.readState()

	def setPreMeasureState(self):
		self.state0 = self.getState().copy()
			
	def measureComaFree(self, tilt_value, correctshift=False):
		tilt0 = self.instrument.tem.BeamTilt
		self.setPreMeasureState()
		calibration_client = self.calibration_clients['beam tilt']
		if correctshift:
			try:
				calibration_client.correctImageShiftComa()
			except Exception as e:
				self.logger.error('Correction failed: %s' % e)
				self.panel.comaMeasurementDone(self.comameasurement)
				return
		try:
			#cftiltsx,cftiltsy = calibration_client.repeatMeasureComaFree(tilt_value, settle=self.settings['settling time'], repeat=1)
			#comatilt = {'x':cftiltsx.mean(),'y':cftiltsy.mean()}
			comatilt = self.readComaFree()
			self.comameasurement = comatilt
		except Exception as e:
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
		except Exception as e:
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
		matrix = numpy.identity(2, numpy.float64)
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
		except Exception as e:
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

			matrix = numpy.identity(2, numpy.float64)
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
		except Exception as e:
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
		except Exception as e:
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
		except Exception as e:
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
		except Exception as e:
			self.logger.exception('Correction failed: %s' % e)
		else:
			self.logger.info('Correction completed')

		self.panel.setInstrumentDone()

	def resetDefocus(self):
		try:
			self.instrument.tem.resetDefocus()
		except Exception as e:
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
		except Exception as e:
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
		except Exception as e:
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
		'''
		Edit calibration of the gui-selected matrix without magnification.  Similar to the function in MatrixCalibrator.
		'''
		try:
			calibrationdata = self.getCurrentNoMagCalibration()
		except calibrationclient.NoMatrixCalibrationError as e:
			if e.state is None:
				raise e
			else:
				self.logger.warning('No calibration found for current state: %s' % e)
				calibrationdata = e.state
		except Exception as e:
			self.logger.error('Calibration edit failed: %s' % e)
			return
		self.panel.editCalibration(calibrationdata)

	def editCurrentFocusCalibration(self):
		try:
			kwargs = self.getCurrentFocusCalibration()
			self.panel.editFocusCalibration(**kwargs)
		except Exception as e:
			self.logger.error('Calibration edit failed: %s' % e)
			return

	def getCurrentNoMagCalibration(self):
		if self.instrument.tem is None:
			raise RuntimeError('cannot access TEM')
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		par = self.parameter
		ht = self.instrument.tem.HighTension
		probe = self.instrument.tem.ProbeMode
		mag = None
		return self.btcalclient.researchMatrix(tem, cam, par, ht, mag, probe)

	def getCurrentFocusCalibration(self):
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
		except Exception as e:
			self.logger.warning(m % ('focus', e))
			matrix = None
		try:
			rotation_center = client.retrieveRotationCenter(tem, high_tension, magnification, probe)
		except Exception as e:
			self.logger.warning(m % ('rotation center', e))
			rotation_center = None
		client = self.calibration_clients['eucentric focus']
		try:
			eucentric_focus_data = client.researchEucentricFocus(high_tension, magnification, probe, tem=tem, ccdcamera=ccd_camera)
			eucentric_focus = eucentric_focus_data['focus']
		except Exception as e:
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

	def saveCalibration(self, matrix, parameter, ht, mag, tem, ccdcamera, probe):
		self.btcalclient.storeMatrix(ht, mag, parameter, matrix, tem, ccdcamera, probe)
		self.logger.info('%s matrix is saved for %s probe' % (parameter, probe))

	def saveFocusCalibration(self, calibration, parameter, high_tension, magnification, tem, ccd_camera, probe):
		matrix, rotation_center, eucentric_focus = calibration
		client = self.calibration_clients['beam tilt']
		client.storeMatrix(high_tension, magnification, parameter, matrix, tem, ccd_camera, probe)
		client.storeRotationCenter(tem, high_tension, magnification, probe, rotation_center)
		client = self.calibration_clients['eucentric focus']
		client.publishEucentricFocus(high_tension, magnification, probe, eucentric_focus)

#--------manual coma-free dialog
	def getBeamTiltList(self):
		tiltlist = []
		anglelist = []
		radlist = []

		tiltlist.append({'x':0.0,'y':0.0})
		anglelist.append(None)

		self.sites = 4
		angleinc = 2*3.14159/self.sites
		startangle = 0
		for i in range(0,self.sites):
			tilt = self.settings['imageshift coma tilt']
			angle = i * angleinc + startangle
			anglelist.append(angle)
			bt = {}
			bt['x']=math.cos(angle)*tilt
			bt['y']=math.sin(angle)*tilt
			tiltlist.append(bt)
		return tiltlist, anglelist

	def initTableau(self):
		self.tableauimages = []
		self.tableauangles = []
		self.tableaurads = []
		self.tabimage = None

	def binPower(self, image, binning=1):
		pow = imagefun.power(image)
		binned = imagefun.bin(pow, binning)
		return binned

	def acquireTableauImages(self):
		oldbt = self.instrument.tem.BeamTilt
		oldstig = self.instrument.tem.Stigmator['objective']
		tiltlist,anglelist = self.getBeamTiltList()
		rad = 1 #radius step.  Fixed at 1 for this

		## initialize a new tableau
		self.initTableau()
		ht = self.instrument.tem.HighTension
		scope = leginondata.ScopeEMData(tem=self.instrument.getTEMData())
		for i, bt in enumerate(tiltlist):
			newbt = {'x': oldbt['x'] + bt['x'], 'y': oldbt['y'] + bt['y']}
			scope['beam tilt'] = newbt
			# acquire image with scope state but not display in node image panel
			imagedata = self.btcalclient.acquireImage(scope, settle=0.0, correct_tilt=False, corchannel=0, display=False)
			self.setManualComaFreeImage(imagedata['image'])
			self.insertTableau(imagedata, anglelist[i], rad)
			self.renderTableau()
		self.instrument.tem.BeamTilt = oldbt

	def setManualComaFreeImage(self,imagearray):
		self.panel.setManualComaFreeImage(imagearray, 'Image')

	def insertTableau(self, imagedata, angle, rad):
		image = imagedata['image']
		binning = 4
		binned = self.binPower(image, binning)
		self.tableauimages.append(binned)
		self.tableauangles.append(angle)
		self.tableaurads.append(rad)

	def renderTableau(self):
		if not self.tableauimages:
			return
		size = self.tableauimages[0].shape[0]
		radinc = numpy.sqrt(2 * size * size)
		tab = tableau.Tableau()
		for i,im in enumerate(self.tableauimages):
			ang = self.tableauangles[i]
			rad = radinc * self.tableaurads[i]
			tab.insertImage(im, angle=ang, radius=rad)
		self.tabimage,self.tabscale = tab.render()
		self.displayTableau()

	def displayTableau(self):
		self.panel.setManualComaFreeImage(self.tabimage, 'Tableau')

	def applyTiltChange(self, deltabt):
			oldbt = self.instrument.tem.BeamTilt
			self.logger.info('Old beam tilt: %.4f, %.4f' % (oldbt['x'],oldbt['y'],))
			newbt = {'x': oldbt['x'] + deltabt['x'], 'y': oldbt['y'] + deltabt['y']}
			self.instrument.tem.BeamTilt = newbt
			self.logger.info('New beam tilt: %.4f, %.4f' % (newbt['x'],newbt['y'],))

	def applyTiltChangeAndReacquireTableau(self,deltabt):
			self.applyTiltChange(deltabt)
			self.acquireTableauImages()
			newbt = self.instrument.tem.BeamTilt
			self.logger.info('Final beam tilt: %.4f, %.4f' % (newbt['x'],newbt['y'],))

	def navigate(self, xy):
		'''
		Calculate the new beam tilt center and then aquire new tableau images.
		This is triggered by clicking at a position in  ManualComaFree_Dialog Tableau Image.
		'''
		clickrow = xy[1]
		clickcol = xy[0]
		try:
			clickshape = self.tabimage.shape
		except:
			self.logger.warning('Can not navigate without a tableau image')
			return
		# calculate delta from image center
		centerr = clickshape[0] / 2.0 - 0.5
		centerc = clickshape[1] / 2.0 - 0.5
		deltarow = clickrow - centerr
		deltacol = clickcol - centerc
		bt = {}
		if self.tabscale is not None:
			bt['x'] = deltacol * self.settings['imageshift coma tilt']/self.tabscale
			bt['y'] = -deltarow * self.settings['imageshift coma tilt']/self.tabscale
			self.applyTiltChangeAndReacquireTableau(bt)
		else:
			self.logger.warning('need more than one beam tilt images in tableau to navigate')

	#--------------Manual Focus---------------
	def acquireManualFocusImage(self):
		scope={}
		# acquire image but not display in node image panel
		imagedata = self.btcalclient.acquireImage(scope, settle=0.0, correct_tilt=False, corchannel=0, display=False)
		# thread to make it possible to acquire the next image before this one is displayed.
		threading.Thread(target=self.setManualFocusImage(imagedata['image'])).start()

	def setManualFocusImage(self,imagearray):
		self.maskradius = 0.01
		self.panel.setManualFocusImage(imagearray, 'Image')
		power = imagefun.power(imagearray, self.maskradius)
		self.man_power = power.astype(numpy.float32)
		self.panel.setManualFocusImage(self.man_power, 'Power')

	def manualFocusLoop(self):
		## go to preset and target
		#pixelsize,center = self.getReciprocalPixelSizeFromPreset(presetname)
		#self.ht = self.instrument.tem.HighTension
		#self.cs = self.getTEMCsValue()
		#self.panel.onNewPixelSize(pixelsize,center,self.ht,self.cs)
		self.logger.info('Starting manual focus loop...')
		self.beep()
		self.manualplayer.play()
		#self.onManualCheck()
		while True:
			state = self.manualplayer.state()
			if state == 'stop':
				break
			elif state == 'pause':
				if self.manualplayer.wait() == 'stop':
					break
			# acquire image, show image and power spectrum
			# allow user to adjust defocus and stig
			self.acquireManualFocusImage()
