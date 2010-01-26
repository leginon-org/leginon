#!/usr/bin/python -O

#pythonlib
import os
import sys
import re
import time
#appion
from appionlib import appionLoop2
from appionlib import appionScript
from appionlib import apImage
from appionlib import apFile
from appionlib import apDisplay
from appionlib import apDatabase

class FilterLoop(appionLoop2.AppionLoop):
	#######################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################
	# see also appionLoop.py

	#=====================
	def setRunDir(self):
		if self.params['sessionname'] is not None:
			#auto set the output directory
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
			path = os.path.abspath(sessiondata['image path'])
			path = re.sub("leginon","appion",path)
			path = re.sub("/rawdata","",path)
			path = os.path.join(path, self.processdirname, self.params['runname'])
			self.params['rundir'] = path

	#=====================
	def setupParserOptions(self):
		"""
		put in any additional parser options
		"""
		apDisplay.printError("you did not create a 'setupParserOptions' function in your script")
		raise NotImplementedError()

	#=====================
	def checkConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		apDisplay.printError("you did not create a 'checkConflicts' function in your script")
		raise NotImplementedError()

	#=====================
	def preLoopFunctions(self):
		"""
		do something before starting the loop
		"""
		return

	#=====================
	def processImage(self, imgdata, filtarray):
		"""
		this is the main component of the script
		where all the processing is done
		inputs:
			imgdata, sinedon dictionary with image info
			filtarray, filtered array ready for processing
		"""
		apDisplay.printError("you did not create a 'processImage' function in your script")
		raise NotImplementedError()

	#=====================
	def commitToDatabase(self, imgdata):
		"""
		put in any additional commit parameters
		"""
		apDisplay.printError("you did not create a 'commitToDatabase' function in your script")
		raise NotImplementedError()

	#=====================
	def postLoopFunctions(self):
		"""
		do something after finishing the loop
		"""
		return

	#################################################
	#### ITEMS BELOW ARE NOT USUALLY OVERWRITTEN ####
	#################################################

	#=====================
	def loopProcessImage(self, imgdata):
		"""
		setup like this to override things
		"""
		self.filtimgpath = os.path.join(self.params['rundir'], imgdata['filename']+'.dwn.mrc')

		if os.path.isfile(self.filtimgpath):
			apDisplay.printMsg("reading filtered image from mrc file")
			self.filtarray = apImage.mrcToArray(self.filtimgpath, msg=False)
		else:
			self.filtarray = apImage.preProcessImage(imgdata['image'], apix=self.params['apix'], params=self.params)
			apImage.arrayToMrc(self.filtarray, self.filtimgpath)

		peaktree = self.processImage(imgdata, self.filtarray)

		return peaktree

	#=====================
	def setupGlobalParserOptions(self):
		"""
		set the input parameters
		"""
		appionLoop2.AppionLoop.setupGlobalParserOptions(self)
		### Input value options
		self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="float",
			help="Low pass filter radius in Angstroms", metavar="FLOAT")
		self.parser.add_option("--highpass", "--hp", dest="highpass", type="float",
			help="High pass filter radius in Angstroms", metavar="FLOAT")
		self.parser.add_option("--median", dest="median", type="int",
			help="Median filter radius in Pixels", metavar="INT")
		self.parser.add_option("--pixlimit", dest="pixlimit", type="float",
			help="Limit pixel values to within <pixlimit> standard deviations", metavar="FLOAT")
		self.parser.add_option("--bin", "--shrink", "--binby", dest="bin", type="int", default=4,
			help="Bin the image", metavar="INT")
		### True / False options
		self.parser.add_option("--invert", dest="invert", default=False,
			action="store_true", help="Invert image density before processing")
		self.parser.add_option("--planereg", dest="planereg", default=False,
			action="store_true", help="Fit a 2d plane regression to the data and subtract")
		self.parser.add_option("--keepall", dest="keepall", default=False,
			action="store_true", help="Do not delete .dwn.mrc files when finishing")

	#=====================
	def checkGlobalConflicts(self):
		"""
		put in any conflicting parameters
		"""
		self.proct0 = time.time()
		appionLoop2.AppionLoop.checkGlobalConflicts(self)
		return

	#=====================
	def close(self):
		"""
		hack to override appionScript close
		"""
		apDisplay.printMsg("Waiting 20 seconds for threads to complete")
		time.sleep(20)
		if self.params['keepall'] is False and self.params['limit'] is None:
			pattern = os.path.join(self.params['rundir'], self.params['sessionname']+'*.dwn.mrc')
			apFile.removeFilePattern(pattern)
		appionScript.AppionScript.close(self)

#=====================
#=====================
#=====================
class MiniFilterLoop(FilterLoop):
	def setupParserOptions(self):
		return
	def checkConflicts(self):
		return
	def commitToDatabase(self):
		return
	def processImage(self, imgdict, filtarray):
		from pyami import mrc
		mrc.write(filtarray, apDisplay.short(imgdict['filename'])+"_sm.mrc")

#=====================
#=====================
#=====================
if __name__ == '__main__':
	miniLoop = MiniFilterLoop()
	miniLoop.run()

