#!/usr/bin/env python

#pythonlib
import os
import sys
import re
import time
#appion
import particleLoop2
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apPeaks
from appionlib import apParticle
from appionlib import apDog
#legacy
#import selexonFunctions  as sf1

class dogPicker(particleLoop2.ParticleLoop):
	#================
	def setupParserOptions(self):
		### Input value options
		self.parser.add_option("--kfactor", dest="kfactor", type="float", default=1.2,
			help="K-factor for the DoG picking algorithm", metavar="FLOAT")
		self.parser.add_option("--numslices", dest="numslices", type="int",
			help="Number of slices (different sizes) to pick", metavar="FLOAT")
		self.parser.add_option("--sizerange", dest="sizerange", type="float",
			help="Range in size of particles to find", metavar="FLOAT")

	#================
	def checkConflicts(self):
		if self.params['lowpass'] > 0:
			apDisplay.printWarning("lowpass filter value greater than zero; will ignore")
		if self.params['highpass'] > 0:
			apDisplay.printWarning("highpass filter value greater than zero; will ignore")
		self.params['highpass'] = None
		self.params['lowpass'] = None
		#if self.params['kfactor'] is not None and self.params['numslices'] is not None:
		#	apDisplay.printError("only one of 'kfactor' or 'numslices' can be defined")
		if self.params['numslices'] is not None and self.params['numslices'] >= 15:
			apDisplay.printError("too many slices defined by numslices, should be more like 2-6")
		if self.params['sizerange'] is not None and self.params['sizerange'] >= 1.95*self.params['diam']:
			apDisplay.printError("size range has be less than twice the diameter")
		return

	#================
	def processImage(self, imgdata, filtarray):
		imgarray = imgdata['image']



		looptdiff = time.time()-self.proct0
		self.proct0 = time.time()
		dogarrays = apDog.diffOfGaussParam(filtarray, self.params)
		proctdiff = time.time()-self.proct0
		f = open("dog_image_timing.dat", "a")
		datstr = "%d\t%.5f\t%.5f\n"%(self.stats['count'], proctdiff, looptdiff)
		f.write(datstr)
		f.close()



		apDisplay.printMsg("finished DoG filter")
		peaktree  = apPeaks.findPeaks(imgdata, dogarrays, self.params, maptype="dogmap")
		return peaktree

	#================
	def getParticleParamsData(self):
		dogparamq = appiondata.ApDogParamsData()
		dogparamq['kfactor'] = self.params['kfactor']
		dogparamq['size_range'] = self.params['sizerange']
		dogparamq['num_slices'] = self.params['numslices']
		return dogparamq

	#================
	def commitToDatabase(self, imgdata, rundata):
		return

if __name__ == '__main__':
	imgLoop = dogPicker()
	imgLoop.run()


