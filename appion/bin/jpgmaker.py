#!/usr/bin/env python

#pythonlib
import os
#appion
import filterLoop
import apImage
#leginon
import pyami.jpg as jpg

class MrcToJpgLoop(filterLoop.FilterLoop):
	def checkConflicts(self):
		return

	def commitToDatabase(self,imagedata):
		return

	def setupParserOptions(self):
		"""
		Writes a maximal 512x512 jpg image
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
		self.parser.add_option("--quality", dest="quality", type="int", default=70,
			help="Quality of the final jpeg images", metavar="INT")

	def processImage(self, imgdata, filtarray):			
		imgmax = self.params['max']
		imgmin = self.params['min']

		outfile = os.path.join(self.params['rundir'], imgdata['filename']+".jpg")
		if imgmin > imgmax:
			imgmax = filtarray.max()
			imgmin = filtarray.min()
		jpg.write(filtarray, outfile, min=imgmin, max=imgmax, quality=self.params['quality'])

if __name__ == '__main__':
	imgLoop = MrcToJpgLoop()
	imgLoop.run()

