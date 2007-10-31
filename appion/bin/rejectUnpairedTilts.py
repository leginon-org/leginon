#!/usr/bin/python -O

import os
import sys
import time
import appionLoop
import apDatabase
from apTilt import apTiltPair
import apDisplay

##################################
##
##################################

class rejectUnpairedTilts(appionLoop.AppionLoop):

	#####################################################
	##### START PRE-DEFINED APPION LOOP FUNCTIONS #####
	#####################################################

	def specialDefaultParams(self):
		"""
		put in any additional default parameters
		"""
		self.params['nowait'] = True
		self.params['background'] = True
		return

	def processImage(self, imgdata):
		time.sleep(0.1)
		return

	def commitToDatabase(self, imgdata):
		"""
		Uses the appionLoop commit
		"""
		imgassess = apDatabase.getImgAssessmentStatus(imgdata)
		tiltdata = apTiltPair.getTiltPair(imgdata)
		if tiltdata is None:
			if imgassess is not False:
				apDisplay.printColor("rejecting unpaired image: "+apDisplay.short(imgdata['filename']), "magenta")
				apDatabase.insertImgAssessmentStatus(imgdata, self.params['runid'], False)
			return

		tiltassess = apDatabase.getImgAssessmentStatus(tiltdata)
		if imgassess is False and tiltassess is not False:
			apDisplay.printColor("rejecting bad tilt image: "+apDisplay.short(tiltdata['filename']), "magenta")
			apDatabase.insertImgAssessmentStatus(tiltdata, self.params['runid'], False)
		if tiltassess is False and imgassess is not False:
			apDisplay.printColor("rejecting bad tilt image: "+apDisplay.short(imgdata['filename']), "magenta")
			apDatabase.insertImgAssessmentStatus(imgdata, self.params['runid'], False)
		return

	##########################################
	##### END PRE-DEFINED LOOP FUNCTIONS #####
	##########################################

if __name__ == '__main__':
	imgLoop = rejectUnpairedTilts()
	imgLoop.run()



