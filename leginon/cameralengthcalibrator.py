#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#
import calibrator
import calibrationclient
import event, leginondata
from pyami import imagefun, fftfun, diffrfun
import node
import math
import scipy
import gui.wx.CameraLengthCalibrator

class CameraLengthCalibrator(calibrator.Calibrator):
	'''
	calibrate the pixel size for different mags
	'''
	panelclass = gui.wx.CameraLengthCalibrator.Panel
	settingsclass = leginondata.CameraLengthCalibratorSettingsData
	defaultsettings = dict(calibrator.Calibrator.defaultsettings)
	defaultsettings.update({
		'spacing': 2.0, #Angstrom
		'distance': None,
	})

	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)
		self.mag = None
		self.bin = None
		self.is_diffr_tem = False
		self.diffr_constant = None
		self.image_camera_length = None
		self.pixeldistance = None
		self.calclient = calibrationclient.CameraLengthCalibrationClient(self)
		self.shape = None

		self.start()

	def fakeImage(self):
		# need an existing image name
		imageq = leginondata.AcquisitionImageData(filename='08oct13d_00045ma_1')
		results = imageq.query()
		return results[0]

	def acquireImage(self):
		imagedata = calibrator.Calibrator.acquireImage(self)
		# fake acquire image for testing
		#imagedata = self.fakeImage()
		if imagedata is None:
			return
		# check tem
		scope = imagedata['scope']
		self.is_diffr_tem = 'Diffr' in scope['tem']['name']
		if not self.is_diffr_tem:
			self.logger.error('image not acquired in diffraction mode,')
			return
		# check camera dimemsion
		camera = imagedata['camera']
		if camera['dimension']['x'] != camera['dimension']['y']:
			self.logger.error('Only know how to handle square image right now.')
			return
		self.mag = scope['magnification']
		self.bin = camera['binning']['x']
		newimage = imagedata['image']
		self.shape = newimage.shape
		self.image_camera_length = self.getImageCameraLength()
		self.setImage(newimage, 'Image')
		self.panel.acquisitionDone()
	
	def extrapolate(self, camera_lengths, mags):
		scales = []
		for mag, camera_length, comment in camera_lengths:
			if camera_length is not None and mag:
				scales.append(camera_length/mag)
		scale = sum(scales)/len(scales)

		camera_lengths = []
		for mag, camera_length, comment in mags:
			camera_length = scale*mag
			camera_lengths.append((mag, camera_length, comment))
		return camera_lengths

	def getImageCameraLength(self):
		camera_lengths = self.getCalibrations()
		mag = self.mag
		if mag is not None:
			for camera_length in camera_lengths:
				if camera_length[0] == mag:
					return camera_length[1]
		return None

	def getCalibrations(self):
		camera_lengths = []
		if self.initInstruments():
			return camera_lengths
		self.is_diffr_tem = 'Diffr' in self.instrument.getTEMName()
		if not self.is_diffr_tem:
			self.logger.error('image not acquired in diffraction mode,')
			return camera_lengths
		calibrations = self.calclient.retrieveLastCameraLengths(None, None)
		mag, mags = self.getMagnification()
		for calibration in calibrations:
			if mags is None or calibration['magnification'] in mags:
				mag = calibration['magnification']
				if mag is None:
					continue
				ps = calibration['camera length']
				comment = calibration['comment']
				if comment is None:
					comment = ''
				camera_lengths.append((mag, ps, comment))
		if mags is not None:
			camera_lengthmags = map(lambda (mag, ps, c): mag, camera_lengths)
			for m in mags:
				if m not in camera_lengthmags:
					camera_lengths.append((m, None, ''))
			
		return camera_lengths

	def _store(self, mag, camlength, comment):
		temdata = self.instrument.getTEMData()
		camdata = self.instrument.getCCDCameraData()
		caldata = leginondata.CameraLengthCalibrationData()
		caldata['magnification'] = mag
		caldata['camera length'] = camlength
		caldata['comment'] = comment
		caldata['session'] = self.session
		caldata['tem'] = temdata
		caldata['ccdcamera'] = camdata
		self.publish(caldata, database=True, dbforce=True)
		self._storePixelSizeCalibration(caldata)

	def _storePixelSizeCalibration(self, camlengthdata):
		cdata = camlengthdata

		rpsize_nm = 1e-18 * self.diffr_constant / cdata['camera length']
		# fudge factor for images to be displayed as 1kx1k images in the viewer.
		rpsize_nm_viewer = rpsize_nm / 4.0
		caldata = leginondata.PixelSizeCalibrationData()
		caldata['magnification'] = cdata['magnification']
		caldata['pixelsize'] = rpsize_nm_viewer
		caldata['comment'] = cdata['comment']+' assuming 2kx2k image'
		caldata['session'] = self.session
		caldata['tem'] = cdata['tem']
		caldata['ccdcamera'] = cdata['ccdcamera']
		self.publish(caldata, database=True, dbforce=True)

	def calculateCameraLength(self):
		if self.shape is None:
			self.logger.error('need image to calculate camera length')
			return
		d_spacing = self.settings['d spacing'] #Angstrum
		radius = self.settings['distance']/2.0 #in binned pixel
		ht = self.instrument.tem.HighTension # in Volt
		cam_psize = self.instrument.ccdcamera.getPixelSize()['x'] # meters
		image_bin = self.bin
		camera_length, rpixel_m = diffrfun.calculateCameraLength(d_spacing, radius, ht, cam_psize,image_bin)
		self.diffr_constant = camera_length * rpixel_m
		return camera_length

	def averageCameraLengths(self,measurements):
		if len(measurements) > 0:
			sum = 0
			for measurement in measurements:
				sum = sum + measurement
			average = sum / len(measurements)
			self.logger.info('averaging %d measurements' % (len(measurements),))
			self._store(self.mag,average,'averaged from %d values' % len(measurements))
			self.image_camera_length = average
			return average
		else:
			return None
