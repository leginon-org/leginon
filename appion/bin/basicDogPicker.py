#!/usr/bin/python -O

#pythonlib
import os
import sys
import re
#appion
import appionLoop
import apImage
import apDisplay
import apTemplate
import apDatabase
import apPeaks
import apParticle
#legacy
#import selexonFunctions  as sf1

class basicDogPicker(appionLoop.AppionLoop):
	def setProcessingDirName(self):
		self.processdirname = "extract"

	def processImage(self, imgdata):
		print "PRE-FILTER IMAGE"
		imgarray = imgdata['image']
		imgarray = apImage.preProcessImage(imgarray, params=self.params)
		print "DOG FILTER"
		if self.params['invert']:
			imgarray=apImage.invertImage(imgarray)
		imgarray = apImage.diffOfGaussParam(imgarray, self.params)
		imgarray = apImage.normStdev(imgarray)/4.0
		self.dogmaplist = [imgarray,]
		print "FINDPEAKS"
		self.peaktree  = apPeaks.findPeaks(imgdata, self.dogmaplist, self.params, maptype="dogmap")
		print "CREATEJPG"
		apPeaks.createPeakJpeg(imgdata, self.peaktree, self.params)

	def commitToDatabase(self, imgdata):
		expid = int(imgdata['session'].dbid)
		apDog.insertDogParams(self.params, expid)
		apParticle.insertParticlePeaks(self.peaktree, imgdata, expid, self.params)
		return

	def specialDefaultParams(self):
		self.params['thresh']=0.5
		self.params['maxthresh']=2.5
		self.params['lp']=0
		self.params['overlapmult']=1.5
		self.params['maxpeaks']=1500
		self.params['invert']=False

	def specialCreateOutputDirs(self):
		self._createDirectory(os.path.join(self.params['rundir'],"pikfiles"),warning=False)
		self._createDirectory(os.path.join(self.params['rundir'],"jpgs"),warning=False)
		self._createDirectory(os.path.join(self.params['rundir'],"dogmaps"),warning=False)

	def specialParseParams(self, args):
		for arg in args:
			elements = arg.split('=')
			elements[0] = elements[0].lower()
			#print elements
			if (elements[0]=='help' or elements[0]=='--help' \
				or elements[0]=='-h' or elements[0]=='-help'):
				sys.exit(1)
			elif (elements[0]=='thresh'):
				self.params['thresh']= float(elements[1])
			elif (elements[0]=='lp'):
				self.params['lp']= float(elements[1])
			elif (elements[0]=='maxthresh'):
				self.params['maxthresh']= float(elements[1])
			elif (elements[0]=='overlapmult'):
				self.params['overlapmult']= float(elements[1])
			elif (elements[0]=='maxpeaks'):
				self.params['maxpeaks']= int(elements[1])
			elif (elements[0]=='invert'):
				self.params['invert']=True
			else:
				print elements[0], "is not recognized as a valid parameter"
				sys.exit()

	def specialParamConflicts(self):
		if not 'diam' in self.params or self.params['diam']==0:
			apDisplay.printError("please input the diameter of your particle")


if __name__ == '__main__':
	imgLoop = basicDogPicker()
	imgLoop.run()

