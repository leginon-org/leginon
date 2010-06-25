#!/usr/bin/env python

#pythonlib
import os
import sys
import re
#appion
from appionlib import appionLoop2
from appionlib import apFindEM
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apPeaks
from appionlib import apParticle
from appionlib import apDefocalPairs
#legacy
#import apViewIt
#import selexonFunctions  as sf1

class AlignDefocLoop(appionLoop2.AppionLoop):

	#======================
	def processImage(self, imgdata):
		self.sibling, self.shiftpeak = apDefocalPairs.getShiftFromImage(imgdata, self.params['sessionname'])

	#======================
	def setProcessingDirName(self):
		self.processdirname = "defocalpairs"

	#======================
	def commitToDatabase(self, imgdata):
		apDefocalPairs.insertShift(imgdata, self.sibling, self.shiftpeak)

	#======================
	def checkConflicts(self):
		return

	#======================
	def setupParserOptions(self):
		self.parser.add_option("--lp", dest="lp", type="int", default=30,
			help="Low pass filter value, default=30", metavar="#")
	

if __name__ == '__main__':
	imgLoop = AlignDefocLoop()
	imgLoop.run()

