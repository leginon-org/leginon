#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import node
import Numeric
import imagefun
import data, event
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
		darkmethod = uidata.Method('Acquire Dark', self.uiAcquireDark)
		brightmethod = uidata.Method('Acquire Bright', self.uiAcquireBright)
		rawmethod = uidata.Method('Acquire Raw', self.uiAcquireRaw)
		correctedmethod = uidata.Method('Acquire Corrected',
																			self.uiAcquireCorrected)

		referencescontainer = uidata.Container('References')
		referencescontainer.addObjects((darkmethod, brightmethod))

		testcontainer = uidata.Container('Test')
		testcontainer.addObjects((rawmethod, correctedmethod))
		controlcontainer = uidata.Container('Control')

		self.despikeon = uidata.Boolean('Despike', False, 'rw', persist=True)
		self.despikevalue = uidata.Float('Despike Threshold', 2.0, 'rw', persist=True)

		controlcontainer.addObjects((self.despikeon, self.despikevalue, referencescontainer, testcontainer))
		self.display_flag = uidata.Boolean('Display Image', True, 'rw', persist=True)

		statscontainer = uidata.Container('Statistics')
		self.statsmean = uidata.Float('Mean', None, 'r')
		self.statsmin = uidata.Float('Min', None, 'r')
		self.statsmax = uidata.Float('Max', None, 'r')
		self.statsstd = uidata.Float('Std. Dev.', None, 'r')
		statscontainer.addObjects((self.statsmean, self.statsmin, self.statsmax, self.statsstd))

		self.ui_image = uidata.Image('Image', None, 'rw')

		self.uiframestoaverage = uidata.Integer('Frames to Average', 3, 'rw')
		self.uifakeflag = uidata.Boolean('Fake Image', False, 'rw')
		cameraconfigure = self.cam.configUIData()
		self.cliplimits = uidata.Array('Clip Limits', (), 'rw')
		self.badrows = uidata.Array('Bad Rows', (), 'rw')
		self.badcols = uidata.Array('Bad Cols', (), 'rw')
		setplan = uidata.Method('Set Plan', self.uiSetPlanParams)
		getplan = uidata.Method('Get Plan', self.uiGetPlanParams)

		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((self.uiframestoaverage, self.uifakeflag,
																	cameraconfigure, self.cliplimits,
																	self.badrows, self.badcols, setplan, getplan))
		container = uidata.LargeContainer('Corrector')
		container.addObjects((settingscontainer, controlcontainer, self.display_flag, statscontainer, self.ui_image))
		self.uiserver.addObject(container)

	def uiSetPlanParams(self):
		camconfig = self.cam.cameraConfig()
		newcamstate = data.CorrectorCamstateData()
		newcamstate['dimension'] = camconfig['dimension']
		newcamstate['offset'] = camconfig['offset']
		newcamstate['binning'] = camconfig['binning']
		current = self.cam.currentCameraEMData()
		plandata = data.CorrectorPlanData()
		plandata['camstate'] = newcamstate
		plandata['clip_limits'] = self.cliplimits.get()
		plandata['bad_rows'] = self.badrows.get()
		plandata['bad_cols'] = self.badcols.get()
		self.storePlan(plandata)

	def uiGetPlanParams(self):
		camconfig = self.cam.cameraConfig()
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

	def uiAcquireBright(self):
		try:
			imagedata = self.acquireReference(dark=False)
		except node.PublishError:
			self.outputError('Cannot set EM parameter, EM may not be running')
		else:
			self.displayImage(imagedata)

	def uiAcquireRaw(self):
		camconfig = self.cam.cameraConfig()
		try:
			imagedata = self.cam.acquireCameraImageData(camconfig=camconfig,
																									correction=0)
		except node.PublishError:
			self.outputError('Cannot set EM parameter, EM may not be running')
		else:
			imagearray = imagedata['image']
			if self.despikeon.get():
				print 'despiking'
				thresh = self.despikevalue.get()
				imagearray = imagefun.despike(imagearray, thresh)
			self.displayImage(imagearray)

	def uiAcquireCorrected(self):
		camconfig = self.cam.cameraConfig()
		try:
			imagedata = self.acquireCorrectedArray(camconfig)
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
		print 'STATS', stats
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
			print 'acquiring %s of %s' % (i+1, n)
			imagedata = self.cam.acquireCameraImageData(correction=False)
			numimage = imagedata['image']
			camdata = imagedata['camera']
			scopedata = imagedata['scope']
			series.append(numimage)
		return {'image series': series, 'scope': scopedata, 'camera':camdata}

	def acquireReference(self, dark=False):
		camconfig = self.cam.cameraConfig()
		camdata = self.cam.configToEMData(camconfig)
		if dark:
			camdata['exposure type'] = 'dark'
			typekey = 'dark'
			print 'DARK'
		else:
			typekey = 'bright'
			print 'BRIGHT'

		self.cam.currentCameraEMData(camdata)

		navg = self.uiframestoaverage.get()

		seriesinfo = self.acquireSeries(navg, camdata=camdata)
		series = seriesinfo['image series']
		for im in series:
			print im.shape, im.typecode()
		seriescam = seriesinfo['camera']
		seriesscope = seriesinfo['scope']

		print 'averaging series'
		ref = imagefun.averageSeries(series)

		if self.despikeon.get():
			print 'despiking reference image'
			thresh = self.despikevalue.get()
			ref = imagefun.despike(ref, thresh)

		corstate = data.CorrectorCamstateData()
		corstate['dimension'] = seriescam['dimension']
		corstate['offset'] = seriescam['offset']
		corstate['binning'] = seriescam['binning']

		refimagedata = self.storeRef(typekey, ref, corstate)

		print 'got ref, calcnorm'
		self.calc_norm(refimagedata)

		# since its not in use yet
		if camdata['exposure type'] == 'dark':
			print 'reseting camera from dark to normal'
			camconfig = self.cam.cameraConfig()
			camdata = self.cam.configToEMData(camconfig)
			camdata['exposure type'] = 'normal'
			self.cam.currentCameraEMData(camdata)

		print 'returning ref'
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
		print 'researching reference image'
		refs = self.research(datainstance=imagetemp, results=1)
		print 'done researching reference image'
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
			print 'loading reference image', key

		## use reference image from database
		ref = self.researchRef(camstate, type)
		if ref:
			image = ref['image']
			self.ref_cache[key] = image
		else:
			print 'No reference image found', camstate, type
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
		print 'publishing'
		self.publish(imagetemp, pubevent=True, database=True)
		return imagetemp

	def calc_norm(self, corimagedata):
		corstate = corimagedata['camstate']
		corstate['id'] = None
		if isinstance(corimagedata, data.DarkImageData):
			dark = corimagedata['image']
			bright = self.retrieveRef(corstate, 'bright')
			if bright is None:
				print 'NO BRIGHT'
				return
		if isinstance(corimagedata, data.BrightImageData):
			bright = corimagedata['image']
			dark = self.retrieveRef(corstate, 'dark')
			if dark is None:
				print 'NO DARK'
				return

		norm = bright - dark

		## there may be a better normavg than this
		normavg = imagefun.mean(norm)

		# division may result infinity or zero division
		# so make sure there are no zeros in norm
		norm = Numeric.clip(norm, 1.0, imagefun.inf)
		norm = normavg / norm
		print 'saving'
		self.storeRef('norm', norm, corstate)

	def acquireCorrectedArray(self, camconfig=None):
		imagedata = self.acquireCorrectedImageData(camconfig)
		return imagedata['image']

	def acquireCorrectedImageData(self, camconfig=None):
		if self.uifakeflag.get():
			camconfig = self.cam.cameraConfig()
			camstate = camconfig['state']
			numimage = Mrc.mrc_to_numeric('fake.mrc')
			corrected = self.correct(numimage, camstate)
			return data.ImageData(id=self.ID, image=corrected)
		else:
			imagedata = self.cam.acquireCameraImageData(camconfig=camconfig, correction=0)
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
		if self.despikeon.get():
			print 'despiking'
			thresh = self.despikevalue.get()
			original = imagefun.despike(original, thresh)

#		print 'normalize'
		normalized = self.normalize(original, camstate)
		plandata = self.retrievePlan(camstate)
		if plandata is not None:
#			print 'touchup'
			touchedup = self.removeBadPixels(normalized, plandata)
#			print 'clip'
			clipped = self.clip(touchedup, plandata)
#			print 'done'
			return clipped
		else:
			return normalized

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


if __name__ == '__main__':
	from Numeric import *
	import Mrc
	from ImageViewer import ImageViewer

	print 'reading darks'
	dark1 = Mrc.mrc_to_numeric('/home/pulokas/test_images/dark1.mrc')
	dark2 = Mrc.mrc_to_numeric('/home/pulokas/test_images/dark2.mrc')
	print 'averaging darks'
	dark = numeric_series_average( (dark1,dark2) )
	print 'reading brights'
	bright1 = Mrc.mrc_to_numeric('/home/pulokas/test_images/bright1.mrc')
	bright2 = Mrc.mrc_to_numeric('/home/pulokas/test_images/bright2.mrc')
	print 'averaging brights'
	bright = numeric_series_average( (bright1,bright2) )
	print 'reading raw'
	raw = Mrc.mrc_to_numeric('/home/pulokas/test_images/raw4.mrc')

	print 'setting up corrector'
	corrector = FlatCorrector()
	corrector.set_dark(dark)
	corrector.set_bright(bright)
	print 'correcting'
	good = corrector.normalize(raw)

	#print 'dark', dark
	#print 'bright', bright
	#print 'norm', corrector.norm
	#print 'good', good


	print 'prparing raw-dark'
	rawmdark = raw - dark
	print 'finding averages of raw-dark and good'
	rawmdarkavg = numeric_mean(rawmdark)
	goodavg = numeric_mean(good)
	print 'rawmdarkavg', rawmdarkavg
	print 'goodavg', goodavg

	print 'darkstdev', numeric_stdev(dark)
	goodstdev = numeric_stdev(good)
	print 'goodstdev', goodstdev

	from Tkinter import *
	root = Tk()
	jim = ImageViewer(root, bg='#488')
	jim.pack()
	jim.import_numeric(good)

	clip = (goodavg - 3 * goodstdev,   goodavg + 3 * goodstdev)
	jim.transform['clip'] = clip
	#jim.transform['output_size'] = (400,400)
	jim.update_image()

	root.mainloop()
