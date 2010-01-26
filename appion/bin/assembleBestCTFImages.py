#!/usr/bin/env python

#pythonlib
import os
import sys
import re
import math
import cPickle
import time
import shutil
#appion
from appionlib import appionLoop2
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apCtf
from appionlib import apParam

class aceLoop(appionLoop2.AppionLoop):

	#======================
	def setProcessingDirName(self):
		self.processdirname = "bestace"
		
	#======================
	def postLoopFunctions(self):
		apCtf.printCtfSummary(self.params)

	#======================
	def reprocessImage(self, imgdata):
		"""
		Returns 
		True, if an image should be reprocessed
		False, if an image was processed and should NOT be reprocessed
		None, if image has not yet been processed 
		e.g. a confidence less than 80%
		"""
		if self.params['reprocess'] is None:
			return None
		ctfvalue, conf = apCtf.getBestCtfValueForImage(imgdata)
		if ctfvalue is None:
			return None

		if conf > self.params['reprocess']:
			return False
		else:
			return True

	#======================
	def processImage(self, imgdata):
		ctfvalue, conf = apCtf.getBestCtfValueForImage(imgdata)
		if ctfvalue is None:
			return None
		defocus = ctfvalue['defocus1']
		acepath = ctfvalue['acerun']['path']['path']
		opimgpath = os.path.join(acepath,"opimages")
		#print opimgpath
		#for i,v in ctfvalue.items():
		#	print i,v

		if conf < 0.5:
			confdir = "doubtful"
		elif conf > 0.8:
			confdir = "probable"
		else:
			confdir = "questionable"

		defocusdir = "defocus"+str(int(math.floor(defocus*-1e6)))
		apParam.createDirectory(os.path.join(self.params['opimage1'], defocusdir), warning=False)
		apParam.createDirectory(os.path.join(self.params['opimage2'], defocusdir), warning=False)

		#copy first file
		opfile = os.path.join(opimgpath, ctfvalue['graph1'])
		if os.path.isfile(opfile):
			shutil.copyfile(opfile, os.path.join(self.params['opimage1'], "all", ctfvalue['graph1']))
			shutil.copyfile(opfile, os.path.join(self.params['opimage1'], confdir, ctfvalue['graph1']))
			shutil.copyfile(opfile, os.path.join(self.params['opimage1'], defocusdir, ctfvalue['graph1']))
		else:
			apDisplay.printWarning("could not find opimage: "+opfile)

		#copy second file
		opfile = os.path.join(opimgpath, ctfvalue['graph2'])
		if os.path.isfile(opfile):
			shutil.copyfile(opfile, os.path.join(self.params['opimage2'], "all", ctfvalue['graph2']))
			shutil.copyfile(opfile, os.path.join(self.params['opimage2'], confdir, ctfvalue['graph2']))
			shutil.copyfile(opfile, os.path.join(self.params['opimage2'], defocusdir, ctfvalue['graph2']))
		else:
			apDisplay.printWarning("could not find opimage: "+opfile)

	#======================
	def commitToDatabase(self, imgdata):
		return

	#======================
	def preLoopFunctions(self):
		self.params['opimage1'] = os.path.join(self.params['rundir'],"opimages1")
		self.params['opimage2'] = os.path.join(self.params['rundir'],"opimages2")
		self.params['tempdir'] = os.path.join(self.params['rundir'],"tempdir")
		apParam.createDirectory(self.params['opimage1'], warning=False)
		apParam.createDirectory(self.params['opimage2'], warning=False)
		apParam.createDirectory(self.params['tempdir'], warning=False)
		for p in ("doubtful", "questionable", "probable", "all"):
			path = os.path.join(self.params['opimage1'], p)
			apParam.createDirectory(path, warning=False)
			path = os.path.join(self.params['opimage2'], p)
			apParam.createDirectory(path, warning=False)

	#======================
	def setupParserOptions(self):		
		return

	#======================
	def checkConflicts(self):
		return

	#======================
	def specialParamConflicts(self):
		return


if __name__ == '__main__':
	imgLoop = aceLoop()
	imgLoop.run()

