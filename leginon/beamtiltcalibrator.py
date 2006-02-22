#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
'''
'''

import calibrator
try:
	import numarray as Numeric
	import numarray.linear_algebra as LinearAlgebra
except:
	import Numeric
	import LinearAlgebra
import data
import calibrationclient
import node
import gui.wx.BeamTiltCalibrator

class BeamTiltCalibrator(calibrator.Calibrator):
	'''
	'''
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
	})

	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)

		self.defaultmeasurebeamtilt = 0.01
		self.resultvalue = None

		self.calclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.euclient = calibrationclient.EucentricFocusClient(self)

		self.start()

	def btFromScope(self):
		## get current value of beam tilt
		estr = 'Unable to get beam tilt: %s'
		try:
			tem = self.instrument.getTEMData()
			cam = self.instrument.getCCDCameraData()
			ht = self.instrument.tem.HighTension
			mag = self.instrument.tem.Magnification
			beamtilt = self.instrument.tem.BeamTilt
		except:
			self.logger.error(estr % 'unable to get instrument state')
			self.panel.getInstrumentDone()
			return
		self.calclient.storeRotationCenter(tem, cam, ht, mag, beamtilt)
		self.logger.info('Publishing HT: %s, Mag.: %s, BeamTilt: %s'
											% (ht, mag, beamtilt))
		self.panel.getInstrumentDone()

	def btToScope(self):
		estr = 'Unable to set beam tilt: %s'
		try:
			tem = self.instrument.getTEMData()
			cam = self.instrument.getCCDCameraData()
			ht = self.instrument.tem.HighTension
			mag = self.instrument.tem.Magnification
		except:
			self.logger.error(estr % 'unable to get instrument state')
			self.panel.setInstrumentDone()
			return
		beamtilt = self.calclient.retreiveRotationCenter(tem, cam, ht, mag)
		if beamtilt is None:
			e = 'none saved for HT: %s, Mag.: %s' % (ht, mag)
			self.logger.error(estr % e)
			self.panel.setInstrumentDone()
			return
		try:
			self.instrument.tem.BeamTilt = beamtilt
		except:
			self.logger.error(estr % 'cannot set instrument parameters')
		self.panel.setInstrumentDone()

	def calibrateRotationCenter(self):
		self.btFromScope()

	def FUTUREcalibrateRotationCenter(self, tilt_value):
		'''rotation center alignment'''
		if self.initInstruments():
			return

		state1 = {'beam tilt': tilt_value}
		state2 = {'beam tilt': -tilt_value}

		matdict = {}

		for axis in ('x','y'):
			self.logger.info('Measuring %s tilt' % (axis,))

			diff1 = self.calclient.measureDispDiff(axis, tilt_value, tilt_value)
			diff2 = self.calclient.measureDispDiff(axis, -tilt_value, tilt_value)

			matcol = self.calclient.eq11(diff1, diff2, 0, 0, tilt_value)
			matdict[axis] = matcol

		self.logger.debug('Making matrix...')
		matrix = Numeric.zeros((2,2), Numeric.Float32)
		self.logger.debug('Matrix type %s, matrix dict type %s'
											% (matrix.type(), matdict['x'].type()))
		matrix[:,0] = matdict['x']
		matrix[:,1] = matdict['y']

		## store calibration
		self.logger.info('Storing calibration...')
		mag, mags = self.getMagnification()
		ht = self.getHighTension()
		self.calclient.storeMatrix(ht, mag, 'coma-free', matrix)
		self.logger.info('Calibration stored')
		return ''

	def calibrateDefocus(self, tilt_value, defocus1, defocus2):
		if self.initInstruments():
			return
		state1 = {'defocus': defocus1}
		state2 = {'defocus': defocus2}
		matdict = {}
		for axis in ('x','y'):
			self.logger.info('Measuring %s tilt' % (axis,))
			shifts = self.calclient.measureDisplacements(axis, tilt_value, state1, state2)
			if shifts is None:
				return
			shift1, shift2 = shifts
			matcol = self.calclient.eq11(shift1, shift2, defocus1, defocus2, tilt_value)
			matdict[axis] = matcol
		self.logger.debug('Making matrix...')
		matrix = Numeric.zeros((2,2), Numeric.Float32)
		self.logger.debug('Matrix type %s, matrix dict type %s'
											% (matrix.type(), matdict['x'].type()))

		m00 = float(matdict['x'][0])
		m10 = float(matdict['x'][1])
		m01 = float(matdict['y'][0])
		m11 = float(matdict['y'][1])
		matrix = Numeric.array([[m00,m01],[m10,m11]],Numeric.Float32)

		## store calibration
		self.logger.info('Storing calibration...')
		ht = self.getHighTension()
		mag, mags = self.getMagnification()
		self.logger.debug('Matrix %s, shape %s, type %s, flat %s'
						% (matrix, matrix.shape, matrix.type(), Numeric.ravel(matrix)))
		self.calclient.storeMatrix(ht, mag, 'defocus', matrix)
		self.logger.info('Calibration stored')
		self.logger.info('Calibration completed')
		self.beep()
		return ''

	def calibrateStigmators(self, lens, tilt_value, delta):
		if self.initInstruments():
			return

		currentstig = self.getStigmator(lens)
		## set up the stig states
		stig = {'x':{}, 'y':{}}
		for axis in ('x','y'):
			for sign in ('+','-'):
				stig[axis][sign] = dict(currentstig)
				if sign == '+':
					stig[axis][sign][axis] += delta/2.0
				elif sign == '-':
					stig[axis][sign][axis] -= delta/2.0

		for stigaxis in ('x','y'):
			self.logger.debug('Calculating matrix for stig %s' % (stigaxis,))
			matdict = {}
			for tiltaxis in ('x','y'):
				self.logger.info('Measuring %s tilt' % (tiltaxis,))
				stig1 = stig[stigaxis]['+']
				stig2 = stig[stigaxis]['-']
				state1 = data.ScopeEMData(stigmator={lens:stig1})
				state2 = data.ScopeEMData(stigmator={lens:stig2})
				shift1, shift2 = self.calclient.measureDisplacements(tiltaxis, tilt_value, state1, state2)
				self.logger.info('Pixel shift (1 of 2): (%.2f, %.2f)'
														% (shift1['col'], shift1['row']))
				self.logger.info('Pixel shift (2 of 2): (%.2f, %.2f)'
														% (shift2['col'], shift2['row']))
				stigval1 = stig1[stigaxis]
				stigval2 = stig2[stigaxis]
				matcol = self.calclient.eq11(shift1, shift2, stigval1, stigval2, tilt_value)
				matdict[tiltaxis] = matcol
			matrix = Numeric.zeros((2,2), Numeric.Float32)
			matrix[:,0] = matdict['x']
			matrix[:,1] = matdict['y']

			## store calibration
			self.logger.info('Storing calibration...')
			mag, mags = self.getMagnification()
			ht = self.getHighTension()
			type = lens + stigaxis
			self.calclient.storeMatrix(ht, mag, type, matrix)
			self.logger.info('Calibration stored')

		## return to original stig
		self.instrument.tem.Stigmator = {lens: currentstig}
		self.logger.info('Calibration completed')
		self.beep()
		return ''

	def measureDefocusStig(self, btilt, stig, correct_tilt=False):
		if self.initInstruments():
			return
		try:
			ret = self.calclient.measureDefocusStig(btilt, stig=stig, correct_tilt=correct_tilt)
		except Exception, e:
			self.logger.exception('Measure defocus failed: %s' % e)
			ret = {}
		self.logger.info('RET %s' % ret)
		return ret

	def getStigmator(self, lens):
		return self.instrument.tem.Stigmator[lens]

	def uiCalibrateDefocus(self):
		self.calibrateDefocus(self.settings['defocus beam tilt'],
													self.settings['first defocus'],
													self.settings['second defocus'])
		self.panel.calibrationDone()

	def uiCalibrateStigmators(self):
		self.calibrateStigmators(self.settings['stig lens'], self.settings['stig beam tilt'],
															self.settings['stig delta'])
		self.panel.calibrationDone()

	def uiMeasureDefocusStig(self, btilt, correct_tilt):
		result = self.measureDefocusStig(btilt, stig=self.settings['stig lens'], correct_tilt=correct_tilt)
		self.resultvalue = result
		self.panel.measurementDone()

	def uiMeasureDefocus(self, btilt):
		result = self.measureDefocusStig(btilt, stig=None)
		self.resultvalue = result
		self.panel.measurementDone()

	def uiCorrectDefocus(self):
		delta = self.resultvalue
		if not delta:
			self.logger.info('No result, you must measure first')
			return
		current = self.getCurrentValues()	

		newdefocus = current['defocus'] + delta['defocus']
		self.instrument.tem.Defocus = newdefocus
		self.panel.setInstrumentDone()

	def uiCorrectStigmator(self):
		delta = self.resultvalue
		if not delta:
			self.logger.info('No result, you must measure first')
			return
		current = self.getCurrentValues()	

		lens = self.settings['stig lens']
		newstigx = current[lens]['x'] + delta['stigx']
		newstigy = current[lens]['y'] + delta['stigy']

		self.instrument.tem.Stigmator = {lens: {'x':newstigx,'y':newstigy}}
		self.panel.setInstrumentDone()

	def uiResetDefocus(self):
		try:
			self.instrument.tem.resetDefocus(True)
		except:
			self.logger.error('Reset defocus failed: unable to set instrument')
		self.panel.setInstrumentDone()

	def getCurrentValues(self):
		defocus = self.instrument.tem.Defocus
		ob = self.instrument.tem.Stigmator['objective']
		dif = self.instrument.tem.Stigmator['diffraction']
		return {'defocus':defocus, 'objective': ob, 'diffraction': dif}

	def eucToScope(self):
		estr = 'Unable to set eucentric focus: %s'
		try:
			ht = self.instrument.tem.HighTension
			mag = self.instrument.tem.Magnification
		except:
			self.logger.error(estr % 'unable to get instrument state')
			self.panel.setInstrumentDone()
			return
		eudata = self.euclient.researchEucentricFocus(ht, mag)
		if eudata is None:
			e = 'none saved for HT: %s, Mag.: %s' % (ht, mag)
			self.logger.error(estr % e)
			self.panel.setInstrumentDone()
			return
		focus = eudata['focus']

		try:
			self.instrument.tem.Focus = focus
		except:
			self.logger.error(estr % 'cannot set instrument parameters')
		self.panel.setInstrumentDone()

	def eucFromScope(self):
		## get current value of focus
		estr = 'Unable to get eucentric focus: %s'
		try:
			ht = self.instrument.tem.HighTension
			mag = self.instrument.tem.Magnification
			focus = self.instrument.tem.Focus
		except:
			self.logger.error(estr % 'unable to get instrument state')
			self.panel.getInstrumentDone()
			return
		self.euclient.publishEucentricFocus(ht, mag, focus)
		self.logger.info('Publishing HT: %s, Mag.: %s, Euc. Focus: %s'
											% (ht, mag, focus))
		self.panel.getInstrumentDone()

	def abortCalibration(self):
		raise NotImplementedError

