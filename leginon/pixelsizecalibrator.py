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
import uidata
import node
import math
import EM
import camerafuncs
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

	def extrapolate(self, fmags, tmag):
		## get pixel size of known mags from DB to calculate scale
		scales = []
		for fmag in fmags:
			psize = self.calclient.retrievePixelSize(fmag)
			scales.append(psize*fmag)
		scale = sum(scales) / len(scales)

		## calculate new pixel sizes
		psize = scale / tmag
		self.logger.info('Magnification: %sx, pixel size: %s' % (tmag, psize))
		#comment = 'extrapolated from %s' % (fmags,)
		#self._store(tmag, psize, comment)
		return psize

	def getCalibrations(self):
		calibrations = self.calclient.retrieveAllPixelSizes()
		pixelsizes = []
		for calibration in calibrations:
			pixelsizes.append((calibration['magnification'],
												calibration['pixelsize'],
												calibration['comment']))
		return pixelsizes

	def _store(self, mag, psize, comment):
		caldata = data.PixelSizeCalibrationData()
		caldata['magnification'] = mag
		caldata['pixelsize'] = psize
		caldata['comment'] = comment
		caldata['session'] = self.session
		self.publish(caldata, database=True)
