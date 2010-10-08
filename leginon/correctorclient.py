#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginondata
import numpy
import scipy.ndimage
import instrument
from pyami import arraystats, imagefun
import time
import cameraclient
import itertools

ref_cache = {}
ref_cache_id = {}
idcounter = itertools.cycle(range(100))

class CorrectorClient(cameraclient.CameraClient):
	def __init__(self):
		cameraclient.CameraClient.__init__(self)

	def acquireCorrectedCameraImageData(self, channel=0, **kwargs):
		imagedata = self.acquireCameraImageData(**kwargs)
		self.correctCameraImageData(imagedata, channel)
		return imagedata

	def researchCorrectorImageData(self, type, scopedata, cameradata, channel):
		if type == 'dark':
			imagetemp = leginondata.DarkImageData()
		elif type == 'bright':
			imagetemp = leginondata.BrightImageData()
		elif type == 'norm':
			imagetemp = leginondata.NormImageData()
		else:
			return None

		## query only based on certain camera parameters, not all
		imagetemp['camera'] = leginondata.CameraEMData()
		for key in ('ccdcamera','dimension','binning','offset'):
			imagetemp['camera'][key] = cameradata[key]
		# query only based on certain scope parameters, not all
		imagetemp['scope'] = leginondata.ScopeEMData()
		for key in ('tem', 'high tension'):
			imagetemp['scope'][key] = scopedata[key]
		imagetemp['channel'] = channel
		try:
			ref = imagetemp.query(results=1)
		except Exception, e:
			self.logger.warning('Reference image query failed: %s' % e)
			ref = None

		if ref:
			ref = ref[0]
		else:
			return None

		if ref['image'] is None:
			return None

		shape = ref['image'].shape
		dim = ref['camera']['dimension']
		if dim['x'] != shape[1] or dim['y'] != shape[0]:
			self.logger.error('%s: bad shape: %s' % (ref['filename'], shape,))
			return None
		return ref

	def formatCorrectorKey(self, key):
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
		s = '%s, %sV, size %sx%s, bin %sx%s, offset (%s,%s), channel %s'
		try:
			return s % (exptype, key[8], key[0], key[1], key[2], key[3], key[4], key[5], key[9])
		except IndexError:
			return str(key)

	def makeCorrectorKey(self, type, scopedata, cameradata, channel):
		mylist = []
		for param in ('dimension', 'binning', 'offset'):
			values = cameradata[param]
			if values is None:
				valuetuple = (None,None)
			else:
				valuetuple = (values['x'],values['y'])
			mylist.extend( valuetuple )
		mylist.append(type)
		mylist.append(cameradata['ccdcamera']['name'])
		mylist.append(scopedata['high tension'])
		mylist.append(channel)
		return tuple(mylist)

	def getCorrectorImageFromCache(self, type, scopedata, cameradata, channel):
		key = self.makeCorrectorKey(type, scopedata, cameradata, channel)
		cachedim = ref_cache[key]
		return cachedim

		### do not need this since all nodes share same cache, but
		### need this again if node on another launcher need correction images
		#newref = self.researchCorrectorImageData(type, scopedata, cameradata, channel)
		#if newref.dbid != ref_cache_id[key]:
		#	ref_cache[key] = newref
		#	ref_cache_id[key] = newref.dbid
		#	return newref
		#else:
		#	return cachedim

	def correctorImageExists(self, type, scopedata, cameradata, channel):
		ref = self.researchCorrectorImageData(type, scopedata, cameradata, channel)
		if not ref:
			return False
		fileref = ref.special_getitem('image', dereference=False)
		if isinstance(fileref, numpy.ndarray):
			return True
		return fileref.exists()

	def retrieveCorrectorImageData(self, type, scopedata, cameradata, channel):
		key = self.makeCorrectorKey(type, scopedata, cameradata, channel)
		## another way to do the cache would be to use the local
		##   data keeper

		## try to use reference image from cache
		try:
			return self.getCorrectorImageFromCache(type, scopedata, cameradata, channel)
		except KeyError:
			self.logger.info('Loading %s...' % self.formatCorrectorKey(key))
		## use reference image from database
		ref = self.researchCorrectorImageData(type, scopedata, cameradata, channel)
		if ref:
			## make it float to do float math later
			## image = numpy.asarray(ref['image'], numpy.float32)
			ref_cache[key] = ref
			ref_cache_id[key] = ref.dbid
			return ref
		else:
			return None

	def normalizeCameraImageData(self, imagedata, channel):
		cameradata = imagedata['camera']
		scopedata = imagedata['scope']
		dark = self.retrieveCorrectorImageData('dark', scopedata, cameradata, channel)
		norm = self.retrieveCorrectorImageData('norm', scopedata, cameradata, channel)
		if dark is None or norm is None:
			self.logger.warning('Cannot find references, image will not be normalized')
			return
		rawarray = imagedata['image']
		darkarray = dark['image']
		normarray = norm['image']
		diff = rawarray - darkarray
		r = diff * normarray
		## remove nan and inf
		r = numpy.where(numpy.isfinite(r), r, 0)
		imagedata['image'] = r	
		imagedata['dark'] = dark
		imagedata['norm'] = norm
		imagedata['correction channel'] = channel

	def denormalizeCameraImageData(self, imagedata):
		'''
		reverse the normalization to create a raw image
		'''
		dark = imagedata['dark']
		norm = imagedata['norm']
		if dark is None or norm is None:
			raise RuntimeError('uncorrected cannot be denormalized')
		corrected = imagedata['image']
		normarray = norm['image']
		darkarray = dark['image']
		raw = corrected / normarray
		raw = numpy.where(numpy.isfinite(raw), raw, 0)
		raw = raw + darkarray
		imagedata['image'] = raw
		imagedata['dark'] = None
		imagedata['norm'] = None
		imagedata['correction channel'] = None

	def reverseCorrectorChannel(self, imagedata):
		oldchannel = imagedata['correction channel']
		if oldchannel == 1:
			newchannel = 0
		elif oldchannel == 0:
			newchannel = 1
		else:
			raise RuntimeError('cannot reverse unknown channel')
		newimagedata = imagedata.copy()
		self.denormalizeCameraImageData(newimagedata)
		self.normalizeCameraImageData(newimagedata, newchannel)
		return newimagedata

	def correctCameraImageData(self, imagedata, channel):
		'''
		this puts an image through a pipeline of corrections
		'''
		try:
			self.normalizeCameraImageData(imagedata, channel)
			imagedata['correction channel'] = channel
		except Exception, e:
			self.logger.error('Normalize failed: %s' % e)
			self.logger.warning('Image will not be normalized')

		cameradata = imagedata['camera']
		plan = self.retrieveCorrectorPlan(cameradata)
		if plan is not None:
			self.fixBadPixels(imagedata['image'], plan)

		pixelmax = imagedata['camera']['ccdcamera']['pixelmax']
		if pixelmax is None:
			pixelmax = 2**16
		imagedata['image'] = numpy.asarray(imagedata['image'], numpy.float32)
		imagedata['image'] = numpy.clip(imagedata['image'], 0, pixelmax)

		if plan is not None and plan['despike']:
			self.logger.debug('Despiking...')
			nsize = plan['despike size']
			thresh = plan['despike threshold']
			imagefun.despike(imagedata['image'], nsize, thresh)
			self.logger.debug('Despiked')
		'''
		final = numpy.asarray(clipped, numpy.float32)
		return final
		'''
	def retrieveCorrectorPlan(self, cameradata):
		qcamera = leginondata.CameraEMData()
		for key in ('ccdcamera','dimension','binning','offset'):
			qcamera[key] = cameradata[key]
		qplan = leginondata.CorrectorPlanData()
		qplan['camera'] = qcamera
		plandatalist = qplan.query()

		if plandatalist:
			plandata = plandatalist[0]
			result = {}
			result['rows'] = list(plandata['bad_rows'])
			result['columns'] = list(plandata['bad_cols'])
			result['despike'] = plandata['despike']
			result['despike size'] = plandata['despike size']
			result['despike threshold'] = plandata['despike threshold']
			if plandata['bad_pixels'] is None:
				result['pixels'] = []
			else:
				result['pixels'] = list(plandata['bad_pixels'])
			return result
		else:
			return {'rows': [], 'columns': [], 'pixels': [], 'despike': False, 'despike size': 11, 'despike threshold': 3.5}

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

	def storeCorrectorImageData(self, imarray, type, scopedata, cameradata, channel):
		# check for bad shape
		shape = imarray.shape
		dim = cameradata['dimension']
		if dim['x'] != shape[1] or dim['y'] != shape[0]:
			raise RuntimeError('%s: bad array shape: %s' % (type, shape,))

		## store in database
		if type == 'dark':
			refdata = leginondata.DarkImageData()
		elif type == 'bright':
			refdata = leginondata.BrightImageData()
		elif type == 'norm':
			refdata = leginondata.NormImageData()
		refdata['image'] = imarray
		refdata['filename'] = self.makeCorrectorImageFilename(type, channel, imarray.shape)
		refdata['session'] = self.session
		refdata['scope'] = scopedata
		refdata['camera'] = cameradata
		refdata['channel'] = channel
		self.logger.info('Saving new %s' % (type,))
		refdata.insert(force=True)
		self.logger.info('Saved: %s' % (refdata['filename'],))

		## store in cache
		key = self.makeCorrectorKey(type, scopedata, cameradata, channel)
		ref_cache[key] = refdata
		ref_cache_id[key] = refdata.dbid

		return refdata

	def getCameraSettings(self):
		return self.settings['camera settings']

	def storeCorrectorPlan(self, plan):
		camsettings = self.settings['camera settings']
		ccdname = self.settings['instruments']['ccdcamera']
		ccdcamera = self.instrument.getCCDCameraData(ccdname)
		cameradata = leginondata.CameraEMData()
		cameradata.update(self.settings['camera settings'])
		cameradata['ccdcamera'] = ccdcamera
		plandata = leginondata.CorrectorPlanData()
		plandata['session'] = self.session
		plandata['camera'] = cameradata
		plandata['bad_rows'] = plan['rows']
		plandata['bad_cols'] = plan['columns']
		plandata['bad_pixels'] = plan['pixels']
		plandata['despike'] = plan['despike']
		plandata['despike size'] = plan['despike size']
		plandata['despike threshold'] = plan['despike threshold']
		plandata.insert(force=True)

	def makeCorrectorImageFilename(self, type, channel, shape):
		sessionname = self.session['name']
		timestamp = time.strftime('%d%H%M%S', time.localtime())
		nextid = idcounter.next()
		shapestr = '%sx%s' % shape
		f = '%s_%s_%02d_%s_%s_%s' % (sessionname, timestamp, nextid, shapestr, type, channel)
		return f

