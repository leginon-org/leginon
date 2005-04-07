#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import copy
import data
import event
import imagefun
import node
try:
	import numarray as Numeric
except:
	import Numeric
import threading
import gui.wx.Corrector
import remotecall
import instrument
import sys

class CameraError(Exception):
	pass

class FindExposureTimeError(Exception):
	pass

class AbortError(Exception):
	pass

class ImageCorrection(remotecall.Object):
	def __init__(self, node):
		self.node = node
		remotecall.Object.__init__(self)

	def getImage(self, ccdcameraname=None):
		if ccdcameraname is not None:
			self.node.instrument.setCCDCamera(ccdcameraname)
		return self.node.acquireCorrectedImage()

	def getImageData(self, ccdcameraname=None):
		if ccdcameraname is not None:
			self.node.instrument.setCCDCamera(ccdcameraname)
		return self.node.acquireCorrectedImageData()

class Corrector(node.Node):
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
	settingsclass = data.CorrectorSettingsData
	defaultsettings = {
		'n average': 3,
		'despike': True,
		'despike size': 11,
		'despike threshold': 3.5,
		'camera settings': None,
	}
	eventinputs = node.Node.eventinputs
	eventoutputs = node.Node.eventoutputs + [event.DarkImagePublishEvent, event.BrightImagePublishEvent]
	def __init__(self, name, session, managerlocation, **kwargs):
		node.Node.__init__(self, name, session, managerlocation, **kwargs)

		self.ref_cache = {}
		self.plan = None

		self.instrument = instrument.Proxy(self.objectservice,
																				self.session,
																				self.panel)
		self.correctionobject = ImageCorrection(self)
		self.objectservice._addObject('Image Correction', self.correctionobject)

		self.imagedata = data.DataHandler(data.CorrectedCameraImageData,
																			getdata=self.acquireCorrectedImageData)
		self.publish(self.imagedata, pubevent=True, broadcast=True)

		self.start()

	def setPlan(self):
		newcamstate = data.CorrectorCamstateData()
		newcamstate['session'] = self.session
		try:
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			newcamstate.friendly_update(self.instrument.ccdcamera.Geometry)
		except Exception, e:
			self.logger.error('Plan not saved: %s' % e)
			return
		plandata = data.CorrectorPlanData()
		plandata['session'] = self.session
		plandata['camstate'] = newcamstate
		plandata['bad_rows'] = self.plan['rows']
		plandata['bad_cols'] = self.plan['columns']
		plandata['tem'] = self.instrument.getTEMData()
		plandata['ccdcamera'] = self.instrument.getCCDCameraData()
		self.storePlan(plandata)

	def getPlan(self):
		newcamstate = data.CorrectorCamstateData()
		if self.settings['camera settings'] is None:
			self.plan = None
		else:
			for i in ['dimension', 'offset', 'binning']:
				newcamstate[i] = dict(self.settings['camera settings'][i])
			self.plan = self.retrievePlan(newcamstate)

	def acquireDark(self):
		try:
			imagedata = self.acquireReference(dark=True)
		except Exception, e:
			self.logger.exception('Cannot acquire dark reference: %s' % e)
		else:
			self.displayImage(imagedata)
			self.beep()
		self.panel.acquisitionDone()

	def acquireBright(self):
		try:
			imagedata = self.acquireReference(dark=False)
		except Exception, e:
			self.logger.exception('Cannot acquire bright reference: %s' % e)
		else:
			self.displayImage(imagedata)
			self.beep()
		self.panel.acquisitionDone()

	def acquireRaw(self):
		try:
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			image = self.instrument.ccdcamera.Image
		except Exception, e:
			self.logger.exception('Raw acquisition failed: %s' % e)
		else:
			self.displayImage(image)
		self.panel.acquisitionDone()

	def acquireCorrected(self):
		try:
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			image = self.acquireCorrectedImage()
		except Exception, e:
			self.logger.exception('Corrected acquisition failed: %s' % e)
		else:
			if image is not None:
				self.displayImage(image)
		self.panel.acquisitionDone()

	def displayImage(self, image):
		if image is None:
			self.setImage(None, stats={})
		else:
			self.setImage(image.astype(Numeric.Float32), stats=self.stats(image))

	def retrievePlan(self, corstate):
		qplan = data.CorrectorPlanData()
		qplan['camstate'] = corstate
		qplan['tem'] = self.instrument.getTEMData()
		qplan['ccdcamera'] = self.instrument.getCCDCameraData()
		plandatalist = self.research(datainstance=qplan)
		if plandatalist:
			plandata = plandatalist[0]
			return {'rows': list(plandata['bad_rows']),
							'columns': list(plandata['bad_cols'])}
		else:
			return {'rows': [], 'columns': []}

	def storePlan(self, plandata):
		self.publish(plandata, database=True, dbforce=True)

	def acquireSeries(self, n):
		series = []
		for i in range(n):
			self.logger.info('Acquiring reference image (%s of %s)' % (i+1, n))
			image = self.instrument.ccdcamera.Image
			series.append(image)
		return series

	def acquireReference(self, dark=False):
		try:
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			exposuretype = self.instrument.ccdcamera.ExposureType
			if dark:
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
			return None

		try:
			series = self.acquireSeries(self.settings['n average'])
		except Exception, e:
			self.logger.error('Reference acquisition failed: %s' % e)

		self.logger.info('Averaging reference series...')
		ref = imagefun.averageSeries(series)

		corstate = data.CorrectorCamstateData()
		geometry = self.instrument.ccdcamera.Geometry
		corstate.friendly_update(geometry)

		refimagedata = self.storeRef(typekey, ref, corstate)
		if refimagedata is not None:
			self.logger.info('Got reference image, calculating normalization')
			self.calc_norm(refimagedata)

		try:
			self.instrument.ccdcamera.ExposureType = exposuretype
		except Exception, e:
			self.logger.error('Reference acquisition failed: %s' % e)
			return None

		return ref

	def researchRef(self, camstate, type):
		if type == 'dark':
			imagetemp = data.DarkImageData()
		elif type == 'bright':
			imagetemp = data.BrightImageData()
		elif type == 'norm':
			imagetemp = data.NormImageData()
		else:
			return None

		imagetemp['camstate'] = camstate
		imagetemp['tem'] = self.instrument.getTEMData()
		imagetemp['ccdcamera'] = self.instrument.getCCDCameraData()
		try:
			ref = self.research(datainstance=imagetemp, results=1)[0]
		except node.ResearchError, e:
			self.logger.warning('Loading reference image failed: %s' % (e,))
			ref = None
		except IndexError:
			self.logger.warning('Loading reference image failed')
			ref = None
		except Exception, e:
			self.logger.error('Loading reference image failed: %s' % e)
			ref = None
		else:
			self.logger.info('Reference image loaded: %s' % (ref['filename'],))
		return ref

	def formatKey(self, key):
		try:
			if key[6] == 'dark':
				exptype = 'dark reference image'
			elif key[6] == 'bright':
				exptype = 'bright reference image'
			elif key[6] == 'norm':
				exptype = 'normalization image'
			else:
				exptype = key[6]
		except IndexError:
			exptype = 'unknown image'
		s = '%s: %dx%d, offset (%d, %d), binned %dx%d'
		try:
			return s % (exptype, key[0], key[1], key[4], key[5], key[2], key[3])
		except IndexError:
			return str(key)

	def refKey(self, camstate, type):
		mylist = []
		for param in ('dimension', 'binning', 'offset'):
			values = camstate[param]
			if values is None:
				valuetuple = (None,None)
			else:
				valuetuple = (values['x'],values['y'])
			mylist.extend( valuetuple )
		mylist.append(type)
		return tuple(mylist)

	def retrieveRef(self, camstate, type):
		key = self.refKey(camstate, type)
		## another way to do the cache would be to use the local
		##   data keeper

		## try to use reference image from cache
		try:
			return self.ref_cache[key]
		except KeyError:
			self.logger.info('Loading %s...' % self.formatKey(key))

		## use reference image from database
		ref = self.researchRef(camstate, type)
		if ref:
			image = ref['image']
			self.ref_cache[key] = image
		else:
			image = None
		return image

	def storeRef(self, type, numdata, camstate):
		## another way to do the cache would be to use the local
		## data keeper

		## store in cache
		key = self.refKey(camstate, type)
		self.ref_cache[key] = numdata

		## store in database
		if type == 'dark':
			imagetemp = data.DarkImageData()
		elif type == 'bright':
			imagetemp = data.BrightImageData()
		elif type == 'norm':
			imagetemp = data.NormImageData()
		imagetemp['image'] = numdata
		imagetemp['camstate'] = camstate
		imagetemp['filename'] = self.filename(type, imagetemp.dmid[-1])
		imagetemp['session'] = self.session
		imagetemp['tem'] = self.instrument.getTEMData()
		imagetemp['ccdcamera'] = self.instrument.getCCDCameraData()
		self.logger.info('Publishing reference image...')
		try:
			self.publish(imagetemp, pubevent=True, database=True)
		except node.PublishError, e:
			self.logger.error('Publishing reference image failed: %s' % (e,))
			return None
		self.logger.info('Reference image published')
		return imagetemp

	def filename(self, reftype, imid):
		f = '%s_%s_%s_%06d' % (self.session['name'], self.name, reftype, imid)
		return f

	def calc_norm(self, corimagedata):
		corstate = corimagedata['camstate']
		if isinstance(corimagedata, data.DarkImageData):
			dark = corimagedata['image']
			bright = self.retrieveRef(corstate, 'bright')
			if bright is None:
				self.logger.warning('No bright reference image for normalization calculations')
				return
		if isinstance(corimagedata, data.BrightImageData):
			bright = corimagedata['image']
			dark = self.retrieveRef(corstate, 'dark')
			if dark is None:
				self.logger.warning('No dark reference image for normalization calculations')
				return

		norm = bright - dark
		norm = norm.astype(Numeric.Float32)

		## there may be a better normavg than this
		normavg = imagefun.mean(norm)

		# division may result infinity or zero division
		# so make sure there are no zeros in norm
		norm = Numeric.clip(norm, 0.001, sys.maxint)
		norm = normavg / norm
		self.storeRef('norm', norm, corstate)

	def acquireCorrectedImage(self):
		try:
			image = self.instrument.ccdcamera.Image
			geometry = self.instrument.ccdcamera.Geometry
		except:
			self.logger.exception('Unable to acquire image')
			return None
		try:
			image = self.correct(image, geometry)
		except Exception, e:
			self.logger.warning('Unable to correct acquired image: %s' % e)
			return None
		return image

	def acquireCorrectedImageData(self):
		self.setStatus('processing')
		errstr = 'Acquisition of corrected image failed: %s'
		try:
			imagedata = self.instrument.getData(data.CameraImageData)
		except Exception, e:
			self.logger.exception(errstr % 'unable to access instrument')
			self.setStatus('idle')
			return None
		numimage = imagedata['image']
		camdata = imagedata['camera']
		corstate = data.CorrectorCamstateData()
		corstate['dimension'] = camdata['dimension']
		corstate['offset'] = camdata['offset']
		corstate['binning'] = camdata['binning']
		corrected = self.correct(numimage, corstate)
		newdata = data.CorrectedCameraImageData(initializer=imagedata,
																						image=corrected)
		self.setStatus('idle')
		return newdata

	def correct(self, original, camstate):
		'''
		this puts an image through a pipeline of corrections
		'''
		if type(camstate) is dict:
			camstate = data.CorrectorCamstateData(initializer=camstate)
		normalized = self.normalize(original, camstate)
		plan = self.retrievePlan(camstate)
		if plan is not None:
			good = self.removeBadPixels(normalized, plan)

		if self.settings['despike']:
			self.logger.debug('Despiking...')
			nsize = self.settings['despike size']
			thresh = self.settings['despike threshold']
			imagefun.despike(normalized, nsize, thresh)
			self.logger.debug('Despiked')

		## this has been commented because original.type()
		## might be unsigned and causes negative values to wrap
		## around to very large positive values
		## before doing this astype, we should maybe clip negative
		## values
		#return good.astype(original.type())

		final = normalized.astype(Numeric.Float32)
		return final

	def removeBadPixels(self, image, plan):
		badrows = plan['rows']
		badcols = plan['columns']
		badrowscols = [badrows,badcols]

		shape = image.shape

		for axis in (0,1):
			for bad in badrowscols[axis]:
				## find a near by good one
				good = None
				for i in range(bad+1,shape[axis]):
					if i not in badrowscols[axis]:
						good = i
						break
				if good is None:
					for i in range(bad-1,-1,-1):
						if i not in badrowscols[axis]:
							good = i
							break
				if good is None:
					raise RuntimeError('image has no good rows/cols')
				else:
					if axis == 0:
						image[bad] = image[good]
					else:
						image[:,bad] = image[:,good]

	def normalize(self, raw, camstate):
		dark = self.retrieveRef(camstate, 'dark')
		norm = self.retrieveRef(camstate, 'norm')
		if dark is not None and norm is not None:
			diff = raw - dark
			## this may result in some infinity values
			r = diff * norm
			return r
		else:
			self.logger.warning('Cannot find references, image will not be normalized')
			return raw

	def stats(self, im):
		mean = imagefun.mean(im)
		stdev = imagefun.stdev(im, known_mean=mean)
		mn = imagefun.min(im)
		mx = imagefun.max(im)
		return {'mean':mean,'stdev':stdev,'min':mn,'max':mx}

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
		mean = darkmean = imagefun.mean(im)
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
			mean = imagefun.mean(im)
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

