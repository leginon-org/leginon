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
	def __init__(self, id, nodelocations, **kwargs):
		calibrator.Calibrator.__init__(self, id, nodelocations, **kwargs)

		self.settle = 1.0

		## default camera config
		currentconfig = self.cam.config()
		currentconfig['state']['dimension']['x'] = 1024
		currentconfig['state']['binning']['x'] = 4
		currentconfig['state']['exposure time'] = 500
		self.cam.config(currentconfig)

		self.calclient = calibrationclient.BeamTiltCalibrationClient(self)

		self.defineUserInterface()
		self.start()

	def setCamState(self):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		self.cam.state(camstate)

	def calibrateAlignment(self):
		pass

	def calibrateDefocus(self, tilt_value, defocus1, defocus2):
		self.setCamState()
		state1 = {'defocus': defocus1}
		state2 = {'defocus': defocus2}
		matdict = {}
		for axis in ('x','y'):
			print 'measuring %s tilt' % (axis,)
			shift1, shift2 = self.measureDisplacements(axis, tilt_value, state1, state2)
			matcol = self.eq11(shift1, shift2, defocus1, defocus2, tilt_value)
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
		self.calclient.setMatrix(mag, 'defocus', matrix)
		return ''

	def calibrateStigmators(self, tilt_value, delta):
		self.setCamState()

		currentstig = self.getStigmator()
		print 'CURRENT', currentstig
		## set up the stig states
		stig = {'x':{}, 'y':{}}
		for axis in ('x','y'):
			for sign in ('+','-'):
				stig[axis][sign] = copy.deepcopy(currentstig)
				if sign == '+':
					stig[axis][sign]['stigmator']['objective'][axis] += delta/2.0
				elif sign == '-':
					stig[axis][sign]['stigmator']['objective'][axis] -= delta/2.0
		print 'STIG', stig

		for stigaxis in ('x','y'):
			print 'calculating matrix for stig %s' % (stigaxis,)
			matdict = {}
			for tiltaxis in ('x','y'):
				print 'measuring %s tilt' % (tiltaxis,)
				state1 = stig[stigaxis]['+']
				state2 = stig[stigaxis]['-']
				shift1, shift2 = self.measureDisplacements(tiltaxis, tilt_value, state1, state2)
				print 'shift1', shift1
				print 'shift2', shift2
				stigval1 = state1['stigmator']['objective'][stigaxis]
				stigval2 = state2['stigmator']['objective'][stigaxis]
				matcol = self.eq11(shift1, shift2, stigval1, stigval2, tilt_value)
				matdict[tiltaxis] = matcol
			matrix = Numeric.zeros((2,2), Numeric.Float32)
			matrix[:,0] = matdict['x']
			matrix[:,1] = matdict['y']

			## store calibration
			mag = self.getMagnification()
			type = 'stig' + stigaxis
			self.calclient.setMatrix(mag, type, matrix)

		return ''

	def measureDisplacements(self, tilt_axis, tilt_value, state1, state2):
		'''
		This measures the displacements that go into eq. (11)
		Each call of this function acquires four images
		and returns two shift displacements.
		'''
		
		beamtilt = self.getBeamTilt()
		print 'BEAMTILT', beamtilt
		beamtilts = (copy.deepcopy(beamtilt),copy.deepcopy(beamtilt))
		beamtilts[0]['beam tilt'][tilt_axis] += tilt_value
		beamtilts[1]['beam tilt'][tilt_axis] -= tilt_value

		## set up to measure states
		states1 = (copy.deepcopy(state1), copy.deepcopy(state1))
		states2 = (copy.deepcopy(state2), copy.deepcopy(state2))

		states1[0].update(beamtilts[0])
		states1[1].update(beamtilts[1])

		states2[0].update(beamtilts[0])
		states2[1].update(beamtilts[1])

		print 'STATES1'
		print states1
		shiftinfo = self.measureStateShift(states1[0], states1[1])
		pixelshift1 = shiftinfo['pixel shift']
		print 'shiftinfo'
		print shiftinfo

		print 'STATES2'
		print states2
		shiftinfo = self.measureStateShift(states2[0], states2[1])
		pixelshift2 = shiftinfo['pixel shift']
		print 'shiftinfo'
		print shiftinfo

		## return to original beam tilt
		emdata = data.EMData('scope', beamtilt)
		self.publishRemote(emdata)

		return (pixelshift1, pixelshift2)


	def getBeamTilt(self):
		emdata = self.researchByDataID('beam tilt')
		beamtilt = emdata.content
		return beamtilt

	def getDefocus(self):
		emdata = self.researchByDataID('defocus')
		defocus = emdata.content
		return defocus

	def getStigmator(self):
		emdata = self.researchByDataID('stigmator')
		defocus = emdata.content
		return defocus

	## equation (11)
	def eq11(self, shift1, shift2, param1, param2, beam_tilt):
		'''
		Equation (11)
		Calculates one column of a beam tilt calibration matrix given
		the following arguments:
		  shift1 - pixel shift resulting from tilt at param1
		  shift2 - pixel shift resulting from tilt at param2
		  beam_tilt - value of the induced beam tilt
		  param1 - value of microscope parameter causing 1
		'''
		d1 = Numeric.array((shift1['row'],shift1['col']), Numeric.Float32)
		d1.shape = (2,)
		d2 = Numeric.array((shift2['row'],shift2['col']), Numeric.Float32)
		d2.shape = (2,)
		ddiff = d2 - d1

		scale = 1.0 / (2 * (param2 - param1) * beam_tilt)

		matrixcolumn = scale * ddiff
		return matrixcolumn.astype(Numeric.Float32)

	def defineUserInterface(self):
		calspec = calibrator.Calibrator.defineUserInterface(self)

		camconfig = self.cam.configUIData()

		argspec = (
			self.registerUIData('Tilt Value', 'float', default=0.01),
			self.registerUIData('Defocus 1', 'float', default=-1e-6),
			self.registerUIData('Defocus 2', 'float', default=-2e-6)
			)
		caldefocus = self.registerUIMethod(self.calibrateDefocus, 'Calibrate Defocus', argspec)

		argspec = (
			self.registerUIData('Tilt Value', 'float', default=0.01),
			self.registerUIData('Stig Delta', 'float', default=0.01),
			)
		calstig = self.registerUIMethod(self.calibrateStigmators, 'Calibrate Stigmators', argspec)
		calcont = self.registerUIContainer('Calibrate', (caldefocus, calstig))

		self.registerUISpec('Beam Tilt Calibrator', (calcont, camconfig, calspec,))



