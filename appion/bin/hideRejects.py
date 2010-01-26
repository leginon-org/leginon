#!/usr/bin/env python

import os
import sys
import time
from appionlib import appionLoop2
from appionlib import apDatabase
from appionlib import apParticle
from appionlib import apCtf
from appionlib.apTilt import apTiltPair
from appionlib import apDisplay

##################################
##
##################################

class ImageRejector(appionLoop2.AppionLoop):

	#####################################################
	##### START PRE-DEFINED APPION LOOP FUNCTIONS #####
	#####################################################

	### ==================================
	def setupParserOptions(self):
		return

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

	#======================
	def checkConflicts(self):
		return

	##########################################
	##### END PRE-DEFINED LOOP FUNCTIONS #####
	##########################################


if __name__ == '__main__':
	imgReject = ImageRejector()
	imgReject.run()



