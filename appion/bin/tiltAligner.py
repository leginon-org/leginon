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
import apTilt
#legacy
#import selexonFunctions  as sf1

class tiltAligner(appionLoop.AppionLoop):
	def setProcessingDirName(self):
		self.processdirname = "extract"

	imagepairs = {}
	for image in images:
		grandparent = image['target']['image']['target']
		grandid = grandparent.dbid
		targetnumber = image['target']['number']
		key = (grandid, targetnumber)
		if key in imagepairs:
			imagepairs[key].append(image)
		else:
			imagepairs[key] = [image]
	del images

	def processImage(self, imgdata):
		apTilt.process(img1,img2,params)

	def commitToDatabase(self, imgdata):
		#expid = int(imgdata['session'].dbid)
		#apDog.insertDogParams(self.params, expid)
		#apDog.insertDogParamsREFLEGINON(self.params, imgdata['session'])
		#apParticle.insertParticlePeaks(self.peaktree, imgdata, expid, self.params)
		#apParticle.insertParticlePeaksREFLEGINON(self.peaktree, imgdata, self.params)
		return

	def specialDefaultParams(self):
		self.params['lp']=0
		self.params['hp']=0
		self.params['prtlrunid']=1.5

	def specialCreateOutputDirs(self):
		self._createDirectory(os.path.join(self.params['rundir'],"ccmaps"),warning=False)
		self._createDirectory(os.path.join(self.params['rundir'],"jpgs"),warning=False)
		self._createDirectory(os.path.join(self.params['rundir'],"dogmaps"),warning=False)

	def specialParseParams(self,args):
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			#print elements
			if (elements[0]=='lp'):
				self.params['lp']= float(elements[1])
			elif (elements[0]=='hp'):
				self.params['hp']= float(elements[1])
			elif (elements[0]=='prtlrunid'):
				self.params['selexonId']= int(elements[1])

	def specialParamConflicts(self):
		if not 'diam' in self.params or self.params['diam']==0:
			apDisplay.printError("please input the diameter of your particle")
		if params['selexonId'] is None:
			params['selexonId'] = apParticle.guessParticlesForSession(images[0]['session'].dbid)
#			params['selexonId'] = apParticle.guessParticlesForSessionREFLEGINON(images[0]['session'])

if __name__ == '__main__':
	imgLoop = tiltAligner()
	imgLoop.run()

