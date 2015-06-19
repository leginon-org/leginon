#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from leginon import leginondata
import event
import imagewatcher
import numpy
import scipy.ndimage
import gui.wx.Corrector
import instrument
import sys
from pyami import arraystats, imagefun, mrc, ccd
import polygon
import time
import os
import cameraclient

class Corrector(imagewatcher.ImageWatcher):
	'''
	Manages dark/bright images and does other corrections
	Basic Instructions:
	  Create a corrector plan for every camera configuration that
	  requires correction.  Right now, camera configuration means:
	   dimension, binning, offset, (future: dose).
	  To create a plan, set the camera configuration in 'Preferences', 
	  set other plan options in 'Plan' and then 'Set Plan Params'.
	  This creates a plan file in the corrections directory.  Acquire
	  a dark and bright image for this plan.  These are stored as MRC
	  in the corrections directory.
	'''
	panelclass = gui.wx.Corrector.Panel
	settingsclass = leginondata.CorrectorSettingsData
	defaultsettings = {
		'instruments': {'tem':None, 'ccdcamera':None},
		'n average': 3,
		'despike': True,
		'despike size': 11,
		'despike threshold': 3.5,
		'clip min': 0,
		'clip max': 2**16,
		'camera settings': cameraclient.default_settings,
		'combine': 'average',
		'store series': False,
	}
	eventinputs = imagewatcher.ImageWatcher.eventinputs + [event.AcquisitionImagePublishEvent]
	eventoutputs = imagewatcher.ImageWatcher.eventoutputs + [event.DarkImagePublishEvent, event.BrightImagePublishEvent]
	def __init__(self, name, session, managerlocation, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, name, session, managerlocation, **kwargs)
		self.instrument = instrument.Proxy(self.objectservice, self.session, self.panel)
		self.start()

	def retrieveCorrectorImageFromSettings(self, reftype, channel):
		ccdcameraname = self.settings['instruments']['ccdcamera']
		camsettings = self.settings['camera settings']
		if ccdcameraname is None or camsettings is None:
			return None
		cameradata = leginondata.CameraEMData()
		try:
			cameradata['ccdcamera'] = self.instrument.getCCDCameraData(ccdcameraname)
		except:
			return None
		cameradata.update(camsettings)
		cdata = self.instrument.getData(leginondata.CameraEMData)
		cameradata['gain index'] = cdata['gain index']
		scopedata = self.instrument.getData(leginondata.ScopeEMData)
		imdata = self.retrieveCorrectorImageData(reftype, scopedata, cameradata, channel)
		return imdata

	def retrieveCorrectorPlanFromSettings(self):
		ccdcameraname = self.settings['instruments']['ccdcamera']
		camsettings = self.settings['camera settings']
		if ccdcameraname is None or camsettings is None:
			return None
		cameradata = leginondata.CameraEMData()
		try:
			cameradata['ccdcamera'] = self.instrument.getCCDCameraData(ccdcameraname)
		except:
			return None
		cameradata.update(camsettings)
		cdata = self.instrument.getData(leginondata.CameraEMData)
		cameradata['gain index'] = cdata['gain index']
		plan, plandata = self.retrieveCorrectorPlan(cameradata)
		return plan

	def changeScreenPosition(self,state):
		try:
			self.instrument.tem.MainScreenPosition = state
			time.sleep(2)
			self.logger.info('screen %s' % state)
		except:
			self.logger.info('screen %s failed (may be unsupported)' % state)

	def acquireDark(self, channels):
		cameraname = self.instrument.getCCDCameraName()
		if cameraname == 'DE12':
			self.changeScreenPosition('down')
		for channel in channels:
			try:
				imagedata = self.acquireReference(type='dark', channel=channel)
			except Exception, e:
				raise
				self.logger.exception('Cannot acquire dark reference: %s' % (e,))
			else:
				self.displayImage(imagedata)
				self.currentimage = imagedata
				self.beep()
		if cameraname == 'DE12':
			self.changeScreenPosition('up')
		self.panel.acquisitionDone()

	def acquireBright(self, channels):
		for channel in channels:
			try:
				imagedata = self.acquireReference(type='bright', channel=channel)
			except Exception, e:
				raise
				self.logger.exception('Cannot acquire bright reference: %s' % (e,))
			else:
				self.displayImage(imagedata)
				self.currentimage = imagedata
				self.beep()
		self.panel.acquisitionDone()

	def acquireRaw(self):
		self.startTimer('acquireRaw')
		try:
			self.startTimer('set cam')
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			self.stopTimer('set cam')
			self.startTimer('get image')
			image = self.acquireCameraImageData()['image']
			self.stopTimer('get image')
		except Exception, e:
                        raise
			self.logger.exception('Raw acquisition failed: %s' % (e,))
		else:
			self.maskimg = numpy.zeros(image.shape)
			self.displayImage(image)
			self.currentimage = image
		self.panel.acquisitionDone()
		self.stopTimer('acquireRaw')

	def acquireCorrected(self, channels):
		for channel in channels:
			self.startTimer('acquireCorrected')
			self.setTargets([], 'Bad_Region', block=False)
			self.startTimer('set ccd')
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			self.stopTimer('set ccd')
			imagedata = self.acquireCorrectedCameraImageData(channel)
			image = imagedata['image']
			self.maskimg = numpy.zeros(image.shape)
			self.displayImage(image)
			self.currentimage = image
			self.panel.acquisitionDone()
			self.stopTimer('acquireCorrected')

	def displayImage(self, image):
		self.startTimer('Corrector.displayImage')
		if image is None:
			self.setImage(None)
		else:
			self.setImage(numpy.asarray(image, numpy.float32))
		self.stopTimer('Corrector.displayImage')

	def displayRef(self, reftype, channel):
		self.setStatus('processing')
		self.logger.info('load channel %s %s image' % (channel, reftype))

		if reftype != 'dark-subtracted':
			imdata = self.retrieveCorrectorImageFromSettings(reftype, channel)
			imarray = imdata['image']
		else:
			brightdata = self.retrieveCorrectorImageFromSettings('bright', channel)
			darkdata = self.retrieveCorrectorImageFromSettings('dark', channel)
			imarray = brightdata['image'] - darkdata['image']
		self.maskimg = numpy.zeros(imarray.shape)
		self.displayImage(imarray)
		self.currentimage = imarray
		self.beep()
		self.setStatus('idle')

	def acquireSeries(self, n):
		series = []
		for i in range(n):
			self.logger.info('Acquiring reference image (%s of %s)' % (i+1, n))
			image = self.acquireCameraImageData()['image']
			series.append(image)
		return series

	def acquireSeriesAverage(self, n, type, channel):
		if type == 'dark':
			exposuretype = 'dark'
		else:
			exposuretype = 'normal'
		for i in range(n):
			self.logger.info('Acquiring reference image (%s of %s)' % (i+1, n))
			try:
				imagedata = self.acquireCameraImageData(type=exposuretype)
			except Exception, e:
				self.logger.error('Error acquiring image: %s' % e)
				raise
			if self.settings['store series']:
				self.storeCorrectorImageData(imagedata, type, channel)
			imagearray = imagedata['image']
			if i == 0:
				avg = numpy.asarray(imagearray, numpy.float32)
			else:
				delta = imagearray - avg
				avg = avg + delta / (i+1)
		## final image based on contents of last image in series
		finaldata = leginondata.CameraImageData(initializer=imagedata)
		finaldata['image'] = avg
		finaldata = self.storeCorrectorImageData(finaldata, type, channel)
		return finaldata

	def acquireSeriesMedian(self, n, type, channel):
		series = []
		if type == 'dark':
			exposuretype = 'dark'
		else:
			exposuretype = 'normal'
		for i in range(n):
			self.logger.info('Acquiring reference image (%s of %s)' % (i+1, n))
			try:
				imagedata = self.acquireCameraImageData(type=exposuretype)
			except Exception, e:
				self.logger.error('Error acquiring image: %s' % e)
				raise
			if self.settings['store series']:
				self.storeCorrectorImageData(imagedata, type, channel)
			imagearray = imagedata['image']
			series.append(imagearray)
		## calc median
		med = imagefun.medianSeries(series)
		med = numpy.asarray(med, numpy.float32)

		## final image based on contents of last image in series
		finaldata = leginondata.CameraImageData(initializer=imagedata)
		finaldata['image'] = med
		finaldata = self.storeCorrectorImageData(finaldata, type, channel)
		return finaldata

	def insert(self, x):
		self.__n += 1
		if self.__n == 1:
			self.__mean = numpy.asarray(x, numpy.float32)
		else:
			delta = x - self.__mean
			self.__mean = self.__mean + delta / self.__n

	def acquireReference(self, type, channel):
		try:
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			if type == 'dark':
				typekey = 'dark'
				self.logger.info('Acquiring dark references...')
			else:
				typekey = 'bright'
				self.logger.info('Acquiring bright references...')
		except Exception, e:
			self.logger.error('Reference acquisition failed: %s' % (e,))
			return None

		combine = self.settings['combine']
		n = self.settings['n average']
		if combine == 'average':
			refimagedata = self.acquireSeriesAverage(n, type, channel)
		elif combine == 'median':
			refimagedata = self.acquireSeriesMedian(n, type, channel)
		refarray = refimagedata['image']

		if refimagedata is not None:
			self.logger.info('Got reference image, calculating normalization')
			self.calc_norm(refimagedata)

		self.maskimg = numpy.zeros(refarray.shape)
		return refarray

	def calc_norm(self, refdata):
		scopedata = refdata['scope']
		cameradata = refdata['camera']
		channel = refdata['channel']
		if isinstance(refdata, leginondata.DarkImageData):
			dark = refdata
			bright = self.retrieveCorrectorImageData('bright', scopedata, cameradata, channel)
			if bright is None:
				self.logger.warning('No bright reference image for normalization calculations')
				return
		if isinstance(refdata, leginondata.BrightImageData):
			bright = refdata
			dark = self.retrieveCorrectorImageData('dark', scopedata, cameradata, channel)
			if dark is None:
				self.logger.warning('No dark reference image for normalization calculations')
				return
		try:
			darkarray = self.prepareDark(dark, bright)
		except:
			self.logger.warning('Unable to load dark image from %s' % dark['session']['image path'])
			return
		try:
			brightarray = bright['image']
		except:
			self.logger.warning('Unable to load bright image from %s' % bright['session']['image path'])
			return

		try:
			normarray = brightarray - darkarray
		except:
			self.logger.error('dark subtraction failed.')
			return
		normarray = numpy.asarray(normarray, numpy.float32)
		normavg = arraystats.mean(normarray)

		# division may result infinity or zero division
		# so make sure there are no zeros in norm
		normarray = numpy.clip(normarray, 0.001, sys.maxint)
		normarray = normavg / normarray
		# Avoid over correcting dead pixels
		normarray = numpy.ma.masked_greater(normarray,20).filled(1)
		# Saving normdata
		normdata = leginondata.CameraImageData(initializer=refdata)
		normdata['image'] = normarray
		normdata['dark'] = dark
		normdata['bright'] = bright
		self.storeCorrectorImageData(normdata, 'norm', channel)

	def uiAutoAcquireReferences(self):
		binning = self.autobinning.get()
		autoexptime = self.autoexptime.get()
		targetmean = self.autotarget.get()
		self.autoAcquireReferences(binning, targetmean, autoexptime)

	def autoAcquireReferences(self, binning, targetmean, initial_exp):
		'''
		for a given binning, figure out the proper exposure time
		which gives the desired mean pixel value
		'''
		config = {
			'dimension':{'x':256, 'y':256},
			'binning':{'x':binning, 'y':binning},
			'auto offset': True,
			'exposure time': 0,
		}

		raise NotImplementedError('need to work out the details of configuring the camera here')

		im = self.acquireCameraImageData()['image']
		mean = darkmean = arraystats.mean(im)
		self.displayImage(im)
		self.logger.info('Dark reference mean: %s' % str(darkmean))

		target_exp = 0
		trial_exp = initial_exp
		tolerance = 100
		minmean = targetmean - tolerance
		maxmean = targetmean + tolerance

		tries = 5
		for i in range(tries):
			config = { 'exposure time': trial_exp }
			raise NotImplementedError('need to work out the details of configuring the camera here')
			im = self.acquireCameraImageData()['image']
			mean = arraystats.mean(im)
			self.displayImage(im)
			self.logger.info('Image mean: %s' % str(mean))

			if minmean <= mean <= maxmean:
				i = -1
				break
			else:
				slope = (mean - darkmean) / trial_exp
				trial_exp = (targetmean - darkmean) / slope

		if i == tries-1:
			self.logger.info('Failed to find target mean after %s tries' % (tries,))

	def onAddPoints(self):
		imageshown = self.currentimage
		plan = self.retrieveCorrectorPlanFromSettings()
		if plan is not None:
			self.fixBadPixels(imageshown, plan)
		imagemean = imageshown.mean()
		badpixelcount = len(plan['pixels'])
		newbadpixels = plan['pixels']
		# Note: Must use numpy min, max function here because arraystats remembers the
		# old value.  If the latter is used, this function only work once per
		# image displayed
		extrema = imageshown.min(),imageshown.max()
		# add points only on max or min depending on how far they are from mean
		usemax = extrema[1] - imagemean > imagemean - extrema[0]
		if usemax:
			indices = [1]
		else:
			indices = [0]
		# also remove values less than or equal to zero
		if extrema[0] <= 0.0 and usemax:
			indices.append(0)
		for i in indices:
			currentvalue = extrema[i]
			coordinates = numpy.argwhere(imageshown == currentvalue)
			coordinates = coordinates.tolist()
			for bad in coordinates:
				# convert to tuple to be consistent with plan
				xy = bad[1], bad[0]
				if xy not in newbadpixels:
					if len(newbadpixels) >= self.max_badpixels:
						self.logger.error("Too many bad pixels, new pixels not added")
						break
					else:
						newbadpixels.append(xy)
						self.logger.info("added bad pixel point at (%d,%d) at %d" % (bad[1], bad[0],int(currentvalue)))
						# Assign the bad pixel intensity to mean so that it will not be found in the next round
						imageshown[bad]=imagemean

		plan['pixels'] = newbadpixels
		self.displayImage(imageshown)
		self.currentimage = imageshown
		self.storeCorrectorPlan(plan)
		self.panel.setPlan(plan)

	def onAddRegion(self):
		vertices = []
		vertices = self.panel.imagepanel.getTargetPositions('Bad_Region')
		if len(vertices) < 3:
			self.logger.error('Need at least 3 vertices to define the region')
			return
		badpixels = polygon.indicesInsidePolygon(self.maskimg.shape,vertices)
		plan = self.retrieveCorrectorPlanFromSettings()
		oldbadpixels = plan['pixels']
		fullbadpixelset = set()
		fullbadpixelset = fullbadpixelset.union(oldbadpixels)
		fullbadpixelset = fullbadpixelset.union(badpixels)
		if len(fullbadpixelset) > self.max_badpixels:
			self.logger.error("Too many bad pixels, new pixels not added")
		else:
			plan['pixels'] = list(fullbadpixelset)
			self.storeCorrectorPlan(plan)
		self.panel.setPlan(plan)
		self.setTargets([], 'Bad_Region', block=False)

	def processImageData(self, imagedata):
		print 'IMAGEDATA******************************'
		import sinedon.data
		print 'IMAGE', imagedata['image']
		imagecopy = imagedata.copy()
		self.correctCameraImageData(imagecopy, 0)
		print 'imagecopy corrected', imagecopy['image']
		pixeltype = str(imagedata['image'].dtype)
		imagecopy['pixeltype'] = pixeltype
		if True:
			## save new record to DB, including writing mrc
			imagecopy.insert(force=True)
		else:
			## only save mrc
			fullname = os.path.join(imagecopy.mkpath(), imagecopy.filename())
			mrc.write(imagecopy['image'], fullname)

		## now we should tell the acquisition node we are done
		## because it may need to delete the original
