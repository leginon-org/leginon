#!/usr/bin/env python

import os
import sys
import time
from appionlib import appionLoop2
from appionlib import apDatabase
from appionlib.apTilt import apTiltPair
from appionlib import apDisplay

##################################
##
##################################

class rejectUnpairedTilts(appionLoop2.AppionLoop):

	#####################################################
	##### START PRE-DEFINED APPION LOOP FUNCTIONS #####
	#####################################################

	def processImage(self, imgdata):
		time.sleep(0.01)
		return

	def setupParserOptions(self):
		return

	def checkConflicts(self):
		return

	def preLoopFunctions(self):
		"""
		do something before starting the loop
		"""
		self.reject = 0
		return

	def checkConflicts(self):
		"""
		do something before starting the loop
		"""
		self.reject = 0
		return

	def postLoopFunctions(self):
		"""
		do something after finishing the loop
		"""
		apDisplay.printColor("rejected "+str(self.reject)+" images","cyan")
		return

	def commitToDatabase(self, imgdata):
		"""
		Uses the appionLoop commit
		"""
		imgassess = apDatabase.getImgCompleteStatus(imgdata)
		tiltdata = apTiltPair.getTiltPair(imgdata)
		msg = not self.params['background']
		if tiltdata is None:
			if imgassess is not False:
				apDisplay.printColor("\nrejecting unpaired image: "+apDisplay.short(imgdata['filename']), "red")
				apDatabase.insertImgAssessmentStatus(imgdata, self.params['runid'], False, msg=msg)
				self.reject+=1
			return
		if self.params['background'] is False:
			apDisplay.printMsg("tiltpair: "+apDisplay.short(tiltdata['filename']))
		tiltassess = apDatabase.getImgCompleteStatus(tiltdata)
		if imgassess is False or tiltassess is False:
			if imgassess is not False:
				apDisplay.printColor("\nrejecting bad tilt images: "+apDisplay.short(imgdata['filename']), "magenta")
			if tiltassess is not False:
				apDisplay.printColor("\nrejecting bad tilt images: "+apDisplay.short(tiltdata['filename']), "magenta")
			apDatabase.insertImgAssessmentStatus(imgdata, self.params['runid'], False, msg=msg)
			apDatabase.insertImgAssessmentStatus(tiltdata, self.params['runid'], False, msg=msg)
			self.reject+=2
		if self.params['background'] is False:
			print "Assessment:", imgassess, tiltassess
		return

	##########################################
	##### END PRE-DEFINED LOOP FUNCTIONS #####
	##########################################

if __name__ == '__main__':
	imgLoop = rejectUnpairedTilts()
	imgLoop.run()



