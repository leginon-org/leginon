#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
import calibrator
import calibrationclient
import event
import leginondata
import node
import gui.wx.MagCalibrator
import time
import libCVwrapper
import numpy
from pyami import arraystats, mrc, affine, msc
import pyami.quietscipy
from scipy import ndimage

class MagCalibrator(calibrator.Calibrator):
	'''
	'''
	panelclass = gui.wx.MagCalibrator.Panel
	settingsclass = leginondata.MagCalibratorSettingsData
	defaultsettings = calibrator.Calibrator.defaultsettings
	defaultsettings.update({
		'minsize': 50,
		'maxsize': 500,
		'pause': 1.0,
		'label': '',
		'maxthreshold': 60000,
		'maxcount': 5000,
		'cutoffpercent': 1.0,
		'minbright': 100,
		'maxbright': 5000,
		'mag1': 5000,
		'mag2': 6500,
	})
	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)
		self.start()

	def OLDuiStart(self):
		mag = self.instrument.tem.Magnification
		print 'MAG', mag
		mags = self.getMags()
		print 'MAGS', mags
		magindex = mags.index(mag)
		othermag = mags[magindex-1]
		self.compareToOtherMag(othermag)
		return
		print 'MAGINDEX', magindex
		if magindex == 0:
			print 'already at lowest mag'
			return
		else:
			previousmags = mags[magindex-5:magindex-1]
			previousmags.reverse()
			print 'PREVIOUSMAGS', previousmags
	
		self.matchMags(previousmags)

	def uiStart(self):
		mag1 = self.settings['mag1']
		mag2 = self.settings['mag2']
		self.compareTwoMags(mag1, mag2)
		return

		mag = self.instrument.tem.Magnification
		print 'MAG', mag
		mags = self.getMags()
		print 'MAGS', mags
		magindex = mags.index(mag)
		print 'MAGINDEX', magindex

		if magindex == 0:
			print 'already at lowest mag'
			return

		steps = self.settings['magsteps']
		maglist = mags[magindex-steps:magindex]
		maglist.reverse()
	
		self.acquireMags(maglist)

	def acquireAcquisitionImageData(self, range=None):
		if range is None:
			im = self.acquireImage()
		else:
			im = self.acquireWithinRange(*range)
		im = leginondata.AcquisitionImageData(initializer=im)
		im['session'] = self.session
		mag = im['scope']['magnification']
		magstring = '%06d' % (mag,)
		label = self.settings['label']
		im['filename'] = self.session['name'] + '-' + label + '-' + magstring
		im['label'] = label
		return im

	def acquireMags(self, maglist):
		firstim = self.acquireAcquisitionImageData()
		firstim.insert(force=True)
		print 'FIRST', firstim['image']
		limitmin = self.settings['minbright']
		limitmax = self.settings['maxbright']
		for mag in maglist:
			self.logger.info('mag: %s' % (mag,))
			self.instrument.tem.Magnification = mag
			self.pause()
			im = self.acquireAcquisitionImageData(range=(limitmin,limitmax))
			im.insert(force=True)
			self.logger.info('inserted mag: %s' % (mag,))

	def uiTest(self):
		imdata = self.acquireImage()
		im = imdata['image']
		regions = self.findRegions(im)

	def pause(self):
		pause = self.settings['pause']
		time.sleep(pause)

	def getMags(self):
		mags = self.instrument.tem.Magnifications
		return mags

	def compareTwoMags(self, mag1, mag2):
		minbright = self.settings['minbright']
		maxbright = self.settings['maxbright']

		## mag1
		self.instrument.tem.Magnification = mag1
		self.pause()
		mag1imdata = self.acquireWithinRange(minbright, maxbright)

		## mag2
		self.instrument.tem.Magnification = mag2
		self.pause()
		mag2imdata = self.acquireWithinRange(minbright, maxbright)

		mag1im = mag1imdata['image']
		mag2im = mag2imdata['image']

		## compare
		anglestart = -3
		angleend = 3
		angleinc = 0.25
		scaleguess = float(mag2) / mag1
		scalestart = scaleguess - 0.08
		scaleend = scaleguess + 0.08
		scaleinc = 0.02
		prebin = 1
		result = msc.findRotationScaleShift(mag1im, mag2im, anglestart, angleend, angleinc, scalestart, scaleend, scaleinc, prebin)
		if result is None:
			self.logger.error('could not determine relation')
			return

		angle = result[0]
		scale = result[1]
		shift = result[2]
		print 'ANGLE', angle
		print 'SCALE', scale
		print 'SHIFT', shift
		magdata = leginondata.MagnificationComparisonData()
		magdata['mag1'] = mag1
		magdata['mag2'] = mag2
		magdata['rotation'] = angle
		magdata['scale'] = scale
		magdata['shiftrow'] = shift[0]
		magdata['shiftcol'] = shift[1]
		magdata.insert(force=True)

	def isSaturated(self, im):
		thresh = self.settings['threshold']
		bins = (thresh,)
		result = numpy.histogram(im, bins=bins)
		count = result[0][0]
		maxcount = self.settings['maxcount']
		if count > maxcount:
			self.logger.info('Overflow:  %s pixels above %s (max allowed: %s)' % (count, thresh, maxcount))
			return True
		else:
			return False

	def isUnderexposed(self, im):
		thresh = self.settings['threshold']

	def brightestStats(self, im, percent):
		# look only at the brightest 1% of the pixels
		sortedpixels = numpy.sort(im, axis=None)
		npixels = len(sortedpixels)
		nbrightest = int(percent / 100.0 * npixels)
		brightest = sortedpixels[-nbrightest:]
		stats = arraystats.all(brightest)
		self.logger.info('Top %.1f%% stats: mean: %.1f, std: %.1f, min: %.1f, max: %.1f' % (percent, stats['mean'],stats['std'],stats['min'],stats['max']))
		return stats

	def acquireWithinRange(self, min, max):
		imagedata = self.acquireImage()
		stats = self.brightestStats(imagedata['image'], self.settings['cutoffpercent'])

		while not (min < stats['mean'] < max):
			if stats['mean'] > max:
				self.logger.info('too bright')
				# assuming we are greater than crossover, increase lens value
				i = self.instrument.tem.Intensity
				if i < 1.0:
					self.logger.info('spreading beam')
					self.instrument.tem.Intensity = 1.02 * i
				else:
					self.logger.info('decreasing exposure time')
					t = self.instrument.ccdcamera.ExposureTime
					self.instrument.ccdcamera.ExposureTime = t / 2

				imagedata = self.acquireImage()
				stats = self.brightestStats(imagedata['image'], self.settings['cutoffpercent'])

			if stats['mean'] < min:
				self.logger.info('not bright enough, condensing beam...')
				# assuming we are greater than crossover, decrease lens value
				i = self.instrument.tem.Intensity
				self.instrument.tem.Intensity = 0.98 * i
				imagedata = self.acquireImage()
				stats = self.brightestStats(imagedata['image'], self.settings['cutoffpercent'])

		return imagedata

	def acquireImage(self):
		im = calibrator.Calibrator.acquireImage(self)
		#im['image'] = ndimage.gaussian_filter(im['image'], 1.2)
		return im

	def matchMags(self, mags):
		# acquire first image at current state
		oldimagedata = self.acquireImage()
		self.findRegions(oldimagedata['image'])
		mrc.write(oldimagedata['image'], 'imref.mrc')
		stats = arraystats.all(oldimagedata['image'])
		shape = oldimagedata['image'].shape

		# determine limits to adjust exposure of other mags
		limitmax = 1.5 * stats['mean']
		limitmin = 0.5 * stats['mean']
		self.logger.info('image1 mean:  %f, limits:  %f-%f' % (stats['mean'], limitmin, limitmax))

		## iterate through mags
		runningresult = numpy.identity(3)
		for i,mag in enumerate(mags):
			self.instrument.tem.Magnification = mag
			self.pause()

			newimagedata = self.acquireWithinRange(limitmin, limitmax)
			self.findRegions(newimagedata['image'])
			mrc.write(newimagedata['image'], 'im%02d.mrc' % (i,))

			minsize = self.settings['minsize']
			maxsize = self.settings['maxsize']
			self.logger.info('matchimages')
			result = self.matchImages(oldimagedata['image'], newimagedata['image'], minsize, maxsize)
			runningresult = numpy.dot(result, runningresult)
			self.logger.info('transforms')
			final_step = affine.transform(newimagedata['image'], result, shape)
			final_all = affine.transform(newimagedata['image'], runningresult, shape)
			self.logger.info('writing result mrcs')
			mrc.write(final_step, 'trans%02d.mrc' % (i,))
			mrc.write(final_all, 'transall%02d.mrc' % (i,))
			oldimagedata = newimagedata

#			self.getMagDiff(imagedata1, imagedata2, result)

	def getMagDiff(self, imdata1, imdata2, matrix):
		ccol = imdata1['camera']['dimension']['x'] / 2 - 0.5
		crow = imdata1['camera']['dimension']['y'] / 2 - 0.5
		center = numpy.array((ccol, crow, 1))
		othercenter = numpy.dot(matrix, center)
		print 'OTHER', othercenter

	def matchImages(self, im1, im2, minsize, maxsize):
		result = libCVwrapper.MatchImages(im1, im2, minsize, maxsize, 0, 0, 1, 1)
		return result

	def findRegions(self, im):
		minsize = self.settings['minsize']
		maxsize = self.settings['maxsize']
		regions, image = libCVwrapper.FindRegions(im, minsize, maxsize, 0, 0, 1, 1)
		coords = map(self.regionCenter, regions)
		self.setTargets(coords, 'Peak')
		return regions

	def regionCenter(self, region):
		coord = region['regionEllipse'][:2]
		coord = coord[1], coord[0]
		return coord
