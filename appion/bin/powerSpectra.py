#!/usr/bin/env python

#pythonlib
import os
import numpy
#appion
from appionlib import appionLoop2
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apFile
from pyami import imagefun

class powerSpectraLoop(appionLoop2.AppionLoop):
	#=====================
	def setProcessingDirName(self):
		self.processdirname = "ctf"

	#======================
	def processImage(self, imgdata):
		stackedname = os.path.join(self.params['rundir'], imgdata['filename']+"power.jpg")

		if os.path.isfile(stackedname) and apFile.fileSize(stackedname) > 100:
			return

		### make the power spectra
		powerspectra = imagefun.power(imgdata['image'], mask_radius=1.0, thresh=4)
		binpowerspectra = imagefun.bin2(powerspectra, self.params['bin'])
		del powerspectra
		if self.params['hp'] is True:
			binpowerspectra = apImage.fermiHighPassFilter(binpowerspectra, apix=4.0, radius=2000.0)
		binpowerspectra = apImage.normStdevMed(binpowerspectra, size=5) 
		binpowerspectra = apImage.pixelLimitFilter(binpowerspectra, pixlimit=4)
		binpowerspectra = apImage.normRange(binpowerspectra)

		### filter the image
		imagedata = imagefun.bin2(imgdata['image'], self.params['bin'])
		del imgdata['image']
		imagedata = apImage.normStdevMed(imagedata, size=5) 
		imagedata = apImage.pixelLimitFilter(imagedata, pixlimit=2)
		imagedata = apImage.normRange(imagedata)

		### write to file
		stacked = numpy.hstack([imagedata, binpowerspectra])
		del imagedata, binpowerspectra
		apImage.arrayToJpeg(stacked, stackedname)

	#======================
	def setupParserOptions(self):
		self.parser.add_option("--bin", dest="bin", type="int", default=4,
			help="Bin the images by X")
		self.parser.add_option("--no-hp", dest="hp", default=True,
			action="store_false", help="Do not use high pass filter")
		return

	#======================
	def checkConflicts(self):
		return

	#======================
	def commitToDatabase(self, imgdata):
		return

if __name__ == '__main__':
	powerLoop = powerSpectraLoop()
	powerLoop.run()

