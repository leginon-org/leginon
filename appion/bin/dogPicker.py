#!/usr/bin/python -O

#pythonlib
import os
import sys
import re
#appion
import particleLoop
import apImage
import apDisplay
import apTemplate
import apDatabase
import appionData
import apPeaks
import apParticle
import apDog
#legacy
#import selexonFunctions  as sf1

class dogPicker(particleLoop.ParticleLoop):

	def preLoopFunctions(self):
		if self.params['lp'] > 0:
			apDisplay.printWarning("lowpass filter value greater than zero; not a good thing for dogpicker")

	def particleProcessImage(self, imgdata):
		imgarray = imgdata['image']
		imgarray = apImage.preProcessImage(imgarray, params=self.params, lowpass=0)
		dogarray = apImage.diffOfGaussParam(imgarray, self.params)
		dogarray = apImage.normStdev(dogarray)/4.0
		peaktree  = apPeaks.findPeaks(imgdata, [dogarray,], self.params, maptype="dogmap")
		return peaktree

	def getParticleParamsData(self):
		dogparamq = appionData.ApDogParamsData()
		dogparamq['kfactor'] = self.params['kfactor']
		#dogparamq['size_range'] = self.params['sizerange']
		#dogparamq['num_slices'] = self.params['numslices']
		return dogparamq

	def particleDefaultParams(self):
		self.params['mapdir']="dogmaps"
		self.params['kfactor']=1.2
		self.params['numslices'] = None
		self.params['sizerange'] = None

	def particleParseParams(self, args):
		for arg in args:
			elements = arg.split('=')
			elements[0] = elements[0].lower()
			if (elements[0]=='kfactor'):
				self.params['kfactor']=float(elements[1])
			elif (elements[0]=='numslices'):
				self.params['numslices']=int(elements[1])
			elif (elements[0]=='sizerange'):
				self.params['sizerange']=int(elements[1])
			else:
				apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

if __name__ == '__main__':
	imgLoop = dogPicker()
	imgLoop.run()

