#!/usr/bin/env python
import node
import Numeric
import cameraimage
reload(cameraimage)
import data, event
import shelve
import threading
from Mrc import mrc_to_numeric, numeric_to_mrc

### these should go in a stats node or module

class DataHandler(node.DataHandler):
	def __init__(self, id, inode):
		self.node = inode
		node.DataHandler.__init__(self, id)
	# acq/rel twice on normal data
	def query(self, id):
		self.lock.acquire()
		if id == 'normalzed image data':
			result = self.node.acquireCorrectedImageData()
			self.lock.release()
			return result
		elif id == 'fake normalized image data':
			result = self.node.acquireCorrectedFakeImageData()
			self.lock.release()
			return result
		else:
			self.lock.release()
			return node.DataHandler.query(self, id)

class Corrector(node.Node):
	def __init__(self, id, nodelocations):

		self.refs = {}

		node.Node.__init__(self, id, nodelocations, DataHandler, (self,))
		self.addEventInput(event.ImageAcquireEvent, self.acquireCorrected)
		self.addEventOutput(event.ImagePublishEvent)
		self.addEventOutput(event.DarkImagePublishEvent)
		self.addEventOutput(event.BrightImagePublishEvent)
		self.addEventOutput(event.ListPublishEvent)

		ids = ['normalized image data', 'fake normalized image data']
		e = event.ListPublishEvent(self.ID(), ids)
		self.outputEvent(e)

		self.start()

	def main(self):
		pass

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		### Acquire Bright/Dark
		acqdark = self.registerUIMethod(self.acquireDark, 'Dark', ())
		acqbright = self.registerUIMethod(self.acquireBright, 'Bright', ())
		acqcorr = self.registerUIMethod(self.acquireCorrected, 'Corrected', ())
		acq = self.registerUIContainer('Acquire References', (acqdark, acqbright, acqcorr))

		### Camera State Data Spec
		defaultsize = (512,512)
		camerasize = (2048,2048)
		offset = cameraimage.centerOffset(camerasize,defaultsize)
		camstate = {
			'exposure time': 500,
			'binning': {'x':1, 'y':1},
			'dimension': {'x':defaultsize[0], 'y':defaultsize[1]},
			'offset': {'x': offset[0], 'y': offset[1]}
		}
		self.defaultcamstate = camstate
		self.camdata = self.registerUIData('Camera', 'struct', default=camstate)

		self.navgdata = self.registerUIData('Frames to Average', 'integer', default=3, permissions='rw')

		self.registerUISpec('Corrector', (acq, self.navgdata, self.camdata, nodespec))

	def saveRefs(self, filename, key):
		strkey = str(key)
		s = shelve.open(filename)
		try:
			s[strkey] = self.refs[key]
		except KeyError:
			pass
		s.close()

	def loadRefs(self, filename, key):
		strkey = str(key)
		s = shelve.open(filename)
		print 'trying to find %s in refs file' % strkey
		try:
			self.refs[key] = s[strkey]
			print 'got %s in refs file' % (key,)
		except KeyError:
			pass
		s.close()

	def acquireSeries(self, n):
		series = []
		for i in range(n):
			print 'acquiring %s of %s' % (i+1, n)
			imagedata = self.researchByDataID('image data')
			numimage = imagedata.content['image data']
			series.append(numimage)
		return series

	def acquireBright(self):
		camstate = dict(self.camdata.get())
		camdata = data.EMData('camera', camstate)
		self.publishRemote(camdata)
		navg = self.navgdata.get()
		series = self.acquireSeries(navg)
		bright = cameraimage.averageSeries(series)

		key = self.cameraKey(camstate)
		if key not in self.refs:
			self.refs[key] = {'dark':None,'bright':None,'norm':None}
		self.refs[key]['bright'] = bright

		imagedata = data.BrightImageData(self.ID(), bright)
		self.publish(imagedata, event.BrightImagePublishEvent)

		print 'bright stats', self.stats(bright)
		self.calc_norm(key)
		return ''

	def acquireDark(self):
		camstate = dict(self.camdata.get())
		camstate['exposure time'] = 0.0
		camdata = data.EMData('camera', camstate)
		self.publishRemote(camdata)
		navg = self.navgdata.get()
		series = self.acquireSeries(navg)
		dark = cameraimage.averageSeries(series)

		key = self.cameraKey(camstate)
		if key not in self.refs:
			self.refs[key] = {'dark':None,'bright':None,'norm':None}
		self.refs[key]['dark'] = dark

		imagedata = data.DarkImageData(self.ID(), dark)
		self.publish(imagedata, event.DarkImagePublishEvent)

		print 'dark stats', self.stats(dark)
		self.calc_norm(key)
		return ''

	def acquireCorrectedImageData(self):
		camdata = self.researchByDataID('camera')
		camstate = camdata.content
		numimage = camstate['image data']
		#binning = self.researchByDataID('binning').content['binning']
		key = self.cameraKey(camstate)
		corrected = self.correct(numimage, key)
		print 'corrected done'
		return data.ImageData(self.ID(), corrected)

	def acquireCorrected(self, ievent=None):
		correctdata = self.acquireCorrectedImageData()
		print 'publishing corrected'
		self.publish(correctdata, event.ImagePublishEvent)
		print 'done pub correct'
		return ''

	def acquireCorrectedFakeImageData(self):
		numimage = mrc_to_numeric('test1.mrc')
		camstate = self.defaultcamstate
		#binning = self.researchByDataID('binning').content['binning']
		key = self.cameraKey(camstate)
		corrected = self.correct(numimage, key)
		numeric_to_mrc(corrected, 'corr.mrc')
		print 'corrected done'
		return data.ImageData(self.ID(), corrected)

	def acquireCorrectedFake(self, ievent=None):
		correctdata = self.acquireCorrectedFakeImageData()
		print 'publishing corrected'
		self.publish(correctdata, event.ImagePublishEvent)
		print 'done pub correct'
		return ''

	def stats(self, im):
		mean = cameraimage.mean(im)
		print 'mean', mean
		stdev = cameraimage.stdev(im)
		print 'stdev', stdev
		mn = cameraimage.min(im)
		print 'mn', mn
		mx = cameraimage.max(im)
		print 'mx', mx
		return {'mean':mean,'stdev':stdev,'min':mn,'max':mx}

	def calc_norm(self, key):
		if key not in self.refs:
			self.refs[key] = {'dark':None,'bright':None,'norm':None}
		bright = self.refs[key]['bright']
		dark = self.refs[key]['dark']
		if bright is not None and dark is not None:
			norm = bright - dark
			## there may be a better norm than this
			normavg = cameraimage.mean(norm)

			# division may result infinity or zero division
			# so make sure there are no zeros in norm
			norm = Numeric.clip(norm, 1.0, cameraimage.inf)
			norm = normavg / norm
			self.refs[key]['norm'] = norm
			
			print 'saving refs'
			self.saveRefs('refs', key)

	def correct(self, raw, key):
		if key not in self.refs:
			print 'loading refs'
			self.loadRefs('refs', key)
		if key not in self.refs:
			print 'no refs, no correction'
			return raw

		refs = self.refs[key]
		dark = refs['dark']
		norm = refs['norm']

		if dark is not None and norm is not None:
			diff = raw - dark
			## this may result in some infinity values
			r = diff * norm
			return r
		else:
			return raw

	def cameraKey(self, camstate):
		'''
		make a hash key from a camera state
		'''
		dim = camstate['dimension']
		bin = camstate['binning']
		off = camstate['offset']
		## ignore exposure time for now
		##camstate['exposure time']
		key = (dim['x'],dim['y'],bin['x'],bin['y'],off['x'],off['y'])
		return key

if __name__ == '__main__':
	from Numeric import *
	from Mrc import *
	from ImageViewer import ImageViewer

	print 'reading darks'
	dark1 = mrc_to_numeric('/home/pulokas/test_images/dark1.mrc')
	dark2 = mrc_to_numeric('/home/pulokas/test_images/dark2.mrc')
	print 'averaging darks'
	dark = numeric_series_average( (dark1,dark2) )
	print 'reading brights'
	bright1 = mrc_to_numeric('/home/pulokas/test_images/bright1.mrc')
	bright2 = mrc_to_numeric('/home/pulokas/test_images/bright2.mrc')
	print 'averaging brights'
	bright = numeric_series_average( (bright1,bright2) )
	print 'reading raw'
	raw = mrc_to_numeric('/home/pulokas/test_images/raw4.mrc')

	print 'setting up corrector'
	corrector = FlatCorrector()
	corrector.set_dark(dark)
	corrector.set_bright(bright)
	print 'correcting'
	good = corrector.correct(raw)

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
