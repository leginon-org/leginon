#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from leginon import leginondata
import numpy
import scipy.ndimage
from pyami import arraystats, imagefun
import time
import cameraclient
import itertools
import leginon.session
import leginon.leginonconfig
import os
import sys
import numextension

ref_cache = {}
idcounter = itertools.cycle(range(100))

class CorrectorClient(cameraclient.CameraClient):
	def __init__(self):
		cameraclient.CameraClient.__init__(self)
		self.max_badpixels = 800

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
		for key in ('ccdcamera','dimension','binning','offset','gain index'):
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

	def getBrightImageFromNorm(self,normdata):
		'''
		Get bright image used to produce the norm image
		This is made to be back compatible to early leginondata that
		has no bright image association but would be the closest in time before
		the norm was calculated
		'''
		if normdata is None:
			return None
		# newer leginon data will have bright image associated with norm image
		if 'bright' in normdata.keys() and normdata['bright'] is not None:
			return normdata['bright']
		# bright image may have the same CameraEMData
		q = leginondata.BrightImageData(camera=normdata['camera'])
		brightresults = q.query(results=1)
		if brightresults:
			return brightresults[0]
		# otherwise need to look up timestamp
		timestamp = normdata.timestamp
		normcam = normdata['camera']
		qcam = leginondata.CameraEMData(dimension=normcam['dimension'],
				offset=normcam['offset'], binning=normcam['binning'],
				ccdcamera=normcam['ccdcamera'])
		qcam['exposure type'] = 'normal'
		qcam['energy filtered'] = normcam['energy filtered']
		qcam['gain index'] = normcam['gain index']

		normscope = normdata['scope']
		qscope = leginondata.ScopeEMData(tem=normscope['tem'])
		qscope['high tension'] = normscope['high tension']
		q = leginondata.BrightImageData(camera=qcam,scope=qscope,channel=normdata['channel'])
		brightlist = q.query()
		for brightdata in brightlist:
			if brightdata.timestamp < timestamp:
				break
		return brightdata

	def createRefQuery(self,reftype,qcam,qscope,channel):
		if reftype == 'norm':
			q = leginondata.NormImageData(camera=qcam,scope=qscope,channel=channel)
		elif reftype == 'bright':
			q = leginondata.BrightImageData(camera=qcam,scope=qscope,channel=channel)
		elif reftype == 'dark':
			q = leginondata.DarkImageData(camera=qcam,scope=qscope,channel=channel)
		return q

	def getAlternativeChannelReference(self,reftype,refdata):
		if refdata is None:
			return None
		altnormdata = self.getAlternativeChannelNorm(refdata)
		if reftype == 'norm':
			return altnormdata
		elif reftype == 'bright':
			return altnormdata['bright']
		elif reftype == 'dark':
			return altnormdata['dark']
		return q
		
	def getAlternativeChannelNorm(self,refdata):
		'''
		Get norm image data of the other channel closest in time
		'''
		if refdata is None:
			return None
		reftype = 'norm'
		timestamp = refdata.timestamp
		refcam = refdata['camera']
		qcam = leginondata.CameraEMData(dimension=refcam['dimension'],
				offset=refcam['offset'], binning=refcam['binning'],
				ccdcamera=refcam['ccdcamera'])
		qcam['exposure time'] = refcam['exposure time']
		qcam['energy filtered'] = refcam['energy filtered']
		qcam['gain index'] = refcam['gain index']

		refscope = refdata['scope']
		qscope = leginondata.ScopeEMData(tem=refscope['tem'])
		qscope['high tension'] = refscope['high tension']
		altchannel = int(refdata['channel'] == 0)
		q = self.createRefQuery(reftype,qcam,qscope,altchannel)
		reflist = q.query()
		if len(reflist) == 0:
			# Not to query exposure time if none found
			qcam['exposure time'] = None
			q = self.createRefQuery(reftype,qcam,qscope,altchannel)
			reflist = q.query()
		if len(reflist) == 0:
			#no switching, no alternative channel found
			return refdata
		for newrefdata in reflist:
			if newrefdata.timestamp < timestamp:
				break
		before_ref = newrefdata
		reflist.reverse()
		for newrefdata in reflist:
			if newrefdata.timestamp > timestamp:
				break
		after_ref = newrefdata
		if after_ref.timestamp - timestamp > timestamp - before_ref.timestamp:
			return before_ref
		else:
			return after_ref

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
		s = '%s, %sV, size %sx%s, bin %sx%s, offset (%s,%s), channel %s, gain %s'
		try:
			return s % (exptype, key[8], key[0], key[1], key[2], key[3], key[4], key[5], key[9], key[10])
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
		mylist.append(cameradata['gain index'])
		return tuple(mylist)

	def getCorrectorImageFromCache(self, type, scopedata, cameradata, channel):
		key = self.makeCorrectorKey(type, scopedata, cameradata, channel)
		cachedim = ref_cache[key]
		return cachedim

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
			return ref
		else:
			return None

	def prepareDark(self, dark, raw):
		'''
		For cameras that return a sum of n frames:
		Rescale the dark image to be same number of frames as raw image.
		Assuming exposure time of each frame (or frame time) is constant.
		'''
		darkarray = dark['image']
		try:
			## NEED TO FIX
			dark_exptime = len(dark['use frames']) * float(dark['camera']['frame time'])
		except:
			return darkarray
		try:
			raw_exptime = len(raw['use frames']) * float(raw['camera']['frame time'])
		except:
			return darkarray
		if	dark_exptime == 0.0:
			return darkarray
		multiplier = float(raw_exptime) / float(dark_exptime)
		if multiplier != 1.0:
			darkarray = multiplier * darkarray
		return darkarray

	def calculateDarkScale(self,rawarray,darkarray):
		'''
		Calculate the scale used for darkarray using
		Gram-Schmidt process for very low signal-to-noise
		ratio such as DD raw frames as suggested by Niko Grigoreiff.
		Need to apply the same factor used in data dark subtraction as
		in dark subtraction for the normarray
		'''
		onedshape = rawarray.shape[0] * rawarray.shape[1]
		a = rawarray.reshape(onedshape)
		b = darkarray.reshape(onedshape)
		a_std = numextension.allstats(a,std=True)['std']
		b_std = numextension.allstats(b,std=True)['std']
		if b_std == 0:
			return 1.0
		ab_corr_coef = numpy.corrcoef(a,b)[(0,1)]
		dark_scale = ab_corr_coef * a_std / b_std
		return dark_scale

	def calculateNorm(self,brightarray,darkarray,scale=None):
		'''
		caculating norm array from bright and dark array.  A scale
		for the dark array can be specified or calculated.  For most
		case, scale of 1 is good enough if the exposure time of the
		bright and dark are equal.  If Gram-Schmidt process is used
		to calculate dark_scale on the data, normarray need to be
		scaled the same by specifying it.
		'''
		if scale:
				dark_scale = scale
		else:
			dark_scale = 1.0
		normarray = brightarray - dark_scale * darkarray
		normarray = numpy.asarray(normarray, numpy.float32)

		# division may result infinity or zero division
		# so make sure there are no zeros in norm
		normarray = numpy.clip(normarray, 0.001, sys.maxint)
		stats = numextension.allstats(normarray, mean=True)
		normavg = stats['mean']
		normarray = normavg / normarray
		# Avoid over correcting dead pixels
		normarray = numpy.ma.masked_greater(normarray,20).filled(1)
		return normarray

	def normalizeImageArray(self, rawarray, darkarray, normarray, is_counting=False):
		diff = rawarray - darkarray
		r = diff * normarray
		## remove nan and inf
		r = numpy.where(numpy.isfinite(r), r, 0)
		return r

	def normalizeCameraImageData(self, imagedata, channel):
		cameradata = imagedata['camera']
		scopedata = imagedata['scope']
		dark = self.retrieveCorrectorImageData('dark', scopedata, cameradata, channel)
		norm = self.retrieveCorrectorImageData('norm', scopedata, cameradata, channel)
		if dark is None or norm is None:
			self.logger.warning('Cannot find references, image will not be normalized')
			return
		rawarray = imagedata['image']
		darkarray = self.prepareDark(dark, imagedata)
		normarray = norm['image']
		r = self.normalizeImageArray(rawarray,darkarray,normarray, 'GatanK2' in cameradata['ccdcamera']['name'])
		imagedata['image'] = r	
		imagedata['dark'] = dark
		imagedata['bright'] = norm['bright']
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
		imagedata['bright'] = None
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
		if imagedata['image'] is None:
			return
		if not 'system corrected' in imagedata['camera'].keys() or not imagedata['camera']['system corrected']:
			try:
				self.normalizeCameraImageData(imagedata, channel)
				imagedata['correction channel'] = channel
			except Exception, e:
				self.logger.error('Normalize failed: %s' % e)
				self.logger.warning('Image will not be normalized')

		cameradata = imagedata['camera']
		plan, plandata = self.retrieveCorrectorPlan(cameradata)
		# save corrector plan for easy post-processing of raw frames
		imagedata['corrector plan'] = plandata
		if plan is not None:
			self.fixBadPixels(imagedata['image'], plan)

		pixelmax = imagedata['camera']['ccdcamera']['pixelmax']
		imagedata['image'] = numpy.asarray(imagedata['image'], numpy.float32)
		if pixelmax is not None:
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
	def reseachCorrectorPlan(self, cameradata):
		qcamera = leginondata.CameraEMData()
		# Fix Me: Ignore gain index for now because camera setting does not have it when theplan is saved.
		for key in ('ccdcamera','dimension','binning','offset'):
			qcamera[key] = cameradata[key]
		qplan = leginondata.CorrectorPlanData()
		qplan['camera'] = qcamera
		plandatalist = qplan.query()

		if plandatalist:
			return plandatalist[0]
		else:
			return None

	def retrieveCorrectorPlan(self, cameradata):
		plandata = self.reseachCorrectorPlan(cameradata)
		return self.formatCorrectorPlan(plandata), plandata

	def formatCorrectorPlan(self, plandata=None):
		if plandata:
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
		if len(badpixels) >= self.max_badpixels:
			self.logger.error('Too many (%d) bad pixels will slow down image acquisition' % len(badpixels))
			self.logger.warning('Clear bad pixel plan in Corrector to speed up')
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

	def createReferenceSession(self):
		session_name = None
		for suffix in 'abcdefghijklmnopqrstuvwxyz':
			maybe_name = time.strftime('%y%b%d_ref_'+suffix).lower()
			try:
				leginon.session.makeReservation(maybe_name)
			except leginon.session.ReservationFailed:
				continue
			else:
				session_name = maybe_name
				break
		if session_name is None:
			raise RuntimeError('no reference session name determined')

		directory = leginon.leginonconfig.mapPath(leginon.leginonconfig.IMAGE_PATH)
		imagedirectory = os.path.join(leginon.leginonconfig.unmapPath(directory), session_name, 'rawdata').replace('\\', '/')

		initializer = {
			'name': session_name,
			'comment': 'reference images',
			'user': self.session['user'],
			'image path': imagedirectory,
			'hidden' : True,
		}
		session = leginondata.SessionData(initializer=initializer)
		session.insert()
		refsession = leginondata.ReferenceSessionData(session=session)
		refsession.insert()
		return session

	def getReferenceSession(self):
		qrefses = leginondata.ReferenceSessionData()
		refsessions = qrefses.query(timelimit='-90 0:0:0')

		# find one that is writable
		refsession = None
		for r in refsessions:
			# some modified database may have emptied the old session
			if not r['session']:
				continue
			impath = r['session']['image path']
			if os.access(impath, os.W_OK):
				refsession = r
				break

		# if none are writable, create my own
		if refsession is None:
			session = self.createReferenceSession()
		else:
			session = refsession['session']
		return session

	def storeCorrectorImageData(self, imagedata, type, channel):

		# check for bad shape
		imarray = imagedata['image']
		shape = imarray.shape
		cameradata = imagedata['camera']
		dim = cameradata['dimension']
		if dim['x'] != shape[1] or dim['y'] != shape[0]:
			raise RuntimeError('%s: bad array shape: %s' % (type, shape,))

		if type == 'dark':
			refclass = leginondata.DarkImageData
		elif type == 'bright':
			refclass = leginondata.BrightImageData
		elif type == 'norm':
			refclass = leginondata.NormImageData
		refdata = refclass(initializer=imagedata)

		refdata['filename'] = self.makeCorrectorImageFilename(type, channel, imarray.shape)

		## replace session of scope, camera, refdata with ref session
		refsession = self.getReferenceSession()
		scopedata = refdata['scope']
		cameradata = refdata['camera']
		newscope = leginondata.ScopeEMData(initializer=scopedata)
		newscope['session'] = refsession
		newcamera = leginondata.CameraEMData(initializer=cameradata)
		newcamera['session'] = refsession
		refdata['session'] = refsession
		refdata['scope'] = newscope
		refdata['camera'] = newcamera
		refdata['channel'] = channel

		self.logger.info('Saving new %s' % (type,))
		refdata.insert(force=True)
		self.logger.info('Saved: %s' % (refdata['filename'],))

		## store in cache
		key = self.makeCorrectorKey(type, scopedata, cameradata, channel)
		ref_cache[key] = refdata

		return refdata

	def getCameraSettings(self):
		return self.settings['camera settings']


	def getCameraSettings(self):
		return self.settings['camera settings']

	def storeCorrectorPlan(self, plan):
		# import instrument here so that wx is not required unless Leginon is running
		import instrument
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

