#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
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
import datetime
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
		self.clock_diff = datetime.timedelta()
		self.start()

	def retrieveCorrectorImageFromSettings(self, reftype, channel):
		ccdcameraname = self.settings['instruments']['ccdcamera']
		camsettings = self.settings['camera settings']
		if ccdcameraname is None or camsettings is None:
			return None
		cameradata = leginondata.CameraEMData()
		if ccdcameraname == 'None':
			# when real camera is not ready, the settings name reverts to
			# to the string 'None'
			return None
		try:
			cameradata['ccdcamera'] = self.instrument.getCCDCameraData(ccdcameraname)
			cameradata.update(camsettings)
			cdata = self.instrument.getData(leginondata.CameraEMData)
			cameradata['gain index'] = cdata['gain index']
			scopedata = self.instrument.getData(leginondata.ScopeEMData)
			imdata = self.retrieveCorrectorImageData(reftype, scopedata, cameradata, channel)
			# returns None if there is no reference found
			return imdata
		except Exception as e:
			self.logger.error(e)
			return None

	def retrieveCorrectorPlanFromSettings(self):
		ccdcameraname = self.settings['instruments']['ccdcamera']
		camsettings = self.settings['camera settings']
		if ccdcameraname is None or camsettings is None:
			# settings never set
			return None
		if ccdcameraname == 'None':
			# when real camera is not ready, the settings name reverts to
			# to the string 'None'
			return None
		try:
			cameradata = leginondata.CameraEMData()
			cameradata['ccdcamera'] = self.instrument.getCCDCameraData(ccdcameraname)
			cameradata.update(camsettings)
			cdata = self.instrument.getData(leginondata.CameraEMData)
			cameradata['gain index'] = cdata['gain index']
			plan, plandata = self.retrieveCorrectorPlan(cameradata)
			return plan
		except Exception as e:
			# catch error but not raise so it can be initialized.
			# most cases there is no plan anyway.
			self.logger.error(e)
			return formatCorrectorPlan(None)

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
		need_dark = not self.instrument.ccdcamera.SystemDarkSubtracted
		if not need_dark:
			self.logger.warning('%s does not need dark reference' % cameraname)
			self.panel.acquisitionDone()
			return
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
		cameraname = self.instrument.getCCDCameraName()
		need_bright = not (self.instrument.ccdcamera.FrameGainCorrected or self.instrument.ccdcamera.SumGainCorrected)
		if not need_bright:
			self.logger.warning('%s does not need bright reference' % cameraname)
			need_norm = not (self.instrument.ccdcamera.FrameGainCorrected and self.instrument.ccdcamera.SumGainCorrected)
			if need_norm:
				self.logger.warning('Use acquire Norm to retrieve gain reference from camera host')
			self.panel.acquisitionDone()
			return
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
			image = self.acquireRawCameraImageData(force_no_frames=True)['image']
			self.stopTimer('get image')
		except Exception, e:
			self.logger.exception('Raw acquisition failed: %s' % (e,))
		else:
			self.maskimg = numpy.zeros(image.shape)
			self.displayImage(image)
			self.currentimage = image
		self.panel.acquisitionDone()
		self.stopTimer('acquireRaw')

	def retrieveNorm(self, channels):
		"""
		Retrieve Norm image (Gain in Falcon terminology) instead of
		acquire our own.  Camera software often has an easier gui.
		"""
		if 1 in channels:
			self.logger.error('Norm retrieval can only be applied to channel 0')
			self.panel.acquisitionDone()
			return
		# save only to channel 0
		channel = 0
		try:
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			imagedata = self._retrieveReference(exp_type='norm', channel=channel)
		except Exception, e:
			self.logger.exception('Cannot retrieve reference: %s' % (e,))
		else:
			image = imagedata['image']
			self.displayImage(image)
			self.currentimage = image
			self.beep()
		self.panel.acquisitionDone()

	def acquireCorrected(self, channels):
		for channel in channels:
			self.startTimer('acquireCorrected')
			self.setTargets([], 'Bad_Region', block=False)
			self.startTimer('set ccd')
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			self.stopTimer('set ccd')
			imagedata = self.acquireCorrectedCameraImageData(channel, force_no_frames=True)
			if imagedata and 'image' in imagedata:
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

		need_dark = not self.instrument.ccdcamera.SystemDarkSubtracted
		need_bright = not (self.instrument.ccdcamera.FrameGainCorrected or self.instrument.ccdcamera.SumGainCorrected)
		if ('dark' in reftype and not need_dark) or ('bright' in reftype and not need_bright):
			self.logger.warning('Displaying %s is not valid for this camera' % reftype.upper())
			self.beep()
			self.setStatus('idle')
			return
		self.logger.info('load channel %s %s image' % (channel, reftype))
		if reftype != 'dark-subtracted':
			imdata = self.retrieveCorrectorImageFromSettings(reftype, channel)
			if imdata == None:
				self.logger.error('Camera settings not valid.  Please check')
				self.beep()
				self.setStatus('idle')
				return
			imarray = imdata['image']
		else:
			brightdata = self.retrieveCorrectorImageFromSettings('bright', channel)
			darkdata = self.retrieveCorrectorImageFromSettings('dark', channel)
			if brightdata == None or darkdata == None:
				self.logger.error('Camera settings not valid.  Please check')
				self.beep()
				self.setStatus('idle')
				return
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
			try:
				image = self.acquireRawCameraImageData(force_no_frames=True)['image']
			except Exception, e:
				self.logger.error(e)
				return
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
				imagedata = self.acquireRawCameraImageData(type=exposuretype, force_no_frames=True)
			except Exception, e:
				self.logger.error('Error acquiring image: %s' % e)
				return
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
				imagedata = self.acquireRawCameraImageData(type=exposuretype, force_no_frames=True)
			except Exception, e:
				self.logger.error('Error acquiring image: %s' % e)
				return
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

	def _retrieveReference(self,exp_type, channel):
		"""
		Pretend to acquire image but in fact return an existing one
		on the camera pc.
		"""
		exposuretype = exp_type
		try:
			imagedata = self.acquireRawCameraImageData(type=exposuretype, force_no_frames=True)
		except Exception, e:
			self.logger.error('Error retrieving image: %s' % e)
			raise
		## final image based on contents of last image in series
		imagedata = self.storeCorrectorImageData(imagedata, 'norm', 0)
		return imagedata

	def insert(self, x):
		self.__n += 1
		if self.__n == 1:
			self.__mean = numpy.asarray(x, numpy.float32)
		else:
			delta = x - self.__mean
			self.__mean = self.__mean + delta / self.__n

	def needCalcNorm(self, type):
			if type == 'bright':
				return True
			else:
				try:
					calc_on_dark = self.instrument.ccdcamera.getCalculateNormOnDark()
					return calc_on_dark
				except:
					self.logger.warning('Camera host pyscope update recommended')
					return True

	def getRecentDarkTimeStamp(self, channel):
		dark = self.retrieveCorrectorImageFromSettings('dark', channel)
		if dark:
			if dark.timestamp is None:
				# dark image collected just now are in cache and has no timestamp.
				# Query it from database since retrieveCorrectorImage will use cached if there.
				dark = leginondata.DarkImageData().direct_query(dark.dbid)
			return dark.timestamp
		return False

	def hasRecentDarkSaved(self, channel):
		trip_value = 600 # seconds
		dark_timestamp = self.getRecentDarkTimeStamp(channel)
		if dark_timestamp:
		# compare timestamps
			time_diff = datetime.datetime.now() - dark_timestamp - self.clock_diff
			return time_diff <= datetime.timedelta(seconds=trip_value)
		return False

	def requireRecentDarkOnBright(self):
		if hasattr(self.instrument.ccdcamera, 'requireRecentDarkOnBright'):
			return self.instrument.ccdcamera.requireRecentDarkOnBright()
		self.logger.warning('Camera host pyscope update recommended')
		return False

	def acquireReference(self, type, channel):
		try:
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			if type == 'dark':
				typekey = 'dark'
				self.logger.info('Acquiring dark references...')
			else:
				typekey = 'bright'
				if self.requireRecentDarkOnBright():
					if not self.hasRecentDarkSaved(channel):
						self.logger.error('Need recent Dark image before acquiring Bright Image')
						return None
				if self.requireRecentDarkCurrentReferenceOnBright():
					if not self.hasRecentDarkCurrentReferenceSaved(3600):
						self.updateCameraDarkCurrentReference(warning=True)
				self.logger.info('Acquiring bright references...')
		except Exception, e:
			self.logger.error('Reference acquisition failed: %s' % (e,))
			return None

		combine = self.settings['combine']
		n = self.settings['n average']
		try:
			if combine == 'average':
				refimagedata = self.acquireSeriesAverage(n, type, channel)
			elif combine == 'median':
				refimagedata = self.acquireSeriesMedian(n, type, channel)
		except Exception, e:
			self.logger.error(e)
			return None
		if refimagedata is None:
			return None
		if typekey == 'dark':
			dark_timestamp = self.getRecentDarkTimeStamp(channel)
			try:
				self.clock_diff = datetime.datetime.now() - dark_timestamp
			except:
				self.warning('Can not determine clock difference between database and this machine.  Assume zero')
				pass
		refarray = refimagedata['image']
		if refimagedata is not None and self.needCalcNorm(type):
			self.logger.info('Got reference image, calculating normalization')
			self.calcNormFromRefData(refimagedata)

		self.maskimg = numpy.zeros(refarray.shape)
		return refarray

	def _retrieveDarkBrightPair(self, refdata):
		scopedata = refdata['scope']
		cameradata = refdata['camera']
		channel = refdata['channel']
		# find the other refdata needed to calculate norm
		if isinstance(refdata, leginondata.DarkImageData):
			dark = refdata
			bright = self.retrieveCorrectorImageData('bright', scopedata, cameradata, channel)
			if bright is None:
				raise ValueError('No bright reference image for normalization calculations')
		if isinstance(refdata, leginondata.BrightImageData):
			bright = refdata
			dark = None
			need_dark = not self.instrument.ccdcamera.SystemDarkSubtracted
			if need_dark:
				dark = self.retrieveCorrectorImageData('dark', scopedata, cameradata, channel)
				if dark is None:
					raise ValueError('No dark reference image for normalization calculations')
		return dark, bright

	def calcNormFromRefData(self, refdata):
		try:
			dark, bright = self._retrieveDarkBrightPair(refdata)
		except ValueError as e:
			self.logger.warning(e)
			return
		except Exception as e:
			self.logger.error(e)
			return
		try:
			brightarray = bright['image']
		except:
			self.logger.warning('Unable to load bright image from %s' % bright['session']['image path'])
			return
		if dark:
			try:
				darkarray = self.prepareDark(dark, bright)
			except:
				self.logger.warning('Unable to load dark image from %s' % dark['session']['image path'])
				return
		else:
			darkarray = numpy.zeros(brightarray.shape)
		# calculation
		normarray = self._calc_norm(darkarray, brightarray)
		# Saving normdata
		normdata = leginondata.CameraImageData(initializer=refdata)
		normdata['image'] = normarray
		normdata['dark'] = dark
		normdata['bright'] = bright
		channel = refdata['channel']
		self.storeCorrectorImageData(normdata, 'norm', channel)

	def _calc_norm(self, darkarray, brightarray):
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
		return normarray

	def onAddPoints(self):
		'''
		Analyze the image and add points to the plan.
		'''
		imageshown = self.currentimage
		plan = self.retrieveCorrectorPlanFromSettings()
		if plan is None:
			self.logger.error('no valid correction plan, aborted. Check camera settings.')
			return
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
		if plan is None:
			self.logger.error('no valid correction plan, aborted. Check camera settings.')
			return
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
