#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginondata
import event
import imagewatcher
import numpy
import scipy.ndimage
import gui.wx.Corrector
import instrument
import sys
from pyami import arraystats, imagefun, mrc
import polygon
import time
import os

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
		'camera settings': None,
		'combine': 'average',
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
		plan = self.retrieveCorrectorPlan(cameradata)
		return plan

	def acquireDark(self, channels):
		for channel in channels:
			try:
				imagedata = self.acquireReference(type='dark', channel=channel)
			except Exception, e:
				raise
				self.logger.exception('Cannot acquire dark reference: %s' % e)
			else:
				self.displayImage(imagedata)
				self.currentimage = imagedata
				self.beep()
		self.panel.acquisitionDone()

	def acquireBright(self, channels):
		for channel in channels:
			try:
				imagedata = self.acquireReference(type='bright', channel=channel)
			except Exception, e:
				raise
				self.logger.exception('Cannot acquire bright reference: %s' % e)
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
			image = self.instrument.ccdcamera.Image
			self.stopTimer('get image')
		except Exception, e:
                        raise
			self.logger.exception('Raw acquisition failed: %s' % e)
		else:
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

		imdata = self.retrieveCorrectorImageFromSettings(reftype, channel)
		imarray = imdata['image']
		self.displayImage(imarray)
		self.currentimage = imarray
		self.beep()
		self.setStatus('idle')

	def acquireSeries(self, n):
		series = []
		for i in range(n):
			self.logger.info('Acquiring reference image (%s of %s)' % (i+1, n))
			image = self.instrument.ccdcamera.Image
			series.append(image)
		return series

	def acquireReference(self, type, channel):
		try:
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			exposuretype = self.instrument.ccdcamera.ExposureType
			if type == 'dark':
				if exposuretype != 'dark':
					self.instrument.ccdcamera.ExposureType = 'dark'
				typekey = 'dark'
				self.logger.info('Acquiring dark references...')
			else:
				if exposuretype != 'normal':
					self.instrument.ccdcamera.ExposureType = 'normal'
				typekey = 'bright'
				self.logger.info('Acquiring bright references...')
		except Exception, e:
			self.logger.error('Reference acquisition failed: %s' % e)
			self.instrument.ccdcamera.ExposureType = 'normal'
			return None

		try:
			series = self.acquireSeries(self.settings['n average'])
		except Exception, e:
			self.logger.error('Reference acquisition failed: %s' % e)
			self.instrument.ccdcamera.ExposureType = 'normal'
			return None

		combine = self.settings['combine']
		self.logger.info('taking %s of image series' % (combine,))
		if combine == 'average':
			ref = imagefun.averageSeries(series)
		elif combine == 'median':
			ref = imagefun.medianSeries(series)
		else:
			self.instrument.ccdcamera.ExposureType = 'normal'
			raise RuntimeError('invalid setting "%s" for combine method' % (combine,))

		## make if float so we can do float math later
		ref = numpy.asarray(ref, numpy.float32)

		scopedata = self.instrument.getData(leginondata.ScopeEMData)
		cameradata = self.instrument.getData(leginondata.CameraEMData)

		refimagedata = self.storeCorrectorImageData(ref, typekey, scopedata, cameradata, channel)
		if refimagedata is not None:
			self.logger.info('Got reference image, calculating normalization')
			self.calc_norm(refimagedata)

		try:
			self.instrument.ccdcamera.ExposureType = exposuretype
		except Exception, e:
			self.logger.error('Reference acquisition failed: %s' % e)
			self.instrument.ccdcamera.ExposureType = 'normal'
			return None

		self.maskimg = numpy.zeros(ref.shape)
		return ref

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
			darkarray = dark['image']
		except:
			self.logger.warning('Unable to load dark image from %s' % dark['session']['image path'])
			return
		try:
			darkarray = dark['image']
			brightarray = bright['image']
		except:
			self.logger.warning('Unable to load bright image from %s' % bright['session']['image path'])
			return
		normarray = brightarray - darkarray
		normarray = numpy.asarray(normarray, numpy.float32)

		normavg = arraystats.mean(normarray)

		# division may result infinity or zero division
		# so make sure there are no zeros in norm
		normarray = numpy.clip(normarray, 0.001, sys.maxint)
		normarray = normavg / normarray
		self.storeCorrectorImageData(normarray, 'norm', scopedata, cameradata, channel)

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

		im = self.instrument.ccdcamera.Image
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
			im = self.instrument.ccdcamera.Image
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
		imagemean = imageshown.mean()
		plan = self.retrieveCorrectorPlanFromSettings()
		badpixelcount = len(plan['pixels'])
		newbadpixels = plan['pixels']
		while  len(newbadpixels) <= badpixelcount+2 :
			extrema = scipy.ndimage.extrema(imageshown)
			# add points only on max or min depending on how far they are from mean
			usemax = extrema[1] - imagemean > imagemean - extrema[0]
			if usemax:
				i = 3
			else:
				i = 2
			currentvalue = extrema[i-2]
			newextrema = extrema
			while newextrema[i-2] == currentvalue:
				if newextrema[i] not in newbadpixels:
					newbadpixels.append(newextrema[i])
					self.logger.info("added bad pixel point at (%d,%d)" % (newextrema[i]))
				imageshown[newextrema[i]]=imagemean
				newextrema=scipy.ndimage.extrema(imageshown)
		plan['pixels'] = newbadpixels
		self.displayImage(imageshown)
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
