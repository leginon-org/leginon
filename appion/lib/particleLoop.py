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
import apDefocalPairs
import apXml
import threading
#legacy
#import selexonFunctions  as sf1

class ParticleLoop(appionLoop.AppionLoop):
	threadJpeg = True

	def setProcessingDirName(self):
		self.processdirname = "extract"

	def particleDefaultParams(self):
		"""
		put in any additional default parameters
		"""
		return

	def particleParseParams(self, args):
		"""
		put in any additional parameters to parse
		"""
		return

	def particleParamConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		return

	def particleCreateOutputDirs(self):
		"""
		put in any additional directories to create
		"""
		return

	def processImage(self, imgdata):
		#creates self.peaktree
		self.peaktree = self.particleProcessImage(imgdata)
		apDisplay.printMsg("Found "+str(len(self.peaktree))+" particles for "+apDisplay.shortenImageName(imgdata['filename']))
		self.stats['lastpeaks'] = len(self.peaktree)

		if self.threadJpeg is True:
			print "THREADING"
			threading.Thread(target=apPeaks.createPeakJpeg, args=(imgdata, self.peaktree, self.params)).start()
		else:
			apPeaks.createPeakJpeg(imgdata, self.peaktree, self.params)
		if self.params['defocpair'] is True:
			self.sibling, self.shiftpeak = apDefocalPairs.getShiftFromImage(imgdata, self.params)

	def commitToDatabase(self, imgdata):
		#commit picker specific params
		self.particleCommitToDatabase(imgdata)

		expid = int(imgdata['session'].dbid)
		apParticle.insertParticlePeaks(self.peaktree, imgdata, expid, self.params)
#		apParticle.insertParticlePeaksREFLEGINON(self.peaktree, imgdata, self.params)
		if self.params['defocpair'] is True:
			apDefocalPairs.insertShift(imgdata, self.sibling, self.shiftpeak)
#			apDefocalPairs.insertShiftREFLEGINON(imgdata, self.sibling, self.shiftpeak)

	def _runHelp(self):
		#OVERRIDE appionLoop help()
		allxml  = os.path.join(self.params['appiondir'],"xml/allAppion.xml")
		partxml = os.path.join(self.params['appiondir'],"xml/allParticle.xml")
		funcxml = os.path.join(self.params['appiondir'],"xml",self.functionname+".xml")
		xmldict = apXml.readOneXmlFile(allxml)
		xmldict = apXml.overWriteDict(xmldict, apXml.readOneXmlFile(partxml))
		xmldict = apXml.overWriteDict(xmldict, apXml.readOneXmlFile(funcxml))
		apXml.printHelp(xmldict)
		sys.exit(1)

	def setProcessingDirName(self):
		self.processdirname = "extract"

	def specialDefaultParams(self):
		self.params['thresh']=0.5
		self.params['maxthresh']=2.5
		self.params['lp']=0.0
		self.params['hp']=600.0
		self.params['maxsize']=1.0
		self.params['overlapmult']=1.5
		self.params['maxpeaks']=1500
		self.params['invert']=False
		self.params['mapdir']="maps"
		self.params['diam']=0
		self.params['median']=0
		self.params['bin']=4
		self.params['pixdiam']=None
		self.params['binpixdiam']=None
		self.params['autopik']=0
		self.params['box']=0
		self.params['defocpair']=False
		self.particleDefaultParams()

	def specialCreateOutputDirs(self):
		self._createDirectory(os.path.join(self.params['rundir'],"pikfiles"),warning=False)
		self._createDirectory(os.path.join(self.params['rundir'],"jpgs"),warning=False)
		self._createDirectory(os.path.join(self.params['rundir'],self.params['mapdir']),warning=False)

		apDisplay.printMsg("creating particle output directories")
		self.particleCreateOutputDirs()

	def specialParseParams(self, args):
		newargs = []
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
			elif (elements[0]=='hp'):
				self.params['hp']= float(elements[1])
			elif (elements[0]=='maxsize'):
				self.params['maxsize']= float(elements[1])
			elif (elements[0]=='maxthresh'):
				self.params['maxthresh']= float(elements[1])
			elif (elements[0]=='overlapmult'):
				self.params['overlapmult']= float(elements[1])
			elif (elements[0]=='maxpeaks'):
				self.params['maxpeaks']= int(elements[1])
			elif (elements[0]=='invert'):
				self.params['invert']=True
			elif (elements[0]=='diam'):
				self.params['diam']=float(elements[1])
			elif (elements[0]=='bin'):
				self.params['bin']=int(elements[1])
			elif (elements[0]=='median'):
				self.params['median']=int(elements[1])
			elif arg=='defocpair':
				self.params['defocpair']=True
			elif arg=='shiftonly':
				self.params['shiftonly']=True
			elif (elements[0]=='box'):
				self.params['box']=int(elements[1])
			else:
				newargs.append(arg)

		if len(newargs) > 0:
			apDisplay.printMsg("parsing particle parameters")
			self.particleParseParams(newargs)

	def specialParamConflicts(self):
		if self.params['diam']==0:
			apDisplay.printError("please input the diameter of your particle")
		if self.functionname != "manualpicker":
			if self.params['autopik'] != 0:
				apDisplay.printError("autopik is currently not supported")
			if self.params['thresh']==0 and self.params['autopik']==0:
				apDisplay.printError("neither manual threshold or autopik parameters are set, please set one.")

		apDisplay.printMsg("checking particle param conflicts")
		self.particleParamConflicts()


if __name__ == '__main__':
	imgLoop = basicDogPicker()
	imgLoop.run()

