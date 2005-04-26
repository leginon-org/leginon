#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import node, data, event
try:
	import numarray as Numeric
	import numarray.linear_algebra as LinearAlgebra
except:
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
	def __init__(self, *args, **kwargs):
		if 'state' in kwargs:
			self.state = kwargs['state']
		else:
			self.state = None
		Exception.__init__(self, *args)

class NoSensitivityError(Exception):
	pass

class CalibrationClient(object):
	'''
	this is a component of a node that needs to use calibrations
	'''
	def __init__(self, node):
		self.node = node
		try:
			self.instrument = self.node.instrument
		except AttributeError:
			raise RuntimeError('CalibrationClient node needs instrument')

		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.abortevent = threading.Event()

	def checkAbort(self):
		if self.abortevent.isSet():
			raise Abort()

	def getPixelSize(self, mag, tem=None, ccdcamera=None):
		queryinstance = data.PixelSizeCalibrationData()
		queryinstance['magnification'] = mag
		if tem is None:
			queryinstance['tem'] = self.instrument.getTEMData()
		else:
			queryinstance['tem'] = tem
		if ccdcamera is None:
			queryinstance['ccdcamera'] = self.instrument.getCCDCameraData()
		else:
			queryinstance['ccdcamera'] = ccdcamera
		caldatalist = self.node.research(datainstance=queryinstance, results=1)
		if len(caldatalist) > 0:
			return caldatalist[0]['pixelsize']
		else:
			return None

	def acquireStateImage(self, state, publish_image=0, settle=0.0):
		self.node.logger.debug('Acquiring image...')
		## acquire image at this state
		newemdata = data.ScopeEMData(initializer=state)
		self.instrument.setData(newemdata)
		time.sleep(settle)

		imagedata = self.instrument.getData(data.CorrectedCameraImageData)
		actual_state = imagedata['scope']

		if publish_image:
			self.node.publish(imagedata, pubevent=True)

		self.node.setImage(imagedata['image'].astype(Numeric.Float32), 'Image')

		## should find image stats to help determine validity of image
		## in correlations
		image_stats = None

		info = {'requested state': state, 'imagedata': imagedata, 'image stats': image_stats}
		return info

	def measureStateShift(self, state1, state2, publish_images=0, settle=0.0, drift_threshold=None, image_callback=None, target=None):
		'''
		Measures the pixel shift between two states
		 Returned dict has these keys:
		    'actual states': tuple with the actual scope states
		    'pixel shift': the resulting pixel shift, 'row', and 'col'
		    'peak value': cross correlation peak value
		    'shape': shape of acquired images
		    'stats': statistics of two images acquired (not implemented)
		'''

		self.node.logger.info('Acquiring images...')

		self.node.logger.info('Acquiring image (1 of 2)')
		info1 = self.acquireStateImage(state1, publish_images, settle)
		imagedata1 = info1['imagedata']
		imagecontent1 = imagedata1
		stats1 = info1['image stats']
		actual1 = imagecontent1['scope']
		t0 = actual1['system time']
		self.numimage1 = imagecontent1['image']
		if image_callback is not None:
			apply(image_callback, (self.numimage1, 'Correlation'))
		self.correlator.insertImage(self.numimage1)

		self.checkAbort()

		## for drift check, continue to acquire at state1
		if drift_threshold is None:
			driftdata = None
		else:
			self.node.logger.info('Checking for drift...')

			info1 = self.acquireStateImage(state1, publish_images, settle)
			imagedata1 = info1['imagedata']
			imagecontent1 = imagedata1
			stats1 = info1['image stats']
			actual1 = imagecontent1['scope']
			t1 = actual1['system time']
			self.numimage1 = imagecontent1['image']
			if image_callback is not None:
				apply(image_callback, (self.numimage1, 'Correlation'))
			self.correlator.insertImage(self.numimage1)

			self.node.logger.info('Calculating shift between the images...')
			self.node.logger.debug('Correlating...')
			if self.node.settings['correlation type'] == 'cross':
				pcimage = self.correlator.crossCorrelate()
			elif self.node.settings['correlation type'] == 'phase':
				pcimage = self.correlator.phaseCorrelate()
			else:
				raise RuntimeError('invalid correlation type')

			self.node.logger.debug('Peak finding...')
			self.peakfinder.setImage(pcimage)
			self.peakfinder.subpixelPeak(npix=9)
			peak = self.peakfinder.getResults()
			pixelpeak = peak['subpixel peak']
			pixelpeak = pixelpeak[1],pixelpeak[0]

			self.node.setImage(pcimage.astype(Numeric.Float32), 'Correlation')
			self.node.setTargets([pixelpeak], 'Peak')

			peakvalue = peak['subpixel peak value']
			shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)
			self.node.logger.info('pixel shift (row,col): %s' % (shift,))
			shiftrows = shift[0]
			shiftcols = shift[1]
			seconds = t1 - t0

			## publish scope and camera to be used with drift data
			scope = imagedata1['scope']
			self.node.publish(scope, database=True, dbforce=True)
			camera = imagedata1['camera']
			self.node.publish(camera, database=True, dbforce=True)
			driftdata = data.DriftData(session=self.node.session, rows=shiftrows, cols=shiftcols, interval=seconds, target=target, scope=scope, camera=camera)
			self.node.publish(driftdata, database=True, dbforce=True)

			pixels = abs(shift[0] + 1j * shift[1])
			# convert to meters
			mag = actual1['magnification']
			pixelsize = self.getPixelSize(mag)
			meters = pixelsize * pixels
			drift = meters / seconds
			self.node.logger.info('Seconds %f, pixels %f, meters %.4e, meters/second %.4e'
							% (seconds, pixels, meters, float(meters)/seconds))
			if drift > drift_threshold:
				## declare drift above threshold
				declared = data.DriftDeclaredData()
				declared['system time'] = t1
				declared['type'] = 'threshold'
				self.node.publish(declared, database=True, dbforce=True)
				raise Drifting()

		self.checkAbort()

		self.node.logger.info('Acquiring image (2 of 2)')
		info2 = self.acquireStateImage(state2, publish_images, settle)
		imagedata2 = info2['imagedata']
		imagecontent2 = imagedata2
		stats2 = info2['image stats']
		actual2 = imagecontent2['scope']
		self.numimage2 = imagecontent2['image']
		if image_callback is not None:
			apply(image_callback, (self.numimage2,))
		self.correlator.insertImage(self.numimage2)

		actual = (actual1, actual2)
		shiftinfo = {}

		self.checkAbort()

		self.node.logger.info('Calculating shift between the images...')
		self.node.logger.debug('Correlating...')
		if self.node.settings['correlation type'] == 'cross':
			pcimage = self.correlator.crossCorrelate()
		elif self.node.settings['correlation type'] == 'phase':
			pcimage = self.correlator.phaseCorrelate()
		else:
			raise RuntimeError('invalid correlation type')

		## peak finding
		self.node.logger.debug('Peak finding...')
		self.peakfinder.setImage(pcimage)
		self.peakfinder.subpixelPeak(npix=9)
		peak = self.peakfinder.getResults()
		self.node.logger.debug('Peak minsum %f' % peak['minsum'])

		pixelpeak = peak['subpixel peak']
		pixelpeak = pixelpeak[1], pixelpeak[0]
		self.node.setImage(pcimage.astype(Numeric.Float32), 'Correlation')
		self.node.setTargets([pixelpeak], 'Peak')

		peakvalue = peak['subpixel peak value']
		shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)
		self.node.logger.debug('pixel shift (row,col): %s' % (shift,))

		## need unbinned result
		binx = imagecontent1['camera']['binning']['x']
		biny = imagecontent1['camera']['binning']['y']
		unbinned = {'row':shift[0] * biny, 'col': shift[1] * binx}

		shiftinfo.update({'actual states': actual, 'pixel shift': unbinned, 'peak value': peakvalue, 'shape':pcimage.shape, 'stats': (stats1, stats2), 'driftdata': driftdata})
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
		newdata['tem'] = self.instrument.getTEMData()
		newdata['ccdcamera'] = self.instrument.getCCDCameraData()
		self.node.publish(newdata, database=True, dbforce=True)

	def retrieveSensitivity(self, ht, tem, ccdcamera):
		qdata = data.CameraSensitivityCalibrationData()
		qdata['tem'] = tem
		qdata['ccdcamera'] = ccdcamera
		qdata['high tension'] = ht
		results = self.node.research(datainstance=qdata, results=1)
		if results:
			result = results[0]['sensitivity']
		else:
			raise NoSensitivityError
		return result

	def dose_from_screen(self, screen_mag, beam_current, beam_diameter):
		## electrons per screen area per second
		beam_area = math.pi * (beam_diameter/2.0)**2
		screen_electrons = beam_current * self.coulomb / beam_area
		## electrons per specimen area per second (dose rate)
		dose_rate = screen_electrons * (screen_mag**2)
		return dose_rate

	def sensitivity(self, dose_rate, camera_mag, camera_pixel_size, exposure_time, counts):
		if camera_mag == 0:
			raise ValueError('invalid camera magnification given')
		camera_dose = float(dose_rate) / float((camera_mag**2))
		self.node.logger.info('Camera dose %.4e' % camera_dose)
		dose_per_pixel = camera_dose * (camera_pixel_size**2)
		electrons_per_pixel = dose_per_pixel * exposure_time
		if electrons_per_pixel == 0:
			raise ValueError('invalid electrons per pixel calculated')
		self.node.logger.info('Calculated electrons/pixel %.4e'
													% electrons_per_pixel)
		counts_per_electron = float(counts) / electrons_per_pixel
		return counts_per_electron

	def sensitivity_from_imagedata(self, imagedata, dose_rate):
		tem = imagedata['scope']['tem']
		ccdcamera = imagedata['camera']['ccdcamera']
		mag = imagedata['scope']['magnification']
		self.node.logger.info('Magnification %.1f' % mag)
		specimen_pixel_size = self.psizecal.retrievePixelSize(tem,
																													ccdcamera, mag)
		self.node.logger.info('Specimen pixel size %.4e' % specimen_pixel_size)
		camera_pixel_size = imagedata['camera']['pixel size']['x']
		self.node.logger.info('Camera pixel size %.4e' % camera_pixel_size)
		camera_mag = camera_pixel_size / specimen_pixel_size
		self.node.logger.info('CCD Camera magnification %.1f' % camera_mag)
		exposure_time = imagedata['camera']['exposure time'] / 1000.0
		binning = imagedata['camera']['binning']['x']
		mean_counts = imagefun.mean(imagedata['image']) / (binning**2)
		return self.sensitivity(dose_rate, camera_mag, camera_pixel_size,
														exposure_time, mean_counts)

	def dose_from_imagedata(self, imagedata):
		'''
		imagedata indirectly contains most info needed to calc dose
		'''
		tem = imagedata['scope']['tem']
		if tem is None:
			tem = self.instrument.getTEMData()
		ccdcamera = imagedata['camera']['ccdcamera']
		if ccdcamera is None:
			ccdcamera = self.instrument.getCCDCameraData()
		camera_pixel_size = imagedata['camera']['pixel size']['x']
		ht = imagedata['scope']['high tension']
		binning = imagedata['camera']['binning']['x']
		mag = imagedata['scope']['magnification']
		specimen_pixel_size = self.psizecal.retrievePixelSize(tem, ccdcamera, mag)
		self.node.logger.info('Specimen pixel size %.4e' % specimen_pixel_size)
		exp_time = imagedata['camera']['exposure time'] / 1000.0
		numdata = imagedata['image']
		sensitivity = self.retrieveSensitivity(ht, tem, ccdcamera)
		self.node.logger.info('Sensitivity %.2f' % sensitivity)
		mean_counts = imagefun.mean(numdata) / (binning**2)
		self.node.logger.info('Mean counts %.1f' % mean_counts)
		totaldose = mean_counts / specimen_pixel_size**2 / sensitivity
		return totaldose


class PixelSizeCalibrationClient(CalibrationClient):
	'''
	basic CalibrationClient for accessing a type of calibration involving
	a matrix at a certain magnification
	'''
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def researchPixelSizeData(self, tem, ccdcamera, mag):
		queryinstance = data.PixelSizeCalibrationData()
		queryinstance['magnification'] = mag
		if tem is None:
			queryinstance['tem'] = self.instrument.getTEMData()
		else:
			queryinstance['tem'] = tem
		if ccdcamera is None:
			queryinstance['ccdcamera'] = self.instrument.getCCDCameraData()
		else:
			queryinstance['ccdcamera'] = ccdcamera
		caldatalist = self.node.research(datainstance=queryinstance, results=1)
		if len(caldatalist) > 0:
			return caldatalist[0]
		else:
			return None

	def retrievePixelSize(self, tem, ccdcamera, mag):
		'''
		finds the requested pixel size using magnification
		'''
		caldata = self.researchPixelSizeData(tem, ccdcamera, mag)
		if caldata is None:
			raise NoPixelSizeError()
		pixelsize = caldata['pixelsize']
		return pixelsize

	def time(self, tem, ccdcamera, mag):
		pdata = self.researchPixelSizeData(tem, ccdcamera, mag)
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
		queryinstance['tem'] = self.instrument.getTEMData()
		queryinstance['ccdcamera'] = self.instrument.getCCDCameraData()
		caldatalist = self.node.research(datainstance=queryinstance)

		return caldatalist

	def retrieveLastPixelSizes(self):
		caldatalist = self.retrieveAllPixelSizes()
		last = {}
		for caldata in caldatalist:
			mag = caldata['magnification']
			if mag not in last:
				last[mag] = caldata
		return last.values()


class MatrixCalibrationClient(CalibrationClient):
	'''
	basic CalibrationClient for accessing a type of calibration involving
	a matrix at a certain magnification
	'''
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def parameter(self):
		raise NotImplementedError

	def researchMatrix(self, tem, ccdcamera, caltype, ht, mag):
		queryinstance = data.MatrixCalibrationData()
		queryinstance['tem'] = tem
		queryinstance['ccdcamera'] = ccdcamera
		queryinstance['type'] = caltype
		queryinstance['magnification'] = mag
		queryinstance['high tension'] = ht
		caldatalist = self.node.research(datainstance=queryinstance, results=1)
		if caldatalist:
			caldata = caldatalist[0]
			return caldata
		else:
			excstr = 'No query results for %s, %s, %s, %seV, %sx' % (tem, ccdcamera, caltype, ht, mag)
			raise NoMatrixCalibrationError(excstr, state=queryinstance)

	def retrieveMatrix(self, tem, ccdcamera, caltype, ht, mag):
		'''
		finds the requested matrix using magnification and type
		'''
		caldata = self.researchMatrix(tem, ccdcamera, caltype, ht, mag)
		matrix = caldata['matrix'].copy()
		return matrix

	def time(self, tem, ccdcamera, ht, mag, caltype):
		try:
			caldata = self.researchMatrix(tem, ccdcamera, caltype, ht, mag)
		except:
			caldata = None
		if caldata is None:
			timestamp = None
		else:
			timestamp = caldata.timestamp
		return timestamp

	def storeMatrix(self, ht, mag, type, matrix, tem=None, ccdcamera=None):
		'''
		stores a new calibration matrix
		'''
		if tem is None:
			tem = self.instrument.getTEMData()
		if ccdcamera is None:
			ccdcamera = self.instrument.getCCDCameraData()
		newmatrix = Numeric.array(matrix, Numeric.Float64)
		caldata = data.MatrixCalibrationData(session=self.node.session, magnification=mag, type=type, matrix=matrix, tem=tem, ccdcamera=ccdcamera)
		caldata['high tension'] = ht
		self.node.publish(caldata, database=True, dbforce=True)


class BeamTiltCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def getBeamTilt(self):
		try:
			return self.instrument.tem.BeamTilt
		except:
			return None

	def measureDefocusStig(self, tilt_value, publish_images=0, drift_threshold=None, image_callback=None, stig=True, target=None):
		self.abortevent.clear()
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		fmatrix = self.retrieveMatrix(tem, cam, 'defocus', ht, mag)
		if fmatrix is None:
				raise RuntimeError('missing calibration matrix')
		if stig:
			amatrix = self.retrieveMatrix(tem, cam, 'stigx', ht, mag)
			bmatrix = self.retrieveMatrix(tem, cam, 'stigy', ht, mag)
			if None in (amatrix, bmatrix):
				raise RuntimeError('missing calibration matrix')

		tiltcenter = self.getBeamTilt()
		self.node.logger.info('Tilt center %s' % tiltcenter)

		### need two tilt displacement measurements
		### easiest is one on each tilt axis
		shifts = {}
		tilts = {}
		self.checkAbort()
		self.node.logger.info('Tilting...')
		nodrift = False
		lastdrift = None
		for tiltaxis in ('x','y'):
			bt1 = dict(tiltcenter)
			bt1[tiltaxis] -= tilt_value
			bt2 = dict(tiltcenter)
			bt2[tiltaxis] += tilt_value
			state1 = data.ScopeEMData()
			state2 = data.ScopeEMData()
			state1['beam tilt'] = bt1
			state2['beam tilt'] = bt2
			## if no drift on 'x' axis, then assume we don't 
			## need to check on 'y' axis
			if nodrift:
				drift_threshold = None
			try:
				shiftinfo = self.measureStateShift(state1, state2, publish_images, settle=0.5, drift_threshold=drift_threshold, image_callback=image_callback, target=target)
			except Abort:
				break
			except Drifting:
				## return to original beam tilt
				self.instrument.tem.BeamTilt = tiltcenter
				self.node.logger.info('Returned to tilt center %s' % tiltcenter)
				raise
			nodrift = True
			if shiftinfo['driftdata'] is not None:
				lastdrift = shiftinfo['driftdata']

			pixshift = shiftinfo['pixel shift']

			shifts[tiltaxis] = (pixshift['row'], pixshift['col'])
			if tiltaxis == 'x':
				tilts[tiltaxis] = (2*tilt_value, 0)
			else:
				tilts[tiltaxis] = (0, 2*tilt_value)
			try:
				self.checkAbort()
			except Abort:
				break

		## return to original beam tilt
		self.instrument.tem.BeamTilt = tiltcenter
		self.node.logger.info('Returned to tilt center %s' % tiltcenter)

		self.checkAbort()

		#self.node.logger.info('Tilts %s, shifts %s' % (tilts, shifts))

		d1 = shifts['x']
		t1 = tilts['x']
		d2 = shifts['y']
		t2 = tilts['y']
		#print 'STIG', stig
		if stig:
			sol = self.solveEq10(fmatrix,amatrix,bmatrix,d1,t1,d2,t2)
		else:
			sol = self.solveEq10_nostig(fmatrix,d1,t1,d2,t2)

		self.node.logger.info('Solution %s' % sol)
		sol['lastdrift'] = lastdrift
		return sol

	def solveEq10(self, F, A, B, d1, t1, d2, t2):
		#print 'SOLVE STIG'
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

	def solveEq10_nostig(self, F, d1, t1, d2, t2):
		#print 'SOLVE NO STIG'
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
		M = Numeric.zeros((4,1), Numeric.Float64)

		# t1 on first two rows
		M[:2,0] = Numeric.matrixmultiply(F,t1)
		# t2 on second two rows
		M[2:,0] = Numeric.matrixmultiply(F,t2)

		solution = LinearAlgebra.linear_least_squares(M, v)
		result = {
			'defocus': solution[0][0],
			'stigx': 0,
			'stigy': 0,
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
		self.node.logger.debug('State 1 %s, State 2 %s' % (state1, state2))
		
		beamtilt = self.getBeamTilt()
		if beamtilt is None:
			e = 'unable to get beam tilt'
			self.node.logger.exception('Calibration measurement failed: %s' % e)
			return

		### try/finally to be sure we return to original beam tilt
		try:
			self.node.logger.debug('Beam tilt %s' % beamtilt)
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

			self.node.logger.debug('States 1 %s' % (states1,))
			shiftinfo = self.measureStateShift(states1[0], states1[1], 1, settle=0.25)
			pixelshift1 = shiftinfo['pixel shift']

			self.node.logger.debug('States 2 %s' % (states2,))
			shiftinfo = self.measureStateShift(states2[0], states2[1], 1, settle=0.25)
			pixelshift2 = shiftinfo['pixel shift']
			self.node.logger.info('Pixel shift (1 of 2): (%.2f, %.2f)'
														% (pixelshift1['col'], pixelshift1['row']))
			self.node.logger.info('Pixel shift (2 of 2): (%.2f, %.2f)'
														% (pixelshift2['col'], pixelshift2['row']))
		except Exception, e:
			self.node.logger.exception('Calibration measurement failed: %s' % e)
		## return to original beam tilt
		self.instrument.tem.BeamTilt = beamtilt

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
			self.node.logger.debug('Beam tilt %s' % beamtilt)

			### apply misalignment, this is the base value
			### from which the two equal and opposite tilts
			### are made
			bt0 = dict(beamtilt)
			bt0[tilt_axis] += tilt_m
			state0 = data.ScopeEMData(initializer={'beam tilt':bt0})
			self.node.logger.debug('State 0 %s' % (state0,))
			### create the two equal and opposite tilted states
			statepos = data.ScopeEMData(initializer={'beam tilt':dict(bt0)})
			stateneg = data.ScopeEMData(initializer={'beam tilt':dict(bt0)})

			statepos['beam tilt'][tilt_axis] += tilt_t
			self.node.logger.debug('State positive %s' % (statepos,))
			stateneg['beam tilt'][tilt_axis] -= tilt_t
			self.node.logger.debug('State negative %s' % (stateneg,))

			shiftinfo = self.measureStateShift(state0, statepos, 1, settle=0.25)
			pixelshift1 = shiftinfo['pixel shift']

			shiftinfo = self.measureStateShift(state0, stateneg, 1, settle=0.25)
			pixelshift2 = shiftinfo['pixel shift']
			self.node.logger.info('Pixel shift 1 %s, Pixel shift 2 %s'
														% (pixelshift1, pixelshift2))
		finally:
			## return to original beam tilt
			self.instrument.tem.BeamTilt = beamtilt

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
		tem = scope['tem']
		ccdcamera = camera['ccdcamera']

		pixrow = pixelshift['row'] * biny
		pixcol = pixelshift['col'] * binx
		pixvect = (pixrow, pixcol)

		matrix = self.retrieveMatrix(tem, ccdcamera, par, ht, mag)

		change = Numeric.matrixmultiply(matrix, pixvect)
		changex = change[0]
		changey = change[1]

		### take into account effect of alpha tilt on Y stage pos
		if par == 'stage position':
			if 'a' in scope[par] and scope[par]['a'] is not None:
				alpha = scope[par]['a']
				changey = changey / Numeric.cos(alpha)

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
		tem = scope['tem']
		cam = camera['ccdcamera']
		newshift = dict(shift)

		### take into account effect of alpha tilt on Y stage pos
		if par == 'stage position' and 'a' in scope[par] and scope[par]['a'] is not None:
			alpha = scope[par]['a']
			newshift['y'] = newshift['y'] * Numeric.cos(alpha)
		vect = (newshift['x'], newshift['y'])

		matrix = self.retrieveMatrix(tem, cam, par, ht, mag)
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

class ImageBeamShiftCalibrationClient(ImageShiftCalibrationClient):
	def __init__(self, node):
		ImageShiftCalibrationClient.__init__(self, node)
		self.beamcal = BeamShiftCalibrationClient(node)

	def transform(self, pixelshift, scope, camera):
		scope2 = ImageShiftCalibrationClient.transform(self, pixelshift, scope, camera)
		## do beam shift in oposite direction
		opposite = {'row': -pixelshift['row'], 'col': -pixelshift['col']}
		scope3 = self.beamcal.transform(opposite, scope2, camera)
		return scope3

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
		caldata['session'] = self.node.session
		caldata['tem'] = self.instrument.getTEMData()
		caldata['ccdcamera'] = self.instrument.getCCDCameraData()
		caldata['label'] = label
		caldata['high tension'] = ht
		caldata['magnification'] = mag
		caldata['axis'] = axis
		caldata['angle'] = angle
		caldata['mean'] = mean
		self.node.publish(caldata, database=True, dbforce=True)

	def researchMagCalibration(self, tem, cam, ht, mag, axis):
		qinst = data.StageModelMagCalibrationData(magnification=mag, axis=axis)
		qinst['high tension'] = ht
		if cam is None:
			qinst['tem'] = self.instrument.getTEMData()
		else:
			qinst['tem'] = tem
		if tem is None:
			qinst['ccdcamera'] = self.instrument.getCCDCameraData()
		else:
			qinst['ccdcamera'] = cam

		caldatalist = self.node.research(datainstance=qinst, results=1)
		if len(caldatalist) > 0:
			caldata = caldatalist[0]
		else:
			caldata = None
		return caldata

	def retrieveMagCalibration(self, tem, cam, ht, mag, axis):
		caldata = self.researchMagCalibration(tem, cam, ht, mag, axis)
		if caldata is None:
			raise RuntimeError('no model mag calibration')
		else:
			caldata2 = dict(caldata)
			return caldata2

	def timeMagCalibration(self, tem, cam, ht, mag, axis):
		caldata = self.researchMagCalibration(tem, cam, ht, mag, axis)
		if caldata is None:
			timeinfo = None
		else:
			timeinfo = caldata.timestamp
		return timeinfo

	def storeModelCalibration(self, label, axis, period, a, b):
		caldata = data.StageModelCalibrationData()
		caldata['session'] = self.node.session
		caldata['tem'] = self.instrument.getTEMData()
		caldata['ccdcamera'] = self.instrument.getCCDCameraData()
		caldata['label'] = label 
		caldata['axis'] = axis
		caldata['period'] = period
		## force it to be 2 dimensional so sqldict likes it
		a.shape = (1,len(a))
		b.shape = (1,len(b))
		caldata['a'] = a
		caldata['b'] = b

		self.node.publish(caldata, database=True, dbforce=True)

	def researchModelCalibration(self, tem, ccdcamera, axis):
		qinst = data.StageModelCalibrationData(axis=axis)
		if tem is None:
			qinst['tem'] = self.instrument.getTEMData()
		else:
			qinst['tem'] = tem
		if ccdcamera is None:
			qinst['ccdcamera'] = self.instrument.getCCDCameraData()
		else:
			qinst['ccdcamera'] = ccdcamera
		caldatalist = self.node.research(datainstance=qinst, results=1)
		if len(caldatalist) > 0:
			caldata = caldatalist[0]
		else:
			caldata = None
		return caldata

	def retrieveModelCalibration(self, tem, ccd, axis):
		caldata = self.researchModelCalibration(tem, ccd, axis)
		if caldata is None:
			raise RuntimeError('no model calibration')
		else:
			self.node.logger.info('Period %s' % caldata['period'])
			self.node.logger.info('A %s %s' % (caldata['a'], caldata['a'].shape))
			self.node.logger.info('B %s %s' % (caldata['b'], caldata['b'].shape))
			## return it to rank 0 array
			caldata2 = {}
			caldata2['axis'] = caldata['axis']
			caldata2['period'] = caldata['period']
			caldata2['a'] = Numeric.ravel(caldata['a']).copy()
			caldata2['b'] = Numeric.ravel(caldata['b']).copy()
			return caldata2

	def timeModelCalibration(self, tem, cam, axis):
		caldata = self.researchModelCalibration(tem, cam, axis)
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
			raise RuntimeError('no measurements')
		self.node.logger.info('len(measurements) %d' % len(measurements))
		ht = measurements[0]['high tension']
		datapoints = []
		for measurement in measurements:
			if measurement['high tension'] != ht:
				raise RuntimeError('inconsistent high tension in measurements')
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
		tem = scope['tem']
		ccd = camera['ccdcamera']

		## do modifications to newstage here
		xmodcal = self.retrieveModelCalibration(tem, ccd, 'x')
		ymodcal = self.retrieveModelCalibration(tem, ccd, 'y')
		self.node.logger.debug('x model a %s' % xmodcal['a'])
		self.node.logger.debug('x model b %s' % xmodcal['b'])
		self.node.logger.debug('y model a shape %s' % ymodcal['a'].shape)
		self.node.logger.debug('y model b shape %s' % ymodcal['b'].shape)
		xmod = gonmodel.GonModel()
		xmod.fromDict(xmodcal)
		ymod = gonmodel.GonModel()
		ymod.fromDict(ymodcal)

		xmagcal = self.retrieveMagCalibration(tem, ccd, scope['high tension'], scope['magnification'], 'x')
		ymagcal = self.retrieveMagCalibration(tem, ccd, scope['high tension'], scope['magnification'], 'y')
		self.node.logger.debug('x mag cal %s' % (xmagcal,))
		self.node.logger.debug('y mag cal %s' % (ymagcal,))


		delta = self.pixtix(xmod, ymod, xmagcal, ymagcal, curstage['x'], curstage['y'], pixcol, pixrow)

		### take into account effect of alpha tilt on Y stage pos
		if 'a' in curstage and curstage['a'] is not None:
			alpha = curstage['a']
			delta['y'] = delta['y'] / Numeric.cos(alpha)

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
		self.node.logger.info('Current position delta %s' % current)
		curx = current['stage position']['x']
		cury = current['stage position']['y']

		xmodfile = self.modfilename('x')
		ymodfile = self.modfilename('y')
		magfile = self.magfilename(mag)

		deltagon = self.pixtix(xmodfile,ymodfile,magfile,curx,cury,delta_col,delta_row)

		current['stage position']['x'] += deltagon['x']
		current['stage position']['y'] += deltagon['y']
		self.node.logger.info('Current position after delta %s' % current)

		self.instrument.tem.StagePosition = current

class EucentricFocusClient(CalibrationClient):
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def researchEucentricFocus(self, ht, mag, tem=None, ccdcamera=None):
		query = data.EucentricFocusData()
		if tem is None:
			query['tem'] = self.instrument.getTEMData()
		else:
			query['tem'] = tem
		if ccdcamera is None:
			query['ccdcamera'] = self.instrument.getCCDCameraData()
		else:
			query['ccdcamera'] = ccdcamera
		query['high tension'] = ht
		query['magnification'] = mag
		datalist = self.node.research(datainstance=query, results=1)
		if datalist:
			eucfoc = datalist[0]
		else:
			eucfoc = None
		return eucfoc

	def publishEucentricFocus(self, ht, mag, ef):
		newdata = data.EucentricFocusData()
		newdata['session'] = self.node.session
		newdata['tem'] = self.instrument.getTEMData()
		newdata['ccdcamera'] = self.instrument.getCCDCameraData()
		newdata['high tension'] = ht
		newdata['magnification'] = mag
		newdata['focus'] = ef
		self.node.publish(newdata, database=True, dbforce=True)

