#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import camerafuncs
import copy
import data
import datatransport
import event
import imagefun
import node
import Numeric
import threading
import uidata
import EM

class CameraError(Exception):
	pass

class FindExposureTimeError(Exception):
	pass

class AbortError(Exception):
	pass

class SimpleCorrector(node.Node):
	eventinputs = node.Node.eventinputs + EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + [event.DarkImagePublishEvent,
																						event.BrightImagePublishEvent] \
																				 + EM.EMClient.eventoutputs
	def __init__(self, name, session, managerlocation, **kwargs):
		self.references = {}
		self.abortevent = threading.Event()
		node.Node.__init__(self, name, session, managerlocation, **kwargs)
		self.emclient = EM.EMClient(self)
		self.camerafuncs = camerafuncs.CameraFuncs(self)

		self.initializeLogger(name)

		self.imagedata = data.DataHandler(data.CorrectedCameraImageData, getdata=self.acquireCorrectedImageData)
		self.logger.debug('CORIMAGE REF: %s' % (self.imagedata.reference(),))
		self.publish(self.imagedata, pubevent=True, broadcast=True)

		self.defineUserInterface()
		self.start()

	def exit(self):
		node.Node.exit(self)
		self.server.exit()

	def getReferenceDataClass(self, referencetype):
		if referencetype == 'dark':
			dataclass = data.DarkImageData
		elif referencetype == 'normal':
			dataclass = data.BrightImageData
		elif referencetype == 'normalization':
			dataclass = data.NormImageData
		else:
			raise ValueError('Invalid reference type specified')
		return dataclass

	def filename(self, reftype, imid):
		f = '%s_%s_%s_%06d' % (self.session['name'], self.name, reftype, imid)
		return f

	def researchReference(self, binning, referencetype):
		referencedata = self.getReferenceDataClass(referencetype)()

		camerasize = self.session['instrument']['camera size']
		correctorcamstatedata = data.CorrectorCamstateData()
		correctorcamstatedata['offset'] = {'x': 0, 'y': 0}
		correctorcamstatedata['binning'] = {'x': binning, 'y': binning}
		correctorcamstatedata['dimension'] = {'x': camerasize/binning,
																					'y': camerasize/binning}

		referencedata['camstate'] = correctorcamstatedata
		referencedata['session'] = data.SessionData()
		referencedata['session']['instrument'] = self.session['instrument']

		self.status.set('Researching reference image...')
		try:
			references = self.research(datainstance=referencedata, results=1)
		except node.ResearchError, e:
			message = 'Error researching reference image from the database'
			if str(e):
				message += ': %s' % str(e)
			self.messagelog.error(message)
			return None
		self.status.set('Reference image researched')
		try:
			return references[0]['image']
		except (TypeError, IndexError, KeyError):
			return None

	def correctImage(self, image, cameradata):
		binning = cameradata['binning']['x']
		rowoffset = cameradata['offset']['y']
		columnoffset = cameradata['offset']['x']
		rows = cameradata['dimension']['y']
		columns = cameradata['dimension']['x']
		try:
			dark = self.references[binning]['dark']
		except KeyError:
			dark = self.researchReference(binning, 'dark')
			if dark is None:
				self.messagelog.error('No dark reference image for binning of %d'
																% binning)
				return None
			if binning in self.references:
				self.references[binning]['dark'] = dark
			else:
				self.references[binning] = {'dark': dark}
		try:
			normalization = self.references[binning]['normalization']
		except KeyError:
			normalization = self.researchReference(binning, 'normalization')
			if normalization is None:
				self.messagelog.error(
					'No normalization reference image for binning of %d' % binning)
				return None
			if binning in self.references:
				self.references[binning]['normalization'] = normalization
			else:
				self.references[binning] = {'normalization': normalization}
		return (image - dark[rowoffset:rowoffset + rows,
													columnoffset:columnoffset + columns]) \
									* normalization[rowoffset:rowoffset + rows,
																	columnoffset:columnoffset + columns]

	def acquireCorrectedImageData(self):
		try:
			imagedata = self.camerafuncs.acquireCameraImageData(correction=False)
		except camerafuncs.NoEMError:
			self.messagelog.error('EM not running')
			return None

		image = imagedata['image']
		cameradata = imagedata['camera']

		correctedimage = self.correctImage(image, cameradata)
		if correctedimage is None:
			return None
		correctedimage = correctedimage.astype(image.typecode())
		newdata = data.CorrectedCameraImageData(initializer=imagedata, image=correctedimage)
		return newdata

	def getImageStats(self, image):
		mean = imagefun.mean(image)
		stdev = imagefun.stdev(image, known_mean=mean)
		min = imagefun.min(image)
		max = imagefun.max(image)
		return {'mean': mean, 'stdev': stdev, 'min': min, 'max': max}

	def displayImageStats(self, image):
		if image is None:
			self.mean.set(None)
			self.min.set(None)
			self.max.set(None)
			self.std.set(None)
		else:
			stats = self.getImageStats(image)
			self.mean.set(stats['mean'])
			self.min.set(stats['min'])
			self.max.set(stats['max'])
			self.std.set(stats['stdev'])

	def getCameraSettings(self, binning, exposuretype, exposuretime=None):
		cameradata = self.camerafuncs.getCameraEMData()
		if cameradata is None:
			raise CameraError('cannot get camera settings')
		camerasize = self.session['instrument']['camera size']
		for axis in ['x', 'y']:
			cameradata['offset'][axis] = 0
			cameradata['binning'][axis] = binning
			cameradata['dimension'][axis] = camerasize/binning
		cameradata['exposure type'] = exposuretype
		cameradata['exposure time'] = exposuretime
		return cameradata

	def setCameraSettings(self, binning, exposuretype, exposuretime=None):
		cameradata = self.getCameraSettings(binning, exposuretype, exposuretime)
		self.camerafuncs.setCameraEMData(cameradata)
		return cameradata

	def getCounts(self):
		cameradata = self.camerafuncs.getCameraEMData()
		min = 0
		if ('maximum pixel value' in cameradata and
				cameradata['maximum pixel value'] is not None):
			max = cameradata['maximum pixel value']
		else:
			pass
		return (max - min)/2

	def findExposureTime(self, binning, counts):
		self.findstatus.set('Finding exposure time...')
		self.findbinning.set(binning)
		self.findcounts.set(counts)
		minexposuretime = self.findminexposuretime.get()
		maxexposuretime = self.findmaxexposuretime.get()
		tolerance = self.findtolerance.get()/100.0 * counts
		exposuretime = (maxexposuretime - minexposuretime)/2 + minexposuretime
		self.findexposuretime.set(exposuretime)
		while exposuretime > minexposuretime and exposuretime < maxexposuretime:
			self.setCameraSettings(binning, 'normal', exposuretime)
			imagedata = self.camerafuncs.acquireCameraImageData(correction=False)
			image = imagedata['image']
			mean = imagefun.mean(image)
			self.findmean.set(mean)
			if mean - tolerance <= counts and mean + tolerance >= counts:
				self.findstatus.set('Exposure time for mean count value found')
				return exposuretime
			if mean > counts:
				maxexposuretime = exposuretime
			elif mean < counts:
				minexposuretime = exposuretime
			exposuretime = (maxexposuretime - minexposuretime)/2 + minexposuretime
			self.findexposuretime.set(exposuretime)
		self.findstatus.set('Cannot find mean counts for exposure time range')
		self.findexposuretime.set(None)
		self.findmean.set(None)
		return None

	def onFindExposureTime(self):
		binning = self.findbinning.get()
		counts = self.findcounts.get()
		try:
			self.findExposureTime(binning, counts)
		except (CameraError, node.ResearchError):
			self.findmessagelog.error('Error configuring camera')

	def getMedianImage(self, naverage):
		images = []
		for i in range(naverage):
			self.status.set('Acquiring image %d of %d...' % (i+1, naverage))
			imagedata = self.camerafuncs.acquireCameraImageData(correction=False)
			images.append(imagedata['image'])
			if self.displayacquire.get():
				self.displayImageStats(imagedata['image'])
				self.image.set(imagedata['image'])
		self.status.set('Calculating median image...')
		image = imagefun.medianSeries(images)
		if self.displaymedian.get():
			self.displayImageStats(image)
			self.image.set(image)
		return image

	def publishReference(self, referencetype, image, camerastate):
		imagedata = self.getReferenceDataClass(referencetype)()
		imagedata['image'] = image
		correctorcamstatedata = data.CorrectorCamstateData()
		correctorcamstatedata['dimension'] = camerastate['dimension']
		correctorcamstatedata['offset'] = camerastate['offset']
		correctorcamstatedata['binning'] = camerastate['binning']
		imagedata['camstate'] = correctorcamstatedata
		imagedata['filename'] = self.filename(referencetype, imagedata.dmid[-1])
		imagedata['session'] = self.session
		self.status.set('Publishing reference image...')
		self.publish(imagedata, pubevent=True, database=True)
		self.status.set('Reference image published')

	def acquireReferenceImage(self, binning, exposuretype, naverage,
														exposuretime):
		self.status.set('Setting up camera...')
		camerastate = self.setCameraSettings(binning, exposuretype, exposuretime)
		image = self.getMedianImage(naverage)
		self.publishReference(exposuretype, image, camerastate)
		return image, camerastate

	def calculateNormalizationImage(self, darkimage, brightimage, camerastate):
		image = brightimage - darkimage
		mean = imagefun.mean(image)
		# clip to ensure corrected values are in range
		image = Numeric.clip(image, 1.0, imagefun.inf)
		image = mean/image
		if self.displaynormalization.get():
			self.displayImageStats(image)
			self.image.set(image)
		self.publishReference('normalization', image, camerastate)
		return image

	def acquireReferenceImages(self):
		naverage = self.imagestoaverage.get()
		exposuretypestrings = {'dark': 'Dark', 'normal': 'Bright'}
		binnings = self.binnings.get()
		binnings.sort()
		binnings.reverse()
		try:
			# invert binning/exposure type for calculating normalizations
			# could be less than optimal if retracting camera on darks
			for binning in binnings:
				self.exposuretype.set('')
				self.binning.set(str(binning))
				self.status.set('Finding exposure time...')
				exposuretime = self.findExposureTime(binning, self.findcounts.get())
				if exposuretime is None:
					message = 'Cannot find mean counts for exposure time range'
					self.messagelog.error(message)
					raise FindExposureTimeError(message)
				for exposuretype in ['dark', 'normal']:
					self.exposuretype.set(exposuretypestrings[exposuretype])
					image, camerastate = \
						self.acquireReferenceImage(binning, exposuretype, naverage,
																				exposuretime)
					if binning not in self.references:
						self.references[binning] = {}
					self.references[binning][exposuretype] = image
					if self.abortevent.isSet():
						raise AbortError
				self.status.set('Calculating normalization image...')
				self.exposuretype.set('')
				self.references[binning]['normalization'] = \
					 self.calculateNormalizationImage(self.references[binning]['dark'],
																						self.references[binning]['normal'],
																						camerastate)
				try:
					del self.references[binning]['normal']
				except (TypeError, KeyError):
					pass
		except (CameraError, node.PublishError, node.ResearchError,
						FindExposureTimeError, AbortError), e:
			errormessage = ''
			statusmessage = 'Error acquiring reference images'
			if isinstance(e, (CameraError, node.ResearchError)):
				errormessage = 'Error configuring camera'
			elif isinstance(e, node.PublishError):
				errormessage = 'Error saving reference to the database'
			elif isinstance(e, AbortError):
				statusmessage = 'Acquire references aborted'
			else:
				errormessage = 'Error acquiring reference images'
			if errormessage:
				if str(e):
					errormessage += ': %s' % str(e)
				self.messagelog.error(errormessage)
			self.status.set(statusmessage)
			self.exposuretype.set('')
			self.binning.set('')
			self.displayImageStats(None)
			return

		self.status.set('Reference images acquired')
		self.exposuretype.set('')
		self.binning.set('')
		self.displayImageStats(None)

	def onAcquireReferenceImages(self):
		self.automethod.disable()
		self.abortevent.clear()
		self.abortmethod.enable()
		try:
			self.acquireReferenceImages()
		except:
			self.automethod.enable()
			self.abortmethod.disable()
			raise
		self.automethod.enable()
		self.abortmethod.disable()

	def onAbort(self):
		self.abortmethod.disable()
		self.abortevent.set()

	def defineUserInterface(self):
		self.initializeLoggerUserInterface()
		node.Node.defineUserInterface(self)

		self.displayacquire = uidata.Boolean('Acquired images', False,
																					'rw', persist=True)
		self.displaymedian = uidata.Boolean('Median images', True,
																					'rw', persist=True)
		self.displaynormalization = uidata.Boolean('Normalization images', True,
																								'rw', persist=True)
		displaycontainer = uidata.Container('Display')
		displaycontainer.addObjects((self.displayacquire, self.displaymedian,
																	self.displaynormalization))
		self.binnings = uidata.Sequence('Binnings', [1, 2, 4, 8], 'rw')
		self.imagestoaverage = uidata.Integer('Images to average', 3, 'rw',
																					persist=True)

		referencesettingscontainer = uidata.Container('Reference Acquisition')
		referencesettingscontainer.addObjects((displaycontainer, self.binnings,
																						self.imagestoaverage))

		self.findcounts = uidata.Number('Desired mean', 1000, 'rw', persist=True)
		self.findtolerance = uidata.Number('Tolerance (% +/-)', 10,
																				'rw', persist=True)
		findcountscontainer = uidata.Container('Counts')
		findcountscontainer.addObjects((self.findcounts, self.findtolerance))

		self.findminexposuretime = uidata.Integer('Minimum', 0, 'rw', persist=True)
		self.findmaxexposuretime = uidata.Integer('Maximum', 1000, 'rw',
																							persist=True)
		findexposurerangecontainer = uidata.Container('Exposure Search Range (ms)')
		findexposurerangecontainer.addObjects((self.findminexposuretime,
																						self.findmaxexposuretime))
		autosettingscontainer = uidata.Container('Auto Exposure Time')
		autosettingscontainer.addObjects((findcountscontainer,
																			findexposurerangecontainer))
		advancedsettingscontainer = uidata.LargeContainer('Advanced Settings')
		advancedsettingscontainer.addObjects((autosettingscontainer,
																					referencesettingscontainer))

		self.findmessagelog = uidata.MessageLog('Message Log')

		self.findstatus = uidata.String('Status', '', 'r')
		self.findexposuretime = uidata.Number('Exposure time', None, 'r')
		self.findmean = uidata.Number('Mean', None, 'r')
		findstatuscontainer = uidata.Container('Status')
		findstatuscontainer.addObjects((self.findstatus, self.findexposuretime,
																		self.findmean))

		self.findbinning = uidata.Integer('Binning', 1, 'rw', persist=True)
		findsettingscontainer = uidata.Container('Settings')
		findsettingscontainer.addObjects((self.findbinning,))

		findexposuretimemethod = uidata.Method('Search',
																						self.onFindExposureTime)
		findcontrolcontainer = uidata.Container('Control')
		findcontrolcontainer.addObjects((findexposuretimemethod,))

		findcontainer = uidata.LargeContainer('Auto Exposure Time')
		findcontainer.addObject(self.findmessagelog, position={'expand': 'all'})
		findcontainer.addObjects((findstatuscontainer, findsettingscontainer,
															findcontrolcontainer))

		self.messagelog = uidata.MessageLog('Message Log')

		self.status = uidata.String('Status', '', 'r')
		self.exposuretype = uidata.String('Exposure type', '', 'r')
		self.binning = uidata.String('Binning', '', 'r')

		self.mean = uidata.Float('Mean', None, 'r')
		self.min = uidata.Float('Min', None, 'r')
		self.max = uidata.Float('Max', None, 'r')
		self.std = uidata.Float('Std. Dev.', None, 'r')
		statisticscontainer = uidata.Container('Statistics')
		statisticscontainer.addObjects((self.mean, self.min, self.max, self.std))

		statuscontainer = uidata.Container('Status')
		statuscontainer.addObjects((self.status, self.exposuretype, self.binning,
																statisticscontainer))

		self.image = uidata.Image('Image', None)

		self.automethod = uidata.Method('Auto', self.onAcquireReferenceImages)
		self.abortmethod = uidata.Method('Abort', self.onAbort)
		self.abortmethod.disable()
		referencescontainer = uidata.Container('References')
		referencescontainer.addObjects((self.automethod, self.abortmethod))

		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((referencescontainer,))

		container = uidata.LargeContainer('Simple Corrector')
		container.addObject(self.messagelog, position={'expand': 'all'})
		container.addObjects((statuscontainer, controlcontainer, self.image))

		self.uicontainer.addObjects((advancedsettingscontainer, findcontainer,
															container,))

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
	eventinputs = node.Node.eventinputs + EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + [event.DarkImagePublishEvent, event.BrightImagePublishEvent] + EM.EMClient.eventoutputs
	def __init__(self, name, session, managerlocation, **kwargs):
		self.initializeLogger(name)

		node.Node.__init__(self, name, session, managerlocation, **kwargs)

		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)

		self.ref_cache = {}

		self.imagedata = data.DataHandler(data.CorrectedCameraImageData, getdata=self.acquireCorrectedImageData)
		self.publish(self.imagedata, pubevent=True, broadcast=True)

		self.defineUserInterface()
		self.start()

	def exit(self):
		node.Node.exit(self)
		self.server.exit()

	def defineUserInterface(self):
		self.initializeLoggerUserInterface()
		node.Node.defineUserInterface(self)

		self.messagelog = uidata.MessageLog('Messages')
		self.uistatus = uidata.String('Status', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObjects((self.uistatus,))

		darkmethod = uidata.Method('Dark', self.uiAcquireDark)
		brightmethod = uidata.Method('Bright', self.uiAcquireBright)
		referencescontainer = uidata.Container('References')
		referencescontainer.addObjects((darkmethod, brightmethod))

		rawmethod = uidata.Method('Raw', self.uiAcquireRaw)
		correctedmethod = uidata.Method('Corrected', self.uiAcquireCorrected)
		acquirecontainer = uidata.Container('Acquire')
		acquirecontainer.addObjects((rawmethod, correctedmethod))

		self.autobinning = uidata.Integer('Binning', 1, 'rw', persist=True)
		self.autoexptime = uidata.Integer('Exposure Time', 500, 'rw', persist=True)
		self.autotarget = uidata.Integer('Target Mean', 2000, 'rw', persist=True)
		automethod = uidata.Method('Auto References', self.uiAutoAcquireReferences)
		autocontainer = uidata.Container('Auto References')
		autocontainer.addObjects((self.autobinning, self.autotarget,
															self.autoexptime, automethod))

		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((referencescontainer, acquirecontainer))

		self.displayflag = uidata.Boolean('Display image', True, 'rw', persist=True)

		camsetup = self.cam.uiSetupContainer()

		self.uiframestoaverage = uidata.Integer('Frames to Average', 3, 'rw')

		self.badrows = uidata.Sequence('Bad Rows', (), 'rw')
		self.badcols = uidata.Sequence('Bad Cols', (), 'rw')
		setplan = uidata.Method('Set Plan', self.uiSetPlanParams)
		getplan = uidata.Method('Get Plan', self.uiGetPlanParams)

		self.despikeon = uidata.Boolean('Despike', True, 'rw', persist=True)
		self.despikevalue = uidata.Float('Despike Threshold', 3.5, 'rw',
																			persist=True)
		self.despikesize = uidata.Integer('Neighborhood Size', 11, 'rw',
																			persist=True)
		despikecontainer = uidata.Container('Despike')
		despikecontainer.addObjects((self.despikeon, self.despikesize,
																	self.despikevalue))

		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((self.displayflag, self.uiframestoaverage,
																	camsetup, self.badrows, self.badcols,
																	setplan, getplan, despikecontainer))

		statscontainer = uidata.Container('Statistics')
		self.statsmean = uidata.Float('Mean', None, 'r')
		self.statsmin = uidata.Float('Min', None, 'r')
		self.statsmax = uidata.Float('Max', None, 'r')
		self.statsstd = uidata.Float('Std. Dev.', None, 'r')
		statscontainer.addObjects((self.statsmean, self.statsmin, self.statsmax,
																self.statsstd))

		self.ui_image = uidata.Image('Image', None, 'rw')

		container = uidata.LargeContainer('Corrector')
		container.addObject(self.messagelog, position={'expand': 'all'})
		container.addObjects((statuscontainer, settingscontainer, controlcontainer,
													statscontainer, self.ui_image))
		self.uicontainer.addObject(container)

	def uiSetPlanParams(self):
		### if apply as needed, use local config
		self.cam.uiApplyAsNeeded()
		camconfig = self.cam.getCameraEMData()

		newcamstate = data.CorrectorCamstateData()
		newcamstate['session'] = self.session
		newcamstate['dimension'] = camconfig['dimension']
		newcamstate['offset'] = camconfig['offset']
		newcamstate['binning'] = camconfig['binning']
		plandata = data.CorrectorPlanData()
		plandata['session'] = self.session
		plandata['camstate'] = newcamstate
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
			self.badrows.set([])
			self.badcols.set([])
		else:
			self.badrows.set(plandata['bad_rows'])
			self.badcols.set(plandata['bad_cols'])

	def uiAcquireDark(self):
		try:
			imagedata = self.acquireReference(dark=True)
		except node.PublishError:
			self.logger.exception('Cannot set EM parameter, EM may not be running')
		else:
			self.displayImage(imagedata)
			node.beep()

	def uiAcquireBright(self):
		try:
			imagedata = self.acquireReference(dark=False)
		except node.PublishError:
			self.logger.exception('Cannot set EM parameter, EM may not be running')
		else:
			self.displayImage(imagedata)
			node.beep()

	def uiAcquireRaw(self):
		try:
			self.cam.uiApplyAsNeeded()
			imagedata = self.cam.acquireCameraImageData(correction=False)
		except node.PublishError:
			self.logger.exception('Cannot set EM parameter, EM may not be running')
		else:
			imagearray = imagedata['image']
			self.displayImage(imagearray)

	def uiAcquireCorrected(self):
		try:
			self.cam.uiApplyAsNeeded()
			imagedata = self.acquireCorrectedArray()
		except node.PublishError:
			self.logger.exception('Cannot set EM parameter, EM may not be running')
		else:
			self.displayImage(imagedata)

	def displayImage(self, imagedata):
		if self.displayflag.get():
			self.ui_image.set(imagedata.astype(Numeric.Float32))
			self.displayStats(imagedata)

	def displayStats(self, imagedata):
		stats = self.stats(imagedata)
		self.statsmean.set(stats['mean'])
		self.statsmin.set(stats['min'])
		self.statsmax.set(stats['max'])
		self.statsstd.set(stats['stdev'])

	def retrievePlan(self, corstate):
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
		self.publish(plandata, database=True, dbforce=True)

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
		self.cam.uiApplyAsNeeded()
		originalcamdata = self.cam.getCameraEMData()
		tempcamdata = data.CameraEMData(initializer=originalcamdata)
		if dark:
			tempcamdata['exposure type'] = 'dark'
			typekey = 'dark'
			self.uistatus.set('Acquiring dark')
		else:
			tempcamdata['exposure type'] = 'normal'
			typekey = 'bright'
			self.uistatus.set('Acquiring bright')
		self.cam.setCameraEMData(tempcamdata)

		navg = self.uiframestoaverage.get()

		seriesinfo = self.acquireSeries(navg, camdata=tempcamdata)
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

		if tempcamdata['exposure type'] == 'dark':
			self.uistatus.set('Reseting camera exposure type to normal from dark')
			self.cam.setCameraEMData(originalcamdata)
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
		imagetemp['image'] = numdata
		imagetemp['camstate'] = camstate
		imagetemp['filename'] = self.filename(type, imagetemp.dmid[-1])
		imagetemp['session'] = self.session
		self.uistatus.set('Publishing reference image...')
		self.publish(imagetemp, pubevent=True, database=True)
		self.uistatus.set('Reference image published')
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
		self.storeRef('norm', norm, corstate)

	def acquireCorrectedArray(self):
		imagedata = self.acquireCorrectedImageData()
		return imagedata['image']

	def acquireCorrectedImageData(self):
		try:
			imagedata = self.cam.acquireCameraImageData(correction=0)
		except camerafuncs.NoEMError:
			self.messagelog.error('EM not running')
			return None
		numimage = imagedata['image']
		camdata = imagedata['camera']
		corstate = data.CorrectorCamstateData()
		corstate['dimension'] = camdata['dimension']
		corstate['offset'] = camdata['offset']
		corstate['binning'] = camdata['binning']
		corrected = self.correct(numimage, corstate)
		newdata = data.CorrectedCameraImageData(initializer=imagedata, image=corrected)
		return newdata

	def correct(self, original, camstate):
		'''
		this puts an image through a pipeline of corrections
		'''
		normalized = self.normalize(original, camstate)
		plandata = self.retrievePlan(camstate)
		if plandata is not None:
			touchedup = self.removeBadPixels(normalized, plandata)
			good = touchedup
		else:
			good = normalized

		if self.despikeon.get():
			self.logger.info('Despiking...')
			thresh = self.despikevalue.get()
			nsize = self.despikesize.get()
			good = imagefun.despike(good, nsize, thresh)
			self.logger.info('Despiked')

		## this has been commented because original.typecode()
		## might be unsigned and causes negative values to wrap
		## around to very large positive values
		## before doing this astype, we should maybe clip negative
		## values
		#return good.astype(original.typecode())

		final = good.astype(Numeric.Float32)
		return final

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
				i = -1
				break
			else:
				slope = (mean - darkmean) / trial_exp
				trial_exp = (targetmean - darkmean) / slope

		if i == tries-1:
			self.uistatus.set('Failed to find target mean after %s tries' % (tries,))

