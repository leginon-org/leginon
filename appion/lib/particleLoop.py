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
import appionData
import apParticle
import apDefocalPairs
import apXml
import threading
#legacy
#import selexonFunctions  as sf1

class ParticleLoop(appionLoop.AppionLoop):
	threadJpeg = True

	#######################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################
	# see also appionLoop.py

	def particleProcessImage(self):
		"""
		This is the main component of the script
		where all the processing is done
		
		This function must return a list of peaks (as dicts), e.g.
		return [{'xcoord': 15, 'ycoord: 10}, {'xcoord': 243, 'ycoord: 476}, ]
		"""
		return NotImplementedError()

	def particleDefaultParams(self):
		"""
		put in any additional default parameters
		"""
		return

	def particleParseParams(self, args):
		"""
		put in any additional parameters to parse
		"""
		for arg in args:
			elements = arg.split('=')
			elements[0] = elements[0].lower()
			apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

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

	def particleCommitToDatabase(self, imgdata):
		"""
		put in any additional commit parameters
		"""
		return

	def getParticleParamsData(self):
		"""
		this function MUST return the parameters to insert into the DB
		"""
		return

	########################################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM FROM APPION LOOP ####
	########################################################################

	def reprocessImage(self, imgdata):
		"""
		Returns 
		True, if an image should be reprocessed
		False, if an image was processed and should NOT be reprocessed
		None, if image has not yet been processed 
		e.g. a confidence less than 80%
		"""
		return None

	def preLoopFunctions(self):
		"""
		do something before starting the loop
		"""
		return

	def postLoopFunctions(self):
		"""
		do something after finishing the loop
		"""
		return

	#################################################
	#### ITEMS BELOW ARE NOT USUALLY OVERWRITTEN ####
	#################################################

	def processImage(self, imgdata):
		#creates self.peaktree
		self.peaktree = self.particleProcessImage(imgdata)
		apDisplay.printMsg("Found "+str(len(self.peaktree))+" particles for "+apDisplay.shortenImageName(imgdata['filename']))
		self.stats['lastpeaks'] = len(self.peaktree)

		if self.threadJpeg is True:
			threading.Thread(target=apPeaks.createPeakJpeg, args=(imgdata, self.peaktree, self.params)).start()
		else:
			apPeaks.createPeakJpeg(imgdata, self.peaktree, self.params)
		if self.params['defocpair'] is True:
			self.sibling, self.shiftpeak = apDefocalPairs.getShiftFromImage(imgdata, self.params)

	def commitToDatabase(self, imgdata):
		#commit the run
		expid = int(imgdata['session'].dbid)
		self.commitRunToDatabase(expid, True)
		#commit picker specific params
		self.particleCommitToDatabase(imgdata)
		#commit the particles
		apParticle.insertParticlePeaks(self.peaktree, imgdata, expid, self.params)
		#commit defocal pairs
		if self.params['defocpair'] is True:
			apDefocalPairs.insertShift(imgdata, self.sibling, self.shiftpeak)

	def commitRunToDatabase(self, expid, insert=True):
		dbmap = {
			'diam': 'diam',
			'bin': 'bin',
			'lp': 'lp_filt',
			'hp': 'hp_filt',
			'invert': 'invert',
			'thresh': 'threshold',
			'thresh': 'manual_thresh',
			'maxthresh': 'max_threshold',
			'maxpeaks': 'max_peaks',
			'maxsize': 'maxsize',
			'median': 'median',
			'defocpair': 'defocal_pairs',
			'overlapmult': 'overlapmult',
		}
		paramQuery = self.getParticleParamsData()

		#insert common parameters
		for pkey,dbkey in dbmap.items():
			if (dbkey in paramQuery 
			 and pkey in self.params 
			 and self.params[pkey] is not None):
				paramQuery[dbkey] = self.params[pkey]

		runq=appionData.ApSelectionRunData()
		runq['name'] = self.params['runid']
		runq['dbemdata|SessionData|session'] = expid
		runids = runq.query(results=1)
		
		if runids:
			paramData = paramQuery.query(results=1)
			#make sure all params are the same as previous session	
			if not paramData:
				apDisplay.printError("All parameters for a picker run name must be identical\n")
			else:
				for key in paramQuery:
					if paramData[0][key] != paramQuery[key]:
						apDisplay.printWarning(str(key)+":"+str(paramQuery[key])+" not equal to "+str(paramData[0][key]))
						apDisplay.printError("All parameters for a picker run name must be identical\n")
			#if I made it here all parameters are the same, so it isn't necessary to commit
			return False

		#set params for run
		if isinstance(paramQuery, appionData.ApSelectionParamsData):
			runq['params']=paramQuery
		elif isinstance(paramQuery, appionData.ApDogParamsData):
			runq['dogparams']=paramQuery
		elif isinstance(paramQuery, appionData.ApManualParamsData):
			runq['manparams']=paramQuery
		elif isinstance(paramQuery, appionData.ApTiltAlignParamsData):
			runq['tiltparams']=paramQuery
		else:
			apDisplay.printError("self.getParticleParamsData() did not return valid parameter data\n")

		#create path
		pathq = appionData.ApPathData()
		pathq['path'] = self.params['rundir']
		runq['extractPath'] = pathq

		if insert is True:
			runq.insert()

		return True

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
		self.params['checkMask']=None
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
				self.params['maxsize']= int(elements[1])
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
			elif (elements[0]=='maskassess'):
				self.params['checkMask']=elements[1]
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

