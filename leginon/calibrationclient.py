import node, data, event
import Numeric
import LinearAlgebra
import math
import copy
import camerafuncs
import fftengine
import correlator
import peakfinder
import time

class CalibrationClient(object):
	'''
	this is a component of a node that needs to use calibrations
	'''
	def __init__(self, node):
		self.node = node
		self.cam = node.cam

		ffteng = fftengine.fftNumeric()
		#ffteng = fftengine.fftFFTW(planshapes=(), estimate=1)
		self.correlator = correlator.Correlator(ffteng)
		self.peakfinder = peakfinder.PeakFinder()
		self.settle = 1.5

	def getCalibration(self, key):
		try:
			calkey = ('calibrations', key)
			cal = self.node.researchByDataID(calkey)
		except node.ResearchError:
			print 'CalibrationClient unable to find calibrations. Maybe CalibrationLibrary is not available.'
			raise

		calvalue = cal.content
		return calvalue

	def setCalibration(self, key, calibration):
		dat = data.CalibrationData(('calibrations',key), calibration)
		self.node.publishRemote(dat)

	def magCalibrationKey(self, magnification, caltype):
		'''
		this determines the key in the main calibrations dict
		where a magnification dependent calibration is located
		'''
		return str(int(magnification)) + caltype

	def acquireStateImage(self, state):
		## acquire image at this state
		newemdata = data.EMData('scope', state)
		self.node.publish(event.LockEvent(self.node.ID()))
		self.node.publishRemote(newemdata)
		print 'state settling time %s' % (self.settle,)
		time.sleep(self.settle)

		print 'XXXXXXXXXXXXXXXXXX', self, self.node
		imagedata = self.cam.acquireCameraImageData()
		actual_state = imagedata.content['scope']
		self.node.publish(imagedata, event.CameraImagePublishEvent)

		## should find image stats to help determine validity of image
		## in correlations
		image_stats = None

		info = {'requested state': state, 'imagedata': imagedata, 'image stats': image_stats}
		return info

	def measureStateShift(self, state1, state2):
		'''
		Measures the pixel shift between two states
		 Returned dict has these keys:
		    'actual states': tuple with the actual scope states
		    'pixel shift': the resulting pixel shift, 'row', and 'col'
		    'peak value': cross correlation peak value
		    'shape': shape of acquired images
		    'stats': statistics of two images acquired (not implemented)
		'''

		print 'acquiring state images'
		info1 = self.acquireStateImage(state1)
		info2 = self.acquireStateImage(state2)

		imagedata1 = info1['imagedata']
		imagedata2 = info2['imagedata']
		imagecontent1 = imagedata1.content
		imagecontent2 = imagedata2.content
		stats1 = info1['image stats']
		stats2 = info2['image stats']

		actual1 = imagecontent1['scope']
		actual2 = imagecontent2['scope']
		actual = (actual1, actual2)

		shiftinfo = {}

		numimage1 = imagecontent1['image']
		numimage2 = imagecontent2['image']

		self.correlator.insertImage(numimage1)
		self.correlator.insertImage(numimage2)
		print 'correlation'
		pcimage = self.correlator.phaseCorrelate()
		pcimagedata = data.PhaseCorrelationImageData(self.node.ID(), pcimage, imagedata1.id, imagedata2.id)

		#self.publish(pcimagedata, event.PhaseCorrelationImagePublishEvent)

		## peak finding
		print 'peak finding'
		self.peakfinder.setImage(pcimage)
		self.peakfinder.subpixelPeak()
		peak = self.peakfinder.getResults()
		peakvalue = peak['subpixel peak value']
		shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)

		## need unbinned result
		binx = imagecontent1['camera']['binning']['x']
		biny = imagecontent1['camera']['binning']['y']
		unbinned = {'row':shift[0] * biny, 'col': shift[1] * binx}

		shiftinfo.update({'actual states': actual, 'pixel shift': unbinned, 'peak value': peakvalue, 'shape':pcimage.shape, 'stats': (stats1, stats2)})
		return shiftinfo


class BeamTiltCalibrationClient(CalibrationClient):
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def setCalibration(self, key, calibration):
		dat = data.MatrixCalibrationData(('calibrations',key), calibration)
		self.node.publishRemote(dat)

	def getMatrix(self, mag, type):
		key = self.magCalibrationKey(mag, type)
		matrix = self.getCalibration(key)
		return matrix

	def setMatrix(self, mag, type, matrix):
		key = self.magCalibrationKey(mag, type)
		self.setCalibration(key, matrix)

	def getBeamTilt(self):
		emdata = self.node.researchByDataID('beam tilt')
		beamtilt = emdata.content
		return beamtilt

	def measureDefocusStig(self, tilt_value):
		emdata = self.node.researchByDataID('magnification')
		mag = emdata.content['magnification']
		fmatrix = self.getMatrix(mag, 'defocus')
		amatrix = self.getMatrix(mag, 'stigx')
		bmatrix = self.getMatrix(mag, 'stigy')

		tiltcenter = self.getBeamTilt()

		### need two tilt displacement measurements
		### easiest is one on each tilt axis
		shifts = {}
		tilts = {}
		for tiltaxis in ('x','y'):
			state1 = copy.deepcopy(tiltcenter)
			state1['beam tilt'][tiltaxis] -= (tilt_value/2.0)
			state2 = copy.deepcopy(tiltcenter)
			state2['beam tilt'][tiltaxis] += (tilt_value/2.0)
			shiftinfo = self.measureStateShift(state1, state2)
			pixshift = shiftinfo['pixel shift']

			shifts[tiltaxis] = (pixshift['row'], pixshift['col'])
			if tiltaxis == 'x':
				tilts[tiltaxis] = (tilt_value, 0)
			else:
				tilts[tiltaxis] = (0, tilt_value)

		## return to original beam tilt
		emdata = data.EMData('scope', tiltcenter)
		self.node.publishRemote(emdata)

		print 'TILTS'
		print tilts
		print 'SHIFTS'
		print shifts

		d1 = shifts['x']
		t1 = tilts['x']
		d2 = shifts['y']
		t2 = tilts['y']
		sol = self.solveEq10(fmatrix,amatrix,bmatrix,d1,t1,d2,t2)
		print sol
		return sol

	def solveEq10(self, F, A, B, d1, t1, d2, t2):
		'''
		This solves Equation 10 from Koster paper
		 F,A,B are the defocus, stigx, and stigy calibration matrices
		   (all must be 2x2 Numeric arrays)
		 d1,d2 are displacements resulting from beam tilts t1,t2
		   (all must be 2x1 Numeric arrays)
		'''
		
		## produce the matrix and vector for least squares fit
		v = Numeric.zeros((4,), Numeric.Float64)
		v[:2] = d1
		v[2:] = d2

		## plug calibration matrices and tilt vectors into M
		M = Numeric.zeros((4,3), Numeric.Float64)

		# t1 on first two rows
		M[:2,0] = Numeric.matrixmultiply(F,t1)
		M[:2,1] = Numeric.matrixmultiply(A,t1)
		M[:2,2] = Numeric.matrixmultiply(B,t1)
		# t2 on second two rows
		M[2:,0] = Numeric.matrixmultiply(F,t2)
		M[2:,1] = Numeric.matrixmultiply(A,t2)
		M[2:,2] = Numeric.matrixmultiply(B,t2)

		solution = LinearAlgebra.linear_least_squares(M, v)
		result = {
			'defocus': solution[0][0],
			'stigx': solution[0][1],
			'stigy': solution[0][2],
			}
		return result

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
		self.node.publishRemote(emdata)

		return (pixelshift1, pixelshift2)

class MatrixCalibrationClient(CalibrationClient):
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def parameter(self):
		'''
		returns a scope key for the calibrated parameter
		'''
		raise NotImplementedError()

	def setCalibration(self, magnification, measurement):
		key = self.magCalibrationKey(magnification, self.parameter())
		mat = self.measurementToMatrix(measurement)
		dat = data.MatrixCalibrationData(('calibrations',key), mat)
		self.node.publishRemote(dat)

	def measurementToMatrix(self, measurement):
		'''
		convert a mesurement in pixels/[TEM parameter] to a matrix
		in [TEM parameter]/pixel
		'''
		xrow = measurement['x']['row']
		xcol = measurement['x']['col']
		yrow = measurement['y']['row']
		ycol = measurement['y']['col']
		matrix = Numeric.array([[xrow,yrow],[xcol,ycol]],Numeric.Float32)
		matrix = LinearAlgebra.inverse(matrix)
		return matrix

	def matrixAnglePixsize(self, scope, camera):
		mag = scope['magnification']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = self.parameter()

		key = self.magCalibrationKey(mag, par)
		matrix = self.getCalibration(key)

		xvect = matrix[:,0]
		yvect = matrix[:,1]

		xangle = math.atan2(xvect[0], xvect[1])
		xpixsize = math.hypot(xvect[0], xvect[1])
		yangle = math.atan2(yvect[0], yvect[1])
		ypixsize = math.hypot(yvect[0], yvect[1])
		ret = {}
		ret['x'] = {'angle': xangle,'pixel size': xpixsize}
		ret['y'] = {'angle': yangle,'pixel size': ypixsize}
		return ret

	def transform(self, pixelshift, scope, camera):
		'''
		Calculate a new scope state from the given pixelshift
		The input scope and camera state should refer to the image
		from which the pixelshift originates
		'''
		mag = scope['magnification']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = self.parameter()

		pixrow = pixelshift['row'] * biny
		pixcol = pixelshift['col'] * binx
		pixvect = (pixrow, pixcol)

		key = self.magCalibrationKey(mag, par)
		matrix = self.getCalibration(key)
		change = Numeric.matrixmultiply(matrix, pixvect)
		changex = change[0]
		changey = change[1]

		new = copy.deepcopy(scope)
		new[par]['x'] += changex
		new[par]['y'] += changey

		return new

	def itransform(self, shift, scope, camera):
		'''
		Calculate a pixel vector from an image center which 
		represents the given parameter shift.
		'''
		mag = scope['magnification']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = self.parameter()

		vect = (shift['x'], shift['y'])

		key = self.magCalibrationKey(mag, par)
		matrix = self.getCalibration(key)
		matrix = LinearAlgebra.inverse(matrix)

		pixvect = Numeric.matrixmultiply(matrix, vect)
		pixvect /= (biny, binx)
		return {'row':pixvect[0], 'col':pixvect[1]}


class ImageShiftCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		return 'image shift'

class BeamShiftCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		return 'beam shift'

class StageCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		return 'stage position'


import gonmodel
class ModeledStageCalibrationClient(CalibrationClient):
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def setMagCalibration(self, magnification, mag_dict):
		key = self.magCalibrationKey(magnification, 'modeled stage position')
		try:
			old_mag_dict = self.getCalibration(key)
			for dictkey in old_mag_dict:
				old_mag_dict[dictkey].update(mag_dict[dictkey])
		except KeyError:
			old_mag_dict = copy.deepcopy(mag_dict)

		self.setCalibration(key, old_mag_dict)

	def getMagCalibration(self, magnification):
		key = self.magCalibrationKey(magnification, 'modeled stage position')
		return self.getCalibration(key)

	def setModel(self, axis, mod_dict):
		key = axis + ' stage position model'
		self.setCalibration(key, mod_dict)

	def getModel(self, axis):
		key = axis + ' stage position model'
		return self.getCalibration(key)

	def transform(self, pixelshift, scope, camera):
		curstage = scope['stage position']

		binx = camera['binning']['x']
		biny = camera['binning']['y']
		pixrow = pixelshift['row'] * biny
		pixcol = pixelshift['col'] * binx

		## do modifications to newstage here
		xmod_dict = self.getModel('x')
		ymod_dict = self.getModel('y')
		mag_dict = self.getMagCalibration(scope['magnification'])
		delta = self.pixtix(xmod_dict, ymod_dict, mag_dict, curstage['x'], curstage['y'], pixcol, pixrow)

		newscope = copy.deepcopy(scope)
		newscope['stage position']['x'] += delta['x']
		newscope['stage position']['y'] += delta['y']
		return newscope

	def pixtix(self, xmod_dict, ymod_dict, mag_dict, gonx, gony, pixx, pixy):
		xmod = gonmodel.GonModel()
		ymod = gonmodel.GonModel()
	
		xmod.fromDict(xmod_dict)
		ymod.fromDict(ymod_dict)
	
		modavgx = mag_dict['model mean']['x']
		modavgy = mag_dict['model mean']['y']
		anglex = mag_dict['data angle']['x']
		angley = mag_dict['data angle']['y']
	
		gonx1 = xmod.rotate(anglex, pixx, pixy)
		gony1 = ymod.rotate(angley, pixx, pixy)
	
		gonx1 = gonx1 * modavgx
		gony1 = gony1 * modavgy
	
		gonx1 = xmod.predict(gonx,gonx1)
		gony1 = ymod.predict(gony,gony1)
	
		return {'x':gonx1, 'y':gony1}
	
	def pixelShift(self, ievent):
		mag = ievent.content['magnification']
		delta_row = ievent.content['row']
		delta_col = ievent.content['column']

		current = self.getStagePosition()
		print 'current before delta', current
		curx = current['stage position']['x']
		cury = current['stage position']['y']

		xmodfile = self.modfilename('x')
		ymodfile = self.modfilename('y')
		magfile = self.magfilename(mag)

		deltagon = self.pixtix(xmodfile,ymodfile,magfile,curx,cury,delta_col,delta_row)

		current['stage position']['x'] += deltagon['x']
		current['stage position']['y'] += deltagon['y']
		print 'current after delta', current

		stagedata = data.EMData('scope', current)
		self.publishRemote(stagedata)
