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
import sys
import threading

class DriftingTimeout(Exception):
	pass

class Abort(Exception):
	pass

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
		self.abortevent = threading.Event()

	def getHost(self):
		'''
		get the host name of the currently connected EM node
		'''
		## just getting something, anything...
		dat = self.node.researchByDataID(('magnification',))
		## when all I want is the em host
		return dat['em host']

	def checkAbort(self):
		if self.abortevent.isSet():
			raise Abort()

	def acquireStateImage(self, state, publish_image=0, settle=0.0):
		## acquire image at this state
		print 'creating EM data'
		print 'state =', state
		newemdata = data.ScopeEMData(id=('scope',), initializer=state)
#		needs unlock too
#		print 'publishing lock'
#		self.node.publish(event.LockEvent(id=self.node.ID()))
#		print 'publishing EM'
		self.node.publishRemote(newemdata)
		print 'state settling time %s' % (settle,)
		time.sleep(settle)

		#myconfig = self.cam.cameraConfig()
		#imagedata = self.cam.acquireCameraImageData(camconfig=myconfig)
		imagedata = self.cam.acquireCameraImageData()
		actual_state = imagedata['scope']

		if publish_image:
			self.node.publish(imagedata, pubevent=True)
			if self.node.ui_image is not None:
				self.node.ui_image.set(imagedata['image'])

		## should find image stats to help determine validity of image
		## in correlations
		image_stats = None

		info = {'requested state': state, 'imagedata': imagedata, 'image stats': image_stats}
		return info

	def measureStateShift(self, state1, state2, publish_images=0, settle=0.0, checkdrift=False, timeout=None):
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

		info1 = self.acquireStateImage(state1, publish_images, settle)
		imagedata1 = info1['imagedata']
		imagecontent1 = imagedata1
		stats1 = info1['image stats']
		actual1 = imagecontent1['scope']
		self.numimage1 = imagecontent1['image']
		self.correlator.insertImage(self.numimage1)

		## for drift check, continue to acquire at state1
		if checkdrift:
			print 'checking for drift'
			if timeout is None:
				timelimit = None
			else:
				timelimit = time.time() + timeout
			while 1:
				info1 = self.acquireStateImage(state1, publish_images, settle)
				imagedata1 = info1['imagedata']
				imagecontent1 = imagedata1
				stats1 = info1['image stats']
				actual1 = imagecontent1['scope']
				self.numimage1 = imagecontent1['image']
				self.correlator.insertImage(self.numimage1)

				print 'correlation'
				pcimage = self.correlator.phaseCorrelate()

				print 'peak finding'
				self.peakfinder.setImage(pcimage)
				self.peakfinder.subpixelPeak()
				peak = self.peakfinder.getResults()
				print 'PEAK MINSUM', peak['minsum']
				peakvalue = peak['subpixel peak value']
				shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)
				shiftrows = shift[0]
				shiftcols = shift[1]
				d = data.DriftData(id=self.node.ID(), rows=shiftrows, cols=shiftcols)
				self.node.publish(d, database=True)

				drift = abs(shift[0] + 1j * shift[1])
				print 'DRIFT: ', drift
				if drift < 2.0:
					print 'no drift'
					break
				else:
					print 'drift', drift

				self.checkAbort()
				
				if timelimit and time.time() > timelimit:
					raise DriftingTimeout()


#		mrcstr = Mrc.numeric_to_mrcstr(numimage1)
#		self.ui_image1.set(xmlbinlib.Binary(mrcstr))

		self.checkAbort()

		info2 = self.acquireStateImage(state2, publish_images, settle)
		imagedata2 = info2['imagedata']
		imagecontent2 = imagedata2
		stats2 = info2['image stats']
		actual2 = imagecontent2['scope']
		self.numimage2 = imagecontent2['image']
		self.correlator.insertImage(self.numimage2)
#		mrcstr = Mrc.numeric_to_mrcstr(numimage2)
#		self.ui_image2.set(xmlbinlib.Binary(mrcstr))

		actual = (actual1, actual2)
		shiftinfo = {}

		self.checkAbort()

		print 'correlation'
		pcimage = self.correlator.phaseCorrelate()
		#pcimagedata = data.PhaseCorrelationImageData(self.node.ID(), pcimage, imagedata1.id, imagedata2.id)
		pcimagedata = data.PhaseCorrelationImageData(id=self.node.ID(), image=pcimage, subject1=imagedata1, subject2=imagedata2)

		#self.publish(pcimagedata, pubevent=True)

		## peak finding
		print 'peak finding'
		self.peakfinder.setImage(pcimage)
		self.peakfinder.subpixelPeak()
		peak = self.peakfinder.getResults()
		print 'PEAK MINSUM', peak['minsum']
		peakvalue = peak['subpixel peak value']
		shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)

		## need unbinned result
		binx = imagecontent1['camera']['binning']['x']
		biny = imagecontent1['camera']['binning']['y']
		unbinned = {'row':shift[0] * biny, 'col': shift[1] * binx}

		shiftinfo.update({'actual states': actual, 'pixel shift': unbinned, 'peak value': peakvalue, 'shape':pcimage.shape, 'stats': (stats1, stats2)})
		return shiftinfo

#	def configUIData(self):
#		self.ui_image1 = self.registerUIData('Image 1', 'binary', permissions='r')
#		self.ui_image2 = self.registerUIData('Image 2', 'binary', permissions='r')
#		imagespec = self.registerUIContainer('Images', (self.image1, self.image2))
#		return imagespec

class PixelSizeCalibrationClient(CalibrationClient):
	'''
	basic CalibrationClient for accessing a type of calibration involving
	a matrix at a certain magnification
	'''
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def retrievePixelSize(self, mag):
		'''
		finds the requested pixel size using magnification
		'''
		emhost = self.getHost()
		qinst = data.PixelSizeCalibrationData()
		qinst['magnification'] = mag
		qinst['em host'] = emhost
		caldatalist = self.node.research(datainstance=qinst, results=1)

		if len(caldatalist) > 0:
			caldata = caldatalist[0]
		else:
			print 'NO PIXEL SIZE CALIBRATION'
			return None
		pixelsize = caldata['pixelsize']
		return pixelsize

class MatrixCalibrationClient(CalibrationClient):
	'''
	basic CalibrationClient for accessing a type of calibration involving
	a matrix at a certain magnification
	'''
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def retrieveGoodTilt(self, mag):
		qinst = data.GoodTiltCalibrationData(magnification=mag)
		emhost = self.getHost()
		qinst['em host'] = emhost
		caldatalist = self.node.research(datainstance=qinst, results=1)
		if len(caldatalist) > 0:
			caldata = caldatalist[0]
		else:
			return None
		goodtilt = caldata['tilt']
		return goodtilt

	def retrieveMatrix(self, mag, caltype):
		'''
		finds the requested matrix using magnification and type
		'''
		qinst = data.MatrixCalibrationData(magnification=mag, type=caltype)
		emhost = self.getHost()
		qinst['em host'] = emhost
		caldatalist = self.node.research(datainstance=qinst, results=1)

		if len(caldatalist) > 0:
			caldata = caldatalist[0]
		else:
			return None
		matrix = caldata['matrix']
		return matrix

	def storeMatrix(self, mag, type, matrix):
		'''
		stores a new calibration matrix
		'''
		newmatrix = Numeric.array(matrix, Numeric.Float64)
		caldata = data.MatrixCalibrationData(id=self.node.ID(), magnification=mag, type=type, matrix=matrix)
		emhost = self.getHost()
		caldata['em host'] = emhost
		self.node.publish(caldata, database=True)


class BeamTiltCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def getBeamTilt(self):
		emdata = self.node.researchByDataID(('beam tilt',))
		return emdata

	def measureDefocusStig(self, tilt_value, publish_images=0, checkdrift=False, drift_timeout=300):
		self.abortevent.clear()
		emdata = self.node.researchByDataID(('magnification',))
		#mag = emdata.content['magnification']
		mag = emdata['magnification']
		fmatrix = self.retrieveMatrix(mag, 'defocus')
		amatrix = self.retrieveMatrix(mag, 'stigx')
		bmatrix = self.retrieveMatrix(mag, 'stigy')

		goodtilt = self.retrieveGoodTilt(mag)
		if goodtilt is not None:
			tilt_value = goodtilt

		if None in (fmatrix, amatrix, bmatrix):
			raise RuntimeError('missing calibration matrix')

		tiltcenter = self.getBeamTilt()

		### need two tilt displacement measurements
		### easiest is one on each tilt axis
		shifts = {}
		tilts = {}
		self.checkAbort()
		for tiltaxis in ('x','y'):
			state1 = copy.deepcopy(tiltcenter)
			state1['beam tilt'][tiltaxis] -= (tilt_value/2.0)
			state2 = copy.deepcopy(tiltcenter)
			state2['beam tilt'][tiltaxis] += (tilt_value/2.0)
			try:
				shiftinfo = self.measureStateShift(state1, state2, publish_images, settle=0.25, checkdrift=checkdrift, timeout=drift_timeout)
			except Abort:
				break

			pixshift = shiftinfo['pixel shift']

			shifts[tiltaxis] = (pixshift['row'], pixshift['col'])
			if tiltaxis == 'x':
				tilts[tiltaxis] = (tilt_value, 0)
			else:
				tilts[tiltaxis] = (0, tilt_value)
			try:
				self.checkAbort()
			except Abort:
				break

		## return to original beam tilt
		emdata = data.ScopeEMData(id=('scope',), initializer=tiltcenter)
		self.node.publishRemote(emdata)

		self.checkAbort()

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
			'min': float(solution[1][0])
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
		print 'STATE1'
		print state1
		print 'STATE2'
		print state2
		
		beamtilt = self.getBeamTilt()

		### try/finally to be sure we return to original beam tilt
		try:
			print 'BEAMTILT', beamtilt
			beamtilts = (copy.deepcopy(beamtilt),copy.deepcopy(beamtilt))
			beamtilts[0]['beam tilt'][tilt_axis] += tilt_value
			beamtilts[1]['beam tilt'][tilt_axis] -= tilt_value

			## set up to measure states
			states1 = (copy.deepcopy(state1), copy.deepcopy(state1))
			states2 = (copy.deepcopy(state2), copy.deepcopy(state2))

			states1[0]['beam tilt'] = beamtilts[0]['beam tilt']
			states1[1]['beam tilt'] = beamtilts[1]['beam tilt']
			states2[0]['beam tilt'] = beamtilts[0]['beam tilt']
			states2[1]['beam tilt'] = beamtilts[1]['beam tilt']

			print 'STATES1'
			print states1
			shiftinfo = self.measureStateShift(states1[0], states1[1], 1, settle=0.25)
			pixelshift1 = shiftinfo['pixel shift']

			print 'STATES2'
			print states2
			shiftinfo = self.measureStateShift(states2[0], states2[1], 1, settle=0.25)
			pixelshift2 = shiftinfo['pixel shift']
			print 'PIXELSHIFT1', pixelshift1
			print 'PIXELSHIFT2', pixelshift2
		except:
			self.node.printException()
		## return to original beam tilt
		emdata = data.ScopeEMData(id=('scope',), initializer=beamtilt)
		self.node.publishRemote(emdata)

		return (pixelshift1, pixelshift2)

	def measureDispDiff(self, tilt_axis, tilt_m, tilt_t):
		'''
		This measures one displacement difference that go into 
		eq. (11). Each call of this function acquires four images
		and returns one shift displacement.  We could also use
		something other than measureStateShift and do this with
		only 3 images.
		'''
		beamtilt = self.getBeamTilt()

		### try/finally to be sure we return to original beam tilt
		try:
			print 'BEAMTILT', beamtilt

			### apply misalignment, this is the base value
			### from which the two equal and opposite tilts
			### are made
			state0 = copy.deepcopy(beamtilt)
			state0['beam tilt'][tilt_axis] += tilt_m
			print 'state0', state0

			### create the two equal and opposite tilted states
			statepos = copy.deepcopy(state0)
			statepos['beam tilt'][tilt_axis] += tilt_t
			print 'statepos', statepos
			stateneg = copy.deepcopy(state0)
			stateneg['beam tilt'][tilt_axis] -= tilt_t
			print 'stateneg', stateneg

			shiftinfo = self.measureStateShift(state0, statepos, 1, settle=0.25)
			pixelshift1 = shiftinfo['pixel shift']

			shiftinfo = self.measureStateShift(state0, stateneg, 1, settle=0.25)
			pixelshift2 = shiftinfo['pixel shift']
			print 'PIXELSHIFT1', pixelshift1
			print 'PIXELSHIFT2', pixelshift2
		finally:
			## return to original beam tilt
			emdata = data.ScopeEMData(id=('scope',), initializer=beamtilt)
			self.node.publishRemote(emdata)

		pixelshiftdiff = {}
		pixelshiftdiff['row'] = pixelshift2['row'] - pixelshift1['row']
		pixelshiftdiff['col'] = pixelshift2['col'] - pixelshift1['col']
		return pixelshiftdiff

	def storeGoodTilt(self, mag, goodtilt):
		'''
		stores a new good tilt calibration
		'''
		caldata = data.GoodTiltCalibrationData(id=self.node.ID(), magnification=mag, tilt=goodtilt)
		emhost = self.getHost()
		caldata['em host'] = emhost
		self.node.publish(caldata, database=True)


class SimpleMatrixCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		'''
		returns a scope key for the calibrated parameter
		'''
		raise NotImplementedError()

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

		matrix = self.retrieveMatrix(mag, par)

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

		matrix = self.retrieveMatrix(mag, par)
		print 'matrix', matrix
		print 'pixvect', pixvect
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

		matrix = self.retrieveMatrix(mag, par)
		if matrix is None:
			return None
		matrix = LinearAlgebra.inverse(matrix)

		pixvect = Numeric.matrixmultiply(matrix, vect)
		pixvect = pixvect / (biny, binx)
		return {'row':pixvect[0], 'col':pixvect[1]}


class ImageShiftCalibrationClient(SimpleMatrixCalibrationClient):
	def __init__(self, node):
		SimpleMatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		return 'image shift'

class BeamShiftCalibrationClient(SimpleMatrixCalibrationClient):
	def __init__(self, node):
		SimpleMatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		return 'beam shift'

class StageCalibrationClient(SimpleMatrixCalibrationClient):
	def __init__(self, node):
		SimpleMatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		return 'stage position'

import gonmodel
# XXX Not up to date with new calibration data research methods
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
		# XXX
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

		stagedata = data.ScopeEMData(id=('scope',), initializer=current)
		self.publishRemote(stagedata)
