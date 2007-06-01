#!/usr/bin/python -O

#pythonlib
import os
import sys
import re
#appion
import appionLoop
import apFindEM
import apImage
import apDisplay
import apTemplate
import apDatabase
import apPeaks
import apParticle
import apDefocalPairs
#legacy
#import apViewIt
#import selexonFunctions  as sf1

class TemplateCorrelationLoop(appionLoop.AppionLoop):
	def setProcessingDirName(self):
		self.processdirname = "extract"

	def preLoopFunctions(self):
		apTemplate.getTemplates(self.params)

	def processImage(self, imgdata):
		imgname = imgdata['filename']
		apTemplate.rescaleTemplates(self.params)
		### RUN FindEM
		if 'method' in self.params and self.params['method'] == "experimental":
			#numpeaks = sf2.runCrossCorr(params,imgname)
			#sf2.createJPG2(params,imgname)
			sys.exit(1)
		else:
			print "FINDEM"
			self.ccmaplist = apFindEM.runFindEM(imgdata, self.params)
			print "FINDPEAKS"
			self.peaktree  = apPeaks.findPeaks(imgdata, self.ccmaplist, self.params)
			print "CREATEJPG"
			apPeaks.createPeakJpeg(imgdata, self.peaktree, self.params)

		if self.params['defocpair'] is True:
			self.sibling, self.shiftpeak = apDefocalPairs.getShiftFromImage(imgdata)

	def postLoopFunctions(self):
		return

	def commitToDatabase(self, imgdata):
		expid = int(imgdata['session'].dbid)
		apParticle.insertSelexonParams(self.params, expid)
		apParticle.insertParticlePeaks(self.peaktree, imgdata, expid, self.params)
		if self.params['defocpair'] is True:
			apDefocalPairs.insertShift(imgdata, self.sibling, self.shiftpeak)

	def specialDefaultParams(self):
		self.params['template']=''
		self.params['templatelist']=[]
		self.params['startang']=0
		self.params['endang']=10
		self.params['incrang']=20
		self.params['thresh']=0.5
		self.params['autopik']=0
		self.params['lp']=30.0
		self.params['hp']=0.0
		self.params['maxsize']=1.0
		self.params['box']=0
		self.params['method']="updated"
		self.params['overlapmult']=1.5
		self.params['maxpeaks']=1500
		self.params['defocpair']=False
		self.params['templateIds']=''
		self.params['multiple_range']=False
		self.params["ogTmpltInfo"]=[]
		self.params["scaledapix"]={}


	def specialCreateOutputDirs(self):
		self._createDirectory(os.path.join(self.params['rundir'],"pikfiles"),warning=False)
		self._createDirectory(os.path.join(self.params['rundir'],"jpgs"),warning=False)
		self._createDirectory(os.path.join(self.params['rundir'],"ccmaxmaps"),warning=False)

	def specialParseParams(self,args):
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			#print elements
			if (elements[0]=='template'):
				self.params['template']=elements[1]
			elif (elements[0]=='range'):
				angs=elements[1].split(',')
				if (len(angs)==3):
					self.params['startang']=int(angs[0])
					self.params['endang']=int(angs[1])
					self.params['incrang']=int(angs[2])
					self.params['startang1']=int(angs[0])
					self.params['endang1']=int(angs[1])
					self.params['incrang1']=int(angs[2])
				else:
					apDisplay.printError("'range' must include 3 angle parameters: start, stop, & increment")
			elif (re.match('range\d+',elements[0])):
				num = re.sub("range(?P<num>[0-9]+)","\g<num>",elements[0])
				#num=elements[0][-1]
				angs=elements[1].split(',')
				if (len(angs)==3):
					self.params['startang'+num]=int(angs[0])
					self.params['endang'+num]=int(angs[1])
					self.params['incrang'+num]=int(angs[2])
					self.params['multiple_range']=True
				else:
	 				apDisplay.printError("'range' must include 3 angle parameters: start, stop, & increment")
			elif (elements[0]=='thresh'):
				self.params['thresh']=float(elements[1])
			elif (elements[0]=='autopik'):
				self.params['autopik']=float(elements[1])
			elif (elements[0]=='lp'):
				self.params['lp']=float(elements[1])
			elif (elements[0]=='hp'):
				self.params['hp']=float(elements[1])
			elif (elements[0]=='maxsize'):
				self.params['maxsize']=float(elements[1])
			elif (elements[0]=='box'):
				self.params['box']=int(elements[1])
			elif (elements[0]=='templateids'):
				templatestring=elements[1].split(',')
				self.params['templateIds']=templatestring
			elif arg=='defocpair':
				self.params['defocpair']=True
			elif arg=='shiftonly':
				self.params['shiftonly']=True
			elif (elements[0]=='method'):
				self.params['method']=str(elements[1])
			elif (elements[0]=='overlapmult'):
				self.params['overlapmult']=float(elements[1])
			elif (elements[0]=='maxpeaks'):
				self.params['maxpeaks']=int(elements[1])

	def specialParamConflicts(self):
		if not self.params['templateIds'] and not self.params['apix']:
			apDisplay.printError("if not using templateIds, you must enter a template pixel size")
		if self.params['templateIds'] and self.params['template']:
			apDisplay.printError("Both template database IDs and mrc file templates are specified,\nChoose only one")
		if (self.params['thresh']==0 and self.params['autopik']==0):
			apDisplay.printError("neither manual threshold or autopik parameters are set, please set one.")
		if not 'diam' in self.params or self.params['diam']==0:
			apDisplay.printError("please input the diameter of your particle")
		if self.params['autopik'] != 0:
			apDisplay.printError("autopik is currently not supported")

if __name__ == '__main__':
	imgLoop = TemplateCorrelationLoop()
	imgLoop.run()

