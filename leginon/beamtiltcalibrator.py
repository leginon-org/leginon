'''
'''

import calibrator
import Numeric
import LinearAlgebra
import copy
import data
import calibrationclient

class BeamTiltCalibrator(calibrator.Calibrator):
	'''
	'''
	def __init__(self, id, session, nodelocations, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, nodelocations, **kwargs)


		self.calclient = calibrationclient.BeamTiltCalibrationClient(self)

		## default camera config
		currentconfig = self.cam.config()
		currentconfig['state']['dimension']['x'] = 1024
		currentconfig['state']['binning']['x'] = 4
		currentconfig['state']['exposure time'] = 500
		currentconfig['correct'] = 1
		self.cam.config(currentconfig)


		self.defineUserInterface()
		self.start()

	def setCamState(self):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		self.cam.state(camstate)

	def calibrateAlignment(self, tilt_value):
		self.setCamState()

		state1 = {'beam tilt': tilt_value}
		state2 = {'beam tilt': -tilt_value}

		matdict = {}

		for axis in ('x','y'):
			print 'measuring %s tilt' % (axis,)

			diff1 = self.calclient.measureDispDiff(axis, tilt_value, tilt_value)
			diff2 = self.calclient.measureDispDiff(axis, -tilt_value, tilt_value)

			matcol = self.calclient.eq11(diff1, diff2, 0, 0, tilt_value)
			matdict[axis] = matcol

		print 'making matrix'
		matrix = Numeric.zeros((2,2), Numeric.Float32)
		print 'matrix type', matrix.typecode()
		print 'matdict type', matdict['x'].typecode()
		matrix[:,0] = matdict['x']
		matrix[:,1] = matdict['y']

		## store calibration
		print 'storing calibration'
		mag = self.getMagnification()
		self.calclient.storeMatrix(mag, 'coma-free', matrix)
		return ''

	def calibrateDefocus(self, tilt_value, defocus1, defocus2):
		self.setCamState()
		state1 = {'defocus': defocus1}
		state2 = {'defocus': defocus2}
		matdict = {}
		for axis in ('x','y'):
			print 'measuring %s tilt' % (axis,)
			shift1, shift2 = self.calclient.measureDisplacements(axis, tilt_value, state1, state2)
			matcol = self.calclient.eq11(shift1, shift2, defocus1, defocus2, tilt_value)
			matdict[axis] = matcol
		print 'making matrix'
		matrix = Numeric.zeros((2,2), Numeric.Float32)
		print 'matdict type', matdict['x'].typecode()

		m00 = float(matdict['x'][0])
		m10 = float(matdict['x'][1])
		m01 = float(matdict['y'][0])
		m11 = float(matdict['y'][1])
		matrix = Numeric.array([[m00,m01],[m10,m11]],Numeric.Float32)

		## store calibration
		print 'storing calibration'
		mag = self.getMagnification()
		print 'MATRIX', matrix
		print 'MATRIX shape', matrix.shape
		print 'MATRIX type', matrix.typecode()
		print 'MATRIX flat', Numeric.ravel(matrix)
		self.calclient.storeMatrix(mag, 'defocus', matrix)
		return ''

	def calibrateStigmators(self, tilt_value, delta):
		self.setCamState()

		currentstig = self.getStigmator()
		## set up the stig states
		stig = {'x':{}, 'y':{}}
		for axis in ('x','y'):
			for sign in ('+','-'):
				stig[axis][sign] = copy.deepcopy(currentstig)
				if sign == '+':
					stig[axis][sign]['stigmator']['objective'][axis] += delta/2.0
				elif sign == '-':
					stig[axis][sign]['stigmator']['objective'][axis] -= delta/2.0

		for stigaxis in ('x','y'):
			print 'calculating matrix for stig %s' % (stigaxis,)
			matdict = {}
			for tiltaxis in ('x','y'):
				print 'measuring %s tilt' % (tiltaxis,)
				state1 = stig[stigaxis]['+']
				state2 = stig[stigaxis]['-']
				shift1, shift2 = self.calclient.measureDisplacements(tiltaxis, tilt_value, state1, state2)
				print 'shift1', shift1
				print 'shift2', shift2
				stigval1 = state1['stigmator']['objective'][stigaxis]
				stigval2 = state2['stigmator']['objective'][stigaxis]
				matcol = self.calclient.eq11(shift1, shift2, stigval1, stigval2, tilt_value)
				matdict[tiltaxis] = matcol
			matrix = Numeric.zeros((2,2), Numeric.Float32)
			matrix[:,0] = matdict['x']
			matrix[:,1] = matdict['y']

			## store calibration
			mag = self.getMagnification()
			type = 'stig' + stigaxis
			self.calclient.storeMatrix(mag, type, matrix)

		return ''

	def measureDefocusStig(self, btilt):
		conf = self.cam.config()
		self.cam.state(conf['state'])
		ret = self.calclient.measureDefocusStig(btilt)
		print 'RET', ret
		return ret

	def getDefocus(self):
		emdata = self.researchByDataID(('defocus',))
		defocus = emdata['em']
		return defocus

	def getStigmator(self):
		emdata = self.researchByDataID(('stigmator',))
		defocus = emdata['em']
		return defocus

	def defineUserInterface(self):
		calspec = calibrator.Calibrator.defineUserInterface(self)

		camconfig = self.cam.configUIData()

		self.defocustiltvalue = self.registerUIData('Defocus Tilt Value', 'float',
																															default=0.01)
		self.defocus1 = self.registerUIData('Defocus 1', 'float', default=-1e-6)
		self.defocus2 = self.registerUIData('Defocus 2', 'float', default=-2e-6)
		caldefocusmethod = self.registerUIMethod(self.uiCalibrateDefocus,
																					'Calibrate Defocus', ())
		caldefocus = self.registerUIContainer('Calibrate Defocus', (self.defocustiltvalue, self.defocus1, self.defocus2, caldefocusmethod))

		self.stigtiltvalue = self.registerUIData('Stigmator Tilt Value', 'float',
																														default=0.01)
		self.stigdelta = self.registerUIData('Stigmator Delta', 'float',
																												default=0.01)
		calstigmethod = self.registerUIMethod(self.uiCalibrateStigmators,
																		'Calibrate Stigmators', ())
		calstig = self.registerUIContainer('Calibrate Stigmators', (self.stigtiltvalue, self.stigdelta, calstigmethod))

		self.measuretiltvalue = self.registerUIData('Measure Tilt Value', 'float',
																														default=0.01)
		self.resultvalue = self.registerUIData('Necessary Correction', 'struct')
		measuremethod = self.registerUIMethod(self.uiMeasureDefocusStig,
										'Measure', ())
		measure = self.registerUIContainer('Measure', (self.measuretiltvalue, measuremethod, self.resultvalue))

		calcont = self.registerUIContainer('Calibrate', (caldefocus, calstig, measure))

		myspec = self.registerUISpec('Beam Tilt Calibrator', (calcont, camconfig,))
		myspec += calspec
		return myspec

	def uiCalibrateDefocus(self):
		self.calibrateDefocus(self.defocustiltvalue.get(),
													self.defocus1.get(),
													self.defocus2.get())

	def uiCalibrateStigmators(self):
		self.calibrateStigmators(self.stigtiltvalue.get(),
													self.stigdelta.get())

	def uiMeasureDefocusStig(self):
		result = self.measureDefocusStig(self.measuretiltvalue.get())
		self.resultvalue.set(result)


