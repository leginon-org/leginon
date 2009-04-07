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
import node
import numpy
import scipy.ndimage as nd
import gui.wx.Corrector
import remotecall
import instrument
import sys
from pyami import arraystats, imagefun
import polygon

class ImageCorrection(remotecall.Object):
	def __init__(self, node):
		self.node = node
		remotecall.Object.__init__(self)

	def getImageData(self, ccdcameraname=None):
		return self.node.acquireCorrectedImageData(ccdcameraname=ccdcameraname)

	def setChannel(self, channel):
		self.node.setChannel(channel)

ref_cache = {}
ref_cache_id = {}

class CorrectorClient(object):
	def __init__(self, node):
		self.node = node
		self.channel = 0

	def acquireCorrectedCameraImageData(self):
		## acquire image and scope/camera params
		imagedata = self.node.instrument.getData(leginondata.CameraImageData)
		imarray = imagedata['image']

		camdata = imagedata['camera']
		camstate = leginondata.CorrectorCamstateData()
		camstate['dimension'] = camdata['dimension']
		camstate['offset'] = camdata['offset']
		camstate['binning'] = camdata['binning']
		ccdcamera = camdata['ccdcamera']
		scopedata = imagedata['scope']
		corrected = self.correct(original=imarray, ccdcamera=ccdcamera, camstate=camstate, scopedata=scopedata)
		imagedata['image'] = corrected
		return imagedata

	def researchRef(self, camstate, type, ccdcameraname, scopedata, channel, readimages=True):
		if type == 'dark':
			imagetemp = leginondata.DarkImageData()
		elif type == 'bright':
			imagetemp = leginondata.BrightImageData()
		elif type == 'norm':
			imagetemp = leginondata.NormImageData()
		else:
			return None

		imagetemp['camstate'] = camstate
		imagetemp['tem'] = self.node.instrument.getTEMData()
		imagetemp['ccdcamera'] = leginondata.InstrumentData()
		imagetemp['ccdcamera']['name'] = ccdcameraname
		# only care about high tension for query
		imagetemp['scope'] = leginondata.ScopeEMData()
		imagetemp['scope']['high tension'] = scopedata['high tension']
		imagetemp['channel'] = channel
		try:
			ref = self.node.research(datainstance=imagetemp, results=1, readimages=readimages)
		except Exception, e:
			self.node.logger.warning('Loading reference image failed: %s' % e)
			ref = None

		if ref:
			ref = ref[0]
		else:
			# check if no results because no ref of requested channel
			# try to get ref of any channel
			imagetemp['channel'] = None
			try:
				ref = self.node.research(datainstance=imagetemp, results=1)
			except Exception, e:
				self.node.logger.warning('Loading reference image from any channel failed: %s' % e)
				ref = None
			if ref:
				ref = ref[0]
				self.node.logger.warning('channel requested: %s, channel available: %s' % (channel, ref['channel']))
			else:
				self.node.logger.error('No reference image in database')
				ref = None

		if ref is not None:
			self.node.logger.info('Reference image loaded: %s' % (ref['filename'],))

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
		s = '%s, %dV, size %dx%d, bin %dx%d, offset (%d,%d), channel %d'
		try:
			return s % (exptype, key[8], key[0], key[1], key[2], key[3], key[4], key[5], key[9])
		except IndexError:
			return str(key)

	def refKey(self, camstate, type, ccdcameraname, scopedata, channel):
		mylist = []
		for param in ('dimension', 'binning', 'offset'):
			values = camstate[param]
			if values is None:
				valuetuple = (None,None)
			else:
				valuetuple = (values['x'],values['y'])
			mylist.extend( valuetuple )
		mylist.append(type)
		mylist.append(ccdcameraname)
		mylist.append(scopedata['high tension'])
		mylist.append(channel)
		return tuple(mylist)

	def getFromCache(self, camstate, type, ccdcameraname, scopedata, channel):
		key = self.refKey(camstate, type, ccdcameraname, scopedata, channel)
		cachedim = ref_cache[key]
		newref = self.researchRef(camstate, type, ccdcameraname, scopedata, channel, readimages=False)
		if newref.dbid != ref_cache_id[key]:
			ref_cache[key] = newref['image']
			ref_cache_id[key] = newref.dbid
			return newref['image']
		else:
			return cachedim

	def retrieveRef(self, camstate, type, ccdcameraname, scopedata, channel):
		key = self.refKey(camstate, type, ccdcameraname, scopedata, channel)
		## another way to do the cache would be to use the local
		##   data keeper

		## try to use reference image from cache
		try:
			return self.getFromCache(camstate, type, ccdcameraname, scopedata, channel)
		except KeyError:
			self.node.logger.info('Loading %s...' % self.formatKey(key))

		## use reference image from database
		ref = self.researchRef(camstate, type, ccdcameraname, scopedata, channel)
		if ref:
			## make it float to do float math later
			image = numpy.asarray(ref['image'], numpy.float32)
			ref_cache[key] = image
			ref_cache_id[key] = ref.dbid
		else:
			image = None
		return image

	def normalize(self, raw, camstate, ccdcameraname, scopedata):
		channel = self.channel
		dark = self.retrieveRef(camstate, 'dark', ccdcameraname, scopedata, channel)
		norm = self.retrieveRef(camstate, 'norm', ccdcameraname, scopedata, channel)
		if dark is not None and norm is not None:
			print 'DARK', id(dark)
			print 'NORM', id(norm)
			diff = raw - dark
			r = diff * norm
			## remove nan and inf
			r = numpy.where(numpy.isfinite(r), r, 0)
			return r
		else:
			self.node.logger.warning('Cannot find references, image will not be normalized')
			return raw

	def denormalize(self, imagedata):
		'''
		reverse the normalization to create a raw image
		'''
		camstate = leginondata.CorrectorCamstateData()
		for key in ('dimension', 'offset', 'binning'):
			camstate[key] = imagedata['camera'][key]
		ccdcameraname = imagedata['camera']['ccdcamera']['name']
		scopedata = imagedata['scope']
		channel = imagedata['correction channel']
		dark = self.retrieveRef(camstate, 'dark', ccdcameraname, scopedata, channel)
		norm = self.retrieveRef(camstate, 'norm', ccdcameraname, scopedata, channel)
		corrected = imagedata['image']
		raw = corrected / norm
		raw = numpy.where(numpy.isfinite(raw), raw, 0)
		raw = raw + dark
		return raw

	def reverse_channel(self, imagedata):
		raw = self.denormalize(imagedata)
		oldchannel = imagedata['correction channel']
		if oldchannel == 1:
			self.channel = 0
		else:
			self.channel = 1
		camstate = leginondata.CorrectorCamstateData()
		for key in ('dimension', 'offset', 'binning'):
			camstate[key] = imagedata['camera'][key]
		ccdcameraname = imagedata['camera']['ccdcamera']['name']
		scopedata = imagedata['scope']
		
		corrected = self.normalize(raw, camstate, ccdcameraname, scopedata)
		newimagedata = leginondata.AcquisitionImageData(initializer=imagedata)
		newimagedata['image'] = corrected
		return newimagedata

	def correct(self, ccdcamera, original, camstate, scopedata, despike=False, despikesize=None, despikethresh=None, clip=None):
		'''
		this puts an image through a pipeline of corrections
		'''
		if type(camstate) is dict:
			camstate = leginondata.CorrectorCamstateData(initializer=camstate)
		normalized = self.normalize(original, camstate, ccdcamera['name'], scopedata)
		plan = self.retrievePlan(ccdcamera, camstate)
		if plan is not None:
			self.fixBadPixels(normalized, plan)

		if clip and (clip[0] or clip[1]):
			clipped = numpy.clip(normalized, clip[0], clip[1])
		else:
			clipped = normalized

		if despike:
			self.node.logger.debug('Despiking...')
			nsize = despikesize
			thresh = despikethresh
			imagefun.despike(clipped, nsize, thresh)
			self.node.logger.debug('Despiked')

		final = numpy.asarray(clipped, numpy.float32)
		return final

	def retrievePlan(self, ccdcamera, corstate):
		qplan = leginondata.CorrectorPlanData()
		qplan['camstate'] = corstate
		qplan['ccdcamera'] = ccdcamera
		plandatalist = self.node.research(datainstance=qplan)
		if plandatalist:
			plandata = plandatalist[0]
			result = {}
			result['rows'] = list(plandata['bad_rows'])
			result['columns'] = list(plandata['bad_cols'])
			if plandata['bad_pixels'] is None:
				result['pixels'] = []
			else:
				result['pixels'] = list(plandata['bad_pixels'])
			return result
		else:
			return {'rows': [], 'columns': [], 'pixels': []}

	def fixBadPixels(self, image, plan):
		badrows = plan['rows']
		badcols = plan['columns']
		badrowscols = [badrows,badcols]
		badpixels = plan['pixels']

		shape = image.shape

		## fix individual pixels (pixels are in x,y format)
		## replace each with median of 8 neighbors, however, some neighbors
		## are also labeled as bad, so we will not use those in the calculation
		for badpixel in badpixels:
			badcol,badrow = badpixel
			if badcol in badcols or badrow in badrows:
				## pixel will be fixed along with entire row/column later
				continue
			neighbors = []

			## d is how far we will go to find good pixels for this calculation
			## this is extra paranoia for the case where there is a whole cluster of
			## bad pixels. Usually it will only interate once (d=1)
			for d in range(1,20):
				for r in range(badrow-d, badrow+d+1):
					# check for out of bounds or bad neighbor
					if r<0 or r>=shape[0] or r in badrows:
						continue
					for c in range(badcol-d, badcol+d+1):
						# check for out of bounds or bad neighbor
						if c<0 or c>=shape[1] or c in badcols or (c,r) in badpixels:
							continue
						neighbors.append(image[r,c])
				if neighbors:
					break

			if not neighbors:
				return

			# median
			neighbors.sort()
			nlen = len(neighbors)
			if nlen % 2:
				# odd
				i = nlen // 2
				med = neighbors[i]
			else:
				i1 = nlen / 2
				i2 = i1 - 1
				med = (neighbors[i1]+neighbors[i2]) / 2
			image[badrow,badcol] = med

		## fix whole rows and columns
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

	def storeRef(self, type, numdata, camstate, scopedata, channel):
		## another way to do the cache would be to use the local
		## data keeper

		ccdcameraname = self.node.instrument.getCCDCameraName()
		ht = scopedata['high tension']
		## store in cache
		key = self.refKey(camstate, type, ccdcameraname, scopedata, channel)
		ref_cache[key] = numdata

		## store in database
		if type == 'dark':
			imagetemp = leginondata.DarkImageData()
		elif type == 'bright':
			imagetemp = leginondata.BrightImageData()
		elif type == 'norm':
			imagetemp = leginondata.NormImageData()
		imagetemp['image'] = numdata
		imagetemp['camstate'] = camstate
		imagetemp['filename'] = self.filename(type, imagetemp.dmid[-1])
		imagetemp['session'] = self.node.session
		imagetemp['tem'] = self.node.instrument.getTEMData()
		imagetemp['ccdcamera'] = self.node.instrument.getCCDCameraData()
		imagetemp['scope'] = scopedata
		imagetemp['channel'] = channel
		self.node.logger.info('Publishing reference image...')
		try:
			self.node.publish(imagetemp, pubevent=True, database=True)
		except node.PublishError, e:
			self.node.logger.error('Publishing reference image failed: %s' % (e,))
			return None
		ref_cache_id[key] = imagetemp.dbid
		self.node.logger.info('Reference image published')
		return imagetemp

	def filename(self, reftype, imid):
		f = '%s_%s_%s_%06d' % (self.node.session['name'], self.node.name, reftype, imid)
		return f



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
		'channels': 1,
	}
	eventinputs = node.Node.eventinputs
	eventoutputs = node.Node.eventoutputs + [event.DarkImagePublishEvent, event.BrightImagePublishEvent]
	def __init__(self, name, session, managerlocation, **kwargs):
		node.Node.__init__(self, name, session, managerlocation, **kwargs)

		self.corclient = CorrectorClient(self)
		self.corclient.channel = 0

		self.instrument = instrument.Proxy(self.objectservice,
																				self.session,
																				self.panel)
		self.correctionobject = ImageCorrection(self)
		self.objectservice._addObject('Image Correction', self.correctionobject)

		self.start()

	def setChannel(self, channel):
		self.corclient.channel = channel

	def getPlan(self):
		ccdcamera = self.instrument.getCCDCameraData()

		newcamstate = leginondata.CorrectorCamstateData()
		if self.settings['camera settings'] is None:
			plan = None
		else:
			for i in ['dimension', 'offset', 'binning']:
				newcamstate[i] = dict(self.settings['camera settings'][i])
			plan = self.corclient.retrievePlan(ccdcamera, newcamstate)
		return plan

	def acquireDark(self):
		channels = self.settings['channels']
		for channel in range(channels):
			try:
				imagedata = self.acquireReference(type='dark', channel=channel)
			except Exception, e:
				self.logger.exception('Cannot acquire dark reference: %s' % e)
			else:
				self.displayImage(imagedata)
				self.currentimage = imagedata
				self.beep()
		self.panel.acquisitionDone()

	def acquireBright(self):
		channels = self.settings['channels']
		for channel in range(channels):
			try:
				imagedata = self.acquireReference(type='bright', channel=channel)
			except Exception, e:
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

	def acquireCorrected(self):
		self.startTimer('acquireCorrected')
		try:
			self.startTimer('set ccd')
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			self.stopTimer('set ccd')
			imagedata = self.acquireCorrectedImageData()
			image = imagedata['image']
		except Exception, e:
			self.logger.exception('Corrected acquisition failed: %s' % e)
		else:
			if image is not None:
				self.displayImage(image)
				self.currentimage = image
		self.panel.acquisitionDone()
		self.stopTimer('acquireCorrected')

	def displayNorm(self,ccdcameraname=None):
		self.setStatus('processing')
		if self.instrument.getTEMName() != 'CM':
			self.logger.info('load channel %d norm image' % self.corclient.channel)
			cameradata = self.instrument.getData(leginondata.CameraEMData, ccdcameraname=ccdcameraname, image=False)
			scopedata = self.instrument.getData(leginondata.ScopeEMData)
			ccdcamera = cameradata['ccdcamera']
			corstate = leginondata.CorrectorCamstateData()
			corstate['dimension'] = cameradata['dimension']
			corstate['offset'] = cameradata['offset']
			corstate['binning'] = cameradata['binning']
			norm = self.corclient.retrieveRef(corstate, 'norm', ccdcameraname, scopedata, self.corclient.channel)
			self.displayImage(norm)
			self.currentimage = norm
			self.beep()
		self.setStatus('idle')

	def displayImage(self, image):
		self.startTimer('Corrector.displayImage')
		if image is None:
			self.setImage(None)
		else:
			self.setImage(numpy.asarray(image, numpy.float32))
		self.stopTimer('Corrector.displayImage')

	def storePlan(self, plan):
		newcamstate = leginondata.CorrectorCamstateData()
		newcamstate['session'] = self.session
		if self.instrument is None or self.instrument.ccdcamera is None:
			self.logger.error('Plan not saved: no camera to associate it with')
			return
		try:
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
			newcamstate.friendly_update(self.instrument.ccdcamera.Geometry)
		except Exception, e:
			self.logger.error('Plan not saved: %s' % e)
			return
		plandata = leginondata.CorrectorPlanData()
		plandata['session'] = self.session
		plandata['camstate'] = newcamstate
		plandata['bad_rows'] = plan['rows']
		plandata['bad_cols'] = plan['columns']
		plandata['bad_pixels'] = plan['pixels']
		plandata['ccdcamera'] = self.instrument.getCCDCameraData()
		self.publish(plandata, database=True, dbforce=True)

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

		corstate = leginondata.CorrectorCamstateData()
		geometry = self.instrument.ccdcamera.Geometry
		corstate.friendly_update(geometry)
		scopedata = self.instrument.getData(leginondata.ScopeEMData)

		refimagedata = self.corclient.storeRef(typekey, ref, corstate, scopedata, channel)
		if refimagedata is not None:
			self.logger.info('Got reference image, calculating normalization')
			self.calc_norm(refimagedata, self.instrument.getCCDCameraName(), scopedata)

		try:
			self.instrument.ccdcamera.ExposureType = exposuretype
		except Exception, e:
			self.logger.error('Reference acquisition failed: %s' % e)
			self.instrument.ccdcamera.ExposureType = 'normal'
			return None

		self.maskimg = numpy.zeros(ref.shape)
		return ref

	def calc_norm(self, corimagedata, ccdcameraname, scopedata):
		corstate = corimagedata['camstate']
		channel = corimagedata['channel']
		if isinstance(corimagedata, leginondata.DarkImageData):
			dark = corimagedata['image']
			bright = self.corclient.retrieveRef(corstate, 'bright', ccdcameraname, scopedata, channel)
			if bright is None:
				self.logger.warning('No bright reference image for normalization calculations')
				return
		if isinstance(corimagedata, leginondata.BrightImageData):
			bright = corimagedata['image']
			dark = self.corclient.retrieveRef(corstate, 'dark', ccdcameraname, scopedata, channel)
			if dark is None:
				self.logger.warning('No dark reference image for normalization calculations')
				return

		norm = bright - dark
		norm = numpy.asarray(norm, numpy.float32)

		## there may be a better normavg than this
		normavg = arraystats.mean(norm)

		# division may result infinity or zero division
		# so make sure there are no zeros in norm
		norm = numpy.clip(norm, 0.001, sys.maxint)
		norm = normavg / norm
		self.corclient.storeRef('norm', norm, corstate, scopedata, channel)

	def acquireCorrectedImageData(self, ccdcameraname=None):
		self.setTargets([], 'Bad_Region', block=False)
		self.startTimer('acquireCorrectedImageData')
		self.setStatus('processing')
		if self.instrument.getTEMName() != 'CM':
			self.logger.info('preload dark/norm')
			cameradata = self.instrument.getData(leginondata.CameraEMData, ccdcameraname=ccdcameraname, image=False)
			scopedata = self.instrument.getData(leginondata.ScopeEMData)
			ccdcamera = cameradata['ccdcamera']
			corstate = leginondata.CorrectorCamstateData()
			corstate['dimension'] = cameradata['dimension']
			corstate['offset'] = cameradata['offset']
			corstate['binning'] = cameradata['binning']
			self.corclient.retrieveRef(corstate, 'dark', ccdcameraname, scopedata, self.corclient.channel)
			self.corclient.retrieveRef(corstate, 'norm', ccdcameraname, scopedata, self.corclient.channel)
			self.logger.info('done preload dark/norm')

		errstr = 'Acquisition of corrected image failed: %s'
		tries = 10
		sucess = False
		for i in range(tries):
			try:
				self.startTimer('instument.getData')
				imagedata = self.instrument.getData(leginondata.CameraImageData, ccdcameraname=ccdcameraname)
				self.stopTimer('instument.getData')
				success = True
				break
			except Exception, e:
				raise
				self.logger.warning(errstr % 'unable to access instrument')
				if i == tries-1:
					self.setStatus('idle')
					return None
				else:
					self.logger.warning('Retrying...')

		numimage = imagedata['image']
		camdata = imagedata['camera']
		scopedata = imagedata['scope']
		ccdcamera = camdata['ccdcamera']
		corstate = leginondata.CorrectorCamstateData()
		corstate['dimension'] = camdata['dimension']
		corstate['offset'] = camdata['offset']
		corstate['binning'] = camdata['binning']
		self.startTimer('correct')
		despike = self.settings['despike']
		clipmin = self.settings['clip min']
		clipmax = self.settings['clip max']
		dsize = self.settings['despike size']
		dthresh = self.settings['despike threshold']
		corrected = self.corclient.correct(ccdcamera, numimage, corstate, scopedata, despike=despike, despikesize=dsize, despikethresh=dthresh, clip=(clipmin,clipmax))
		self.stopTimer('correct')
		newdata = leginondata.CorrectedCameraImageData(initializer=imagedata,
																						image=corrected)
		newdata['correction channel'] = self.corclient.channel
		self.setStatus('idle')
		self.stopTimer('acquireCorrectedImageData')
		
		self.maskimg = numpy.zeros(numimage.shape)
		return newdata

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
		plan = self.getPlan()
		badpixelcount = len(plan['pixels'])
		newbadpixels = plan['pixels']
		while  len(newbadpixels) <= badpixelcount+2 :
			extrema = nd.extrema(imageshown)
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
				newextrema=nd.extrema(imageshown)
		plan['pixels'] = newbadpixels
		self.displayImage(imageshown)
		self.storePlan(plan)
		self.panel.setPlan(plan)

	def onAddRegion(self):
		vertices = []
		vertices = self.panel.imagepanel.getTargetPositions('Bad_Region')
		if len(vertices) < 3:
			self.logger.error('Need at least 3 vertices to define the region')
			return
		badpixels = polygon.indicesInsidePolygon(self.maskimg.shape,vertices)
		plan = self.getPlan()
		oldbadpixels = plan['pixels']
		fullbadpixelset = set()
		fullbadpixelset = fullbadpixelset.union(oldbadpixels)
		fullbadpixelset = fullbadpixelset.union(badpixels)
		plan['pixels'] = list(fullbadpixelset)
		self.storePlan(plan)
		self.panel.setPlan(plan)
		self.setTargets([], 'Bad_Region', block=False)
		
