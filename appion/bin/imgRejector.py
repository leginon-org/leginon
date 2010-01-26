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
		self.parser.add_option("--mindefocus", dest="mindefocus", type="float",
			help="mindefocus", metavar="#")
		self.parser.add_option("--maxdefocus", dest="maxdefocus", type="float",
			help="maxdefocus", metavar="#")
		self.parser.add_option("--acecutoff", dest="acecutoff", type="float",
			help="acecutoff", metavar="#")
		self.parser.add_option("--noace", dest="noace", default=False,
			action="store_true", help="noace")
		self.parser.add_option("--nopicks", dest="nopicks", default=False,
			action="store_true", help="nopicks")
		self.parser.add_option("--notiltpairs", dest="notiltpairs", default=False,
			action="store_true", help="notiltpairs")

	#======================
	def checkConflicts(self):
		if (self.params['mindefocus'] is not None and
				(self.params['mindefocus'] < -1e-3 or self.params['mindefocus'] > -1e-9)):
			apDisplay.printError("min defocus is not in an acceptable range, e.g. mindefocus=-1.5e-6")
		if (self.params['maxdefocus'] is not None and
				(self.params['maxdefocus'] < -1e-3 or self.params['maxdefocus'] > -1e-9)):
			apDisplay.printError("max defocus is not in an acceptable range, e.g. maxdefocus=-1.5e-6")

	### ==================================
	def processImage(self, imgdata):
		### reset global value
		self.imgassess = True

		### get initial assessment
		imgassess = apDatabase.getImgAssessmentStatus(imgdata)
		if imgassess is False:
			return
		if imgassess is None:
			imgassess = True

		### hidden image
		imgview = apDatabase.getImgViewerStatus(imgdata)
		if imgview is False:
			apDisplay.printColor("\nrejecting hidden image: "+apDisplay.short(imgdata['filename']), "green")
			self.imgassess = False
			return

		### tilt pair stuff
		if imgassess is not False and self.params['notiltpairs'] is True:
			imgassess = self.rejectTiltPairs(imgdata)

		### picking stuff
		if imgassess is not False and self.params['nopicks'] is True:
			part = apParticle.getOneParticle(imgdata)
			if not part:
				apDisplay.printColor("\nrejecting unpicked image: "+apDisplay.short(imgdata['filename']), "cyan")
				imgassess = False

		### ace stuff
		if imgassess is not False:
			imgassess = self.rejectAceInfo(imgdata)

		### set global value
		self.imgassess = imgassess


		return

	### ==================================
	def preLoopFunctions(self):
		"""
		do something before starting the loop
		"""
		self.reject = 0
		self.params['background'] = True
		return

	### ==================================
	def postLoopFunctions(self):
		"""
		do something after finishing the loop
		"""
		apDisplay.printColor("rejected "+str(self.reject)+" images","cyan")
		return

	### ==================================
	def commitToDatabase(self, imgdata):
		"""
		Uses the appionLoop commit
		"""
		msg = not self.params['background']
		### insert False values
		if self.imgassess is False:
			time.sleep(0.1)
			self.reject += 1
			apDatabase.insertImgAssessmentStatus(imgdata, self.params['runname'], False, msg=True)
			f = open("imageRejectList-"+self.timestamp+".txt", "a")
			f.write(imgdata['filename']+"\n")
			f.close()

	##########################################
	##### END PRE-DEFINED LOOP FUNCTIONS #####
	##########################################

	### ==================================
	def rejectTiltPairs(self, imgdata):
		tiltdata = apTiltPair.getTiltPair(imgdata)
		if tiltdata is None:
			apDisplay.printColor("\nrejecting unpaired image: "+apDisplay.short(imgdata['filename']), "red")
			return False
		tiltassess = apDatabase.getImgCompleteStatus(tiltdata)
		if tiltassess is False:
			apDisplay.printColor("\nrejecting bad tilt images: "+apDisplay.short(imgdata['filename']), "magenta")
			return False
		return True

	### ==================================
	def rejectAceInfo(self, imgdata):
		shortname = apDisplay.short(imgdata['filename'])

		### get best defocus value
		ctfvalue, conf = apCtf.getBestCtfValueForImage(imgdata)

		if ctfvalue is None:
			if self.params['noace'] is True:
				apDisplay.printColor("\nrejecting no ACE values: "+apDisplay.short(imgdata['filename']), "yellow")
				return False
			else:
				#apDisplay.printWarning("skipping no ACE values for "+apDisplay.short(imgdata['filename']))
				return True

		### check that ACE estimation is above confidence threshold
		if self.params['acecutoff'] and conf < self.params['acecutoff']:
			apDisplay.printColor("\nrejecting below ACE cutoff: "+apDisplay.short(imgdata['filename'])+" conf="+str(round(conf,3)), "cyan")
			return False


		### defocus should be in negative meters
		if ctfvalue['defocus2'] is not None and ctfvalue['defocus1'] != ctfvalue['defocus2']:
			defocus = (ctfvalue['defocus1'] + ctfvalue['defocus2'])/2.0
		else:
			defocus = ctfvalue['defocus1']
		defocus = -1.0*abs(defocus)

		### skip micrograph that have defocus above or below min & max defocus levels
		if self.params['mindefocus'] and defocus > self.params['mindefocus']:
			apDisplay.printColor(shortname+" defocus ("+str(round(defocus*1e6,2))+\
				" um) is less than mindefocus ("+str(self.params['mindefocus']*1e6)+" um)\n","cyan")
			return False
		if self.params['maxdefocus'] and defocus < self.params['maxdefocus']:
			apDisplay.printColor(shortname+" defocus ("+str(round(defocus*1e6,2))+\
				" um) is greater than maxdefocus ("+str(self.params['maxdefocus']*1e6)+" um)\n","cyan")
			return False

		return True


if __name__ == '__main__':
	imgReject = ImageRejector()
	imgReject.run()



