'''
'''

import calibrator
import Numeric
import LinearAlgebra
import copy

class BeamTiltCalibrator(calibrator.Calibrator):
	'''
	'''
	def __init__(self, id, nodelocations, **kwargs):
		calibrator.Calibrator.__init__(self, id, nodelocations, **kwargs)

	def calibrate(self):
		for tiltaxis in ('x','y'):
			for param in twoparams:
				self.measureStateShift()

	
		calMatrixColumn()
		calMatrixColumn()

	def measureDisplacement(self, tilt_axis, tilt_value, state1, state2):
		'''
		This measures the displacements that go into eq. (11)
		Each call of this function acquires four images
		and returns two shift displacements.
		'''
		
		beamtilt = self.getBeamTilt()
		beamtilts = (copy.deepcopy(beamtilt),copy.deepcopy(beamtilt))
		beamtilts[0][tilt_axis] += tilt_value
		beamtilts[1][tilt_axis] -= tilt_value

		## set up to measure states
		states1 = (copy.deepcopy(state1), copy.deepcopy(state1))
		states2 = (copy.deepcopy(state2), copy.deepcopy(state2))

		states1[0].update(beamtilts[0])
		states1[1].update(beamtilts[1])

		states2[0].update(beamtilts[0])
		states2[1].update(beamtilts[1])

		shiftinfo = self.measureStateShifts(states1[0], states1[1])
		pixelshift = shiftinfo['pixel shift']

		shiftinfo = self.measureStateShifts(states1[0], states1[1])
		pixelshift = shiftinfo['pixel shift']


	def getBeamTilt(self):
		emdata = self.researchByDataID('beam tilt')
		beamtilt = emdata.content['beam tilt']
		return beamtilt

	def getDefocus(self):
		emdata = self.researchByDataID('defocus')
		defocus = emdata.content['defocus']
		return defocus

	def getStigmator(self):
		emdata = self.researchByDataID('stigmator')
		defocus = emdata.content['stigmator']['objective']
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
		d1 = Numeric.array((shift1['row'],shift1['col']))
		d1.shape = (2,)
		d2 = Numeric.array((shift2['row'],shift2['col']))
		d2.shape = (2,)
		ddiff = d2 - d1

		scale = 1.0 / (2 * (param2 - param1) * beam_tilt)

		matrixcolumn = scale * ddiff
		return matrixcolumn
