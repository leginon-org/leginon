#!/usr/bin/env python
import node
import Numeric
import cameraimage
import data

### these should go in a stats node or module


class Corrector(node.Node):
	def __init__(self, id, nodelocations):

		self.dark = None
		self.bright = None
		self.norm = None

		node.Node.__init__(self, id, nodelocations)

	def main(self):
		pass

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		### Acquire Bright/Dark
		acqdark = self.registerUIMethod(self.acquireDark, 'Dark', ())
		acqbright = self.registerUIMethod(self.acquireBright, 'Bright', ())
		acq = self.registerUIContainer('Acquire References', (acqdark, acqbright))

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
		self.camdata = self.registerUIData('Camera', 'struct', default=camstate)

		self.navgdata = self.registerUIData('Frames to Average', 'integer', default=3)

		self.registerUISpec('Corrector', (acq, self.camdata, nodespec))

	def acquireSeries(self, n):
		series = []
		for i in n:
			imagedata = self.researchByDataID('image data')
			numimage = imagedata.content['image data']
			series.append(numimage)
		return series

	def acquireBright(self):
		camstate = self.camdata.get()
		camdata = data.EMData('camera', camstate)
		self.publishRemote(camdata)
		navg = self.navgdata.get()
		series = self.acquireSeries(navg)
		self.bright = self.averageSeries(series)
		self.calc_norm()

	def acquireDark(self):
		camstate = self.camdata.get()
		camstate['exposure time'] = 0.0
		camdata = data.EMData('camera', camstate)
		self.publishRemote(camdata)
		navg = self.navgdata.get()
		series = self.acquireSeries(navg)
		self.dark = self.averageSeries(series)
		self.calc_norm()

	def calc_norm(self):
		if self.bright and self.dark:
			norm = self.bright - self.dark
			## there may be a better norm than this
			normavg = cameraimage.mean(norm)
			print "normavg", normavg
			self.norm = normavg / norm
			print "self.norm avg", cameraimage.mean(self.norm)

	def correct(self, raw):
		if self.dark is not None and self.norm is not None:
			return (raw - self.dark) * self.norm
		else:
			return None


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
