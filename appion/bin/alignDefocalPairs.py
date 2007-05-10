#!/usr/bin/python -O

#pythonlib
import os
import sys
import re
#appion
import appionLoop
import apFindEM
import apImage
import apDisplay
import apTemplate
import apDatabase
import apPeaks
import apParticle
import apDefocalPairs
#legacy
#import apViewIt
#import selexonFunctions  as sf1

class TemplateCorrelationLoop(appionLoop.AppionLoop):
	def processImage(self, imgdata):
		self.sibling, self.shiftpeak = apDefocalPairs.getShiftFromImage(imgdata)

	def setProcessingDirName(self):
		self.processdirname = "defocalpairs"

	def commitToDatabase(self, imgdata):
		apDefocalPairs.insertShift(imgdata, self.sibling, self.shiftpeak)

	def specialDefaultParams(self):
		self.params['lp']=30

	def specialParseParams(self,args):
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			#print elements
			if (elements[0]=='lp'):
				self.params['lp']=float(elements[1])

if __name__ == '__main__':
	imgLoop = TemplateCorrelationLoop()
	imgLoop.run()

