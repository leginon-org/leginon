#!/usr/bin/env python

#pythonlib
import os
import numpy
#appion
from appionlib import appionLoop2
from appionlib import apDisplay

class LoopTester(appionLoop2.AppionLoop):
	'''
	This simple script just print the image filename. It can
	be used to test appionLoop and or simply propogate donedict.
	'''

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "test"

	#======================
	def processImage(self, imgdata):
		apDisplay.printMsg('processing %s' % (imgdata['filename']))

	#======================
	def setupParserOptions(self):
		return

	#======================
	def checkConflicts(self):
		return

	#======================
	def commitToDatabase(self, imgdata):
		return

if __name__ == '__main__':
	testLoop = LoopTester()
	testLoop.run()

