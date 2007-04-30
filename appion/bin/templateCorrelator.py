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
#legacy
import selexonFunctions  as sf1
import selexonFunctions2 as sf2

class TemplateCorrelationLoop(appionLoop.AppionLoop):
	def preLoopFunctions(self):
		apTemplate.getTemplates(self.params)

	def processImage(self, imgdict):
		imgname = imgdict['filename']
		apTemplate.rescaleTemplates(self.params)
		### RUN FindEM
		if 'method' in self.params and self.params['method'] == "experimental":
			numpeaks = sf2.runCrossCorr(params,imgname)
			sf2.createJPG2(params,imgname)
		else:
			print "PROCESSING"
			self._processAndSaveImage(imgdict)
			print "FINDEM"
			self.ccmaplist = apFindEM.runFindEM(imgname, self.params)
			print "FINDPEAKS"
			self.peaktree  = apPeaks.findPeaks(imgdict, self.ccmaplist, self.params)
			print "CREATEJPG"
			apPeaks.createPeakJpeg(imgdict, self.peaktree, self.params)
			#sf2.createJPG2(self.params,imgname)

	def commitToDatabase(self, imgdict):
		expid = int(imgdict['session'].dbid)
		sf1.insertSelexonParams(self.params, expid)
		apParticle.insertParticlePeaks(self.peaktree, imgdict, expid, self.params)

	def specialDefaultParams(self):
		self.params['template']=''
		self.params['templatelist']=[]
		self.params['startang']=0
		self.params['endang']=10
		self.params['incrang']=20
		self.params['thresh']=0.5
		self.params['autopik']=0
		self.params['lp']=30
		self.params['hp']=600
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
			if (elements[0]=='help' or elements[0]=='--help' \
				or elements[0]=='-h' or elements[0]=='-help'):
				sys.exit(1)
			elif (elements[0]=='template'):
				self.params['template']=elements[1]
			elif (elements[0]=='range'):
				angs=elements[1].split(',')
				if (len(angs)==3):
					self.params['startang']=int(angs[0])
					self.params['endang']=int(angs[1])
					self.params['incrang']=int(angs[2])
				else:
					print "\nERROR: \'range\' must include 3 angle parameters: start, stop, & increment\n"
					sys.exit(1)
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
	 				print "\nERROR: \'range\' must include 3 angle parameters: start, stop, & increment\n"
					sys.exit(1)
			elif (elements[0]=='thresh'):
				self.params['thresh']=float(elements[1])
			elif (elements[0]=='autopik'):
				self.params['autopik']=float(elements[1])
			elif (elements[0]=='lp'):
				self.params['lp']=float(elements[1])
			elif (elements[0]=='hp'):
				self.params['hp']=float(elements[1])
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

	def _processAndSaveImage(self, imgdict):
		imgdata = apImage.preProcessImage(imgdict['image'], params=self.params)
		smimgname = os.path.join(self.params['rundir'],imgdict['filename']+".dwn.mrc")
		apImage.arrayToMrc(imgdata, smimgname)


if __name__ == '__main__':
	imgLoop = TemplateCorrelationLoop()
	imgLoop.run()

