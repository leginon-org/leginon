#!/usr/bin/env python

#pythonlib
import os
import sys
import re
#appion
from appionlib import filterLoop
from appionlib import appionLoop2
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apPeaks
from appionlib import appiondata
from appionlib import apParticle
from appionlib import apDefocalPairs
import threading
from appionlib import apParam

class ParticleLoop(filterLoop.FilterLoop):
	threadJpeg = False

	#######################################################
	#### ITEMS BELOW MUST BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################
	# see also appionScript.py, appionLoop2.py and filterLoop.py

	def getParticleParamsData(self):
		"""
		this function MUST return the parameters to insert into the DB
		"""
		apDisplay.printError("you did not create a 'getParticleParamsData' function in your script")
		raise NotImplementedError()

	########################################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM FROM APPION LOOP ####
	########################################################################

	#=====================
	def setRunDir(self):
		if self.params['sessionname'] is not None:
			#auto set the output directory
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
			path = os.path.abspath(sessiondata['image path'])
			path = re.sub("leginon","appion",path)
			path = re.sub("/rawdata","",path)
			path = os.path.join(path, self.processdirname, self.params['runname'])
			self.params['rundir'] = path

	#=====================
	def setupParserOptions(self):
		"""
		put in any additional parser options
		"""
		apDisplay.printError("you did not create a 'setupParserOptions' function in your script")
		raise NotImplementedError()

	#=====================
	def checkConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		apDisplay.printError("you did not create a 'checkConflicts' function in your script")
		raise NotImplementedError()

	#=====================
	def preLoopFunctions(self):
		"""
		do something before starting the loop
		"""
		return

	#=====================
	def processImage(self, imgdata, filtarray):
		"""
		this is the main component of the script
		where all the processing is done
		inputs:
			imgdata, sinedon dictionary with image info
			filtarray, filtered array ready for processing
		"""
		apDisplay.printError("you did not create a 'processImage' function in your script")
		raise NotImplementedError()

	#=====================
	def commitToDatabase(self, imgdata,rundata=None):
		"""
		put in any additional commit parameters
		"""
		return

	#=====================
	def postLoopFunctions(self):
		"""
		do something after finishing the loop
		"""
		return

	#################################################
	#### ITEMS BELOW ARE NOT USUALLY OVERWRITTEN ####
	#################################################

	#=====================
	def __init__(self):
		"""
		Starts a new function and gets all the parameters
		overrides appionScript
		"""
		appionLoop2.AppionLoop.__init__(self)
		apParam.createDirectory(os.path.join(self.params['rundir'],"pikfiles"),warning=False)
		apParam.createDirectory(os.path.join(self.params['rundir'],"jpgs"),warning=False)
		apParam.createDirectory(os.path.join(self.params['rundir'],"maps"),warning=False)

	#=====================
	def loopProcessImage(self, imgdata):

		#creates self.peaktree and filterLoop sets self.filtarray
		self.peaktree = filterLoop.FilterLoop.loopProcessImage(self, imgdata)

		if self.params['background'] is False:
			apDisplay.printMsg("Found "+str(len(self.peaktree))+" particles for "
				+apDisplay.shortenImageName(imgdata['filename']))
		self.stats['lastpeaks'] = len(self.peaktree)

		if self.params['nojpegs'] is False:
			if self.threadJpeg is True:
				threading.Thread(target=apPeaks.createPeakJpeg, args=(imgdata, self.peaktree, self.params, self.filtarray)).start()
			else:
				apPeaks.createPeakJpeg(imgdata, self.peaktree, self.params, self.filtarray)
		elif self.params['background'] is False:
			apDisplay.printWarning("Skipping JPEG creation")

		if self.params['defocpair'] is True:
			self.sibling, self.shiftpeak = apDefocalPairs.getShiftFromImage(imgdata, self.params)
		return

	#=====================
	def loopCommitToDatabase(self, imgdata):
		### commit the run
		sessiondata = imgdata['session']
		rundata = self.commitRunToDatabase(sessiondata, True)

		### commit custom picker specific params
		value = self.commitToDatabase(imgdata, rundata)

		### commit the particles
		apParticle.insertParticlePeaks(self.peaktree, imgdata, 
			runname=self.params['runname'], msg=(not self.params['background']))

		### commit defocal pairs
		if self.params['defocpair'] is True:
			apDefocalPairs.insertShift(imgdata, self.sibling, self.shiftpeak)

		return value

	#=====================
	def commitRunToDatabase(self, sessiondata, insert=True):
		### this dict maps the contents of self.params to the sinedon object
		dbmap = {
			'diam': 'diam',
			'bin': 'bin',
			'lp': 'lp_filt',
			'hp': 'hp_filt',
			'pixlimit': 'pixel_value_limit',
			'invert': 'invert',
			#'thresh': 'threshold', # major bug, do not overwrite dict variables!!!
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

		runq=appiondata.ApSelectionRunData()
		runq['name'] = self.params['runname']
		runq['session'] = sessiondata
		rundatas = runq.query(results=1)

		if rundatas:
			#get previous params
			if isinstance(paramQuery, appiondata.ApSelectionParamsData):
				paramData = rundatas[0]['params']
			elif isinstance(paramQuery, appiondata.ApDogParamsData):
				paramData = rundatas[0]['dogparams']
			elif isinstance(paramQuery, appiondata.ApManualParamsData):
				paramData = rundatas[0]['manparams']
			elif isinstance(paramQuery, appiondata.ApTiltAlignParamsData):
				paramData = rundatas[0]['tiltparams']
			else:
				apDisplay.printError("selection run does not have valid parameter data\n")

			#make sure all params are the same as previous session
			if not paramData:
				apDisplay.printError("No parameters\n")
			else:
				for key in paramQuery:

					if paramData[key] != paramQuery[key] and paramData[key] is not None:
						try:
							data_dbid=paramData[key].dbid
							query_dbid=paramQuery[key].dbid
							if data_dbid != query_dbid:
								apDisplay.printWarning(str(key)+":"+str(paramQuery[key].dbid)+" not equal to "+str(paramData[key].dbid))
								apDisplay.printError("All parameters for a picker run name must be identical\n")
						except:
							apDisplay.printWarning(str(key)+":"+str(paramQuery[key])+" not equal to "+str(paramData[key]))
							apDisplay.printError("All parameters for a picker run name must be identical\n")
			#if I made it here all parameters are the same, so it isn't necessary to commit
			return rundatas[0]

		#set params for run
		if isinstance(paramQuery, appiondata.ApSelectionParamsData):
			runq['params']=paramQuery
		elif isinstance(paramQuery, appiondata.ApDogParamsData):
			runq['dogparams']=paramQuery
		elif isinstance(paramQuery, appiondata.ApManualParamsData):
			runq['manparams']=paramQuery
		elif isinstance(paramQuery, appiondata.ApTiltAlignParamsData):
			runq['tiltparams']=paramQuery
		else:
			apDisplay.printError("self.getParticleParamsData() did not return valid parameter data\n")

		#create path
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))

		if insert is True:
			runq.insert()

		return runq

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "extract"

	#=====================
	def setupGlobalParserOptions(self):
		"""
		set the input parameters
		"""
		filterLoop.FilterLoop.setupGlobalParserOptions(self)
		### Input value options
		self.parser.add_option("--thresh", dest="thresh", type="float", default=0.5,
			help="Threshold of map to pick particles", metavar="FLOAT")
		self.parser.add_option("--maxthresh", dest="maxthresh", type="float", default=2.5,
			help="Max threshold of map to toss particles", metavar="FLOAT")
		self.parser.add_option("--maxsize", dest="maxsize", type="float", default=1.0,
			help="Maximum size of a picked peak in terms of the diameter", metavar="FLOAT")
		self.parser.add_option("--overlapmult", dest="overlapmult", type="float", default=1.5,
			help="Distance between picked particles in terms of the diameter", metavar="FLOAT")
		self.parser.add_option("--maxpeaks", dest="maxpeaks", type="int", default=1500,
			help="Maximum number of pciked particle from an image", metavar="FLOAT")
		self.parser.add_option("--diam", dest="diam", type="int",
			help="Diameter of the particle in Angstroms", metavar="INT")
		### True / False options
		self.parser.add_option("--nojpegs", dest="nojpegs", default=False,
			action="store_true", help="Do write summary jpegs during processing")
		self.parser.add_option("--defocpair", dest="defocpair", default=False,
			action="store_true", help="Use defocal pairs")
		self.parser.add_option("--checkmask", "--maskassess", dest="checkmask", default=False,
			action="store_true", help="Check mask")
		self.parser.add_option("--doubles", dest="doubles", default=False,
			action="store_true", help="Picks only particles picked by at least two templates")
		### Choices
		peaktypechoices = ("maximum", "centerofmass")
		self.parser.add_option("--peaktype", dest="peaktype",
			help="Peak extraction type", metavar="TYPE",
			type="choice", choices=peaktypechoices, default="centerofmass" )

	#=====================
	def checkGlobalConflicts(self):
		"""
		put in any conflicting parameters
		"""
		filterLoop.FilterLoop.checkGlobalConflicts(self)

		if self.params['diam'] is None or self.params['diam'] < 1:
			apDisplay.printError("please input the diameter of your particle")


#=====================
#=====================
#=====================
class MiniParticleLoop(ParticleLoop):
	def setupParserOptions(self):
		return
	def checkConflicts(self):
		return
	def getParticleParamsData(self):
		return None
	def processImage(self, imgdict, filtarray):
		return [[10,10]]

#=====================
#=====================
#=====================
if __name__ == '__main__':
	miniLoop = MiniParticleLoop()
	miniLoop.run()


