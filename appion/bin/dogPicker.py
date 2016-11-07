#!/usr/bin/env python

#pythonlib
import time
#appion
from appionlib import apDog
from appionlib import apParam
from appionlib import apPeaks
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import particleLoop2

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
		if self.params['numslices'] is not None and self.params['numslices'] >= 15:
			apDisplay.printError("too many slices defined by numslices, should be more like 2-6")
		if self.params['diam'] < 1:
			apDisplay.printError("difference of Gaussian; radius = 0")
		if self.params['sizerange'] is not None and self.params['sizerange'] > 2*self.params['diam']-3:
			apDisplay.printError("size range %d has be less than twice the diameter %d"
				%(self.params['sizerange'], 2*self.params['diam']-3))
		### get number of processors:
		nproc = apParam.getNumProcessors()
		if not self.params['nproc']:
			self.params['nproc'] = nproc
		elif nproc < self.params['nproc']:
			apDisplay.printWarning("Limiting number of processors to the %i that are available"%nproc)
			self.params['nproc'] = nproc
		return

	#================
	def processImage(self, imgdata, filtarray):
		dogarrays = apDog.diffOfGaussParam(filtarray, self.params)
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


