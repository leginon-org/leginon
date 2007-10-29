#!/usr/bin/python -O

import os
import sys
import time
import appionLoop
import apDatabase
import apDisplay

##################################
##
##################################

class rejectUnpairedTilts(appionLoop.AppionLoop):

	#####################################################
	##### START PRE-DEFINED APPION LOOP FUNCTIONS #####
	#####################################################

	def processImage(self, imgdata):
		time.sleep(0.2)
		return

	def commitToDatabase(self, imgdata):
		"""
		Uses the appionLoop commit
		"""
		tiltdata = apTiltPair.getTiltPair(imgdata)
		if tiltdata is None:
			apDisplay.printColor("rejecting image: "+apDisplay.short(imgdata['filename']), "magenta")
			apDatabase.insertImgAssessmentStatus(imgdata, self.params['runid'], False)
		return

	##########################################
	##### END PRE-DEFINED LOOP FUNCTIONS #####
	##########################################

if __name__ == '__main__':
	imgLoop = rejectUnpairedTilts()
	imgLoop.run()



