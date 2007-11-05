#!/usr/bin/python -O

#pythonlib
import os
import sys
import re
#appion
import particleLoop
import apImage
import apDisplay
import apDatabase
import appionData
import apPeaks
import apParticle
import apDog
#legacy
#import selexonFunctions  as sf1

class dogPicker(particleLoop.ParticleLoop):

	def particleParamConflicts(self):
		if self.params['lp'] > 0:
			apDisplay.printWarning("lowpass filter value greater than zero; will ignore for maps and only use it for summary images")
		if self.params['hp'] > 0:
			apDisplay.printWarning("highpass filter value greater than zero; will ignore for maps and only use it for summary images")
		#if self.params['kfactor'] is not None and self.params['numslices'] is not None:
		#	apDisplay.printError("only one of 'kfactor' or 'numslices' can be defined")
		if self.params['sizerange'] is not None and self.params['sizerange'] >= 1.95*self.params['diam']:
			apDisplay.printError("size range has be less than twice the diameter")
		return

	def particleProcessImage(self, imgdata):
		imgarray = imgdata['image']
		#you are not allowed to have highpass and lowpass values
		imgarray  = apImage.preProcessImage(imgarray, params=self.params, lowpass=0, highpass=0)
		dogarrays = apDog.diffOfGaussParam(imgarray, self.params)
		peaktree  = apPeaks.findPeaks(imgdata, dogarrays, self.params, maptype="dogmap")
		return peaktree

	def getParticleParamsData(self):
		dogparamq = appionData.ApDogParamsData()
		dogparamq['kfactor'] = self.params['kfactor']
		dogparamq['size_range'] = self.params['sizerange']
		dogparamq['num_slices'] = self.params['numslices']
		return dogparamq

	def particleDefaultParams(self):
		self.params['mapdir'] = "dogmaps"
		self.params['kfactor'] = 1.2
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
				self.params['sizerange']=float(elements[1])
			else:
				apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

if __name__ == '__main__':
	imgLoop = dogPicker()
	imgLoop.run()

