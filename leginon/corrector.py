#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import node
import Numeric
import imagefun
import event
import cPickle
import string
import threading
import Mrc
import camerafuncs
import dbdatakeeper
import os
import copy
import uidata

False = 0
True = 1

class DataHandler(node.DataHandler):
	def query(self, id):
		self.lock.acquire()
		if id == ('corrected image data',):
			result = self.node.acquireCorrectedImageData()
			self.lock.release()
			return result
		else:
			self.lock.release()
			return node.DataHandler.query(self, id)

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
	eventoutputs = node.Node.eventoutputs + [event.DarkImagePublishEvent, event.BrightImagePublishEvent, event.ListPublishEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)

		node.Node.__init__(self, id, session, nodelocations, datahandler=DataHandler, **kwargs)

		self.ref_cache = {}

		ids = [('corrected image data',)]
		e = event.ListPublishEvent(id=self.ID(), idlist=ids)
		self.outputEvent(e)

		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.uistatus = uidata.String('Status', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObjects((self.uistatus,))

		darkmethod = uidata.Method('Acquire Dark', self.uiAcquireDark)
		brightmethod = uidata.Method('Acquire Bright', self.uiAcquireBright)
		rawmethod = uidata.Method('Acquire Raw', self.uiAcquireRaw)
		correctedmethod = uidata.Method('Acquire Corrected',
																			self.uiAcquireCorrected)

		self.autobinning = uidata.Integer('Binning', 1, 'rw', persist=True)
		self.autoexptime = uidata.Integer('Exposure Time', 500, 'rw', persist=True)
		self.autotarget = uidata.Integer('Target Mean', 2000, 'rw', persist=True)
		automethod = uidata.Method('Auto References', self.uiAutoAcquireReferences)

		referencescontainer = uidata.Container('References')
		referencescontainer.addObjects((darkmethod, brightmethod))

		autocontainer = uidata.Container('Auto References')
		autocontainer.addObjects((self.autobinning, self.autotarget,
															self.autoexptime, automethod))

		testcontainer = uidata.Container('Test')
		testcontainer.addObjects((rawmethod, correctedmethod))
		controlcontainer = uidata.Container('Control')

		self.despikeon = uidata.Boolean('Despike', True, 'rw', persist=True)
		self.despikevalue = uidata.Float('Despike Threshold', 3.5, 'rw',
																			persist=True)
		self.despikesize = uidata.Integer('Neighborhood Size', 11, 'rw',
																			persist=True)

		controlcontainer.addObjects((self.despikeon, self.despikesize,
																	self.despikevalue, referencescontainer,
																	autocontainer, testcontainer))
		self.display_flag = uidata.Boolean('Display image', True, 'rw',
																				persist=True)

		statscontainer = uidata.Container('Statistics')
		self.statsmean = uidata.Float('Mean', None, 'r')
		self.statsmin = uidata.Float('Min', None, 'r')
		self.statsmax = uidata.Float('Max', None, 'r')
		self.statsstd = uidata.Float('Std. Dev.', None, 'r')
		statscontainer.addObjects((self.statsmean, self.statsmin, self.statsmax,
																self.statsstd))

		self.ui_image = uidata.Image('Image', None, 'rw')

		self.uiframestoaverage = uidata.Integer('Frames to Average', 3, 'rw')
		self.cliplimits = uidata.Sequence('Clip Limits', (), 'rw')
		self.badrows = uidata.Sequence('Bad Rows', (), 'rw')
		self.badcols = uidata.Sequence('Bad Cols', (), 'rw')
		setplan = uidata.Method('Set Plan', self.uiSetPlanParams)
		getplan = uidata.Method('Get Plan', self.uiGetPlanParams)
		camsetup = self.cam.uiSetupContainer()

		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((self.uiframestoaverage,
																	camsetup, self.cliplimits,
																	self.badrows, self.badcols, setplan, getplan))
		container = uidata.LargeContainer('Corrector')
		container.addObjects((statuscontainer, settingscontainer, controlcontainer,
													self.display_flag, statscontainer, self.ui_image))
		self.uiserver.addObject(container)

	def uiSetPlanParams(self):
		camconfig = self.cam.uiGetParams()
		newcamstate = data.CorrectorCamstateData()
		newcamstate['dimension'] = camconfig['dimension']
		newcamstate['offset'] = camconfig['offset']
		newcamstate['binning'] = camconfig['binning']
		plandata = data.CorrectorPlanData()
		plandata['camstate'] = newcamstate
		plandata['clip_limits'] = self.cliplimits.get()
		plandata['bad_rows'] = self.badrows.get()
		plandata['bad_cols'] = self.badcols.get()
		self.storePlan(plandata)

	def uiGetPlanParams(self):
		camconfig = self.cam.uiGetParams()
		newcamstate = data.CorrectorCamstateData()
		newcamstate['dimension'] = camconfig['dimension']
		newcamstate['offset'] = camconfig['offset']
		newcamstate['binning'] = camconfig['binning']
		plandata = self.retrievePlan(newcamstate)
		if plandata is None:
			self.cliplimits.set([])
			self.badrows.set([])
			self.badcols.set([])
		else:
			self.cliplimits.set(plandata['clip_limits'])
			self.badrows.set(plandata['bad_rows'])
			self.badcols.set(plandata['bad_cols'])

	def uiAcquireDark(self):
		try:
			imagedata = self.acquireReference(dark=True)
		except node.PublishError:
			self.outputError('Cannot set EM parameter, EM may not be running')
		else:
			self.displayImage(imagedata)
			node.beep()

	def uiAcquireBright(self):
		try:
			imagedata = self.acquireReference(dark=False)
		except node.PublishError:
			self.outputError('Cannot set EM parameter, EM may not be running')
		else:
			self.displayImage(imagedata)
			node.beep()

	def uiAcquireRaw(self):
		try:
			self.cam.uiApplyAsNeeded()
			imagedata = self.cam.acquireCameraImageData(correction=False)
		except node.PublishError:
			self.outputError('Cannot set EM parameter, EM may not be running')
		else:
			imagearray = imagedata['image']
			self.displayImage(imagearray)

	def uiAcquireCorrected(self):
		try:
			self.cam.uiApplyAsNeeded()
			imagedata = self.acquireCorrectedArray()
		except node.PublishError:
			self.outputError('Cannot set EM parameter, EM may not be running')
		else:
			self.displayImage(imagedata)

	def displayImage(self, imagedata):
		if self.display_flag.get():
			self.ui_image.set(imagedata)
			self.displayStats(imagedata)

	def displayStats(self, imagedata):
		stats = self.stats(imagedata)
		#print 'STATS', stats
		self.statsmean.set(stats['mean'])
		self.statsmin.set(stats['min'])
		self.statsmax.set(stats['max'])
		self.statsstd.set(stats['stdev'])

	def newCamstate(self, camdata):
		camdatacopy = copy.deepcopy(camdata)
		camstate = data.CorrectorCamstateData(id=self.ID())
		camstate['dimension'] = camdatacopy['dimension']
		camstate['offset'] = camdatacopy['offset']
		camstate['binning'] = camdatacopy['binning']
		return camstate

	def retrievePlan(self, corstate):
		corstate['id'] = None
		qplan = data.CorrectorPlanData()
		qplan['camstate'] = corstate
		qplan['session'] = data.SessionData()
		qplan['session']['instrument'] = self.session['instrument']
		plandatalist = self.research(datainstance=qplan)
		if plandatalist:
			return plandatalist[0]
		else:
			return None

	def storePlan(self, plandata):
		self.publish(plandata, database=True)

	def acquireSeries(self, n, camdata):
		series = []
		for i in range(n):
			self.uistatus.set('Acquiring %s of %s' % (i+1, n))
			imagedata = self.cam.acquireCameraImageData(correction=False)
			numimage = imagedata['image']
			camdata = imagedata['camera']
			scopedata = imagedata['scope']
			series.append(numimage)
		return {'image series': series, 'scope': scopedata, 'camera':camdata}

	def acquireReference(self, dark=False):
		camdata = self.cam.getCameraEMData()
		if dark:
			camdata['exposure type'] = 'dark'
			typekey = 'dark'
			self.uistatus.set('Acquiring dark')
		else:
			typekey = 'bright'
			self.uistatus.set('Acquiring bright')
		self.cam.setCameraEMData(camdata)

		navg = self.uiframestoaverage.get()

		seriesinfo = self.acquireSeries(navg, camdata=camdata)
		series = seriesinfo['image series']
		seriescam = seriesinfo['camera']
		seriesscope = seriesinfo['scope']

		self.uistatus.set('Averaging series')
		ref = imagefun.averageSeries(series)

		corstate = data.CorrectorCamstateData()
		corstate['dimension'] = seriescam['dimension']
		corstate['offset'] = seriescam['offset']
		corstate['binning'] = seriescam['binning']

		refimagedata = self.storeRef(typekey, ref, corstate)

		self.uistatus.set('Got reference image, calculating normalization')
		self.calc_norm(refimagedata)

		# since its not in use yet
		if camdata['exposure type'] == 'dark':
			self.uistatus.set('Reseting camera exposure type to normal from dark')
			camdata['exposure type'] = 'normal'
			self.cam.setCameraEMData(camdata)

		return ref

	def researchRef(self, camstate, type):
		camstate['id'] = None
		if type == 'dark':
			imagetemp = data.DarkImageData()
		elif type == 'bright':
			imagetemp = data.BrightImageData()
		elif type == 'norm':
			imagetemp = data.NormImageData()
		else:
			return None

		imagetemp['camstate'] = camstate
		imagetemp['session'] = data.SessionData()
		imagetemp['session']['instrument'] = self.session['instrument']
		self.uistatus.set('Researching reference image')
		refs = self.research(datainstance=imagetemp, results=1)
		self.uistatus.set('Reference image researched')
		if refs:
			ref = refs[0]
		else:
			ref = None
		return ref

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
			self.uistatus.set('Loading reference image "%s"' % str(key))

		## use reference image from database
		ref = self.researchRef(camstate, type)
		if ref:
			image = ref['image']
			self.ref_cache[key] = image
		else:
			self.uistatus.set('No reference image found')
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
		imagetemp['id'] = self.ID()
		imagetemp['image'] = numdata
		imagetemp['camstate'] = camstate
		self.uistatus.set('Publishing reference image...')
		self.publish(imagetemp, pubevent=True, database=True)
		self.uistatus.set('Reference image published')
		return imagetemp

	def calc_norm(self, corimagedata):
		corstate = corimagedata['camstate']
		corstate['id'] = None
		if isinstance(corimagedata, data.DarkImageData):
			dark = corimagedata['image']
			bright = self.retrieveRef(corstate, 'bright')
			if bright is None:
				self.uistatus.set('No bright reference image')
				return
		if isinstance(corimagedata, data.BrightImageData):
			bright = corimagedata['image']
			dark = self.retrieveRef(corstate, 'dark')
			if dark is None:
				self.uistatus.set('No dark reference image')
				return

		norm = bright - dark

		## there may be a better normavg than this
		normavg = imagefun.mean(norm)

		# division may result infinity or zero division
		# so make sure there are no zeros in norm
		norm = Numeric.clip(norm, 1.0, imagefun.inf)
		norm = normavg / norm
		#print 'saving'
		self.storeRef('norm', norm, corstate)

	def acquireCorrectedArray(self):
		imagedata = self.acquireCorrectedImageData()
		return imagedata['image']

	def acquireCorrectedImageData(self):
		imagedata = self.cam.acquireCameraImageData(correction=0)
		numimage = imagedata['image']
		camdata = imagedata['camera']
		corstate = data.CorrectorCamstateData()
		corstate['dimension'] = camdata['dimension']
		corstate['offset'] = camdata['offset']
		corstate['binning'] = camdata['binning']
		corrected = self.correct(numimage, corstate)
		imagedata['image'] = corrected
		return imagedata

	def correct(self, original, camstate):
		'''
		this puts an image through a pipeline of corrections
		'''
		normalized = self.normalize(original, camstate)
		plandata = self.retrievePlan(camstate)
		if plandata is not None:
			touchedup = self.removeBadPixels(normalized, plandata)
			#clipped = self.clip(touchedup, plandata)
			good = touchedup
		else:
			good = normalized

		if self.despikeon.get():
			#print 'despiking'
			thresh = self.despikevalue.get()
			nsize = self.despikesize.get()
			good = imagefun.despike(good, nsize, thresh)
		return good

	def removeBadPixels(self, image, plandata):
		badrows = plandata['bad_rows']
		badcols = plandata['bad_cols']

		shape = image.shape

		goodrow = None
		for row in range(shape[0]):
			if row not in badrows:
				goodrow = row
				break
		imagefun.fakeRows(image, badrows, goodrow)

		goodcol = None
		for col in range(shape[1]):
			if col not in badcols:
				goodcol = col
				break
		imagefun.fakeCols(image, badcols, goodcol)

		return image

	def clip(self, image, plandata):
		cliplimits = plandata['clip_limits']
		if len(cliplimits) == 0:
			return image
		minclip,maxclip = cliplimits
		return Numeric.clip(image, minclip, maxclip)

	def normalize(self, raw, camstate):
		dark = self.retrieveRef(camstate, 'dark')
		norm = self.retrieveRef(camstate, 'norm')
		if dark is not None and norm is not None:
			diff = raw - dark
			## this may result in some infinity values
			r = diff * norm
			return r
		else:
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

		imagedata = self.cam.acquireCameraImageData(correction=False)
		im = imagedata['image']
		mean = darkmean = imagefun.mean(im)
		self.displayImage(im)
		self.uistatus.set('Dark reference mean: %s' % str(darkmean))

		target_exp = 0
		trial_exp = initial_exp
		tolerance = 100
		minmean = targetmean - tolerance
		maxmean = targetmean + tolerance

		tries = 5
		for i in range(tries):
			config = { 'exposure time': trial_exp }
			raise NotImplementedError('need to work out the details of configuring the camera here')
			imagedata = self.cam.acquireCameraImageData(correction=False)
			im = imagedata['image']
			mean = imagefun.mean(im)
			self.displayImage(im)
			self.uistatus.set('Image mean: %s' % str(mean))

			if minmean <= mean <= maxmean:
				#print 'exposure time %s is good'
				i = -1
				break
			else:
				slope = (mean - darkmean) / trial_exp
				trial_exp = (targetmean - darkmean) / slope

		if i == tries-1:
			self.uistatus.set('Failed to find target mean after %s tries' % (tries,))

