#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import calibrator
import calibrationclient
import event, leginondata
from pyami import imagefun
import node
import math
import scipy
import gui.wx.PixelSizeCalibrator

class PixelSizeCalibrator(calibrator.Calibrator):
	'''
	calibrate the pixel size for different mags
	'''
	panelclass = gui.wx.PixelSizeCalibrator.Panel
	settingsclass = leginondata.PixelSizeCalibratorSettingsData
	defaultsettings = calibrator.Calibrator.defaultsettings
	defaultsettings.update({
		'lattice a': 69.0,
		'lattice b': 173.5,
		'lattice gamma': 90.0,
		'h1': 0,
		'h2': 0,
		'k1': 6,
		'k2': -6,
		'distance': None,
	})

	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)
		self.mag = None
		self.bin = None
		self.imagepixelsize = None
		self.pixeldistance = None
		self.calclient = calibrationclient.PixelSizeCalibrationClient(self)
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
		scope = imagedata['scope']
		camera = imagedata['camera']
		self.mag = scope['magnification']
		self.bin = camera['binning']['x']
		newimage = imagedata['image']
		self.shape = newimage.shape
		self.imagepixelsize = self.getImagePixelSize()
		size = max(self.shape)
		if size > 2048:
			newimage = scipy.ndimage.zoom(newimage, 2048.0/max(self.shape))
		pow = imagefun.power(newimage, 1,10)
		pow[(0,0)] =  pow.max()*2
		self.setImage(pow, 'Power')
		self.panel.acquisitionDone()
	
	def extrapolate(self, pixelsizes, mags):
		scales = []
		for mag, pixelsize, comment in pixelsizes:
			if pixelsize is not None:
				scales.append(mag*pixelsize)
		scale = sum(scales)/len(scales)

		pixelsizes = []
		for mag, pixelsize, comment in mags:
			pixelsize = scale/mag
			pixelsizes.append((mag, pixelsize, comment))
		return pixelsizes

	def getImagePixelSize(self):
		pixelsizes = self.getCalibrations()
		mag = self.mag
		if mag is not None:
			for pixelsize in pixelsizes:
				if pixelsize[0] == mag:
					return pixelsize[1]
		return None

	def getCalibrations(self):
		pixelsizes = []
		if self.initInstruments():
			return pixelsizes
		calibrations = self.calclient.retrieveLastPixelSizes(None, None)
		mag, mags = self.getMagnification()
		for calibration in calibrations:
			if mags is None or calibration['magnification'] in mags:
				mag = calibration['magnification']
				if mag is None:
					continue
				ps = calibration['pixelsize']
				comment = calibration['comment']
				if comment is None:
					comment = ''
				pixelsizes.append((mag, ps, comment))
		if mags is not None:
			pixelsizemags = map(lambda (mag, ps, c): mag, pixelsizes)
			for m in mags:
				if m not in pixelsizemags:
					pixelsizes.append((m, None, ''))
			
		return pixelsizes

	def _store(self, mag, psize, comment):
		temdata = self.instrument.getTEMData()
		camdata = self.instrument.getCCDCameraData()
		caldata = leginondata.PixelSizeCalibrationData()
		caldata['magnification'] = mag
		caldata['pixelsize'] = psize
		caldata['comment'] = comment
		caldata['session'] = self.session
		caldata['tem'] = temdata
		caldata['ccdcamera'] = camdata
		self.publish(caldata, database=True)

	def calculatePixelSize(self):
		if self.shape is None:
			self.logger.error('need image to calculate pixel size')
			return
		latticea = self.settings['lattice a']
		latticeb = self.settings['lattice b']
		latticegamma = self.settings['lattice gamma']*math.pi/180.0
		astar = 1.0/latticea*math.sin(latticegamma)
		bstar = 1.0/latticeb*math.sin(latticegamma)
		gammastar = math.pi - latticegamma
		deltaindex = (self.settings['h2']-self.settings['h1'], self.settings['k2']-self.settings['k1'])
		dastar = deltaindex[0]*astar+deltaindex[1]*bstar*math.cos(gammastar)	
		dbstar = deltaindex[1]*bstar+deltaindex[0]*astar*math.cos(gammastar)
		angstrumdistance = 1/math.sqrt(dastar**2+dbstar**2)
		if self.shape[0] != self.shape[1]:
			self.logger.error('non-square image pixel size calculation not implemented')
			return
		pixeldistance = self.shape[0]/(self.settings['distance']*self.bin)
		pixelsize = angstrumdistance*1e-10/pixeldistance
		self.imagepixelsize = pixelsize
		return pixelsize

	def averagePixelSizes(self,measurements):
		if len(measurements) > 0:
			sum = 0
			for measurement in measurements:
				sum = sum + measurement
			average = sum / len(measurements)
			self._store(self.mag,average,'averaged from %d values' % len(measurements))
			self.imagepixelsize = average
			return average
		else:
			return None
