#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import node, data, event
import Numeric
import LinearAlgebra
import math
import correlator
import peakfinder
import time
import sys
import threading
import gonmodel
import imagefun

class Drifting(Exception):
	pass

class Abort(Exception):
	pass

class NoPixelSizeError(Exception):
	pass

class NoMatrixCalibrationError(Exception):
	pass

class CalibrationClient(object):
	'''
	this is a component of a node that needs to use calibrations
	'''
	def __init__(self, node):
		self.node = node
		self.cam = node.cam

		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.abortevent = threading.Event()

	def checkAbort(self):
		if self.abortevent.isSet():
			raise Abort()

	def acquireStateImage(self, state, publish_image=0, settle=0.0):
		## acquire image at this state
		print 'creating EM data'
		newemdata = data.ScopeEMData(id=('scope',), initializer=state)
#		needs unlock too
#		print 'publishing lock'
#		self.node.publish(event.LockEvent(id=self.node.ID()))
#		print 'publishing EM'
		self.node.publishRemote(newemdata)
		print 'state settling time %s' % (settle,)
		time.sleep(settle)

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

	def measureStateShift(self, state1, state2, publish_images=0, settle=0.0, drift_threshold=None, image_callback=None):
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
		t0 = actual1['system time']
		self.numimage1 = imagecontent1['image']
		if image_callback is not None:
			apply(image_callback, (self.numimage1,))
		self.correlator.insertImage(self.numimage1)

		self.checkAbort()

		## for drift check, continue to acquire at state1
		if drift_threshold is not None:
			print 'checking for drift'

			info1 = self.acquireStateImage(state1, publish_images, settle)
			imagedata1 = info1['imagedata']
			imagecontent1 = imagedata1
			stats1 = info1['image stats']
			actual1 = imagecontent1['scope']
			t1 = actual1['system time']
			self.numimage1 = imagecontent1['image']
			if image_callback is not None:
				apply(image_callback, (self.numimage1,))
			self.correlator.insertImage(self.numimage1)

			print 'correlation'
			pcimage = self.correlator.phaseCorrelate()

			print 'peak finding'
			self.peakfinder.setImage(pcimage)
			self.peakfinder.subpixelPeak()
			peak = self.peakfinder.getResults()
			peakvalue = peak['subpixel peak value']
			shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)
			shiftrows = shift[0]
			shiftcols = shift[1]
			d = data.DriftData(id=self.node.ID(), rows=shiftrows, cols=shiftcols)
			self.node.publish(d, database=True, dbforce=True)

			drift = abs(shift[0] + 1j * shift[1])
			seconds = t1 - t0
			print 'SECONDS: ', seconds
			print 'PIXELS: ', drift
			print 'PIXELS/SECOND: %.4e' % (float(drift) / seconds,)
			if drift > drift_threshold:
				raise Drifting()

#		mrcstr = Mrc.numeric_to_mrcstr(numimage1)
#		self.ui_image1.set(xmlbinlib.Binary(mrcstr))

		self.checkAbort()

		info2 = self.acquireStateImage(state2, publish_images, settle)
		imagedata2 = info2['imagedata']
		imagecontent2 = imagedata2
		stats2 = info2['image stats']
		actual2 = imagecontent2['scope']
		self.numimage2 = imagecontent2['image']
		if image_callback is not None:
			apply(image_callback, (self.numimage2,))
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


class DoseCalibrationClient(CalibrationClient):
	coulomb = 6.2414e18
	def __init__(self, node):
		CalibrationClient.__init__(self, node)
		self.psizecal = PixelSizeCalibrationClient(node)

	def storeSensitivity(self, ht, sensitivity):
		newdata = data.CameraSensitivityCalibrationData()
		newdata['session'] = self.node.session
		newdata['high tension'] = ht
		newdata['sensitivity'] = sensitivity
		self.node.publish(newdata, database=True, dbforce=True)

	def researchSensitivity(self, ht, instrument):
		qdata = data.CameraSensitivityCalibrationData()
		qdata['session'] = data.SessionData()
		qdata['session']['instrument'] = instrument
		qdata['high tension'] = ht
		results = self.node.research(datainstance=qdata, fill=False, results=1)
		if results:
			result = results[0]
		else:
			result = None
		return result

	def dose_from_screen(self, screen_mag, beam_current, beam_diameter):
		## electrons per screen area per second
		beam_area = math.pi * (beam_diameter/2.0)**2
		screen_electrons = beam_current * self.coulomb / beam_area
		## electrons per specimen area per second (dose rate)
		dose_rate = screen_electrons * (screen_mag**2)
		return dose_rate

	def retrieveSensitivity(self, ht, instrument):
		sdata = self.researchSensitivity(ht, instrument)
		if sdata is None:
			return None
		sens = sdata['sensitivity']
		return sens

	def sensitivity(self, dose_rate, camera_mag, camera_pixel_size, exposure_time, counts):
		camera_dose = float(dose_rate) / float((camera_mag**2))
		print 'camera dose', camera_dose
		dose_per_pixel = camera_dose * (camera_pixel_size**2)
		electrons_per_pixel = dose_per_pixel * exposure_time
		print 'el per pix', electrons_per_pixel
		counts_per_electron = float(counts) / electrons_per_pixel
		return counts_per_electron

	def sensitivity_from_imagedata(self, imagedata, dose_rate):
		inst = imagedata['session']['instrument']
		mag = imagedata['scope']['magnification']
		print 'mag', mag
		specimen_pixel_size = self.psizecal.retrievePixelSize(mag, instrument=inst)
		print 'spec pix size', specimen_pixel_size
		camera_pixel_size = inst['camera pixel size']
		print 'cam pix size', camera_pixel_size
		camera_mag = camera_pixel_size / specimen_pixel_size
		print 'camera_mag', camera_mag
		exposure_time = imagedata['camera']['exposure time'] / 1000.0
		binning = imagedata['camera']['binning']['x']
		mean_counts = imagefun.mean(imagedata['image']) / (binning**2)
		return self.sensitivity(dose_rate, camera_mag, camera_pixel_size, exposure_time, mean_counts)

	def dose_from_imagedata(self, imagedata):
		'''
		imagedata indirectly contains most info needed to calc dose
		'''
		inst = imagedata['session']['instrument']
		camera_pixel_size = inst['camera pixel size']
		ht = imagedata['scope']['high tension']
		binning = imagedata['camera']['binning']['x']
		mag = imagedata['scope']['magnification']
		specimen_pixel_size = self.psizecal.retrievePixelSize(mag, instrument=inst)
		print 'SPECIMEN PIXSIZE', specimen_pixel_size
		exp_time = imagedata['camera']['exposure time'] / 1000.0
		numdata = imagedata['image']
		sensitivity = self.retrieveSensitivity(ht, inst)
		print 'SENSITIVITY', sensitivity
		mean_counts = imagefun.mean(numdata) / (binning**2)
		print 'MEAN', mean_counts
		totaldose = mean_counts / specimen_pixel_size**2 / sensitivity
		return totaldose


class PixelSizeCalibrationClient(CalibrationClient):
	'''
	basic CalibrationClient for accessing a type of calibration involving
	a matrix at a certain magnification
	'''
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def researchPixelSizeData(self, mag, instrument=None):
		queryinstance = data.PixelSizeCalibrationData()
		queryinstance['magnification'] = mag
		queryinstance['session'] = data.SessionData()
		if instrument is None:
			queryinstance['session']['instrument'] = self.node.session['instrument']
		else:
			queryinstance['session']['instrument'] = instrument
		caldatalist = self.node.research(datainstance=queryinstance, results=1)
		if len(caldatalist) > 0:
			return caldatalist[0]
		else:
			return None

	def retrievePixelSize(self, mag, instrument=None):
		'''
		finds the requested pixel size using magnification
		'''
		caldata = self.researchPixelSizeData(mag, instrument)
		if caldata is None:
			raise NoPixelSizeError()
		pixelsize = caldata['pixelsize']
		return pixelsize

	def time(self, mag, instrument=None):
		pdata = self.researchPixelSizeData(mag, instrument)
		if pdata is None:
			timeinfo = None
		else:
			timeinfo = pdata.timestamp
		return timeinfo

	def retrieveAllPixelSizes(self):
		'''
		finds the requested pixel size using magnification
		'''
		queryinstance = data.PixelSizeCalibrationData()
		queryinstance['session'] = data.SessionData()
		queryinstance['session']['instrument'] = self.node.session['instrument']
		caldatalist = self.node.research(datainstance=queryinstance)

		return caldatalist


class MatrixCalibrationClient(CalibrationClient):
	'''
	basic CalibrationClient for accessing a type of calibration involving
	a matrix at a certain magnification
	'''
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def researchMatrix(self, ht, mag, caltype):
		queryinstance = data.MatrixCalibrationData(magnification=mag, type=caltype)
		queryinstance['high tension'] = ht
		queryinstance['session'] = data.SessionData()
		queryinstance['session']['instrument'] = self.node.session['instrument']
		caldatalist = self.node.research(datainstance=queryinstance, results=1)
		if len(caldatalist) > 0:
			caldata = caldatalist[0]
		else:
			caldata = None
		return caldata

	def retrieveMatrix(self, ht, mag, caltype):
		'''
		finds the requested matrix using magnification and type
		'''
		caldata = self.researchMatrix(ht, mag, caltype)
		if caldata is None:
			raise NoMatrixCalibrationError('HT: %s, mag: %s, cal type: %s' % (ht, mag, caltype))
		matrix = caldata['matrix'].copy()
		return matrix

	def time(self, ht, mag, caltype):
		caldata = self.researchMatrix(ht, mag, caltype)
		if caldata is None:
			timestamp = None
		else:
			timestamp = caldata.timestamp
		return timestamp

	def storeMatrix(self, ht, mag, type, matrix):
		'''
		stores a new calibration matrix
		'''
		newmatrix = Numeric.array(matrix, Numeric.Float64)
		caldata = data.MatrixCalibrationData(id=self.node.ID(), magnification=mag, type=type, matrix=matrix)
		caldata['high tension'] = ht
		self.node.publish(caldata, database=True, dbforce=True)


class BeamTiltCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def getBeamTilt(self):
		emdata = self.node.researchByDataID(('beam tilt',))
		bt = dict(emdata['beam tilt'])
		return bt

	def measureDefocusStig(self, tilt_value, publish_images=0, drift_threshold=None, image_callback=None):
		self.abortevent.clear()
		emdata = self.node.researchByDataID(('magnification',))
		#mag = emdata.content['magnification']
		mag = emdata['magnification']
		ht = emdata['high tension']
		fmatrix = self.retrieveMatrix(ht, mag, 'defocus')
		amatrix = self.retrieveMatrix(ht, mag, 'stigx')
		bmatrix = self.retrieveMatrix(ht, mag, 'stigy')

		if None in (fmatrix, amatrix, bmatrix):
			raise RuntimeError('missing calibration matrix')

		tiltcenter = self.getBeamTilt()
		print 'TILTCENTER', tiltcenter

		### need two tilt displacement measurements
		### easiest is one on each tilt axis
		shifts = {}
		tilts = {}
		self.checkAbort()
		print 'TILTING'
		for tiltaxis in ('x','y'):
			bt1 = dict(tiltcenter)
			bt1[tiltaxis] -= (tilt_value/2.0)
			bt2 = dict(tiltcenter)
			bt2[tiltaxis] += (tilt_value/2.0)
			state1 = data.ScopeEMData(id=('scope',))
			state2 = data.ScopeEMData(id=('scope',))
			state1['beam tilt'] = bt1
			state2['beam tilt'] = bt2
			try:
				shiftinfo = self.measureStateShift(state1, state2, publish_images, settle=0.5, drift_threshold=drift_threshold, image_callback=image_callback)
			except Abort:
				break
			except Drifting:
				## return to original beam tilt
				emdata = data.ScopeEMData(id=('scope',), initializer={'beam tilt':tiltcenter})
				self.node.publishRemote(emdata)
				print 'RETURNED TO TILT CENTER', tiltcenter
				raise

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
		emdata = data.ScopeEMData(id=('scope',), initializer={'beam tilt':tiltcenter})
		self.node.publishRemote(emdata)
		print 'RETURNED TO TILT CENTER', tiltcenter

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
			beamtilts = (dict(beamtilt),dict(beamtilt))
			beamtilts[0][tilt_axis] += tilt_value
			beamtilts[1][tilt_axis] -= tilt_value

			## set up to measure states
			states1 = (data.ScopeEMData(initializer=state1), data.ScopeEMData(initializer=state1))
			states2 = (data.ScopeEMData(initializer=state2), data.ScopeEMData(initializer=state2))

			states1[0]['beam tilt'] = beamtilts[0]
			states1[1]['beam tilt'] = beamtilts[1]
			states2[0]['beam tilt'] = beamtilts[0]
			states2[1]['beam tilt'] = beamtilts[1]

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
		emdata = data.ScopeEMData(id=('scope',), initializer={'beam tilt':beamtilt})
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
			bt0 = dict(beamtilt)
			bt0[tilt_axis] += tilt_m
			state0 = data.ScopeEMData(id=('scope',), initializer={'beam tilt':bt0})
			print 'state0', state0
			### create the two equal and opposite tilted states
			statepos = data.ScopeEMData(id=('scope',), initializer={'beam tilt':dict(bt0)})
			stateneg = data.ScopeEMData(id=('scope',), initializer={'beam tilt':dict(bt0)})

			statepos['beam tilt'][tilt_axis] += tilt_t
			print 'statepos', statepos
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
			emdata = data.ScopeEMData(id=('scope',), initializer={'beam tilt':beamtilt})
			self.node.publishRemote(emdata)

		pixelshiftdiff = {}
		pixelshiftdiff['row'] = pixelshift2['row'] - pixelshift1['row']
		pixelshiftdiff['col'] = pixelshift2['col'] - pixelshift1['col']
		return pixelshiftdiff

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
		ht = scope['high tension']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = self.parameter()

		matrix = self.retrieveMatrix(ht, mag, par)

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
		ht = scope['high tension']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = self.parameter()

		pixrow = pixelshift['row'] * biny
		pixcol = pixelshift['col'] * binx
		pixvect = (pixrow, pixcol)

		matrix = self.retrieveMatrix(ht, mag, par)
		#print 'matrix', matrix
		#print 'pixvect', pixvect
		change = Numeric.matrixmultiply(matrix, pixvect)
		changex = change[0]
		changey = change[1]

		new = data.ScopeEMData(initializer=scope)
		## make a copy of this since it will be modified
		new[par] = dict(scope[par])
		new[par]['x'] += changex
		new[par]['y'] += changey

		return new

	def itransform(self, shift, scope, camera):
		'''
		Calculate a pixel vector from an image center which 
		represents the given parameter shift.
		'''
		mag = scope['magnification']
		ht = scope['high tension']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = self.parameter()

		vect = (shift['x'], shift['y'])

		try:
			matrix = self.retrieveMatrix(ht, mag, par)
			if matrix is None:
				return None
		except NoMatrixCalibrationError:
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

class ModeledStageCalibrationClient(CalibrationClient):
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def storeMagCalibration(self, label, ht, mag, axis, angle, mean):
		caldata = data.StageModelMagCalibrationData()
		caldata['label'] = label
		caldata['high tension'] = ht
		caldata['magnification'] = mag
		caldata['axis'] = axis
		caldata['angle'] = angle
		caldata['mean'] = mean
		self.node.publish(caldata, database=True, dbforce=True)

	def researchMagCalibration(self, ht, mag, axis):
		tmpsession = data.SessionData()
		tmpsession['instrument'] = self.node.session['instrument']
		qinst = data.StageModelMagCalibrationData(magnification=mag, axis=axis)
		qinst['high tension'] = ht
		qinst['session'] = tmpsession

		caldatalist = self.node.research(datainstance=qinst, results=1)
		if len(caldatalist) > 0:
			caldata = caldatalist[0]
		else:
			caldata = None
		return caldata

	def retrieveMagCalibration(self, ht, mag, axis):
		caldata = self.researchMagCalibration(ht, mag, axis)
		if caldata is None:
			raise RuntimeError('no model mag calibration')
		else:
			caldata2 = dict(caldata)
			return caldata2

	def timeMagCalibration(self, ht, mag, axis):
		caldata = self.researchMagCalibration(ht, mag, axis)
		if caldata is None:
			timeinfo = None
		else:
			timeinfo = caldata.timestamp
		return timeinfo

	def storeModelCalibration(self, label, axis, period, a, b):
		caldata = data.StageModelCalibrationData()
		caldata['label'] = label 
		caldata['axis'] = axis
		caldata['period'] = period
		## force it to be 2 dimensional so sqldict likes it
		a.shape = (1,len(a))
		b.shape = (1,len(b))
		caldata['a'] = a
		caldata['b'] = b

		self.node.publish(caldata, database=True, dbforce=True)

	def researchModelCalibration(self, instrument, axis):
		tmpsession = data.SessionData()
		tmpsession['instrument'] = self.node.session['instrument']
		qinst = data.StageModelCalibrationData(axis=axis)
		qinst['session'] = tmpsession
		caldatalist = self.node.research(datainstance=qinst, results=1)
		if len(caldatalist) > 0:
			caldata = caldatalist[0]
		else:
			caldata = None
		return caldata

	def retrieveModelCalibration(self, axis):
		caldata = self.researchModelCalibration(self.node.session['instrument'], axis)
		if caldata is None:
			raise RuntimeError('no model calibration')
		else:
			print 'PERIOD', caldata['period']
			print 'A', caldata['a'], caldata['a'].shape
			print 'B', caldata['b'], caldata['b'].shape
			## return it to rank 0 array
			caldata2 = {}
			caldata2['axis'] = caldata['axis']
			caldata2['period'] = caldata['period']
			caldata2['a'] = Numeric.ravel(caldata['a']).copy()
			caldata2['b'] = Numeric.ravel(caldata['b']).copy()
			return caldata2

	def timeModelCalibration(self, axis):
		inst = self.node.session['instrument']
		caldata = self.researchModelCalibration(inst, axis)
		if caldata is None:
			timeinfo = None
		else:
			timeinfo = caldata.timestamp
		return timeinfo

	def getLabeledData(self, label, mag, axis):
		qdata = data.StageMeasurementData()
		qdata['label'] = label
		qdata['magnification'] = mag
		qdata['axis'] = axis
		measurements = self.node.research(datainstance=qdata)
		if not measurements:
			raise RuntimeError('no measurements!')
		print 'LEN(MEASUREMENTS)', len(measurements)
		ht = measurements[0]['high tension']
		datapoints = []
		for measurement in measurements:
			if measurement['high tension'] != ht:
				raise RuntimeError('inconsistent high tension in measurements!')
			datapoint = []
			datapoint.append(measurement['x'])
			datapoint.append(measurement['y'])
			datapoint.append(measurement['delta'])
			datapoint.append(measurement['imagex'])
			datapoint.append(measurement['imagey'])
			datapoints.append(datapoint)
		return {'datapoints':datapoints, 'ht': ht}

	def fit(self, label, mag, axis, terms, magonly=1):
		# get data from DB
		info = self.getLabeledData(label, mag, axis)
		datapoints = info['datapoints']
		ht = info['ht']
		dat = gonmodel.GonData()
		dat.import_data(mag, axis, datapoints)

		## fit a model to the data
		mod = gonmodel.GonModel()
		mod.fit_data(dat, terms)

		### mag info
		axis = dat.axis
		mag = dat.mag
		angle = dat.angle
		# using data mean, could use model mean
		mean = dat.avg
		#mean = mod.a0

		### model info
		period = mod.period
		a = mod.a
		b = mod.b
		
		self.storeMagCalibration(label, ht, mag, axis, angle, mean)
		if magonly:
			return
		self.storeModelCalibration(label, axis, period, a, b)

	def transform(self, pixelshift, scope, camera):
		curstage = scope['stage position']

		binx = camera['binning']['x']
		biny = camera['binning']['y']
		pixrow = pixelshift['row'] * biny
		pixcol = pixelshift['col'] * binx

		## do modifications to newstage here
		xmodcal = self.retrieveModelCalibration('x')
		ymodcal = self.retrieveModelCalibration('y')
		print 'xmod a', xmodcal['a']
		print 'xmod b', xmodcal['b']
		print 'ymod a shape', ymodcal['a'].shape
		print 'ymod b shape', ymodcal['b'].shape
		xmod = gonmodel.GonModel()
		xmod.fromDict(xmodcal)
		ymod = gonmodel.GonModel()
		ymod.fromDict(ymodcal)

		xmagcal = self.retrieveMagCalibration(scope['high tension'], scope['magnification'], 'x')
		ymagcal = self.retrieveMagCalibration(scope['high tension'], scope['magnification'], 'y')


		delta = self.pixtix(xmod, ymod, xmagcal, ymagcal, curstage['x'], curstage['y'], pixcol, pixrow)

		newscope = data.ScopeEMData(initializer=scope)
		newscope['stage position'] = dict(scope['stage position'])
		newscope['stage position']['x'] += delta['x']
		newscope['stage position']['y'] += delta['y']
		return newscope

	def pixtix(self, xmod, ymod, xmagcal, ymagcal, gonx, gony, pixx, pixy):
		modavgx = xmagcal['mean']
		modavgy = ymagcal['mean']
		anglex = xmagcal['angle']
		angley = ymagcal['angle']
	
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
