#!/usr/bin/env python

import os
import sys
import time
import appionLoop
import apDatabase
import apParticle
import apCtf
from apTilt import apTiltPair
import apDisplay

##################################
##
##################################

class ImageRejector(appionLoop.AppionLoop):

	#####################################################
	##### START PRE-DEFINED APPION LOOP FUNCTIONS #####
	#####################################################

	### ==================================
	def specialDefaultParams(self):
		"""
		put in any additional default parameters
		"""
		#default overrides
		self.params['nowait'] = True
		self.params['background'] = True
		return

	### ==================================
	def specialParseParams(self, args):
		for arg in args:
			apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

	### ==================================
	def processImage(self, imgdata):
		### get initial assessment
		self.imgassess = apDatabase.getImgAssessmentStatus(imgdata)
		return

	### ==================================
	def preLoopFunctions(self):
		"""
		do something before starting the loop
		"""
		self.reject = 0
		return

	### ==================================
	def postLoopFunctions(self):
		"""
		do something after finishing the loop
		"""
		apDisplay.printColor("hid "+str(self.reject)+" images","cyan")
		return

	### ==================================
	def commitToDatabase(self, imgdata):
		"""
		Uses the appionLoop commit
		"""
		### insert False values
		if self.imgassess is False:
			self.reject += 1
			apDatabase.setImgViewerStatus(imgdata, False, msg=True)
			f = open("imageRejectList.txt", "a")
			f.write(imgdata['filename']+"\n")
			f.close()

	##########################################
	##### END PRE-DEFINED LOOP FUNCTIONS #####
	##########################################


if __name__ == '__main__':
	imgReject = ImageRejector()
	imgReject.run()



