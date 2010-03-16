#!/usr/bin/env python

#pythonlib
import os
import numpy
#appion
from appionlib import appionLoop2
from appionlib import apImage
from appionlib import apDisplay
from pyami import imagefun

class powerSpectraLoop(appionLoop2.AppionLoop):
	#=====================
	def setProcessingDirName(self):
		self.processdirname = "ctf"

	#======================
	def processImage(self, imgdata):
		### make the power spectra
		powerspectra = imagefun.power(imgdata['image'], mask_radius=3.0, thresh=3)
		powerspectra = imagefun.bin2(powerspectra, self.params['bin'])
		imagedata = imagefun.bin2(imgdata['image'], self.params['bin'])
		stacked = numpy.hstack(imagedata, powerspectra)
		stackedname = os.path.join(self.params['rundir'], imgdata['filename']+"power.jpg")
		apImage.arrayToJpeg(stacked, stackedname)

	#======================
	def setupParserOptions(self):
		self.parser.add_option("--bin", dest="bin", type="int", default=4,
			help="Bin the images by X")
		return

	#======================
	def checkConflicts(self):
		return


if __name__ == '__main__':
	powerLoop = powerSpectraLoop()
	powerLoop.run()

