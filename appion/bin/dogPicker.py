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
		imgarray = apImage.diffOfGaussParam(imgarray, self.params)
		imgarray = apImage.normStdev(imgarray)/4.0
		peaktree  = apPeaks.findPeaks(imgdata, [imgarray,], self.params, maptype="dogmap")
		return peaktree

	def particleCommitToDatabase(self, imgdata):
		expid = int(imgdata['session'].dbid)
		apDog.insertDogParams(self.params, expid)
#		apDog.insertDogParamsREFLEGINON(self.params, imgdata['session'])
		return

	def particleDefaultParams(self):
		self.params['mapdir']="dogmaps"

	def particleParseParams(self, args):
		for arg in args:
			elements = arg.split('=')
			elements[0] = elements[0].lower()
			if (elements[0]=='invert'):
				self.params['invert']=True
			else:
				apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

if __name__ == '__main__':
	imgLoop = dogPicker()
	imgLoop.run()

