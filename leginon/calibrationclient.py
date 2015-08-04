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
import numpy.linalg
import scipy
import pyami.quietscipy
import scipy.ndimage
import math
from pyami import correlator, peakfinder, arraystats, imagefun, fftfun, numpil, ellipse
import time
import sys
import threading
import gonmodel
import tiltcorrector
import tableau

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
			self.instrument = None

		self.correlator = correlator.Correlator()
		self.abortevent = threading.Event()
		self.tiltcorrector = tiltcorrector.TiltCorrector(node)
		self.stagetiltcorrector = tiltcorrector.VirtualStageTilter(node)
		self.rpixelsize = None
		self.powerbinning = 2
		self.debug = False

	def checkAbort(self):
		if self.abortevent.isSet():
			raise Abort()

	def setDBInstruments(self,caldata,tem=None,cam=None):	
		if tem is None:
			caldata['tem'] = self.instrument.getTEMData()
		else:
			caldata['tem'] = tem
		if cam is None:
			caldata['ccdcamera'] = self.instrument.getCCDCameraData()
		else:
			caldata['ccdcamera'] = cam

	def getPixelSize(self, mag, tem=None, ccdcamera=None):
		queryinstance = leginondata.PixelSizeCalibrationData()
		queryinstance['magnification'] = mag
		self.setDBInstruments(queryinstance,tem,ccdcamera)
		caldatalist = self.node.research(datainstance=queryinstance, results=1)
		if len(caldatalist) > 0:
			return caldatalist[0]['pixelsize']
		else:
			return None
	
	def getImagePixelSize(self,imagedata):
		scope = imagedata['scope']['tem']
		ccd = imagedata['camera']['ccdcamera']
		mag = imagedata['scope']['magnification']
		campixelsize = self.getPixelSize(mag,tem=scope, ccdcamera=ccd)
		binning = imagedata['camera']['binning']
		dimension = imagedata['camera']['dimension']
		pixelsize = {'x':campixelsize*binning['x'],'y':campixelsize*binning['y']}
		return pixelsize

	def getImageReciprocalPixelSize(self,imagedata):
		imagepixelsize = self.getImagePixelSize(imagedata)
		dimension = imagedata['camera']['dimension']
		rpixelsize = {'x':1.0/(imagepixelsize['x']*dimension['x']),'y':1.0/(imagepixelsize['y']*dimension['y'])}
		return rpixelsize

	def correctTilt(self, imagedata):
		try:
			self.tiltcorrector.correct_tilt(imagedata)
		except RuntimeError, e:
			self.node.logger.error('Failed tilt correction: %s' % (e))

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

	def measureScopeChange(self, previousimage, nextscope, settle=0.0, correct_tilt=False, correlation_type='phase', lp=None):
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
		imagearray = nextimage['image']
		if imagearray.max() == 0:
			raise RuntimeError('Bad image intensity range')

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

		if lp is not None and lp > 0.0001:
			cor = scipy.ndimage.gaussian_filter(cor, lp)

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
	
	def measureStateDefocus(self, nextscope, settle=0.0):
		'''
		Acquire an image at nextscope and estimate the ctf parameters
		'''
		self.checkAbort()
		## acquire neximage
		nextimage = self.acquireImage(nextscope, settle, correct_tilt=False)
		## get ctf parameters
		self.ht = nextimage['scope']['high tension']
		self.cs = nextimage['scope']['tem']['cs']
		if not self.rpixelsize:
			self.rpixelsize = self.getImageReciprocalPixelSize(nextimage)
		imagearray = nextimage['image']
		if imagearray.max() == 0:
			raise RuntimeError('Bad image intensity range')
		pow = imagefun.power(imagearray)
		ctfdata = fftfun.fitFirstCTFNode(pow,self.rpixelsize['x'], None, self.ht, self.cs)

		self.checkAbort()
		if ctfdata is not None:
			self.node.logger.info('defocus: %.3f um, zast: %.3f um' % (ctfdata[0]*1e6,ctfdata[1]*1e6))
			defocusinfo = {'next': nextimage, 'defocus': ctfdata[0]}
		else:
			self.node.logger.warning('ctf estimation failed')
			defocusinfo = {'next': nextimage, 'defocus': None}
		return nextimage, defocusinfo

	def initTableau(self):
		self.tableauimages = []
		self.tableauangles = []
		self.tableaurads = []
		self.tabimage = None
		self.ctfdata = []

	def insertTableau(self, imagedata, angle, rad):
		image = imagedata['image']
		binning = self.powerbinning
		
		if True:
			pow = imagefun.power(image)
			binned = imagefun.bin(pow, binning)
			s = None
			self.ht = imagedata['scope']['high tension']
			if not self.rpixelsize:
				self.rpixelsize = self.getImageReciprocalPixelSize(imagedata)
			ctfdata = fftfun.fitFirstCTFNode(pow,self.rpixelsize['x'], None, self.ht, self.cs)
			self.ctfdata.append(ctfdata)

			# show defocus estimate on tableau
			if ctfdata:
				self.node.logger.info('tabeau defocus: %.3f um, zast: %.3f um' % (ctfdata[0]*1e6,ctfdata[1]*1e6))
				s = '%d' % int(ctfdata[0]*1e9)
				eparams = ctfdata[4]
				self.node.logger.info('eparams a:%.3f, b:%.3f, alpha:%.3f' % (eparams['a'],eparams['b'],eparams['alpha']))
				center = numpy.divide(eparams['center'], binning)
				a = eparams['a'] / binning
				b = eparams['b'] / binning
				alpha = eparams['alpha']
				ellipse1 = pyami.ellipse.drawEllipse(binned.shape, 2*numpy.pi/180, center, a, b, alpha)
				ellipse2 = pyami.ellipse.drawEllipse(binned.shape, 5*numpy.pi/180, center, a, b, alpha)
				min = arraystats.min(binned)
				max = arraystats.max(binned)
				numpy.putmask(binned, ellipse1, min)
				numpy.putmask(binned, ellipse2, max)
			#elif self.ace2exe:
			elif False:
				ctfdata = self.estimateCTF(imagedata)
				z0 = (ctfdata['defocus1'] + ctfdata['defocus2']) / 2
				s = '%d' % (int(z0*1e9),)
			if s:
				t = numpil.textArray(s, binning)
				t = min + t * (max-min)
				imagefun.pasteInto(t, binned, (20,20))
		else:
			binned = imagefun.bin(image, binning)
		self.tableauimages.append(binned)
		self.tableauangles.append(angle)
		self.tableaurads.append(rad)

	def renderTableau(self):
		if not self.tableauimages:
			return
		size = self.tableauimages[0].shape[0]
		radinc = numpy.sqrt(2 * size * size)
		tab = tableau.Tableau()
		for i,im in enumerate(self.tableauimages):
			ang = self.tableauangles[i]
			rad = radinc * self.tableaurads[i]
			tab.insertImage(im, angle=ang, radius=rad)
		self.tabimage,self.tabscale = tab.render()
		mean = self.tabimage.mean()
		std = self.tabimage.std()
		newmax = mean + 5 * std
		a = numpy.where(self.tabimage >= newmax, newmax, self.tabimage)
		a = numpy.clip(a, 0, mean*1.5)
		self.tabimage = scipy.ndimage.zoom(a,self.powerbinning/3.0)
		self.displayTableau(self.tabimage)

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

	def displayTableau(self, im):
		try:
			self.node.setImage(im, 'Tableau')
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

	def storeSensitivity(self, ht, sensitivity,tem=None,ccdcamera=None):
		newdata = leginondata.CameraSensitivityCalibrationData()
		newdata['session'] = self.node.session
		newdata['high tension'] = ht
		newdata['sensitivity'] = sensitivity
		self.setDBInstruments(newdata,tem,ccdcamera)
		self.node.publish(newdata, database=True, dbforce=True)

	def retrieveSensitivity(self, ht, tem, ccdcamera):
		qdata = leginondata.CameraSensitivityCalibrationData()
		self.setDBInstruments(qdata,tem,ccdcamera)
		qdata['high tension'] = ht
		results = self.node.research(datainstance=qdata, results=1)
		if results:
			result = results[0]['sensitivity']
		else:
			raise NoSensitivityError('No sensitivity calibration.')
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

	def getTemCCDCameraFromImageData(self,imagedata):
		tem = imagedata['scope']['tem']
		if tem is None:
			tem = self.instrument.getTEMData()
		ccdcamera = imagedata['camera']['ccdcamera']
		if ccdcamera is None:
			ccdcamera = self.instrument.getCCDCameraData()
		return tem,ccdcamera

	def sensitivity_from_imagedata(self, imagedata, dose_rate):
		tem,ccdcamera = self.getTemCCDCameraFromImageData(imagedata)
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
		binningx = imagedata['camera']['binning']['x']
		binningy = imagedata['camera']['binning']['y']
		binmult = imagedata['camera']['binned multiplier']
		mean_counts = binmult * arraystats.mean(imagedata['image']) / (binningx*binningy)
		return self.sensitivity(dose_rate, camera_mag, camera_pixel_size,
														exposure_time, mean_counts)

	def dose_from_imagedata(self, imagedata):
		'''
		dose in number of electrons per meter^2 in the duration of exposure time.
		'''
		pixel_totaldose = self.pixel_totaldose_from_imagedata(imagedata)
		tem,ccdcamera = self.getTemCCDCameraFromImageData(imagedata)
		mag = imagedata['scope']['magnification']
		specimen_pixel_size = self.psizecal.retrievePixelSize(tem, ccdcamera, mag)
		self.node.logger.debug('Specimen pixel size %.4e' % specimen_pixel_size)
		totaldose = pixel_totaldose / specimen_pixel_size**2
		return totaldose

	def pixel_framedose_from_imagedata(self, imagedata):
		'''
		dose in number of electron per camera pixel.  For frame integration
		camera such as DE-12, this is per frame.  For other camera, this is
		per total integration time
		'''
		pixel_totaldose = self.pixel_totaldose_from_imagedata(imagedata)
		nframes = imagedata['camera']['nframes']
		if nframes is None or nframes == 0:
			nframes = 1
			has_frames = False
		else:
			has_frames = True
		self.node.logger.debug('Number of integration frames per exposure %d' % nframes)
		pixel_framedose = pixel_totaldose / nframes
		return has_frames,pixel_framedose

	def pixel_dose_rate_from_imagedata(self, imagedata):
		'''
		dose rate in number of electron per camera pixel per second.
		'''
		pixel_totaldose = self.pixel_totaldose_from_imagedata(imagedata)
		exp_time_in_second = imagedata['camera']['exposure time'] / 1000.0
		return pixel_totaldose / exp_time_in_second

	def pixel_totaldose_from_imagedata(self, imagedata):
		'''
		Dose per camera pixel. Binning does not affect the result.
		Imagedata indirectly contains most info needed to calc dose
		'''
		tem,ccdcamera = self.getTemCCDCameraFromImageData(imagedata)
		camera_pixel_size = imagedata['camera']['pixel size']['x']
		ht = imagedata['scope']['high tension']
		binningx = imagedata['camera']['binning']['x']
		binningy = imagedata['camera']['binning']['y']
		binmult = imagedata['camera']['binned multiplier']
		exp_time = imagedata['camera']['exposure time'] / 1000.0
		numdata = imagedata['image']
		sensitivity = self.retrieveSensitivity(ht, tem, ccdcamera)
		self.node.logger.debug('Sensitivity %.2f' % sensitivity)
		mean_counts = binmult * arraystats.mean(numdata) / (binningx*binningy)
		self.node.logger.debug('Mean counts %.1f' % mean_counts)
		pixel_totaldose = mean_counts / sensitivity
		return pixel_totaldose


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
		self.setDBInstruments(queryinstance,tem,ccdcamera)
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
				raise RuntimeError('Failed retrieving last pixelsize')
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

	def researchMatrix(self, tem, ccdcamera, caltype, ht, mag, probe=None):
		queryinstance = leginondata.MatrixCalibrationData()
		self.setDBInstruments(queryinstance,tem,ccdcamera)
		queryinstance['type'] = caltype
		queryinstance['magnification'] = mag
		queryinstance['high tension'] = ht
		queryinstance['probe'] = probe
		caldatalist = self.node.research(datainstance=queryinstance, results=1)
		if caldatalist:
			caldata = caldatalist[0]
			self.node.logger.debug('matrix calibration dbid: %d' % caldata.dbid)
			return caldata
		else:
			excstr = 'no matrix for %s, %s, %s, %seV, %sx' % (tem['name'], ccdcamera['name'], caltype, ht, mag)
			raise NoMatrixCalibrationError(excstr, state=queryinstance)

	def retrieveMatrix(self, tem, ccdcamera, caltype, ht, mag, probe=None):
		'''
		finds the requested matrix using magnification and type
		'''
		caldata = self.researchMatrix(tem, ccdcamera, caltype, ht, mag, probe)
		matrix = caldata['matrix'].copy()
		return matrix

	def time(self, tem, ccdcamera, ht, mag, caltype, probe=None):
		try:
			caldata = self.researchMatrix(tem, ccdcamera, caltype, ht, mag, probe)
		except:
			caldata = None
		if caldata is None:
			timestamp = None
		else:
			timestamp = caldata.timestamp
		return timestamp

	def storeMatrix(self, ht, mag, caltype, matrix, tem=None, ccdcamera=None, probe=None):
		'''
		stores a new calibration matrix.
		'''
		# the matrix stored needs to be ndarray type
		newmatrix = numpy.array(matrix, numpy.float64)
		caldata = leginondata.MatrixCalibrationData(session=self.node.session, magnification=mag, type=caltype, matrix=newmatrix, probe=probe)
		self.setDBInstruments(caldata,tem,ccdcamera)
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
		self.instrument.tem.BeamTilt = bt

	def storeRotationCenter(self, tem, ht, mag, probe, beamtilt):
		rc = leginondata.RotationCenterData()
		rc['high tension'] = ht
		rc['magnification'] = mag
		rc['probe'] = probe
		rc['beam tilt'] = beamtilt
		rc['tem'] = tem
		rc['session'] = self.node.session
		self.node.publish(rc, database=True, dbforce=True)

	def retrieveRotationCenter(self, tem, ht, mag, probe=None):
		if probe is None:
			probe = self.instrument.tem.ProbeMode
		rc = leginondata.RotationCenterData()
		rc['tem'] = tem
		rc['high tension'] = ht
		rc['magnification'] = mag
		rc['probe'] = probe
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
		except (NoMatrixCalibrationError,RuntimeError), e:
			self.node.logger.error('Measurement failed: %s' % e)
			return {'x':0.0, 'y': 0.0}
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
		# Can not handle the exception for retrieveMatrix here. 
		# Focuser node that calls this need to know the type of error
		fmatrix = self.retrieveMatrix(tem, cam, 'defocus', ht, mag)

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
				shiftinfo = self.measureScopeChange(image0, state2, settle=settle, correct_tilt=correct_tilt, correlation_type=correlation_type)
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

	def measureDefocusDifference(self, tiltvector, settle):
		'''
		Measure defocus difference between tilting plus tiltvector
		compared to minus tiltvector
		'''
		btorig = self.getBeamTilt()
		bt0 = btorig['x'], btorig['y']
		#im0 = self.acquireImage(None, settle=settle)
		d_diff = None
		try:
			d = []
			for tsign in (1,-1):
				delta = numpy.multiply(tsign, tiltvector)
				bt = numpy.add(bt0, delta)
				state1 = leginondata.ScopeEMData()
				state1['beam tilt'] = {'x': bt[0], 'y': bt[1]}
				im1, defocusinfo = self.measureStateDefocus(state1, settle=settle)
				defocusshift = defocusinfo['defocus']
				self.measured_defocii.append(defocusshift)
				d.append(defocusshift)
				angle = math.atan2(tiltvector[1],tiltvector[0]) * tsign
				if angle == 0.0 and tsign == -1:
					angle = math.pi
				self.insertTableau(im1, angle, 1/math.sqrt(2))
			self.renderTableau()
			if None in d:
				d_diff = d
			else:
				tlength = math.hypot(tiltvector[0],tiltvector[1])
				d_diff = numpy.multiply((d[1]-d[0])/tlength, tiltvector)
		finally:
			self.node.logger.info('Setting beam tilt back')
			self.setBeamTilt(btorig)
		return d_diff

	def getMeasured_Defocii(self):
		return self.measured_defocii

	def measureMatrixC(self, m, t, settle):
		'''
		determine matrix C, the beam-tilt coma matrix
		m = misalignment value, t = tilt value
		'''
		self.rpixelsize = None
		self.ht = None
		self.initTableau()
		# original beam tilt
		btorig = self.getBeamTilt()
		bt0 = btorig['x'], btorig['y']
		diffs = {}
		self.measured_defocii = []
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
					tvect = [0, 0]
					tvect[axisn] = t
					diff = self.measureDefocusDifference(tvect, settle)
					if None in diff:
						raise RuntimeError('Can not determine Defocus Difference with failed ctf estimation')
					elif not self.confirmDefocusInRange():
						raise RuntimeError('Deofucs Range confirmation failed')
					diffs[axisname][msign] = diff
		finally:
			## return to original beam tilt
			self.setBeamTilt(btorig)

		matrix = numpy.zeros((2,2), numpy.float32)
		if m!=0:
			matrix[:,0] = numpy.divide(numpy.subtract(diffs['x'][-1], diffs['x'][1]), 2 * m * t)
			matrix[:,1] = numpy.divide(numpy.subtract(diffs['y'][-1], diffs['y'][1]), 2 * m * t)
		return matrix

	def confirmDefocusInRange(self):
		if len(self.measured_defocii) < 1:
			return False
		defocusarray = numpy.array(self.measured_defocii)
		defocusmean = defocusarray.mean()
		aimed_defocus = self.instrument.tem.Defocus
		if (((abs(aimed_defocus)+1e-6)*3) < defocusmean) or (abs((aimed_defocus+1e-6)*0.2)) > defocusmean:
			self.node.logger.warning('Estimated defocus out of range at %e' % defocusmean)
			return False
		return True

	def calculateImageShiftComaMatrix(self,tdata,xydata):
		''' Fit the beam tilt vector induced by image shift 
				to a straight line on individual axis.  
				Strickly speaking we should use orthogonal distance regression.''' 
		ordered_axes = ['x','y']
		matrix = numpy.zeros((2,2))
		coma0 = {'x':0.0,'y':0.0}
		for index1, axis1 in enumerate(ordered_axes):
			data = xydata[axis1]
			for axis2 in data.keys():
				(slope,t_intercept) = scipy.polyfit(numpy.array(tdata[axis1]),numpy.array(xydata[axis1][axis2]),1)
				index2 = ordered_axes.index(axis2)
				matrix[index1,index2] = slope
				coma0[axis2] += t_intercept
			coma0[axis2] /= len(ordered_axes)
		return matrix, coma0

	def measureComaFree(self, tilt_value, settle, raise_error=False):
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		self.rpixelsize = None
		self.ht = ht
		self.initTableau()

		par = 'beam-tilt coma'
		cmatrix = self.retrieveMatrix(tem, cam, 'beam-tilt coma', ht, mag)

		dc = [0,0]
		failed_measurement = False
		for axisn, axisname in ((0,'x'),(1,'y')):
			tvect = [0, 0]
			tvect[axisn] = tilt_value
			def_diff = self.measureDefocusDifference(tvect, settle)
			if None in def_diff:
				failed_measurement = True
			dc[axisn] = def_diff
		if not failed_measurement:
			dc = numpy.array(dc) / tilt_value
			cftilt = numpy.linalg.solve(cmatrix, dc)
			if not self.confirmDefocusInRange():
				cftilt[(0,0)] = 0
				cftilt[(1,1)] = 0
		else:
			cftilt = numpy.zeros((2,2))
			if raise_error:
				raise Exception('Coma Free Beam Tilt Measurement Failed')
		return cftilt

	def repeatMeasureComaFree(self, tilt_value, settle, repeat=1,raise_error=False):
		'''repeat measuremnet to increase precision'''
		tilts = {'x':[],'y':[]}
		self.measured_defocii = []
		self.node.logger.debug("===================")
		for i in range(0,repeat):
			try:
				cftilt = self.measureComaFree(tilt_value, settle, raise_error)
			except Exception, e:
				cftilt = None
				raise
			if cftilt is None:
				comatilt = {'x':None, 'y':None}
			else:
				tilts['x'].append(cftilt[(0,0)])
				tilts['y'].append(cftilt[(1,1)])
				comatilt = {'x':cftilt[(0,0)],'y':cftilt[(1,1)]}
				self.node.logger.debug("    %5.2f,  %5.2f" % (cftilt[(0,0)]*1000,cftilt[(1,1)]*1000))
		if len(tilts['x']):
			xarray = numpy.array(tilts['x'])
			yarray = numpy.array(tilts['y'])
			self.node.logger.debug("--------------------")
			self.node.logger.debug("m   %5.2f,  %5.2f" %(xarray.mean()*1000,yarray.mean()*1000))
			self.node.logger.debug("std %5.2f,  %5.2f" %(xarray.std()*1000,yarray.std()*1000))
			return xarray,yarray

	def transformImageShiftToBeamTilt(self, imageshift, tem, cam, ht, zerobeamtilt, mag):
		newbeamtilt = {}
		par = 'image-shift coma'
		try:
			# not to query specific mag for now
			matrix = self.retrieveMatrix(tem, cam, 'image-shift coma', ht, None)
		except NoMatrixCalibrationError:
			raise RuntimeError('missing %s calibration matrix' % par)
		self.node.logger.debug("Image Shift ( %5.2f, %5.2f)" % (imageshift['x']*1e6,imageshift['y']*1e6))
		shiftvect = numpy.array((imageshift['x'], imageshift['y']))
		change = numpy.dot(matrix, shiftvect)
		newbeamtilt['x'] = zerobeamtilt['x'] - change[0]
		newbeamtilt['y'] = zerobeamtilt['y'] - change[1]
		self.node.logger.debug("Beam Tilt Correction ( %5.2f, %5.2f)" % (change[0]*1e3,change[1]*1e3))
		self.node.logger.debug("Beam Tilt ( %5.2f, %5.2f)" % (newbeamtilt['x']*1e3,newbeamtilt['y']*1e3))
		return newbeamtilt

	def correctImageShiftComa(self):
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		shift0 = self.instrument.tem.ImageShift
		scopestate = leginondata.ScopeEMData(tem=tem,magnification=mag)
		camerastate = leginondata.CameraEMData(ccdcamera=cam)
		tilt0 = self.instrument.tem.BeamTilt
		scopestate['high tension'] = ht
		scopestate['image shift'] = shift0
		scopestate['beam tilt'] = tilt0
		beamtilt = scopestate['beam tilt']
		beamtilt = self.transformImageShiftToBeamTilt(shift0, tem, cam, ht, beamtilt, mag)
		self.setBeamTilt(beamtilt)

	def alignRotationCenter(self, defocus1, defocus2):
		bt = self.measureRotationCenter(defocus1, defocus2, correlation_type=None, settle=0.5)
		self.node.logger.info('Misalignment correction: %.4f, %.4f' % (bt['x'],bt['y'],))
		oldbt = self.instrument.tem.BeamTilt
		self.node.logger.info('Old beam tilt: %.4f, %.4f' % (oldbt['x'],oldbt['y'],))
		newbt = {'x': oldbt['x'] + bt['x'], 'y': oldbt['y'] + bt['y']}
		self.instrument.tem.BeamTilt = newbt
		self.node.logger.info('New beam tilt: %.4f, %.4f' % (newbt['x'],newbt['y'],))

	def _rotationCenterToScope(self):
		tem = self.instrument.getTEMData()
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		probe = self.instrument.tem.ProbeMode
		beam_tilt = self.retrieveRotationCenter(tem, ht, mag, probe)
		if not beam_tilt:
			raise RuntimeError('no rotation center for %geV, %gX' % (ht, mag))
		self.instrument.tem.BeamTilt = beam_tilt

	def rotationCenterToScope(self):
		try:
			self._rotationCenterToScope()
		except Exception, e:
			self.node.logger.error('Unable to set rotation center: %s' % e)
		else:
			self.node.logger.info('Set instrument rotation center')

	def _rotationCenterFromScope(self):
		tem = self.instrument.getTEMData()
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		probe = self.instrument.tem.ProbeMode
		beam_tilt = self.instrument.tem.BeamTilt
		self.storeRotationCenter(tem, ht, mag, probe, beam_tilt)

	def rotationCenterFromScope(self):
		try:
			self._rotationCenterFromScope()
		except Exception, e:
			self.node.logger.error('Unable to get rotation center: %s' % e)
		else:
			self.node.logger.info('Saved instrument rotation center')
	
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

	def MatrixToMeasurement(self, matrix):
		'''
		convert matrix in [TEM parameter]/pixel to a mesurement in pixels/[TEM parameter] 
		'''
		matrix = numpy.linalg.inv(matrix)
		measurement = {'x':{},'y':{}}
		measurement['x']['row'] = matrix[0,0]
		measurement['x']['col'] = matrix[0,1]
		measurement['y']['row'] = matrix[1,0]
		measurement['y']['col'] = matrix[1,1]
		return measurement

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
		try:
			matrix = self.retrieveMatrix(tem, ccdcamera, par, ht, mag)
		except NoMatrixCalibrationError, e:
			self.node.logger.error(e)
			return scope
			

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
		# By defining new parameters by change, physical movement scale
		# in physical unit has to be accurate.
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
		shift = dict(position)
		# By defining shift by position, physical movement scale
		# in physical unit has to be accurate.
		shift['x'] -= scope[parameter]['x']
		shift['y'] -= scope[parameter]['y']

		try:
			matrix = self.retrieveMatrix(*args)
		except NoMatrixCalibrationError, e:
			self.node.logger.error(e)
			return {'row':0.0,'col':0.0}
		inverse_matrix = numpy.linalg.inv(matrix)

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

	def calculateCalibrationAngleDifference(self, tem1, ccdcamera1, tem2, ccdcamera2, ht, mag1, mag2):
		par = self.parameter()
		matrix1 = self.retrieveMatrix(tem1, ccdcamera1, par, ht, mag1)
		matrix2 = self.retrieveMatrix(tem2, ccdcamera2, par, ht, mag2)
		return self.angleFromMatrix(matrix2) - self.angleFromMatrix(matrix1)

	def angleFromMatrix(self, matrix):
		'''
		calculate calibration 2D vectors (as an ndimage array)
		average angle to the axis of (1,0),(0,1) vectors, respectively.
		The result return is in radians
		'''
		angles = []
		angles.append(math.atan2(matrix[0,1],matrix[0,0]))
		# y axis is assumed to be 90 degrees from x
		yangle = math.atan2(matrix[1,1],matrix[1,0]) - math.pi/2
		if yangle < -math.pi:
			yangle += 2*math.pi
		angles.append(yangle)
		angle_average = sum(angles) / 2
		return angle_average

	def matrixFromPixelAndPositionShifts(self,pixel_shift1,position_shift1, pixel_shift2, position_shift2, camera_binning):
		'''
		returns calibration matrix as ndarray type from pixel shift and position shift matrix(or ndarray)
		image pixel_shift1 (row,col) is the result of scope position_shift1 (x,y)
		image pixel_shift2 (row,col) is the result of scope position_shift2 (x,y)
		camera_binnings {'x':bin_col,'y':bin_row}
		'''
		pixel_shift_matrix = self.convertImagePixelShiftsToArray(pixel_shift1,pixel_shift2,camera_binning)
		position_shift_matrix = self.convertScopePositionShiftsToArray(position_shift1, position_shift2).transpose()
		ipixel_shift = numpy.linalg.inv(pixel_shift_matrix)
		return numpy.dot(position_shift_matrix,ipixel_shift)

	def convertImagePixelShiftsToArray(self,pixel_shift1,pixel_shift2,camera_binning):
		# Need to transpose pixel_shift so the array looks like this:
		# [[pixel_shift1_row  pixel_shift2_row]
		#  [pixel_shift2_col  pixel_shift2_col]]
		bins = numpy.array((camera_binning['y'],camera_binning['x']))
		pixel_shift_matrix = numpy.array((pixel_shift1*bins,pixel_shift2*bins)).transpose()
		return pixel_shift_matrix

	def convertScopePositionShiftsToArray(self,position_shift1, position_shift2):
		'''
		Scope position shifts is a list of dictionary with keys of 'x' and 'y'
		'''
		position_shift_matrix = numpy.array(((position_shift1['x'],position_shift1['y']), (position_shift2['x'],position_shift2['y'])))
		return position_shift_matrix

class ImageShiftCalibrationClient(SimpleMatrixCalibrationClient):
	def __init__(self, node):
		SimpleMatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		return 'image shift'

	def pixelToPixel(self, tem1, ccdcamera1, tem2, ccdcamera2, ht, mag1, mag2, p1):
		'''
		Using physical position as a global coordinate system, we can
		do pixel to pixel transforms between mags.
		This function will calculate a pixel vector at mag2, given
		a pixel vector at mag1.
		For image shift, this means: the physical image shift values in meters
		need to be properly calibrated for this to work right
		'''
		par = self.parameter()
		physicalpos = self.pixelToPosition(tem1,ccdcamera1, par, ht, mag1, p1)
		p2 = self.positionToPixel(tem2,ccdcamera2, par, ht, mag2, physicalpos)
		return p2

	def pixelToPosition(self,tem, ccdcamera, matrix_type, ht, mag, pixel_shift):
		'''
		Using matrix to transform a pixel shift on camera to relative physical position.
		'''
		par = matrix_type
		matrix = self.retrieveMatrix(tem, ccdcamera, par, ht, mag)
		shift = numpy.array(pixel_shift)
		physicalpos = numpy.dot(matrix, pixel_shift)
		return physicalpos

	def positionToPixel(self,tem, ccdcamera, matrix_type, ht, mag, position):
		'''
		Using matrix to transform a relative physical position to pixel shift on camera.
		'''
		par = matrix_type
		matrix = self.retrieveMatrix(tem, ccdcamera, par, ht, mag)
		matrix_inv = numpy.linalg.inv(matrix)
		physicalpos = numpy.array(position)
		pixel_shift = numpy.dot(matrix_inv, physicalpos)
		return pixel_shift

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

	def pixelToPixel(self, tem1, ccdcamera1, tem2, ccdcamera2, ht, mag1, mag2, p1):
		'''
		Using stage position as a global coordinate system, we can
		do pixel to pixel transforms between mags.
		This function will calculate a pixel vector at mag2, given
		a pixel vector at mag1.
		'''
		par = self.parameter()
		matrix1 = self.retrieveMatrix(tem1, ccdcamera1, par, ht, mag1)
		matrix2 = self.retrieveMatrix(tem2, ccdcamera2, par, ht, mag2)
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

		state = {}
		shiftinfo = {}
		state[0] = leginondata.ScopeEMData()
		state[1] = leginondata.ScopeEMData()
		state[2] = leginondata.ScopeEMData()
		state[0]['stage position'] = {'a':0.0}
		state[1]['stage position'] = {'a':-tilt_value}
		state[2]['stage position'] = {'a':tilt_value}
		## alpha backlash correction
		self.instrument.tem.StagePosition = state[1]['stage position']
		# make sure main screen is up since there is no failure in this function
		self.instrument.tem.setMainScreenPosition('up')

		## do tilt and measure image shift
		## move from state2, through 0, to state1 to remove backlash
		self.instrument.tem.StagePosition = state[2]['stage position']
		self.instrument.tem.StagePosition = state[0]['stage position']
		im0 = self.acquireImage(state[0])
		# measure the change from 0 to state1
		shiftinfo[1] = self.measureScopeChange(im0, state[1], correlation_type=correlation_type, lp=1)
		## move from state1, through 0, to state2 to remove backlash
		self.instrument.tem.StagePosition = state[0]['stage position']
		im0 = self.acquireImage(state[0])
		# measure the change from 0 to state1
		shiftinfo[2] = self.measureScopeChange(im0, state[2], correlation_type=correlation_type,lp=1)

		# return to original
		self.instrument.tem.StagePosition = {'a':orig_a}

		state[1] = shiftinfo[1]['next']['scope']
		state[2] = shiftinfo[2]['next']['scope']
		pixelshift = {}
		# combine the two half of the tilts

		z = {}
		for t in (1,2):
			for axis in shiftinfo[1]['pixel shift'].keys():
				pixelshift[axis] = shiftinfo[t]['pixel shift'][axis]
			# fake the current state for the transform with alpha = 0
			scope = leginondata.ScopeEMData(initializer=state[1])
			scope['stage position']['a'] = 0.0
			cam = leginondata.CameraEMData()
			# measureScopeChange already unbinned it, so fake cam bin = 1
			cam['binning'] = {'x':1,'y':1}
			cam['ccdcamera'] = self.instrument.getCCDCameraData()
			# get the virtual x,y movement
			newscope = self.transform(pixelshift, scope, cam)
			# y component is all we care about to get Z
			y = newscope['stage position']['y'] - scope['stage position']['y']
			z[t] = y / math.sin(state[t]['stage position']['a'])

		zmean = (z[1]+z[2]) / 2
		return zmean

	def measureTiltAxisLocation(self, tilt_value=0.26, numtilts=1, tilttwice=False,
	  update=False, snrcut=10.0, correlation_type='phase', medfilt=False):
		"""
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
		except (NoMatrixCalibrationError,RuntimeError), e:
			self.node.logger.error(e)
			return imagedata0, None 
		def0 = defresult['defocus']
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

	def pixelToPixel(self, tem1, ccdcamera1, tem2, ccdcamera2, ht, mag1, mag2, p1):
		'''
		Using stage position as a global coordinate system, we can
		do pixel to pixel transforms between mags.
		This function will calculate a pixel vector at mag2, given
		a pixel vector at mag1.
		'''

		scope = leginondata.ScopeEMData()
		scope['tem'] = tem1
		scope['high tension'] = ht
		scope['stage position'] = {'x':0.0, 'y':0.0}
		camera = leginondata.CameraEMData()
		camera['ccdcamera'] = ccdcamera1
		camera['binning'] = {'x':1,'y':1}

		scope['magnification'] = mag1
		pixelshift = {'row':p1[0], 'col':p1[1]}
		newscope = self.transform(pixelshift, scope, camera)

		scope['tem'] = tem2
		scope['magnification'] = mag2
		camera['ccdcamera'] = ccdcamera2
		position = newscope['stage position']
		pix = self.itransform(position, scope, camera)

		return pix['row'],pix['col']

	def storeMagCalibration(self, tem, cam, label, ht, mag, axis, angle, mean):
		caldata = leginondata.StageModelMagCalibrationData()
		caldata['session'] = self.node.session
		self.setDBInstruments(caldata,tem,cam)
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
		self.setDBInstruments(qinst,tem,cam)

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
		caldata['session'] = self.node.session
		self.setDBInstruments(caldata,tem,cam)
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
		self.setDBInstruments(qinst,tem,ccdcamera)
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
			caldata2['label'] = caldata['label']
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
		self.node.logger.debug('x mag cal angle=%6.3f, scale=%e' % (xmagcal['angle'],xmagcal['mean']))
		self.node.logger.debug('y mag cal angle=%6.3f, scale=%e' % (ymagcal['angle'],ymagcal['mean'],))

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
		self.node.logger.debug('x mag cal angle=%6.3f, scale=%e' % (xmagcal['angle'],xmagcal['mean']))
		self.node.logger.debug('y mag cal angle=%6.3f, scale=%e' % (ymagcal['angle'],ymagcal['mean'],))


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

	def researchEucentricFocus(self, ht, mag, probe=None, tem=None, ccdcamera=None):
		query = leginondata.EucentricFocusData()
		self.setDBInstruments(query,tem,ccdcamera)
		query['high tension'] = ht
		query['magnification'] = mag
		if probe is None:
			probe = self.instrument.tem.ProbeMode
		query['probe'] = probe
		datalist = self.node.research(datainstance=query, results=1)
		if datalist:
			eucfoc = datalist[0]
		else:
			eucfoc = None
		return eucfoc

	def publishEucentricFocus(self, ht, mag, probe, ef):
		camera_names = self.instrument.getCCDCameraNames()
		# need to publish for all cameras since it can be used by any
		for name in camera_names:
			newdata = leginondata.EucentricFocusData()
			newdata['session'] = self.node.session
			newdata['tem'] = self.instrument.getTEMData()
			newdata['ccdcamera'] = self.instrument.getCCDCameraData(name)
			newdata['high tension'] = ht
			newdata['magnification'] = mag
			newdata['probe'] = probe
			newdata['focus'] = ef
			self.node.publish(newdata, database=True, dbforce=True)

class BeamSizeCalibrationClient(CalibrationClient):
	def getCrossOverIntensityDial(self,scopedata):
		return self.researchBeamSizeCalibration(scopedata,'focused beam')[0]

	def getSizeIntensityDialScale(self,scopedata):
		scale,c2size = self.researchBeamSizeCalibration(scopedata,'scale')
		if not c2size:
			return None
		c2results = leginondata.C2ApertureSizeData(session=self.node.session,tem=scopedata['tem']).query(results=1)
		if c2results and c2results[0]['size']:
			session_c2size = float(c2results[0]['size'])
			return scale * (c2size / session_c2size)

	def researchBeamSizeCalibration(self,scopedata,key):
		if not scopedata:
			return None, None
		# search beamsize
		queryinstance = leginondata.BeamSizeCalibrationData()
		queryinstance['tem'] = scopedata['tem']
		queryinstance['spot size'] = scopedata['spot size']
		queryinstance['probe mode'] = scopedata['probe mode']
		caldatalist = self.node.research(datainstance=queryinstance, results=1)
		if len(caldatalist) > 0:
			return caldatalist[0][key], caldatalist[0]['c2 size']
		else:
			return None, None
	
	def getBeamSize(self,scopedata):
		'''Return beam diameter in meters'''
		slope = self.getSizeIntensityDialScale(scopedata)
		intercept = self.getCrossOverIntensityDial(scopedata)
		intensity = scopedata['intensity']
		if slope is not None and intercept is not None:
			intensity_delta = intensity - intercept
			beamsize = intensity_delta / slope
			return beamsize

	def getIlluminatedArea(self,scopedata):
		beam_diameter = self.getBeamSize(scopedata) 
		if beam_diameter:
			return math.pi * (beam_diameter/2)**2
		else:
			return None

	def getIntensityFromAreaScale(self,scopedata,area_scale_factor):
		beam_cross_over = self.getCrossOverIntensityDial(scopedata)
		if not beam_cross_over:
			return None
		intensity = scopedata['intensity']
		intensity_scale_factor = 1 / math.sqrt(area_scale_factor)
		new_intensity = (intensity - beam_cross_over) * intensity_scale_factor + beam_cross_over
		return new_intensity
