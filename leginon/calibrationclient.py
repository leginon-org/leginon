# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/calibrationclient.py,v $
# $Revision: 1.196 $
# $Name: not supported by cvs2svn $
# $Date: 2007-02-16 21:15:22 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import node, data, event
import numarray
import numarray.linear_algebra
import math
import correlator
import peakfinder
import time
import sys
import threading
import gonmodel
import imagefun
import tiltcorrector

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
		self.tiltcorrector = tiltcorrector.TiltCorrector(node)
		self.stagetiltcorrector = tiltcorrector.VirtualStageTilter(node)

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

	def correctTilt(self, imagedata):
		self.tiltcorrector.correct_tilt(imagedata)

	def acquireStateImage(self, state, publish_image=False, settle=0.0, correct_tilt=False, corchannel=0):
		self.node.logger.debug('Acquiring image...')
		## acquire image at this state

		if state is not None:
			newemdata = data.ScopeEMData(initializer=state)
			self.instrument.setData(newemdata)

		self.node.startTimer('acquire state pause')
		time.sleep(settle)
		self.node.stopTimer('acquire state pause')

		self.instrument.setCorrectionChannel(corchannel)
		imagedata = self.instrument.getData(data.CorrectedCameraImageData)
		if correct_tilt:
			self.correctTilt(imagedata)
		actual_state = imagedata['scope']

		if publish_image:
			self.node.publish(imagedata, pubevent=True)

		self.node.setImage(imagedata['image'].astype(numarray.Float), 'Image')

		## should find image stats to help determine validity of image
		## in correlations
		image_stats = None

		info = {'requested state': state, 'imagedata': imagedata, 'image stats': image_stats}
		return info

	def measureStateShift(self, state1, state2, publish_images=False, settle=0.0, drift_threshold=None, target=None, correct_tilt=False, correlation_type=None):
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
		corchannel=0
		info1 = self.acquireStateImage(state1, publish_images, settle, correct_tilt=correct_tilt, corchannel=corchannel)
		binning = info1['imagedata']['camera']['binning']['x']
		imagedata1 = info1['imagedata']
		imagecontent1 = imagedata1
		stats1 = info1['image stats']
		actual1 = imagecontent1['scope']
		t0 = actual1['system time']
		self.numimage1 = imagecontent1['image']
		self.displayImage(self.numimage1)
		self.correlator.insertImage(self.numimage1)

		self.checkAbort()

		## for drift check, continue to acquire at state1
		if drift_threshold is None:
			driftdata = None
		else:
			self.node.logger.info('Checking for drift...')

			## use opposite correction channel
			if corchannel:
				corchannel = 0
			else:
				corchannel = 1
			## state=None means do not set the values on the scope
			info1 = self.acquireStateImage(None, publish_images, settle, correct_tilt=correct_tilt, corchannel=corchannel)
			imagedata1 = info1['imagedata']
			imagecontent1 = imagedata1
			stats1 = info1['image stats']
			actual1 = imagecontent1['scope']
			t1 = actual1['system time']
			self.numimage1 = imagecontent1['image']
			self.displayCorrelation(self.numimage1)
			self.correlator.insertImage(self.numimage1)

			self.node.logger.info('Correlating...')
			self.node.startTimer('shift correction')
			if correlation_type is None:
				try:
					correlation_type = self.node.settings['correlation type']
				except KeyError:
					raise ValueError
			if correlation_type == 'cross':
				pcimage = self.correlator.crossCorrelate()
			elif correlation_type == 'phase':
				pcimage = self.correlator.phaseCorrelate()
			else:
				raise RuntimeError('invalid correlation type')
			self.node.stopTimer('shift correction')

			self.node.logger.debug('Peak finding...')
			self.peakfinder.setImage(pcimage)
			self.node.startTimer('shift peak')
			self.peakfinder.subpixelPeak()
			self.node.stopTimer('shift peak')
			peak = self.peakfinder.getResults()
			pixelpeak = peak['subpixel peak']
			self.node.startTimer('shift display')
			self.displayCorrelation(pcimage)
			self.displayPeak(pixelpeak)
			self.node.stopTimer('shift display')

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

			pixels = binning * abs(shift[0] + 1j * shift[1])
			# convert to meters
			mag = actual1['magnification']
			pixelsize = self.getPixelSize(mag)
			self.node.logger.info('pixelsize: %s, binning: %s' % (pixelsize, binning))
			meters = pixelsize * pixels
			drift = meters / seconds
			self.node.logger.info('Seconds %f, pixels %f, meters %.4e, meters/second %.4e'
							% (seconds, pixels, meters, drift))
			if drift > drift_threshold:
				## declare drift above threshold
				self.node.declareDrift('threshold')
				raise Drifting()

		self.checkAbort()

		self.node.logger.info('Acquiring image (2 of 2)')
		## use opposite correction channel
		if corchannel:
			corchannel = 0
		else:
			corchannel = 1
		info2 = self.acquireStateImage(state2, publish_images, settle, correct_tilt=correct_tilt, corchannel=corchannel)
		imagedata2 = info2['imagedata']
		imagecontent2 = imagedata2
		stats2 = info2['image stats']
		actual2 = imagecontent2['scope']
		self.numimage2 = imagecontent2['image']
		self.displayImage(self.numimage2)
		self.correlator.insertImage(self.numimage2)

		actual = (actual1, actual2)
		shiftinfo = {}

		self.checkAbort()

		self.node.logger.info('Calculating shift between the images...')
		self.node.logger.debug('Correlating...')
		self.node.startTimer('shift correlation')
		if correlation_type is None:
			try:
				correlation_type = self.node.settings['correlation type']
			except KeyError:
				correlation_type = 'phase'
		if correlation_type == 'cross':
			pcimage = self.correlator.crossCorrelate()
		elif correlation_type == 'phase':
			pcimage = self.correlator.phaseCorrelate()
		else:
			raise RuntimeError('invalid correlation type')
		self.node.stopTimer('shift correlation')

		## peak finding
		self.node.logger.debug('Peak finding...')
		self.peakfinder.setImage(pcimage)
		self.node.startTimer('shift peak')
		self.peakfinder.subpixelPeak()
		self.node.stopTimer('shift peak')
		peak = self.peakfinder.getResults()
		self.node.logger.debug('Peak minsum %f' % peak['minsum'])

		pixelpeak = peak['subpixel peak']
		self.node.startTimer('shift display')
		self.displayCorrelation(pcimage)
		self.displayPeak(pixelpeak)
		self.node.stopTimer('shift display')

		peakvalue = peak['subpixel peak value']
		shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)
		self.node.logger.debug('pixel shift (row,col): %s' % (shift,))

		## need unbinned result
		binx = imagecontent1['camera']['binning']['x']
		biny = imagecontent1['camera']['binning']['y']
		unbinned = {'row':shift[0] * biny, 'col': shift[1] * binx}

		shiftinfo.update({'actual states': actual, 'pixel shift': unbinned, 'peak value': peakvalue, 'shape':pcimage.shape, 'stats': (stats1, stats2), 'driftdata': driftdata})
		return shiftinfo

	def displayImage(self, im):
		try:
			self.node.setImage(im.astype(numarray.Float), 'Image')
		except:
			pass

	def displayCorrelation(self, im):
		try:
			self.node.setImage(im.astype(numarray.Float), 'Correlation')
		except:
			pass

	def displayPeak(self, rowcol=None):
		if rowcol is None:
			targets = []
		else:
			# target display requires x,y order not row,col
			targets = [(rowcol[1], rowcol[0])]
		try:
			self.node.setTargets(targets, 'Peak')
		except:
			pass

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
		self.node.logger.debug('Specimen pixel size %.4e' % specimen_pixel_size)
		exp_time = imagedata['camera']['exposure time'] / 1000.0
		numdata = imagedata['image']
		sensitivity = self.retrieveSensitivity(ht, tem, ccdcamera)
		self.node.logger.debug('Sensitivity %.2f' % sensitivity)
		mean_counts = imagefun.mean(numdata) / (binning**2)
		self.node.logger.debug('Mean counts %.1f' % mean_counts)
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
		caldatalist = self.node.research(datainstance=queryinstance)
		return caldatalist

	def retrievePixelSize(self, tem, ccdcamera, mag):
		'''
		finds the requested pixel size using magnification
		'''
		caldatalist = self.researchPixelSizeData(tem, ccdcamera, mag)
		if len(caldatalist) < 1:
			raise NoPixelSizeError()
		caldata = caldatalist[0]
		pixelsize = caldata['pixelsize']
		return pixelsize

	def time(self, tem, ccdcamera, mag):
		pdata = self.researchPixelSizeData(tem, ccdcamera, mag)
		if len(pdata) < 1:
			timeinfo = None
		else:
			timeinfo = pdata[0].timestamp
		return timeinfo

	def retrieveLastPixelSizes(self, tem, camera):
		caldatalist = self.researchPixelSizeData(tem, camera, None)
		last = {}
		for caldata in caldatalist:
			try:
				mag = caldata['magnification']
			except:
				print 'CALDATA', caldata
				raise
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
			excstr = 'no query results for %s, %s, %s, %seV, %sx' % (tem['name'], ccdcamera['name'], caltype, ht, mag)
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
		newmatrix = numarray.array(matrix, numarray.Float64)
		caldata = data.MatrixCalibrationData(session=self.node.session, magnification=mag, type=type, matrix=matrix, tem=tem, ccdcamera=ccdcamera)
		caldata['high tension'] = ht
		self.node.publish(caldata, database=True, dbforce=True)

	def getMatrixAngles(self, matrix):
		matrix = numarray.linear_algebra.inverse(matrix)
		x_shift_row = matrix[0, 0]
		x_shift_col = matrix[1, 0]
		y_shift_row = matrix[0, 1]
		y_shift_col = matrix[1, 1]

		# calculations invert image coordinates (+y top, -y bottom)
		# angle from the x shift of the parameter
		theta_x = math.atan2(-x_shift_row, x_shift_col)
		# angle from the y shift of the parameter
		theta_y = math.atan2(-y_shift_row, -y_shift_col)

		return theta_x, theta_y

	def getAngles(self, *args):
		matrix = self.retrieveMatrix(*args)
		return self.getMatrixAngles(matrix)

class BeamTiltCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def getBeamTilt(self):
		try:
			return self.instrument.tem.BeamTilt
		except:
			return None

	def setBeamTilt(self, bt):
		self.instrument.tem.BeamTilt = bt

	def storeRotationCenter(self, tem, ht, mag, beamtilt):
		rc = data.RotationCenterData()
		rc['high tension'] = ht
		rc['magnification'] = mag
		rc['beam tilt'] = beamtilt
		rc['tem'] = tem
		rc['session'] = self.node.session
		self.node.publish(rc, database=True, dbforce=True)

	def retrieveRotationCenter(self, tem, ht, mag):
		rc = data.RotationCenterData()
		rc['tem'] = tem
		rc['high tension'] = ht
		rc['magnification'] = mag
		results = self.node.research(datainstance=rc, results=1)
		if results:
			return results[0]['beam tilt']
		else:
			return None

	def measureRotationCenter(self, defocus1, defocus2, drift_threshold=None, target=None, correlation_type=None, settle=0.5):
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		try:
			fmatrix = self.retrieveMatrix(tem, cam, 'defocus', ht, mag)
		except NoMatrixCalibrationError:
				raise RuntimeError('missing calibration matrix')

		state1 = data.ScopeEMData()
		state2 = data.ScopeEMData()
		state1['defocus'] = defocus1
		state2['defocus'] = defocus2

		shiftinfo = self.measureStateShift(state1, state2, settle=settle, drift_threshold=drift_threshold, target=target, correlation_type=correlation_type)
		shift = shiftinfo['pixel shift']
		d = shift['row'],shift['col']
		bt = self.solveEq10_t(fmatrix, defocus1, defocus2, d)
		return {'x':bt[0], 'y':bt[1]}

	def measureDefocusStig(self, tilt_value, publish_images=False, drift_threshold=None, stig=True, target=None, correct_tilt=False, correlation_type=None, settle=0.5):
		self.abortevent.clear()
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		try:
			fmatrix = self.retrieveMatrix(tem, cam, 'defocus', ht, mag)
		except NoMatrixCalibrationError:
				raise RuntimeError('missing calibration matrix')
		if stig:
			try:
				amatrix = self.retrieveMatrix(tem, cam, 'stigx', ht, mag)
				bmatrix = self.retrieveMatrix(tem, cam, 'stigy', ht, mag)
			except NoMatrixCalibrationError:
				stig = False

		tiltcenter = self.getBeamTilt()
		#self.node.logger.info('Tilt center: x = %g, y = %g.' % (tiltcenter['x'], tiltcenter['y']))

		### need two tilt displacement measurements
		### easiest is one on each tilt axis
		shifts = {}
		tilts = {}
		self.checkAbort()
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
				shiftinfo = self.measureStateShift(state1, state2, publish_images, settle=settle, drift_threshold=drift_threshold, target=target, correct_tilt=correct_tilt, correlation_type=correlation_type)
			except Abort:
				break
			except Drifting:
				## return to original beam tilt
				self.instrument.tem.BeamTilt = tiltcenter
				#self.node.logger.info('Returned to tilt center: x = %g, y = %g.' % (tiltcenter['x'], tiltcenter['y']))

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
		#self.node.logger.info('Returned to tilt center: x = %g, y = %g.' % (tiltcenter['x'], tiltcenter['y']))

		self.checkAbort()

		#self.node.logger.info('Tilts %s, shifts %s' % (tilts, shifts))

		d1 = shifts['x']
		t1 = tilts['x']
		d2 = shifts['y']
		t2 = tilts['y']
		if stig:
			sol = self.solveEq10(fmatrix,amatrix,bmatrix,d1,t1,d2,t2)
			#self.node.logger.info('Defocus: %g, stig.: (%g, %g), min. = %g' % (sol['defocus'], sol['stigx'], sol['stigy'], sol['min']))
		else:
			sol = self.solveEq10_nostig(fmatrix,d1,t1,d2,t2)
			#self.node.logger.info('Defocus: %g, stig.: (not measured), min. = %g' % (sol['defocus'], sol['min']))

		sol['lastdrift'] = lastdrift
		return sol

	def solveEq10(self, F, A, B, d1, t1, d2, t2):
		#print 'SOLVE STIG'
		'''
		This solves Equation 10 from Koster paper
		 F,A,B are the defocus, stigx, and stigy calibration matrices
		   (all must be 2x2 numarray arrays)
		 d1,d2 are displacements resulting from beam tilts t1,t2
		   (all must be 2x1 numarray arrays)
		'''
		## produce the matrix and vector for least squares fit
		v = numarray.zeros((4,), numarray.Float64)
		v[:2] = d1
		v[2:] = d2

		## plug calibration matrices and tilt vectors into M
		M = numarray.zeros((4,3), numarray.Float64)

		t1 = numarray.array(t1)
		t2 = numarray.array(t2)

		# t1 on first two rows
		M[:2,0] = numarray.matrixmultiply(F,t1)
		M[:2,1] = numarray.matrixmultiply(A,t1)
		M[:2,2] = numarray.matrixmultiply(B,t1)
		# t2 on second two rows
		M[2:,0] = numarray.matrixmultiply(F,t2)
		M[2:,1] = numarray.matrixmultiply(A,t2)
		M[2:,2] = numarray.matrixmultiply(B,t2)

		solution = numarray.linear_algebra.linear_least_squares(M, v)
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
		   (all must be 2x2 numarray arrays)
		 d1,d2 are displacements resulting from beam tilts t1,t2
		   (all must be 2x1 numarray arrays)
		'''
		## produce the matrix and vector for least squares fit
		v = numarray.zeros((4,), numarray.Float64)
		v[:2] = d1
		v[2:] = d2

		## plug calibration matrices and tilt vectors into M
		M = numarray.zeros((4,1), numarray.Float64)

		# t1 on first two rows
		M[:2,0] = numarray.matrixmultiply(F,t1)
		# t2 on second two rows
		M[2:,0] = numarray.matrixmultiply(F,t2)

		solution = numarray.linear_algebra.linear_least_squares(M, v)
		result = {
			'defocus': solution[0][0],
			'stigx': None,
			'stigy': None,
			'min': float(solution[1][0])
			}
		return result

	def solveEq10_t(self, F, f1, f2, d):
		'''
		This solves t (misalignment) in equation 10 from Koster paper
		given a displacement resulting from a defocus change
		F is defocus calibration matric
		f1, f2 are two defoci used to measure displacement d (row,col)
		'''
		a = (f2-f1) * F
		b = numarray.array(d, numarray.Float)
		tiltx,tilty = numarray.linear_algebra.solve_linear_equations(a,b)
		return tiltx,tilty

	def eq11(self, shifts, parameters, beam_tilt):
		'''
		Equation (11)
		Calculates one column of a beam tilt calibration matrix given
		the following arguments:
		  shifts - pixel shift resulting from tilt at parameters
		  parameters - value of microscope parameters causing shifts
		  beam_tilt - value of the induced beam tilt
		'''
		shift = numarray.zeros((2,), numarray.Float)
		shift[0] = shifts[1]['row'] - shifts[0]['row']
		shift[1] = shifts[1]['col'] - shifts[0]['col']

		try:
			return shift/(2*(parameters[1] - parameters[0])*beam_tilt)
		except ZeroDivisionError:
			raise ValueError('invalid measurement, scale is zero')

	def measureDisplacements(self, tilt_axis, tilt_value, states, **kwargs):
		'''
		This measures the displacements that go into eq. (11)
		Each call of this function acquires four images
		and returns two shift displacements.
		'''
		
		# try/finally to be sure we return to original beam tilt
		try:
			# set up to measure states
			beam_tilt = self.instrument.tem.BeamTilt
			beam_tilts = (dict(beam_tilt), dict(beam_tilt))
			beam_tilts[0][tilt_axis] += tilt_value
			beam_tilts[1][tilt_axis] -= tilt_value

			pixel_shifts = []
			m = 'Beam tilt measurement (%d of '
			m += str(len(states))
			m += '): (%g, %g) pixels'
			for i, state in enumerate(states):
				args = []
				for bt in beam_tilts:
					s = data.ScopeEMData(initializer=state)
					s['beam tilt'] = bt
					args.append(s)
			
				result = self.measureStateShift(*args, **kwargs)
				pixel_shift = result['pixel shift']
				pixel_shifts.append(pixel_shift)

				args = (i + 1, pixel_shift['col'], pixel_shift['row'])
				self.node.logger.info(m % args)
		finally:
			# return to original beam tilt
			self.instrument.tem.BeamTilt = beam_tilt

		return tuple(pixel_shifts)

	def measureMatrixC(self, m, t):
		'''
		determine matrix C, the coma-free matrix
		m = misalignment value, t = tilt value
		'''
		# original beam tilt
		btorig = self.getBeamTilt()
		### try/finally to be sure we return to original beam tilt
		try:
			bt0 = btorig['x'], btorig['y']
			## tilt x makes first column, tilt y makes second column
			matrix = numarray.zeros((2,2), numarray.Float32)
			for axisn, axisname in ((0,'x'),(1,'y')):
				## misalign + then -
				dc = {}
				for msign in (1,-1):
					misbt = list(bt0)
					misbt[axisn] += msign*m
					btdict = {'beam tilt': {'x':misbt[0], 'y':misbt[1]}}
					state0 = data.ScopeEMData(initializer=btdict)
					## tilt + then -
					displace = {}
					for tsign in (1,-1):
						tiltbt = list(misbt)
						tiltbt[axisn] += tsign*t
						btdict = {'beam tilt': {'x':tiltbt[0], 'y':tiltbt[1]}}
						state1 = data.ScopeEMData(initializer=btdict)
						shiftinfo = self.measureStateShift(state0, state1)
						pixelshift = shiftinfo['pixel shift']
						displace[tsign] = pixelshift['row'],pixelshift['col']
					## calculate displacemnt diff
					dc[msign] = numarray.subtract(displace[-1],displace[1])
				## calculate matrix column
				matrix[:,axisn] = (dc[-1]-dc[1]) / 2.0 / m
		finally:
			## return to original beam tilt
			self.setBeamTilt(btorig)

		return matrix

	def measureComaFree(self, tilt_value):

		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		try:
			cmatrix = self.retrieveMatrix(tem, cam, 'coma-free', ht, mag)
		except NoMatrixCalibrationError:
			raise RuntimeError('missing calibration matrix')

		btorig = self.getBeamTilt()
		btdict = {'beam tilt': btorig}
		state0 = data.ScopeEMData(initializer=btdict)
		### try/finally to be sure we return to original beam tilt
		try:
			displace = {}
			for tsign in (1,-1):
				tiltbt = dict(btorig)
				tiltbt['x'] += tsign*tilt_value
				tiltbt['y'] += tsign*tilt_value
				btdict = {'beam tilt': tiltbt}
				state1 = data.ScopeEMData(initializer=btdict)
				shiftinfo = self.measureStateShift(state0, state1)
				pixelshift = shiftinfo['pixel shift']
				displace[tsign] = pixelshift['row'],pixelshift['col']
		finally:
			self.setBeamTilt(btorig)

		## calculate displacemnt diff
		dc = numarray.subtract(displace[-1],displace[1])
		cftilt = numarray.linear_algebra.solve_linear_equations(cmatrix, dc)
		return cftilt

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
		matrix = numarray.array([[xrow,yrow],[xcol,ycol]],numarray.Float)
		matrix = numarray.linear_algebra.inverse(matrix)
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
		matrix = self.retrieveMatrix(tem, ccdcamera, par, ht, mag)

		pixrow = pixelshift['row'] * biny
		pixcol = pixelshift['col'] * binx
		pixvect = numarray.array((pixrow, pixcol))

		change = numarray.matrixmultiply(matrix, pixvect)
		changex = change[0]
		changey = change[1]

		### take into account effect of alpha tilt on Y stage pos
		if par == 'stage position':
			if 'a' in scope[par] and scope[par]['a'] is not None:
				alpha = scope[par]['a']
				changey = changey / numarray.cos(alpha)

		new = data.ScopeEMData(initializer=scope)
		## make a copy of this since it will be modified
		new[par] = dict(scope[par])
		new[par]['x'] += changex
		new[par]['y'] += changey
		return new

	def itransform(self, position, scope, camera):
		parameter = self.parameter()
		args = (
			scope['tem'],
			camera['ccdcamera'],
			parameter,
			scope['high tension'],
			scope['magnification'],
		)
		matrix = self.retrieveMatrix(*args)
		inverse_matrix = numarray.linear_algebra.inverse(matrix)

		shift = dict(position)
		shift['x'] -= scope[parameter]['x']
		shift['y'] -= scope[parameter]['y']

		# take into account effect of stage alpha tilt on y stage position
		if parameter == 'stage position':
			if 'a' in scope[parameter] and scope[parameter]['a'] is not None:
				alpha = scope[parameter]['a']
				shift['y'] = shift['y']*numarray.cos(alpha)

		shift_vector = numarray.array((shift['x'], shift['y']))
		pixel = numarray.matrixmultiply(inverse_matrix, shift_vector)

		pixel_shift = {
			'row': pixel[0]/camera['binning']['y'],
			'col': pixel[1]/camera['binning']['x'],
		}

		return pixel_shift

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

	def pixelToPixel(self, tem, ccdcamera, ht, mag1, mag2, p1):
		'''
		Using stage position as a global coordinate system, we can
		do pixel to pixel transforms between mags.
		This function will calculate a pixel vector at mag2, given
		a pixel vector at mag1.
		'''
		par = self.parameter()
		matrix1 = self.retrieveMatrix(tem, ccdcamera, par, ht, mag1)
		matrix2 = self.retrieveMatrix(tem, ccdcamera, par, ht, mag2)
		matrix2inv = numarray.linear_algebra.inverse(matrix2)
		p1 = numarray.array(p1)
		stagepos = numarray.matrixmultiply(matrix1, p1)
		p2 = numarray.matrixmultiply(matrix2inv, stagepos)
		return p2

class StageTiltCalibrationClient(StageCalibrationClient):
	def __init__(self, node):
		StageCalibrationClient.__init__(self, node)

	def measureZ(self, tilt_value, correlation_type=None):
		'''
		This is currently hard coded based on our Tecnai, but should be calibrated
		for every scope.
		For a positive stage tilt on Tecnai:
			If Z is too positive, Y moves negative
			If Z is too negative, Y moves positive
		'''
		orig_a = self.instrument.tem.StagePosition['a']

		## do positive tilt and measure image shift
		state1 = data.ScopeEMData()
		state2 = data.ScopeEMData()
		state1['stage position'] = {'a':-tilt_value}
		state2['stage position'] = {'a':tilt_value}
		shiftinfo = self.measureStateShift(state1, state2, correlation_type=correlation_type)
		self.instrument.tem.StagePosition = {'a':orig_a}

		state1,state2 = shiftinfo['actual states']
		pixelshift = shiftinfo['pixel shift']
		#psize = self.getPixelSize(state1['magnification'])
		#dist = psize * math.hypot(pixelshift['row'], pixelshift['col'])
		
		# fake the current state for the transform with alpha = 0
		scope = data.ScopeEMData(initializer=state1)
		scope['stage position']['a'] = 0.0
		cam = data.CameraEMData()
		# measureStateShift already unbinned it, so fake cam bin = 1
		cam['binning'] = {'x':1,'y':1}
		cam['ccdcamera'] = self.instrument.getCCDCameraData()
		# get the virtual x,y movement
		newscope = self.transform(pixelshift, scope, cam)
		# y component is all we care about to get Z
		y = newscope['stage position']['y'] - scope['stage position']['y']
		z = y / 2.0 / math.sin(tilt_value)
		return z

	def measureTiltAxisLocation(self, tilt_value, correlation_type=None):
		'''
		measure position on image of tilt axis
		'''
		orig_a = self.instrument.tem.StagePosition['a']

		state0 = data.ScopeEMData()
		state1 = data.ScopeEMData()
		state2 = data.ScopeEMData()
		state0['stage position'] = {'a':0}
		state1['stage position'] = {'a':-tilt_value}
		state2['stage position'] = {'a':tilt_value}

		self.node.logger.info('acquiring tilt=0')
		self.instrument.setData(state0)
		imagedata0 = self.instrument.getData(data.CorrectedCameraImageData)
		im0 = imagedata0['image']
		self.displayImage(im0)

		self.node.logger.info('acquiring tilt=%s' % (-tilt_value,))
		self.instrument.setData(state1)
		imagedata1 = self.instrument.getData(data.CorrectedCameraImageData)
		self.stagetiltcorrector.undo_tilt(imagedata1)
		im1 = imagedata1['image']
		self.displayImage(im1)

		self.instrument.tem.StagePosition = {'a':orig_a}

		self.node.logger.info('correlating')
		self.correlator.setImage(0, im0)
		self.correlator.setImage(1, im1)
		if correlation_type == 'phase':
			pc = self.correlator.phaseCorrelate()
		else:
			pc = self.correlator.crossCorrelate()
		self.displayCorrelation(pc)

		peak01 = self.peakfinder.subpixelPeak(pc)
		shift01 = correlator.wrap_coord(peak01, pc.shape)
		self.displayPeak(peak01)

		pixelshift = {'row':shift01[0], 'col':shift01[1]}
		self.node.logger.info('measured pixel shift: %s' % (pixelshift,))

		## convert pixel shift into stage movement
		newscope = self.transform(pixelshift, imagedata0['scope'], imagedata0['camera'])
		## only want the y offset (distance from tilt axis)
		deltay = newscope['stage position']['y'] - imagedata0['scope']['stage position']['y']
		self.node.logger.info('stage delta y: %s' % (deltay,))
		shift = {'x':0, 'y':deltay}
		position = dict(imagedata0['scope']['stage position'])
		position['x'] += shift['x']
		position['y'] += shift['y']
		pixelshift = self.itransform(position, imagedata0['scope'], imagedata0['camera'])
		self.node.logger.info('pixelshift for delta y: %s' % (pixelshift,))

		# after drawing lots triangles, you get this equation:
		scale = 1.0 / numarray.tan(tilt_value/2.0) / numarray.tan(tilt_value)
		pixelshift = {'row':scale*pixelshift['row'], 'col':scale*pixelshift['col']}
		self.node.logger.info('pixelshift from axis: %s' % (pixelshift,))

		return imagedata0, pixelshift

class ModeledStageCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def parameter(self):
		return 'stage position'

	def pixelToPixel(self, tem, ccdcamera, ht, mag1, mag2, p1):
		'''
		Using stage position as a global coordinate system, we can
		do pixel to pixel transforms between mags.
		This function will calculate a pixel vector at mag2, given
		a pixel vector at mag1.
		'''

		scope = data.ScopeEMData()
		scope['tem'] = tem
		scope['high tension'] = ht
		scope['stage position'] = {'x':0.0, 'y':0.0}
		camera = data.CameraEMData()
		camera['ccdcamera'] = ccdcamera
		camera['binning'] = {'x':1,'y':1}

		scope['magnification'] = mag1
		pixelshift = {'row':p1[0], 'col':p1[1]}
		newscope = self.transform(pixelshift, scope, camera)

		scope['magnification'] = mag2
		position = newscope['stage position']
		pix = self.itransform(position, scope, camera)

		return pix['row'],pix['col']

	def storeMagCalibration(self, tem, cam, label, ht, mag, axis, angle, mean):
		caldata = data.StageModelMagCalibrationData()
		caldata['session'] = self.node.session
		caldata['tem'] = tem
		caldata['ccdcamera'] = cam
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
			raise RuntimeError('no model mag calibration in axis %s'% axis)
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

	def getMatrixFromStageModelMag(self, tem, cam, ht, mag):
		try:
			caldatax = self.retrieveMagCalibration(tem, cam, ht, mag, 'x')
			caldatay = self.retrieveMagCalibration(tem, cam, ht, mag, 'y')
		except Exception, e:
			matrix = None
			self.node.logger.warning('Cannot get matrix from stage model: %s' % e)
			return matrix
			
		means = [caldatax['mean'],caldatay['mean']]
		angles = [caldatax['angle'],caldatay['angle']]
		matrix = numarray.ones((2,2), numarray.Float64)
		matrix[0, 0]=means[0]*math.sin(angles[0])
		matrix[1, 0]=means[0]*math.cos(angles[0])
		matrix[0, 1]=means[1]*math.sin(angles[1])
		matrix[1, 1]=means[1]*math.cos(angles[1])
		
		return matrix

	def storeModelCalibration(self, tem, cam, label, axis, period, a, b):
		caldata = data.StageModelCalibrationData()
		caldata['tem'] = tem
		caldata['ccdcamera'] = cam
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
			raise RuntimeError('no model calibration in axis %s'% axis)
		else:
			## return it to rank 0 array
			caldata2 = {}
			caldata2['axis'] = caldata['axis']
			caldata2['period'] = caldata['period']
			caldata2['a'] = numarray.ravel(caldata['a']).copy()
			caldata2['b'] = numarray.ravel(caldata['b']).copy()
			return caldata2

	def timeModelCalibration(self, tem, cam, axis):
		caldata = self.researchModelCalibration(tem, cam, axis)
		if caldata is None:
			timeinfo = None
		else:
			timeinfo = caldata.timestamp
		return timeinfo

	def getLabeledData(self, tem, cam, label, mag, axis):
		qdata = data.StageMeasurementData()
		qdata['tem'] = tem
		qdata['ccdcamera'] = cam
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

	def fit(self, tem, cam, label, mag, axis, terms):
		if tem is None:
			tem = self.node.instrument.getTEMData()
		if cam is None:
			cam = self.node.instrument.getCCDCameraData()
		# get data from DB
		info = self.getLabeledData(tem, cam, label, mag, axis)
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
		self.node.logger.info('model mean: %5.3e meter/pixel, angle: %6.3f radian' % (mean,angle))

		### model info
		period = mod.period
		a = mod.a
		b = mod.b
		if terms > 0:
			self.node.logger.info('model period: %6.1f micrometer' % (period*1e6,))
		
		self.storeMagCalibration(tem, cam, label, ht, mag, axis, angle, mean)
		self.storeModelCalibration(tem, cam, label, axis, period, a, b)

		matrix = self.getMatrixFromStageModelMag(tem, cam, ht, mag)
		if matrix is not None:
			self.storeMatrix(ht, mag, 'stage position', matrix, tem, cam)
		
	def fitMagOnly(self, tem, cam, label, mag, axis):
		if tem is None:
			tem = self.node.instrument.getTEMData()
		if cam is None:
			cam = self.node.instrument.getCCDCameraData()
		# get data from DB
		info = self.getLabeledData(tem, cam, label, mag, axis)
		datapoints = info['datapoints']
		ht = info['ht']
		dat = gonmodel.GonData()
		dat.import_data(mag, axis, datapoints)

		## fit a model to existing model
		modeldata = self.retrieveModelCalibration(tem, cam, axis)
		mod = gonmodel.GonModel()
		mod.fromDict(modeldata)

		mean = mod.fitInto(dat)

		### mag info
		axis = dat.axis
		mag = dat.mag
		angle = dat.angle
		self.node.logger.info('model mean: %5.3e, angle: %6.3e ' % (mean,angle))

		self.storeMagCalibration(tem, cam, label, ht, mag, axis, angle, mean)

		matrix = self.getMatrixFromStageModelMag(tem, cam, ht, mag)
		if matrix is not None:
			self.storeMatrix(ht, mag, 'stage position', matrix, tem, cam)

	def itransform(self, position, scope, camera):
		curstage = scope['stage position']

		tem = scope['tem']
		ccd = camera['ccdcamera']
		binx = camera['binning']['x']
		biny = camera['binning']['y']

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

		newx = position['x']
		newy = position['y']
		pix = self.tixpix(xmod, ymod, xmagcal, ymagcal, curstage['x'], curstage['y'], newx, newy)
		pixelshift = {'row': pix[0]/biny, 'col': pix[1]/binx}
		return pixelshift

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
			delta['y'] = delta['y'] / numarray.cos(alpha)

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

	def tixpix(self, xmod, ymod, xmagcal, ymagcal, gonx0, gony0, gonx1, gony1):
		## integrate
		gonx = xmod.integrate(gonx0,gonx1)
		gony = ymod.integrate(gony0,gony1)

		## rotate/scale
		modavgx = xmagcal['mean']
		modavgy = ymagcal['mean']
		anglex = xmagcal['angle']
		angley = ymagcal['angle']

		gonx = gonx / modavgx
		gony = gony / modavgy
	
		m = numarray.array(((numarray.cos(anglex),numarray.sin(anglex)),(numarray.cos(angley),numarray.sin(angley))), numarray.Float32)
		minv = numarray.linear_algebra.inverse(m)
		ix,iy = numarray.matrixmultiply(minv, (gonx,gony))
	
		return iy,ix
	
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

