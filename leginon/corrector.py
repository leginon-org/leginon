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
import xmlrpclib
#import xmlrpclib2 as xmlbinlib
xmlbinlib = xmlrpclib

False = 0
True = 1

class DataHandler(node.DataHandler):
	def __init__(self, id, inode):
		self.node = inode
		node.DataHandler.__init__(self, id)
	# acq/rel twice on normal data
	def query(self, id):
		self.lock.acquire()
		if id == 'normalized image data':
			result = self.node.acquireCorrectedImageData()
			self.lock.release()
			return result
		else:
			self.lock.release()
			return node.DataHandler.query(self, id)

class Corrector(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)
		self.plans = {}

		node.Node.__init__(self, id, nodelocations, DataHandler, (self,), **kwargs)
		self.addEventOutput(event.DarkImagePublishEvent)
		self.addEventOutput(event.BrightImagePublishEvent)
		self.addEventOutput(event.ListPublishEvent)

		ids = ['normalized image data',]
		e = event.ListPublishEvent(self.ID(), ids)
		self.outputEvent(e)

		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		### Acquire Bright/Dark
		acqret = self.registerUIData('Image', 'binary')
		acqdark = self.registerUIMethod(self.uiAcquireDark, 'Acquire Dark', (), returnspec=acqret)
		acqbright = self.registerUIMethod(self.uiAcquireBright, 'Acquire Bright', (), returnspec=acqret)
		acqcorr = self.registerUIMethod(self.uiAcquireCorrected, 'Acquire Corrected', (), returnspec=acqret)

		self.navgdata = self.registerUIData('Frames to Average', 'integer', default=3, permissions='rw')


		self.fakeflag = self.registerUIData('Fake', 'boolean', default=False, permissions='rw')

		camconfigdata = self.cam.configUIData()
		prefs = self.registerUIContainer('Preferences', (self.navgdata, self.fakeflag, camconfigdata))

		argspec = (
			self.registerUIData('clip limits', 'array', default=()),
			self.registerUIData('bad rows', 'array', default=()),
			self.registerUIData('bad cols', 'array', default=())
		)
		setplan = self.registerUIMethod(self.uiSetPlanParams, 'Set Plan Params', argspec)

		ret = self.registerUIData('Current Plan', 'struct')
		getplan = self.registerUIMethod(self.uiGetPlanParams, 'Get Plan Params', (), returnspec=ret)
		plan = self.registerUISpec('Plan', (getplan, setplan))

		self.registerUISpec('Corrector', (plan, acqdark, acqbright, acqcorr, prefs, nodespec))

	def uiSetPlanParams(self, cliplimits, badrows, badcols):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		key = self.newPlan(camstate)
		newplan = self.plans[key]
		newplan['clip limits'] = cliplimits
		newplan['bad rows'] = badrows
		newplan['bad cols'] = badcols
		print 'updated %s to %s' % (key, self.plans[key])
		return ''

	def uiGetPlanParams(self):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		key = self.newPlan(camstate)
		plan = self.plans[key]
		plandict = {}
		plandict['key'] = key
		plandict['clip limits'] = plan['clip limits']
		plandict['bad rows'] = plan['bad rows']
		plandict['bad cols'] = plan['bad cols']
		print 'plandict', plandict
		return plandict

	def uiAcquireDark(self):
		dark = self.acquireReference(dark=True)
		print 'Dark Stats: %s' % (self.stats(dark),)
		mrcstr = Mrc.numeric_to_mrcstr(dark)
		return xmlbinlib.Binary(mrcstr)

	def uiAcquireBright(self):
		bright = self.acquireReference(dark=False)
		print 'Bright Stats: %s' % (self.stats(bright),)
		mrcstr = Mrc.numeric_to_mrcstr(bright)
		return xmlbinlib.Binary(mrcstr)

	def uiAcquireCorrected(self):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		self.cam.state(camstate)
		imdata = self.acquireCorrectedArray()
		print 'Corrected Stats: %s' % (self.stats(imdata),)
		mrcstr = Mrc.numeric_to_mrcstr(imdata)
		return xmlbinlib.Binary(mrcstr)

	def newPlan(self, camstate):
		key = self.planKey(camstate)
		if key not in self.plans:
			plan = CorrectorPlan(key)
			self.plans[key] = plan
		return key

	def updatePlan(self, plankey, itemkey, value):
		self.plans[plankey][itemkey] = value

	def planKey(self, camstate):
		'''
		make a string key from a camera state
		'''
		dim = camstate['dimension']
		bin = camstate['binning']
		off = camstate['offset']
		## ignore exposure time for now
		## exp = self.camstate['exposure time']

		tuplekey = (dim['x'],dim['y'],bin['x'],bin['y'],off['x'],off['y'])
		strtuplekey = map( lambda a: str(int(a)), tuplekey)
		strkey = string.join(strtuplekey, '_')
		return strkey

	def acquireSeries(self, n):
		series = []
		for i in range(n):
			print 'acquiring %s of %s' % (i+1, n)
			imagedata = self.cam.acquireCameraImageData()
			numimage = imagedata.content['image']
			series.append(numimage)
		return series

	def acquireReference(self, dark=False):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		tempcamstate = dict(camstate)
		if dark:
			tempcamstate['exposure time'] = 0.0
			typekey = 'dark'
			datatype = data.DarkImageData
			pubtype = event.DarkImagePublishEvent
		else:
			typekey = 'bright'
			datatype = data.BrightImageData
			pubtype = event.BrightImagePublishEvent

		self.cam.state(tempcamstate)

		navg = self.navgdata.get()
		series = self.acquireSeries(navg)
		ref = cameraimage.averageSeries(series)

		plankey = self.newPlan(camstate)

		self.plans[plankey][typekey] = ref

		imagedata = datatype(self.ID(), ref)
		self.publish(imagedata, pubtype)

		self.calc_norm(plankey)
		return ref

	def calc_norm(self, key):
		bright = self.plans[key]['bright']
		dark = self.plans[key]['dark']
		if bright is None:
			return
		if dark is None:
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
		self.plans[key]['norm'] = norm
		
	def acquireCorrectedArray(self):
		imagedata = self.acquireCorrectedImageData()
		return imagedata.content['image']

	def acquireCorrectedImageData(self):
		if self.fakeflag.get():
			camconfig = self.cam.config()
			camstate = camconfig['state']
			numimage = Mrc.mrc_to_numeric('fake.mrc')
			corrected = self.correct(numimage, camstate)
			return data.ImageData(self.ID, corrected)
		else:
			imagedata = self.cam.acquireCameraImageData()
			numimage = imagedata.content['image']
			camstate = imagedata.content['camera']
			corrected = self.correct(numimage, camstate)
			imagedata.content['image'] = corrected
			return imagedata

	def correct(self, original, camstate):
		'''
		this puts an image through a pipeline of corrections
		'''
		key = self.newPlan(camstate)
		print 'normalize'
		normalized = self.normalize(original, key)
		print 'touchup'
		touchedup = self.removeBadPixels(normalized, key)
		print 'clip'
		clipped = self.clip(touchedup, key)
		print 'done'
		return clipped

	def removeBadPixels(self, image, key):
		badrows = self.plans[key]['bad rows']
		badcols = self.plans[key]['bad cols']

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

	def clip(self, image, key):
		cliplimits = self.plans[key]['clip limits']
		if len(cliplimits) == 0:
			return image
		minclip,maxclip = cliplimits
		return Numeric.clip(image, minclip, maxclip)

	def normalize(self, raw, key):
		dark = self.plans[key]['dark']
		norm = self.plans[key]['norm']
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

class CorrectorPlan(object):
	def __init__(self, id):
		self.id = id
		self.plan = {}
		self.refs = {}
		self.reftypes = ('dark','bright','norm')

		## defaults
		self.plan['bad rows'] = ()
		self.plan['bad cols'] = ()
		self.plan['clip limits'] = ()

		## load existing state
		self.load()

		## load existing reference images
		for reftype in self.reftypes:
			self.loadRef(reftype)

	def __setitem__(self, key, value):
		if key in self.reftypes:
			self.refs[key] = value
			self.saveRef(key)
		else:
			self.plan[key] = value
			self.save()

	def __getitem__(self, key):
		if key in self.reftypes:
			return self.refs[key]
		else:
			return self.plan[key]

	def keys(self):
		return self.plan.keys() + self.refs.keys()

	def __hash__(self):
		return hash(self.id)

	def planFilename(self):
		return self.id + '.plan'

	def refFilename(self, reftype):
		return self.id + '_' + reftype + '.mrc'

	def save(self):
		filename = self.planFilename()
		f = open(filename, 'w')
		cPickle.dump(self.plan, f, 1)
		f.close()

	def load(self):
		filename = self.planFilename()
		try:
			f = open(filename, 'r')
		except IOError:
			print 'creating plan file: %s' % (filename,)
			self.save()
			return
		self.plan = cPickle.load(f)
		f.close()

	def saveRef(self, reftype):
		filename = self.refFilename(reftype)
		if self.refs[reftype] is not None:
			print 'saving %s' % (filename,)
			Mrc.numeric_to_mrc(self.refs[reftype], filename)

	def loadRef(self, reftype):
		filename = self.refFilename(reftype)
		self.refs[reftype] = Mrc.mrc_to_numeric(filename)


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
