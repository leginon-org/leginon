#!/usr/bin/env python

#pythonlib
import os
import math
#appion
from appionlib import filterLoop
from appionlib import apImage
#leginon
import pyami.jpg as jpg
from pyami import imagefun

class MrcToJpgLoop(filterLoop.FilterLoop):
	def loopProcessImage(self, imgdata):
		peaktree = self.processImage(imgdata, imgdata['image'])
		return peaktree

	def checkConflicts(self):
		return

	def commitToDatabase(self,imagedata):
		return

	def setupParserOptions(self):
		"""
		Writes a maximal 'imgsize' jpg image
		default is 
			min = mean - 3 * stdev
			max = mean + 3 * stdev
		if params['min'] > params['max'], use the image min and max to scale.
		Otherwise min and max are specified by params['min'],params['max']
		"""
		self.parser.add_option("--min", dest="min", type="float",
			help="Minimum pixel value", metavar="FLOAT")
		self.parser.add_option("--max", dest="max", type="float",
			help="Maximum pixel value", metavar="FLOAT")
		self.parser.add_option("--stdval", dest="stdval", type="float", default=5,
			help="standard deviation multiplier (default=5)")
		self.parser.add_option("--imgsize", dest="imgsize", type="int", default=512,
			help="Maximum image size", metavar="INT")
		self.parser.add_option("--quality", dest="quality", type="int", default=70,
			help="Quality of the final jpeg images", metavar="INT")
		self.parser.add_option("--fft", dest="fft", action="store_true",
			help="Create jpgs of the FFT")

	def processImage(self, imgdata, filtarray):			
		#Ignore array filter
		array = imgdata['image']
		imgmax = self.params['max']
		imgmin = self.params['min']

		outfile = os.path.join(self.params['rundir'], imgdata['filename'])
		if self.params['fft'] is True:
			outfile+=".fft"
		outfile+=".jpg"
		if imgmin > imgmax:
			imgmax = array.max()
			imgmin = array.min()
		shape = array.shape
		maxdim = max(shape)
		if self.params['fft'] is True:
			## fft's are binned by 2
			array = imagefun.bin(array,2)
			array = imagefun.power(array)
			maxdim/=2
		bin = int(math.ceil(float(maxdim/self.params['imgsize'])))	
		array = imagefun.bin(array,bin)
		jpg.write(array, outfile, min=imgmin, max=imgmax, quality=self.params['quality'], stdval=self.params['stdval'])

if __name__ == '__main__':
	imgLoop = MrcToJpgLoop()
	imgLoop.run()

