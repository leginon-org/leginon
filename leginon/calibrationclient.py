# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/calibrationclient.py,v $
# $Revision: 1.211 $
# $Name: not supported by cvs2svn $
# $Date: 2007-05-22 19:21:07 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import node, leginondata, event
import numpy
import pyami.quietscipy
import scipy.ndimage
import math
from pyami import correlator, peakfinder, arraystats
import time
import sys
import threading
import gonmodel
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
	mover = False
	def __init__(self, node):
		self.node = node
		try:
			self.instrument = self.node.instrument
		except AttributeError:
			raise RuntimeError('CalibrationClient node needs instrument')

		self.correlator = correlator.Correlator()
		self.abortevent = threading.Event()
		self.tiltcorrector = tiltcorrector.TiltCorrector(node)
		self.stagetiltcorrector = tiltcorrector.VirtualStageTilter(node)

	def checkAbort(self):
		if self.abortevent.isSet():
			raise Abort()

	def getPixelSize(self, mag, tem=None, ccdcamera=None):
		queryinstance = leginondata.PixelSizeCalibrationData()
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

	def acquireImage(self, scope, settle=0.0, correct_tilt=False, corchannel=0):
		if scope is not None:
			newemdata = leginondata.ScopeEMData(initializer=scope)
			self.instrument.setData(newemdata)

		self.node.startTimer('calclient acquire pause')
		time.sleep(settle)
		self.node.stopTimer('calclient acquire pause')

		imagedata = self.node.acquireCorrectedCameraImageData(corchannel)
		if correct_tilt:
			self.correctTilt(imagedata)
		newscope = imagedata['scope']

		self.node.setImage(imagedata['image'], 'Image')

		return imagedata

	def measureScopeChange(self, previousimage, nextscope, settle=0.0, correct_tilt=False, correlation_type='phase'):
		'''
		Acquire an image at nextscope and correlate to previousimage
		'''

		self.checkAbort()

		# make sure previous image is in the correlator
		if self.correlator.getImage(1) is not previousimage['image']:
			self.correlator.insertImage(previousimage['image'])

		## use opposite correction channel
		corchannel = previousimage['correction channel']
		if corchannel:
			corchannel = 0
		else:
			corchannel = 1

		self.checkAbort()

		## acquire neximage
		nextimage = self.acquireImage(nextscope, settle, correct_tilt=correct_tilt, corchannel=corchannel)
		self.correlator.insertImage(nextimage['image'])

		self.checkAbort()

		## correlate
		self.node.startTimer('scope change correlation')
		if correlation_type is None:
			try:
				correlation_type = self.node.settings['correlation type']
			except KeyError:
				correlation_type = 'phase'
		if correlation_type == 'cross':
			cor = self.correlator.crossCorrelate()
		elif correlation_type == 'phase':
			cor = self.correlator.phaseCorrelate()
		else:
			raise RuntimeError('invalid correlation type')
		self.node.stopTimer('scope change correlation')
		self.displayCorrelation(cor)

		## find peak
		self.node.startTimer('shift peak')
		peak = peakfinder.findSubpixelPeak(cor)
		self.node.stopTimer('shift peak')

		self.node.logger.debug('Peak %s' % (peak,))

		pixelpeak = peak['subpixel peak']
		self.node.startTimer('shift display')
		self.displayPeak(pixelpeak)
		self.node.stopTimer('shift display')

		peakvalue = peak['subpixel peak value']
		shift = correlator.wrap_coord(peak['subpixel peak'], cor.shape)
		self.node.logger.debug('pixel shift (row,col): %s' % (shift,))

		## need unbinned result
		binx = nextimage['camera']['binning']['x']
		biny = nextimage['camera']['binning']['y']
		unbinned = {'row':shift[0] * biny, 'col': shift[1] * binx}

		shiftinfo = {'previous': previousimage, 'next': nextimage, 'pixel shift': unbinned}
		return shiftinfo

	def displayImage(self, im):
		try:
			self.node.setImage(im, 'Image')
		except:
			pass

	def displayCorrelation(self, im):
		try:
			self.node.setImage(im, 'Correlation')
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
		newdata = leginondata.CameraSensitivityCalibrationData()
		newdata['session'] = self.node.session
		newdata['high tension'] = ht
		newdata['sensitivity'] = sensitivity
		newdata['tem'] = self.instrument.getTEMData()
		newdata['ccdcamera'] = self.instrument.getCCDCameraData()
		self.node.publish(newdata, database=True, dbforce=True)

	def retrieveSensitivity(self, ht, tem, ccdcamera):
		qdata = leginondata.CameraSensitivityCalibrationData()
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
		mean_counts = arraystats.mean(imagedata['image']) / (binning**2)
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
		mean_counts = arraystats.mean(numdata) / (binning**2)
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
		queryinstance = leginondata.PixelSizeCalibrationData()
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
		queryinstance = leginondata.MatrixCalibrationData()
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
			excstr = 'no matrix for %s, %s, %s, %seV, %sx' % (tem['name'], ccdcamera['name'], caltype, ht, mag)
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
		newmatrix = numpy.array(matrix, numpy.float64)
		caldata = leginondata.MatrixCalibrationData(session=self.node.session, magnification=mag, type=type, matrix=matrix, tem=tem, ccdcamera=ccdcamera)
		caldata['high tension'] = ht
		self.node.publish(caldata, database=True, dbforce=True)

	def getMatrixAngles(self, matrix):
		matrix = numpy.linalg.inv(matrix)
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
		'SET BT', bt
		self.instrument.tem.BeamTilt = bt

	def storeRotationCenter(self, tem, ht, mag, beamtilt):
		rc = leginondata.RotationCenterData()
		rc['high tension'] = ht
		rc['magnification'] = mag
		rc['beam tilt'] = beamtilt
		rc['tem'] = tem
		rc['session'] = self.node.session
		self.node.publish(rc, database=True, dbforce=True)

	def retrieveRotationCenter(self, tem, ht, mag):
		rc = leginondata.RotationCenterData()
		rc['tem'] = tem
		rc['high tension'] = ht
		rc['magnification'] = mag
		results = self.node.research(datainstance=rc, results=1)
		if results:
			return results[0]['beam tilt']
		else:
			return None

	def measureRotationCenter(self, defocus1, defocus2, correlation_type=None, settle=0.5):
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		try:
			fmatrix = self.retrieveMatrix(tem, cam, 'defocus', ht, mag)
		except NoMatrixCalibrationError:
				raise RuntimeError('missing calibration matrix')

		state1 = leginondata.ScopeEMData()
		state2 = leginondata.ScopeEMData()
		state1['defocus'] = defocus1
		state2['defocus'] = defocus2

		im1 = self.acquireImage(state1, settle=settle)
		shiftinfo = self.measureScopeChange(im1, state2, settle=settle, correlation_type=correlation_type)

		shift = shiftinfo['pixel shift']
		d = shift['row'],shift['col']
		bt = self.solveEq10_t(fmatrix, defocus1, defocus2, d)
		return {'x':bt[0], 'y':bt[1]}

	def measureDefocusStig(self, tilt_value, stig=True, correct_tilt=False, correlation_type=None, settle=0.5, image0=None):
		self.abortevent.clear()
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		try:
			fmatrix = self.retrieveMatrix(tem, cam, 'defocus', ht, mag)
		except NoMatrixCalibrationError:
				raise RuntimeError('missing calibration matrix')

		## only do stig if stig matrices exist
		amatrix = bmatrix = None
		if stig:
			tiltaxes = ('x','y')
			try:
				amatrix = self.retrieveMatrix(tem, cam, 'stigx', ht, mag)
				bmatrix = self.retrieveMatrix(tem, cam, 'stigy', ht, mag)
			except NoMatrixCalibrationError:
				stig = False
				tiltaxes = ('x',)
		else:
			tiltaxes = ('x',)

		tiltcenter = self.getBeamTilt()

		if image0 is None:
			image0 = self.acquireImage(None, settle=settle, correct_tilt=correct_tilt)

		### need two tilt displacement measurements to get stig
		shifts = []
		tilts = []
		self.checkAbort()
		for tiltaxis in tiltaxes:
			bt2 = dict(tiltcenter)
			bt2[tiltaxis] += tilt_value
			state2 = leginondata.ScopeEMData()
			state2['beam tilt'] = bt2
			try:
				shiftinfo = self.measureScopeChange(image0, state2, settle=settle, correlation_type=correlation_type)
			except Abort:
				break

			pixshift = shiftinfo['pixel shift']

			shifts.append( (pixshift['row'], pixshift['col']) )
			if tiltaxis == 'x':
				tilts.append( (tilt_value, 0) )
			else:
				tilts.append( (0, tilt_value) )
			try:
				self.checkAbort()
			except Abort:
				break

		## return to original beam tilt
		self.instrument.tem.BeamTilt = tiltcenter

		self.checkAbort()

		sol = self.solveEq10(fmatrix, amatrix, bmatrix, tilts, shifts)
		return sol

	def OLDmeasureDefocusStig(self, tilt_value, publish_images=False, drift_threshold=None, stig=True, target=None, correct_tilt=False, correlation_type=None, settle=0.5):
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
			state1 = leginondata.ScopeEMData()
			state2 = leginondata.ScopeEMData()
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

	def solveEq10(self, F, A, B, tilts, shifts):
		'''
		This solves Equation 10 from Koster paper
		 F,A,B are the defocus, stigx, and stigy calibration matrices
		   (all must be 2x2 numpy arrays)
		 d1,d2 are displacements resulting from beam tilts t1,t2
		   (all must be 2x1 numpy arrays)
		'''

		v = numpy.array(shifts, numpy.float64).ravel()

		matrices = []
		for matrix in (F,A,B):
			if matrix is not None:
				matrices.append(matrix)

		mt = []
		for tilt in tilts:
			t = numpy.array(tilt)
			t.shape=(2,1)
			mm = []
			for matrix in matrices:
				m = numpy.dot(matrix, t)
				mm.append(m)
			m = numpy.concatenate(mm, 1)
			mt.append(m)
		M = numpy.concatenate(mt, 0)

		solution = numpy.linalg.lstsq(M, v)

		result = {'defocus': solution[0][0], 'min': float(solution[1][0])}
		if len(solution[0]) == 3:
			result['stigx'] = solution[0][1]
			result['stigy'] = solution[0][2]
		else:
			result['stigx'] = None
			result['stigy'] = None
		return result
	solveEq10 = classmethod(solveEq10)

	def solveDefocus(self, F, d, t, tiltaxis):
		if tiltaxis == 'x':
			ft = t * numpy.hypot(*F[:,0])
		else:
			ft = t * numpy.hypot(*F[:,1])
		print 'FT', ft
		f = d / ft
		return f
	solveDefocus = classmethod(solveDefocus)

	def solveEq10_t(self, F, f1, f2, d):
		'''
		This solves t (misalignment) in equation 10 from Koster paper
		given a displacement resulting from a defocus change
		F is defocus calibration matric
		f1, f2 are two defoci used to measure displacement d (row,col)
		'''
		a = (f2-f1) * F
		b = numpy.array(d, numpy.float)
		tiltx,tilty = numpy.linalg.solve(a,b)
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
		shift = numpy.zeros((2,), numpy.float)
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
				s0 = leginondata.ScopeEMData(initializer=state)
				s0['beam tilt'] = beam_tilts[0]
				s1 = leginondata.ScopeEMData(initializer=state)
				s1['beam tilt'] = beam_tilts[1]
				im0 = self.acquireImage(s0, **kwargs)
				result = self.measureScopeChange(im0, s1, **kwargs)
				pixel_shift = result['pixel shift']
				pixel_shifts.append(pixel_shift)

				args = (i + 1, pixel_shift['col'], pixel_shift['row'])
				self.node.logger.info(m % args)
		finally:
			# return to original beam tilt
			self.instrument.tem.BeamTilt = beam_tilt

		return tuple(pixel_shifts)

	def measureDisplacementDifference(self, tiltvector):
		'''
		Measure displacement difference between tilting plus tiltvector
		compared to minus tiltvector
		'''
		btorig = self.getBeamTilt()
		bt0 = btorig['x'], btorig['y']
		im0 = self.acquireImage(None)
		try:
			d = []
			for tsign in (1,-1):
				delta = numpy.multiply(tsign, tiltvector)
				bt = numpy.add(bt0, delta)
				state1 = leginondata.ScopeEMData()
				state1['beam tilt'] = {'x': bt[0], 'y': bt[1]}
				shiftinfo = self.measureScopeChange(im0, state1)
				pixelshift = shiftinfo['pixel shift']
				d.append(pixelshift)
			d_diff = d[1]['row']-d[0]['row'], d[1]['col']-d[0]['col']
		finally:
			self.setBeamTilt(btorig)
		return d_diff

	def measureMatrixC(self, m, t):
		'''
		determine matrix C, the coma-free matrix
		m = misalignment value, t = tilt value
		'''
		# original beam tilt
		btorig = self.getBeamTilt()
		bt0 = btorig['x'], btorig['y']
		diffs = {}
		tvect = (t, 0)
		try:
			for axisn, axisname in ((0,'x'),(1,'y')):
				diffs[axisname] = {}
				for msign in (1,-1):
					## misalign beam tilt
					mis_delta = [0,0]
					mis_delta[axisn] = msign * m
					mis_bt = numpy.add(bt0, mis_delta)
					mis_bt = {'x': mis_bt[0], 'y': mis_bt[1]}
					self.setBeamTilt(mis_bt)
					diff = self.measureDisplacementDifference(tvect)
					diffs[axisname][msign] = diff
		finally:
			## return to original beam tilt
			self.setBeamTilt(btorig)

		matrix = numpy.zeros((2,2), numpy.float32)
		matrix[:,0] = numpy.divide(numpy.subtract(diffs['x'][-1], diffs['x'][1]), 2 * m)
		matrix[:,1] = numpy.divide(numpy.subtract(diffs['y'][-1], diffs['y'][1]), 2 * m)
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

		tvect = (t, 0)
		dc = self.measureDisplacementDifference(tvect)
		cftilt = numpy.linalg.solve(cmatrix, dc)
		return cftilt

class SimpleMatrixCalibrationClient(MatrixCalibrationClient):
	mover = True
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
		matrix = numpy.array([[xrow,yrow],[xcol,ycol]],numpy.float)
		matrix = numpy.linalg.inv(matrix)
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
		pixvect = numpy.array((pixrow, pixcol))

		change = numpy.dot(matrix, pixvect)
		changex = change[0]
		changey = change[1]

		### take into account effect of alpha tilt on Y stage pos
		if par == 'stage position':
			if 'a' in scope[par] and scope[par]['a'] is not None:
				alpha = scope[par]['a']
				changey = changey / numpy.cos(alpha)

		new = leginondata.ScopeEMData(initializer=scope)
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
		inverse_matrix = numpy.linalg.inv(matrix)

		shift = dict(position)
		shift['x'] -= scope[parameter]['x']
		shift['y'] -= scope[parameter]['y']

		# take into account effect of stage alpha tilt on y stage position
		if parameter == 'stage position':
			if 'a' in scope[parameter] and scope[parameter]['a'] is not None:
				alpha = scope[parameter]['a']
				shift['y'] = shift['y']*numpy.cos(alpha)

		shift_vector = numpy.array((shift['x'], shift['y']))
		pixel = numpy.dot(inverse_matrix, shift_vector)

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
		matrix2inv = numpy.linalg.inv(matrix2)
		p1 = numpy.array(p1)
		stagepos = numpy.dot(matrix1, p1)
		p2 = numpy.dot(matrix2inv, stagepos)
		return p2

class BeamShiftCalibrationClient(SimpleMatrixCalibrationClient):
	mover = False
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
		matrix2inv = numpy.linalg.inv(matrix2)
		p1 = numpy.array(p1)
		stagepos = numpy.dot(matrix1, p1)
		p2 = numpy.dot(matrix2inv, stagepos)
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

		state1 = leginondata.ScopeEMData()
		state2 = leginondata.ScopeEMData()
		state1['stage position'] = {'a':-tilt_value}
		state2['stage position'] = {'a':tilt_value}
		## alpha backlash correction
		self.instrument.tem.StagePosition = state1['stage position']
		self.instrument.tem.StagePosition = state2['stage position']
		## do tilt and measure image shift
		im1 = self.acquireImage(state1)
		shiftinfo = self.measureScopeChange(im1, state2, correlation_type=correlation_type)
		self.instrument.tem.StagePosition = {'a':orig_a}

		state1 = shiftinfo['previous']['scope']
		state2 = shiftinfo['next']['scope']
		pixelshift = shiftinfo['pixel shift']
		#psize = self.getPixelSize(state1['magnification'])
		#dist = psize * math.hypot(pixelshift['row'], pixelshift['col'])
		
		# fake the current state for the transform with alpha = 0
		scope = leginondata.ScopeEMData(initializer=state1)
		scope['stage position']['a'] = 0.0
		cam = leginondata.CameraEMData()
		# measureScopeChange already unbinned it, so fake cam bin = 1
		cam['binning'] = {'x':1,'y':1}
		cam['ccdcamera'] = self.instrument.getCCDCameraData()
		# get the virtual x,y movement
		newscope = self.transform(pixelshift, scope, cam)
		# y component is all we care about to get Z
		y = newscope['stage position']['y'] - scope['stage position']['y']
		z = y / 2.0 / math.sin(tilt_value)
		return z

	def measureTiltAxisLocation(self, tilt_value=0.26, numtilts=1, tilttwice=False,
	  update=False, snrcut=10.0, correlation_type='phase', medfilt=False):
		"""
		print 'onMeasure', update
		measure position on image of tilt axis
		tilt_value is in radians
		"""

		### BEGIN TILTING

		# need to do something with this data
		pixelshiftree = []
		for i in range(numtilts):
			#get first image
			imagedata0, ps = self._getPeakFromTiltStates(tilt0imagedata=None, 
				tilt1=-tilt_value, medfilt=medfilt, snrcut=snrcut, correlation_type=correlation_type)
			if ps['snr'] > snrcut:
				pixelshiftree.append(ps)

			if tilttwice is True:
				#get second image
				imagedata0, ps = self._getPeakFromTiltStates(tilt0imagedata=imagedata0, 
					tilt1=tilt_value, medfilt=medfilt, snrcut=snrcut)
				if ps['snr'] > snrcut:
					pixelshiftree.append(ps)
		
		### END TILTING; BEGIN ASSESSMENT

		if len(pixelshiftree) < 1:
			#wasn't a good enough fit
			self.node.logger.error("image correction failed, snr below cutoff")
			return imagedata0, pixelshift
		else:
			self.node.logger.info("averaging %s measurements for final value" % (len(pixelshiftree)))

		snrtotal = 0.0
		rowtotal = 0.0
		coltotal = 0.0
		for ps in pixelshiftree:
			snrtotal += ps['snr']
			rowtotal += ps['row']*ps['snr']
			coltotal += ps['col']*ps['snr']
			self.node.logger.info("measured pixel shift: %s, %s" % (ps['row'], ps['col']))

		pixelshift = {
			'row':rowtotal/snrtotal,
			'col':coltotal/snrtotal,
			'snr':snrtotal/float(len(pixelshiftree))
		}
		self.node.logger.info("final pixel shift: %s, %s" % (pixelshift['row'], pixelshift['col']))
		
		### END ASSESSMENT; BEGIN CORRECTION

		## convert pixel shift into stage movement
		newscope = self.transform(pixelshift, imagedata0['scope'], imagedata0['camera'])
		## only want the y offset (distance from tilt axis)
		deltay = newscope['stage position']['y'] - imagedata0['scope']['stage position']['y']
		## scale correlation shift to the axis offset
		scale = 1.0 / numpy.tan(tilt_value/2.0) / numpy.tan(tilt_value)
		deltay *= scale

		tem = self.instrument.getTEMData()
		ccdcamera = self.instrument.getCCDCameraData()

		axisoffset = leginondata.StageTiltAxisOffsetData(offset=deltay,tem=tem,ccdcamera=ccdcamera)

		if update:
			q = leginondata.StageTiltAxisOffsetData(tem=tem,ccdcamera=ccdcamera)
			offsets = self.node.research(q, results=1)
			if offsets:
				axisoffset['offset'] += offsets[0]['offset']

		self.node.publish(axisoffset, database=True, dbforce=True)

		self.node.logger.info('stage delta y: %s' % (deltay,))

		shift = {'x':0, 'y':deltay}
		position = dict(imagedata0['scope']['stage position'])
		position['x'] += shift['x']
		position['y'] += shift['y']
		pixelshift = self.itransform(position, imagedata0['scope'], imagedata0['camera'])
		self.node.logger.info('pixelshift for delta y: %s' % (pixelshift,))

		pixelshift = {'row':pixelshift['row'], 'col':pixelshift['col']}
		self.node.logger.info('pixelshift from axis: %s' % (pixelshift,))

		return imagedata0, pixelshift


	def measureTiltAxisLocation2(self, tilt_value=0.0696, tilttwice=False,
	  update=False, correlation_type='phase', beam_tilt=0.01):
		"""
		print 'onMeasure', update
		measure position on image of tilt axis
		tilt_value is in radians
		"""

		### BEGIN TILTING

		# need to do something with this data
		defshifts = []
		#get first image
		imagedata0, defshift = self._getDefocDiffFromTiltStates(tilt0imagedata=None, 
			tilt1=-tilt_value, correlation_type=correlation_type, beam_tilt_value=beam_tilt)
		if defshift is not None and abs(defshift) < 1e-5:
			defshifts.append(-defshift)

		if tilttwice is True:
			#get second image
			imagedata0, defshift = self._getDefocDiffFromTiltStates(tilt0imagedata=imagedata0, 
				tilt1=tilt_value, correlation_type=correlation_type, beam_tilt_value=beam_tilt)
			if defshift is not None and abs(defshift) < 1e-5:
				defshifts.append(defshift)
		print defshifts	
		### END TILTING; BEGIN ASSESSMENT

		if len(defshifts) < 1:
			#no good defocus measurement
			self.node.logger.error("bad defocus measurements")
			return imagedata0, None
		else:
			self.node.logger.info("averaging %s measurements for final value" % (len(defshifts)))

		deltaz = sum(defshifts)/len(defshifts)
		self.node.logger.info("final defocus shift: %.2f um" % (deltaz/1e-6))
		
		### END ASSESSMENT; BEGIN CORRECTION

		## only want the y offset (distance from tilt axis)
		deltay = deltaz/math.sin(tilt_value)
		## scale correlation shift to the axis offset

		tem = self.instrument.getTEMData()
		ccdcamera = self.instrument.getCCDCameraData()

		axisoffset = leginondata.StageTiltAxisOffsetData(offset=deltay,tem=tem,ccdcamera=ccdcamera)

		if update:
			q = leginondata.StageTiltAxisOffsetData(tem=tem,ccdcamera=ccdcamera)
			offsets = self.node.research(q, results=1)
			if offsets:
				axisoffset['offset'] += offsets[0]['offset']

		self.node.publish(axisoffset, database=True, dbforce=True)

		self.node.logger.info('stage delta y: %s' % (deltay,))

		shift = {'x':0, 'y':deltay}
		position = dict(imagedata0['scope']['stage position'])
		position['x'] += shift['x']
		position['y'] += shift['y']
		pixelshift = self.itransform(position, imagedata0['scope'], imagedata0['camera'])
		self.node.logger.info('pixelshift for delta y: %s' % (pixelshift,))

		pixelshift = {'row':pixelshift['row'], 'col':pixelshift['col']}
		self.node.logger.info('pixel shift from axis: %s' % (pixelshift,))

		return imagedata0, pixelshift

	def _getPeakFromTiltStates(self, tilt0imagedata=None, tilt1=0.26, medfilt=True, snrcut=10.0, correlation_type='phase'):
		orig_a = self.instrument.tem.StagePosition['a']
		state0 = leginondata.ScopeEMData()
		state1 = leginondata.ScopeEMData()
		state0['stage position'] = {'a':0.0}
		state1['stage position'] = {'a':tilt1}
		tilt1deg = round(-tilt1*180.0/math.pi,4)

		if tilt0imagedata is None:
			self.node.logger.info('acquiring tilt=0 degrees')
			self.instrument.setData(state0)
			time.sleep(0.5)
			imagedata0 = self.node.acquireCorrectedCameraImageData()
			im0 = imagedata0['image']
			self.displayImage(im0)
		else:
			imagedata0 = tilt0imagedata
			im0 = imagedata0['image']
			self.displayImage(im0)

		self.node.logger.info('acquiring tilt=%s degrees' % (tilt1deg))
		self.instrument.setData(state1)
		time.sleep(0.5)
		imagedata1 = self.node.acquireCorrectedCameraImageData()
		self.stagetiltcorrector.undo_tilt(imagedata1)
		im1 = imagedata1['image']
		self.displayImage(im1)

		### RETURN SCOPE TO ORIGINAL STATE
		self.instrument.tem.StagePosition = {'a':orig_a}

		self.node.logger.info('correlating images for tilt %s' % (tilt1deg))
		self.correlator.setImage(0, im0)
		self.correlator.setImage(1, im1)
		if correlation_type is 'phase':
			pc = self.correlator.phaseCorrelate()
			if medfilt is True:
				pc = scipy.ndimage.median_filter(pc, size=3)
		else:
			pc = self.correlator.crossCorrelate()
		self.displayCorrelation(pc)

		peak01 = peakfinder.findSubpixelPeak(pc)
		snr = 1.0
		if 'snr' in peak01:
			snr = peak01['snr']
			if snr < snrcut:
				#wasn't a good enough fit
				self.node.logger.warning("beam tilt axis measurement failed, snr below cutoff; "+
				  "continuing for rest of images")

		## translate peak into image shift coordinates
		peak01a = peak01['subpixel peak']
		shift01 = correlator.wrap_coord(peak01a, pc.shape)
		self.displayPeak(peak01a)
		if tilt1 > 0:
			pixelshift = {'row':-1.0*shift01[0], 'col':-1.0*shift01[1], 'snr':snr }
		else:
			pixelshift = {'row':shift01[0], 'col':shift01[1], 'snr':snr }

		self.node.logger.info("measured pixel shift: %s, %s" % (pixelshift['row'], pixelshift['col']))
		self.node.logger.info("signal-to-noise ratio: %s" % (round(snr,2),))

		return imagedata0, pixelshift

	def _getDefocDiffFromTiltStates(self, tilt0imagedata=None, tilt1=0.26, correlation_type='phase',beam_tilt_value=0.01):
		orig_a = self.instrument.tem.StagePosition['a']
		state0 = leginondata.ScopeEMData()
		state1 = leginondata.ScopeEMData()
		state0['stage position'] = {'a':0.0}
		state1['stage position'] = {'a':tilt1}
		tilt1deg = round(-tilt1*180.0/math.pi,4)

		if tilt0imagedata is None:
			self.node.logger.info('acquiring tilt=0 degrees')
			self.instrument.setData(state0)
			time.sleep(0.5)
			imagedata0 = self.node.acquireCorrectedCameraImageData()
			im0 = imagedata0['image']
			self.displayImage(im0)
		else:
			imagedata0 = tilt0imagedata
			im0 = imagedata0['image']
			self.displayImage(im0)
		try:
			defresult = self.node.btcalclient.measureDefocusStig(beam_tilt_value, False, False, correlation_type, 0.5, imagedata0)
		except RuntimeError, e:
			self.node.logger.error('Measurement failed: %s' % e)
			return imagedata0, None 
		def0 = defresult['defocus']
		print defresult
		minres = defresult['min']
		self.node.logger.info('acquiring tilt=%s degrees' % (tilt1deg))
		self.instrument.setData(state1)
		time.sleep(0.5)
		imagedata1 = self.node.acquireCorrectedCameraImageData()
		self.stagetiltcorrector.undo_tilt(imagedata1)
		im1 = imagedata1['image']
		self.displayImage(im1)
		defresult = self.node.btcalclient.measureDefocusStig(beam_tilt_value, False, False, correlation_type, 0.5, imagedata1)
		def1 = defresult['defocus']
		print defresult
		minres = min((minres,defresult['min']))
		if minres > 5000000:
			self.node.logger.error('Measurement not reliable: residual= %.0f' % minres)
			return imagedata0, None

		### RETURN SCOPE TO ORIGINAL STATE
		self.instrument.tem.StagePosition = {'a':orig_a}

		## calculate defocus difference
		defocusdiff = def1 - def0
		self.node.logger.info("measured defocus difference is %.2f um" % (defocusdiff*1e6))

		return imagedata0, defocusdiff 

class ModeledStageCalibrationClient(MatrixCalibrationClient):
	mover = True
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

		scope = leginondata.ScopeEMData()
		scope['tem'] = tem
		scope['high tension'] = ht
		scope['stage position'] = {'x':0.0, 'y':0.0}
		camera = leginondata.CameraEMData()
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
		caldata = leginondata.StageModelMagCalibrationData()
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
		qinst = leginondata.StageModelMagCalibrationData(magnification=mag, axis=axis)
		qinst['high tension'] = ht
		if tem is None:
			qinst['tem'] = self.instrument.getTEMData()
		else:
			qinst['tem'] = tem
		if cam is None:
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
		matrix = numpy.ones((2,2), numpy.float64)
		matrix[0, 0]=means[0]*math.sin(angles[0])
		matrix[1, 0]=-means[0]*math.cos(angles[0])
		matrix[0, 1]=-means[1]*math.sin(angles[1])
		matrix[1, 1]=means[1]*math.cos(angles[1])
		
		return matrix

	def storeModelCalibration(self, tem, cam, label, axis, period, a, b):
		caldata = leginondata.StageModelCalibrationData()
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
		qinst = leginondata.StageModelCalibrationData(axis=axis)
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
			caldata2['a'] = numpy.ravel(caldata['a']).copy()
			caldata2['b'] = numpy.ravel(caldata['b']).copy()
			return caldata2

	def timeModelCalibration(self, tem, cam, axis):
		caldata = self.researchModelCalibration(tem, cam, axis)
		if caldata is None:
			timeinfo = None
		else:
			timeinfo = caldata.timestamp
		return timeinfo

	def getLabeledData(self, tem, cam, label, mag, axis):
		qdata = leginondata.StageMeasurementData()
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
			delta['y'] = delta['y'] / numpy.cos(alpha)

		newscope = leginondata.ScopeEMData(initializer=scope)
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

		m = numpy.array(((numpy.cos(anglex),numpy.sin(anglex)),(numpy.cos(angley),numpy.sin(angley))), numpy.float32)
		minv = numpy.linalg.inv(m)
		ix,iy = numpy.dot(minv, (gonx,gony))

		return iy,ix

class EucentricFocusClient(CalibrationClient):
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def researchEucentricFocus(self, ht, mag, tem=None, ccdcamera=None):
		query = leginondata.EucentricFocusData()
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
		newdata = leginondata.EucentricFocusData()
		newdata['session'] = self.node.session
		newdata['tem'] = self.instrument.getTEMData()
		newdata['ccdcamera'] = self.instrument.getCCDCameraData()
		newdata['high tension'] = ht
		newdata['magnification'] = mag
		newdata['focus'] = ef
		self.node.publish(newdata, database=True, dbforce=True)
