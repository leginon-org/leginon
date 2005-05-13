#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import calibrator
import calibrationclient
import event, data
import node
import math
import gui.wx.PixelSizeCalibrator

class PixelSizeCalibrator(calibrator.Calibrator):
	'''
	calibrate the pixel size for different mags
	'''
	panelclass = gui.wx.PixelSizeCalibrator.Panel
	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)
		self.mag = None
		self.bin = None
		self.pixeldistance = None
		self.calclient = calibrationclient.PixelSizeCalibrationClient(self)

		self.start()

	def acquireImage(self):
		imagedata = calibrator.Calibrator.acquireImage(self)
		if imagedata is None:
			return
		scope = imagedata['scope']
		camera = imagedata['camera']
		self.mag = scope['magnification']
		self.bin = camera['binning']['x']
		newimage = imagedata['image']
		self.shape = newimage.shape

	def calculateMeasured(self, pdist, dist):
		return dist / (self.bin * pdist)

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

	def getCalibrations(self):
		self.initInstruments()
		calibrations = self.calclient.retrieveLastPixelSizes(None, None)
		pixelsizes = []
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
		caldata = data.PixelSizeCalibrationData()
		caldata['magnification'] = mag
		caldata['pixelsize'] = psize
		caldata['comment'] = comment
		caldata['session'] = self.session
		caldata['tem'] = self.settings['instruments']['tem']
		caldata['ccdcamera'] = self.settings['instruments']['ccdcamera']
		self.publish(caldata, database=True)

