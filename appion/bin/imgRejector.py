#!/usr/bin/python -O

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
		#new params
		self.params['mindefocus'] = None
		self.params['maxdefocus'] = None
		self.params['acecutoff'] = None
		self.params['noace'] = False
		self.params['nopicks'] = False
		self.params['notiltpairs'] = False
		return

	### ==================================
	def specialParseParams(self, args):
		for arg in args:
			elements = arg.split('=')
			elements[0] = elements[0].lower()
			if (arg == 'notiltpairs'):
				self.params['notiltpairs']=True
			elif (arg == 'noace'):
				self.params['noace']=True
			elif (arg == 'nopicks'):
				self.params['nopicks']=True
			elif (elements[0]=='mindefocus'):
				self.params['mindefocus']=float(elements[1])
			elif (elements[0]=='maxdefocus'):
				self.params['maxdefocus']=float(elements[1])
			elif (elements[0]=='acecutoff'):
				self.params['acecutoff']=float(elements[1])
			else:
				apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

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
			imgassess *= self.rejectTiltPairs(imgdata)

		### picking stuff
		if imgassess is not False and self.params['nopicks'] is True:
			part = apParticle.getOneParticle(imgdata)
			if not part:
				apDisplay.printColor("\nrejecting unpicked image: "+apDisplay.short(imgdata['filename']), "cyan")
				imgassess = False

		### ace stuff
		if imgassess is not False:
			imgassess *= self.rejectAceInfo(imgdata)

		### set global value
		self.imgassess = imgassess

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
			self.reject += 1
			apDatabase.insertImgAssessmentStatus(imgdata, self.params['runid'], False, msg=msg)
			f = open("imageRejectList.txt", "a")
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
		ctfvalue, conf = apCtf.getBestCtfValueForImage(imgdata)

 		if ctfvalue is None:
			if self.params['noace'] is True:
				apDisplay.printColor("\nrejecting no ACE values: "+apDisplay.short(imgdata['filename']), "yellow")
				return False
			else:
				apDisplay.printWarning("skipping no ACE values for "+apDisplay.short(imgdata['filename']))
				return True

		### check that ACE estimation is above confidence threshold
		if self.params['acecutoff'] and conf < self.params['acecutoff']:
			apDisplay.printColor("\nrejecting below ACE cutoff: "+apDisplay.short(imgdata['filename'])+" conf="+str(round(conf,3)), "cyan")
			return False

		defocus = apCtf.getBestDefocusForImage(imgdata)
		### skip micrograph that have defocus above or below min & max defocus levels
		if self.params['mindefocus'] and defocus > self.params['mindefocus']:
			apDisplay.printColor("\nrejecting below defocus cutoff: "+apDisplay.short(imgdata['filename'])+" def="+str(round(defocus,3)), "blue")
			return False
		if self.params['maxdefocus'] and defocus < self.params['maxdefocus']:
			apDisplay.printColor("\nrejecting above defocus cutoff: "+apDisplay.short(imgdata['filename'])+" def="+str(round(defocus,3)), "magenta")
			return False

		return True


if __name__ == '__main__':
	imgReject = ImageRejector()
	imgReject.run()



