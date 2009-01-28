#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import copy
import leginondata
import event
import node
import numpy
ma = numpy.ma
import threading
import gui.wx.Corrector
import remotecall
import instrument
import sys
from pyami import arraystats, imagefun, ccd
import polygon

class ImageCorrection(remotecall.Object):
	def __init__(self, node):
		self.node = node
		remotecall.Object.__init__(self)

	def getImageData(self, ccdcameraname=None):
		return self.node.acquireCorrectedImageData(ccdcameraname=ccdcameraname)

	def setChannel(self, channel):
		self.node.setChannel(channel)

class CorrectorClient(object):
	def __init__(self, node):
		self.node = node
		self.channel = 0
		self.cache = {}
		self.ccdcorrector = ccd.Corrector()

	def queryCorrectionImage(self, scopedata, camdata, type, channel):


		# only query based on instrument and high tension
		scope = leginondata.ScopeEMData()
		scope['tem'] = scopedata['tem']
		scope['high tension'] = scopedata['high tension']

		# only query based on instrument, dimension, binning, offset
		camera = leginondata.CameraEMData()
		camera['ccdcamera'] = camdata['ccdcamera']
		camera['dimension'] = camdata['dimenion']
		camera['binning'] = camdata['binning']
		camera['offset'] = camdata['offset']

		## first try requested channel, then try any channel
		corimg = None
		for channel in (channel, None):
			## try cache
			try:
				key = self.getkey(scopedata, camdata, type, channel)
				return self.cache[key]
			except KeyError:
				pass
			self.node.logger.info('Loading %s...' % self.formatKey(key))
			qimage = leginondata.CorrectionImageData(scope=scope, camera=camera, type=type, channel=channel)
			try:
				corimg = qimage.query(results=1)
				corimg = corimg[0]
				break
			except:
				pass

				self.node.logger.warning('requested correction channel %s not available, using channel: %s' % (channel, corimg['channel']))
			else:
				self.node.logger.error('No correction image in database')
				corimg = None

		if corimg is not None:
			self.node.logger.info('Correction image loaded: %s' % (corimg['filename'],))
			## make it float to do float math later
			image = numpy.asarray(corimg['image'], numpy.float32)
			key = self.getkey(corimg['scope'], corimg['camera'], corimg['type'], corimg['channel'])
			self.cache[key] = image
		else:
			image = None
		return image

	def formatKey(self, key):
		s = '%s, %dV, size %dx%d, bin %dx%d, offset (%d,%d), channel %d'
		return s % (key[6], key[8], key[0], key[1], key[2], key[3], key[4], key[5], key[9])

	def getkey(self, scope, camera, type, channel):
		mylist = []
		for param in ('dimension', 'binning', 'offset'):
			values = camera[param]
			if values is None:
				valuetuple = (None,None)
			else:
				valuetuple = (values['x'],values['y'])
			mylist.extend( valuetuple )
		mylist.append(type)
		mylist.append(camera['ccdcamera'])
		mylist.append(scope['high tension'])
		mylist.append(channel)
		return tuple(mylist)

	def normalize(self, imagedata):
		channel = self.channel
		
		scopedata = imagedata['scope']
		camdata = imagedata['camera']
		raw = imagedata['image']
		exposuretime = camdata['exposure time']
		bias = self.queryCorrectionImage(scopedata, camdata, 'bias', channel)
		dark = self.queryCorrectionImage(scopedata, camdata, 'dark', channel)
		flat = self.queryCorrectionImage(scopedata, camdata, 'flat', channel)
		if dark is not None and flat is not None and bias is not None:
			## load images into ccd corrector
			self.ccdcorrector.setBias(bias)
			self.ccdcorrector.setDark(dark)
			self.ccdcorrector.setFlat(flat)
			corrected = self.ccdcorrector.correctBiasDarkFlat(raw, exposuretime)
			return corrected
		else:
			self.node.logger.warning('Cannot find references, image will not be normalized')
			return raw

	def correct(self, imagedata, despike=False, despikesize=None, despikethresh=None, clip=None):
		'''
		this puts an image through a pipeline of corrections
		'''
		
		normalized = self.normalize(imagedata)
		plan = self.retrievePlan(imagedata)
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

	def retrievePlan(self, camdata):
		qcam = leginondata.CameraEMData()
		qcam['ccdcamera'] = camdata['ccdcamera']
		qcam['dimension'] = camdata['dimension']
		qcam['offset'] = camdata['offset']
		qcam['binning'] = camdata['binning']
		qplan = leginondata.CorrectionPlanData(camera=qcam)
		plandatalist = qplan.query(results=1)
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
		self.cache[key] = numdata

		## store in database
		if type == 'dark':
			imagetemp = leginondata.DarkImageData()
		elif type == 'bright':
			imagetemp = leginondata.BrightImageData()
		elif type == 'flat':
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

		newcam = leginondata.CameraEMData(ccdcamera=ccdcamera)
		if self.settings['camera settings'] is None:
			plan = None
		else:
			for i in ['dimension', 'offset', 'binning']:
				newcam[i] = dict(self.settings['camera settings'][i])
			plan = self.corclient.retrievePlan(newcam)
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

	def modifyNorm(self):
		self.startTimer('modifyNorm')
		try:
			camdata = self.settings['camera settings']
			scopedata = self.instrument.getData(leginondata.ScopeEMData)
			newcamdata = leginondata.CameraEMData()
			newcamdata['ccdcamera'] = self.instrument.getCCDCamera()
			for key in ('dimension','offset','binning'):
				newcamdata[key] = camdata[key]
			self.modifyByMask(self.maskimg, newcamdata, scopedata)
		except Exception, e:
			self.logger.exception('Modify normalization image failed: %s' % e)
		self.stopTimer('modifyNorm')
		self.maskimg = numpy.zeros(self.maskimg.shape)
		self.displayImage(self.currentimage)

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
			return None

		try:
			series = self.acquireSeries(self.settings['n average'])
		except Exception, e:
			self.logger.error('Reference acquisition failed: %s' % e)
			return None

		combine = self.settings['combine']
		self.logger.info('taking %s of image series' % (combine,))
		if combine == 'average':
			ref = imagefun.averageSeries(series)
		elif combine == 'median':
			ref = imagefun.medianSeries(series)
		else:
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
		self.corclient.storeRef('flat', norm, corstate, scopedata, channel)

	def acquireCorrectedImageData(self, ccdcameraname=None):
		self.setTargets([], 'Regions', block=False)
		self.startTimer('acquireCorrectedImageData')
		self.setStatus('processing')
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
		exptime = corstate['exposure time'] / 1000.0
		self.startTimer('correct')
		despike = self.settings['despike']
		clipmin = self.settings['clip min']
		clipmax = self.settings['clip max']
		dsize = self.settings['despike size']
		dthresh = self.settings['despike threshold']
		corrected = self.corclient.correct(ccdcamera, numimage, corstate, scopedata, despike=despike, despikesize=dsize, despikethresh=dthresh, clip=(clipmin,clipmax), exposuretime=exptime)
		self.stopTimer('correct')
		newdata = leginondata.CorrectedCameraImageData(initializer=imagedata,
																						image=corrected)
		newdata['correction channel'] = self.corclient.channel
		self.setStatus('idle')
		self.stopTimer('acquireCorrectedImageData')
		
		self.maskimg = numpy.zeros(numimage.shape)
		return newdata

	def modifyByMask(self,mask, ccdcameraname, camstate, scopedata):
		for channel in range(0,self.settings['channels']):
			## use reference image from database
			flat = self.corclient.queryCorrectionImage(scopedata, camdata, 'flat', channel)
			if flat:
				## make it float to do float math later
				flat = numpy.asarray(flat['image'], numpy.float32)
			else:
				self.logger.warning('No flat image for modifications')
				return

			if mask is not None:
				if flat.shape != mask.shape:
					self.logger.warning('Wrong mask dimension for channel %d' %channel)
					return
				else:
					maskedflat=ma.masked_array(flat,mask=mask)
					nmean = maskedflat.mean()
					nstd = maskedflat.std()
					nmax = maskedflat.max()
					nmin = maskedflat.min()
					sigma = 100
					ntop = nmean+sigma * nstd
					if nmax < ntop:
						ntop = nmax
			else:
				nmax = flat.max()
				nmin = flat.min()
				ntop = nmax
				nbottom = nmin
			self.logger.info('Unmasked region normalization is between %e and %e'% (nmax,nmin))	
			## make it 20 if the unmask region has large norm factor
			if ntop > 20:
				ntop = 20
			nbottom = 1 / ntop
			newflat = numpy.clip(flat, nbottom, ntop) 
			self.logger.info('Clipped normalization to between %e and %e'% (ntop,nbottom))	
			try:
				self.corclient.storeRef('flat', newflat, camstate, scopedata, channel)
				self.logger.info('Saved modified flat image for channel %d' %channel)
			except:
				pass
		return

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


	def onAdd(self):
		vertices = []
		dir(self)
		vertices = self.panel.imagepanel.getTargetPositions('Regions')
		def reversexy(coord):
			clist=list(coord)
			clist.reverse()
			return tuple(clist)
		vertices = map(reversexy,vertices)
		polygonimg = polygon.filledPolygon(self.maskimg.shape,vertices)
		type(polygonimg)
		self.maskimg = self.maskimg + polygonimg
		self.maskimg = numpy.where(self.maskimg==0,0,1)
		imageshown = self.currentimage * (numpy.ones(self.maskimg.shape)+self.maskimg*0.5)
		self.displayImage(imageshown)
		self.setTargets([], 'Regions', block=False)
