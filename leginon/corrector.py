#!/usr/bin/env python
import node
import Numeric
import cameraimage
import data, event
import cPickle
import string
import threading
import Mrc
import camerafuncs
import dbdatakeeper
import xmlrpclib
import os
import copy
#import xmlrpclib2 as xmlbinlib
xmlbinlib = xmlrpclib

False = 0
True = 1

class DataHandler(node.DataHandler):
	def __init__(self, id, session, inode):
		self.node = inode
		node.DataHandler.__init__(self, id, session)
	# acq/rel twice on normal data
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
	def __init__(self, id, session, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)

		node.Node.__init__(self, id, session, nodelocations,
												[(DataHandler, (self,)),
													(dbdatakeeper.DBDataKeeper, ())], **kwargs)
		self.addEventOutput(event.DarkImagePublishEvent)
		self.addEventOutput(event.BrightImagePublishEvent)
		self.addEventOutput(event.ListPublishEvent)

		ids = [('corrected image data',)]
		e = event.ListPublishEvent(self.ID(), idlist=ids)
		self.outputEvent(e)

		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		### Acquire Bright/Dark
		acqdark = self.registerUIMethod(self.uiAcquireDark, 'Acquire Dark', ())
		acqbright = self.registerUIMethod(self.uiAcquireBright, 'Acquire Bright',())
		acqcorr = self.registerUIMethod(self.uiAcquireCorrected,
																					'Acquire Corrected', ())
		self.acquireimage = self.registerUIData('Image', 'binary', permissions='r')
		acquirecontainer = self.registerUIContainer('Acquire',
															(acqdark, acqbright, acqcorr, self.acquireimage))

		self.navgdata = self.registerUIData('Frames to Average', 'integer',
																						default=3, permissions='rw')


		self.fakeflag = self.registerUIData('Fake', 'boolean', default=False,
																													permissions='rw')

		camconfigdata = self.cam.configUIData()
		prefs = self.registerUIContainer('Preferences',
																	(self.navgdata, self.fakeflag, camconfigdata))

		argspec = (
			self.registerUIData('clip limits', 'array', default=()),
			self.registerUIData('bad rows', 'array', default=()),
			self.registerUIData('bad cols', 'array', default=())
		)
		setplan = self.registerUIMethod(self.uiSetPlanParams, 'Set Plan Params',
																																			argspec)

		ret = self.registerUIData('Current Plan', 'struct')
		getplan = self.registerUIMethod(self.uiGetPlanParams, 'Get Plan Params',
																													(), returnspec=ret)
		plan = self.registerUISpec('Plan', (getplan, setplan))

		myspec = self.registerUISpec('Corrector', (plan, acquirecontainer, prefs))
		myspec += nodespec
		return myspec

	def uiSetPlanParams(self, cliplimits, badrows, badcols):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		plandata = self.newPlan(camstate)
		plandata['clip_limits'] = cliplimits
		plandata['bad_rows'] = badrows
		plandata['bad_cols'] = badcols
		self.storePlan(plandata)
		return ''

	def uiGetPlanParams(self):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		plandata = self.retrievePlan(camstate)
		print 'plandata', plandata
		return dict(plandata)

	def uiAcquireDark(self):
		imagedata = self.acquireReference(dark=True)
		print 'Dark Stats: %s' % (self.stats(imagedata),)
		mrcstr = Mrc.numeric_to_mrcstr(imagedata)
		self.acquireimage.set(xmlbinlib.Binary(mrcstr))
		return ''

	def uiAcquireBright(self):
		imagedata = self.acquireReference(dark=False)
		print 'Bright Stats: %s' % (self.stats(imagedata),)
		mrcstr = Mrc.numeric_to_mrcstr(imagedata)
		self.acquireimage.set(xmlbinlib.Binary(mrcstr))
		return ''

	def uiAcquireCorrected(self):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		self.cam.state(camstate)
		imagedata = self.acquireCorrectedArray()
		print 'Corrected Stats: %s' % (self.stats(imagedata),)
		mrcstr = Mrc.numeric_to_mrcstr(imagedata)
		self.acquireimage.set(xmlbinlib.Binary(mrcstr))
		return ''

	def newPlan(self, camstate):
		newcamstate = copy.deepcopy(camstate)
		del newcamstate['exposure time']
		plan = data.CorrectorPlanData(self.ID(), camstate=newcamstate)
		return plan

	def retrievePlan(self, camstate):
		newcamstate = copy.deepcopy(camstate)
		del newcamstate['exposure time']
		plandatalist = self.research(dataclass=data.CorrectorPlanData, camstate=newcamstate)
		if not plandatalist:
			self.printerror('cannot find plan data for camera state')
			return None
		plandata = plandatalist[0]
		return plandata

	def storePlan(self, plandata):
		self.publish(plandata, database=True)

	def acquireSeries(self, n, camstate):
		series = []
		for i in range(n):
			print 'acquiring %s of %s' % (i+1, n)
			imagedata = self.cam.acquireCameraImageData(camstate=camstate, correction=False)
			numimage = imagedata['image']
			camstate = imagedata['camera']
			scopestate = imagedata['scope']
			series.append(numimage)
		return {'image series': series, 'scope': scopestate, 'camera':camstate}

	def acquireReference(self, dark=False):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		tempcamstate = copy.deepcopy(camstate)
		if dark:
			tempcamstate['exposure time'] = 0
			typekey = 'dark'
		else:
			typekey = 'bright'

		self.cam.state(tempcamstate)

		navg = self.navgdata.get()

		seriesinfo = self.acquireSeries(navg, camstate=tempcamstate)
		series = seriesinfo['image series']
		for im in series:
			print im.shape, im.typecode()
		seriescam = seriesinfo['camera']
		seriesscope = seriesinfo['scope']

		print 'averaging series'
		ref = cameraimage.averageSeries(series)
		self.storeRef(typekey, ref, camstate)

		print 'got ref, calcnorm'
		self.calc_norm(camstate)
		print 'returning ref'
		return ref

	def retrieveRef(self, camstate, type):
		newcamstate = copy.deepcopy(camstate)
		del newcamstate['exposure time']
		if type == 'dark':
			imageclass = data.DarkImageData
		elif type == 'bright':
			imageclass = data.BrightImageData
		elif type == 'norm':
			imageclass = data.NormImageData
		else:
			return None

		try:
			ref = self.research(dataclass=imageclass, camstate=newcamstate)
			ref = ref[0]
			return ref['image']
		except:
			return None

	def storeRef(self, type, numdata, camstate):
		newcamstate = copy.deepcopy(camstate)
		del newcamstate['exposure time']
		if type == 'dark':
			imageclass = data.DarkImageData
			eventclass = event.DarkImagePublishEvent
		elif type == 'bright':
			imageclass = data.BrightImageData
			eventclass = event.BrightImagePublishEvent
		elif type == 'norm':
			imageclass = data.NormImageData
			eventclass = event.NormImagePublishEvent
		
		imagedata = imageclass(self.ID(), image=numdata, camstate=newcamstate)
		print 'publishing'
		self.publish(imagedata, eventclass=eventclass, database=True)

	def calc_norm(self, camstate):
		dark = self.retrieveRef(camstate, 'dark')
		bright = self.retrieveRef(camstate, 'bright')
		if bright is None:
			print 'NO BRIGHT'
			return
		if dark is None:
			print 'NO DARK'
			return

		print 'norm 1'

		norm = bright - dark

		## there may be a better normavg than this
		print 'normavg'
		normavg = cameraimage.mean(norm)

		# division may result infinity or zero division
		# so make sure there are no zeros in norm
		print 'norm 2'
		norm = Numeric.clip(norm, 1.0, cameraimage.inf)
		print 'norm 3'
		norm = normavg / norm
		print 'saving'
		self.storeRef('norm', norm, camstate)

	def acquireCorrectedArray(self):
		imagedata = self.acquireCorrectedImageData()
		return imagedata['image']

	def acquireCorrectedImageData(self):
		if self.fakeflag.get():
			camconfig = self.cam.config()
			camstate = camconfig['state']
			numimage = Mrc.mrc_to_numeric('fake.mrc')
			corrected = self.correct(numimage, camstate)
			return data.ImageData(self.ID, image=corrected)
		else:
			imagedata = self.cam.acquireCameraImageData(correction=0)
			numimage = imagedata['image']
			camstate = imagedata['camera']
			corrected = self.correct(numimage, camstate)
			imagedata['image'] = corrected
			return imagedata

	def correct(self, original, camstate):
		'''
		this puts an image through a pipeline of corrections
		'''
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
		cameraimage.fakeRows(image, badrows, goodrow)

		goodcol = None
		for col in range(shape[1]):
			if col not in badcols:
				goodcol = col
				break
		cameraimage.fakeCols(image, badcols, goodcol)

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
		mean = cameraimage.mean(im)
		stdev = cameraimage.stdev(im)
		mn = cameraimage.min(im)
		mx = cameraimage.max(im)
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
