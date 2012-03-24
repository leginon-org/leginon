#!/usr/bin/env python
#
import os
import time
import sys
import random
import math
import shutil
import re
import glob
import numpy
import cPickle
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apParam
from appionlib import apStack
from appionlib import apImage
from appionlib import apEMAN
from appionlib import apImagicFile
from appionlib.apSpider import operations
from appionlib import appiondata
from appionlib import apProject
from appionlib import apFourier
from pyami import spider

#=====================
#=====================
class UploadCL2DScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --jobid=ID [ --commit ]")
		self.parser.add_option("-j", "--jobid", dest="jobid", type="int",
			help="CL2D jobid", metavar="#")
		self.parser.add_option("-t", "--timestamp", dest="timestamp",
			help="Timestamp of files, e.g. 08nov02b35", metavar="CODE")

	#=====================
	def checkConflicts(self):
		if self.params['timestamp'] is None:
			self.params['timestamp'] = self.getTimestamp()

	#=====================
	def getTimestamp(self):
		if self.params["jobid"] is not None:
			jobdata = appiondata.ApCL2DRunData.direct_query(self.params["jobid"])
			timestamp = jobdata['timestamp']
		elif timestamp is None:
			wildcard = "part*_*.*"
			files = glob.glob(wildcard)
			if len(files) == 0:
				apDisplay.printError("Could not determine timestamp\n"
					+"please provide it, e.g. -t 08nov27e54")
			reg = re.match("part([0-9a-z]*)_", files[0])
			if len(reg.groups()) == 0:
				apDisplay.printError("Could not determine timestamp\n"
					+"please provide it, e.g. -t 08nov27e54")
			timestamp = reg.groups()[0]
		apDisplay.printMsg("Found timestamp = '"+timestamp+"'")
		return timestamp

	#=====================
	def readRunParameters(self):
		paramfile = "cl2d-"+self.params['timestamp']+"-params.pickle"
		if not os.path.isfile(paramfile):
			apDisplay.printError("Could not find run parameters file: "+paramfile)
		f = open(paramfile, "r")
		runparams = cPickle.load(f)
		return runparams

	#=====================
	def getCL2DJob(self):
		cl2djobq = appiondata.ApCL2DRunData()
		cl2djobq['runname'] = self.runparams['runname']
		cl2djobq['path'] = appiondata.ApPathData(path=os.path.abspath(self.runparams['rundir']))
		cl2djobq['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(self.runparams['stackid'])
		cl2djobq['timestamp'] = self.params['timestamp']
		cl2djobdata = cl2djobq.query(results=1)
		if not cl2djobdata:
			return None
		return cl2djobdata[0]

	#=====================
	def calcResolution(self, level):
		self.resdict = {}
		D=self.getClassificationAtLevel(level)
		for classref in D:
			stack=[]
			for partnum in D[classref]:
				stack.append(apImagicFile.readSingleParticleFromStack("alignedStack.hed",int(partnum)+1,msg=False))
			apImagicFile.writeImagic(stack,"tmp.hed")

			frcdata = apFourier.spectralSNRStack("tmp.hed", self.apix)
			self.resdict[classref] = apFourier.getResolution(frcdata, self.apix, self.boxsize)
		apFile.removeStack("tmp.hed")

	#=====================
	def getClassificationAtLevel(self,level):
		D={}
		for classSel in glob.glob("part"+self.params['timestamp']+"_level_%02d_[0-9]*.sel"%level):
				fh=open(classSel)
				listOfParticles=[]
				for line in fh:
						fileName=line.split(" ")[0]
						particleNumber=os.path.split(fileName)[1][4:10]
						listOfParticles.append(particleNumber)
				classNumber=int(os.path.splitext(classSel.split("_")[-1])[0])
				D[classNumber]=listOfParticles
				fh.close()
		return D

	#=====================
	def insertAlignStackRunIntoDatabase(self, alignimagicfile):
		apDisplay.printMsg("Inserting CL2D Run into DB")

		### setup alignment run
		alignrunq = appiondata.ApAlignRunData()
		alignrunq['runname'] = self.runparams['runname']
		alignrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
#		if uniquerun:
#			apDisplay.printError("Run name '"+self.runparams['runname']+"' and path already exist in database")

		### setup cl2d run
		cl2dq = appiondata.ApCL2DRunData()
		cl2dq['runname'] = self.runparams['runname']
		cl2dq['run_seconds'] = self.runparams['runtime']
		cl2dq['fast'] = self.runparams['fast']
		self.cl2dqdata=cl2dq

		### finish alignment run
		alignrunq['cl2drun'] = cl2dq
		alignrunq['hidden'] = False
		alignrunq['runname'] = self.runparams['runname']
		alignrunq['description'] = self.runparams['description']
		alignrunq['lp_filt'] = self.runparams['lowpass']
		alignrunq['hp_filt'] = self.runparams['highpass']
		alignrunq['bin'] = self.runparams['bin']

		### setup alignment stack
		alignstackq = appiondata.ApAlignStackData()
		if self.runparams['align'] is True:		### option to create aligned stack
			alignstackq['imagicfile'] = alignimagicfile
			alignstackq['avgmrcfile'] = "average.mrc"
			alignstackq['refstackfile'] = "part"+self.params['timestamp']+"_level_%02d_.hed"%(self.Nlevels-1)
		alignstackq['iteration'] = self.runparams['maxiter']
		alignstackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		alignstackq['alignrun'] = alignrunq
		### check to make sure files exist
		if self.runparams['align'] is True:		### option to create aligned stack
			alignimagicfilepath = os.path.join(self.params['rundir'], alignstackq['imagicfile'])
			if not os.path.isfile(alignimagicfilepath):
				apDisplay.printError("could not find stack file: "+alignimagicfilepath)
			avgmrcfile = os.path.join(self.params['rundir'], alignstackq['avgmrcfile'])
			if not os.path.isfile(avgmrcfile):
				apDisplay.printError("could not find average mrc file: "+avgmrcfile)
			refstackfile = os.path.join(self.params['rundir'], alignstackq['refstackfile'])
			if not os.path.isfile(refstackfile):
				apDisplay.printError("could not find reference stack file: "+refstackfile)
		alignstackq['stack'] = apStack.getOnlyStackData(self.runparams['stackid'])
		alignstackq['boxsize'] = self.boxsize
		alignstackq['pixelsize'] = apStack.getStackPixelSizeFromStackId(self.runparams['stackid'])*self.runparams['bin']
		alignstackq['description'] = self.runparams['description']
		alignstackq['hidden'] =  False
		alignstackq['num_particles'] =  self.runparams['numpart']

		### insert
		if self.params['commit'] is True:
			alignstackq.insert()
		self.alignstackdata = alignstackq

		return

	#=====================
	def insertAlignParticlesIntoDatabase(self, level):
		count = 0
		inserted = 0
		t0 = time.time()
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		D=self.getClassificationAtLevel(level)
		for ref in D:
			### setup reference
			refq = appiondata.ApAlignReferenceData()
			refq['refnum'] = ref+1
			refq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			refq['alignrun'] = self.alignstackdata['alignrun']
			if ref in self.resdict:
				refq['ssnr_resolution'] = self.resdict[ref]

			### setup particle info ... NOTE: ALIGNMENT PARAMETERS ARE NOT SAVED IN XMIPP 2.4
			for partnum in D[ref]:
				alignpartq = appiondata.ApAlignParticleData()
				alignpartq['partnum'] = int(partnum)+1
				alignpartq['alignstack'] = self.alignstackdata
				stackpartdata = apStack.getStackParticle(self.runparams['stackid'], int(partnum)+1)	### particle numbering starts with 0!!!!!!!
				alignpartq['stackpart'] = stackpartdata
				alignpartq['ref'] = refq
				### insert
				if self.params['commit'] is True:
					inserted += 1
					alignpartq.insert()

		apDisplay.printColor("\ninserted "+str(inserted)+" of "+str(count)+" particles into the database in "
			+apDisplay.timeString(time.time()-t0), "cyan")

		return

	#=====================
	def insertClusterRunIntoDatabase(self):
		# create a Clustering Run object
		clusterrunq = appiondata.ApClusteringRunData()
		clusterrunq['runname'] = self.params['runname']
		clusterrunq['description'] = self.params['description']
		clusterrunq['cl2dparams'] = self.cl2dqdata
		clusterrunq['boxsize'] = self.boxsize
		clusterrunq['pixelsize'] = self.apix
		clusterrunq['num_particles'] = self.runparams['numpart']
		if self.runparams['align'] is True:
			clusterrunq['alignstack'] = self.alignstackdata

		apDisplay.printMsg("inserting clustering parameters into database")
		if self.params['commit'] is True:
			clusterrunq.insert()
		self.clusterrun = clusterrunq
		return

	#=====================
	def getAlignParticleData(self, partnum):
		alignpartq = appiondata.ApAlignParticleData()
		alignpartq['alignstack'] = self.alignstackdata
		alignpartq['partnum'] = partnum
		alignparts = alignpartq.query(results=1)
		return alignparts[0]			

	#=====================
	def insertClusterStackIntoDatabase(self, clusterstackfile, classnum, partlist, num_classes):
		clusterstackq = appiondata.ApClusteringStackData()
		clusterstackq['avg_imagicfile'] = clusterstackfile
		clusterstackq['var_imagicfile'] = None
		clusterstackq['num_classes'] = num_classes
		clusterstackq['clusterrun'] = self.clusterrun
		clusterstackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		clusterstackq['hidden'] = False

		if not os.path.isfile(clusterstackfile):
			apDisplay.printError("could not find average stack file: "+clusterstackfile)

		apDisplay.printMsg("inserting clustering stack into database")
		if self.params['commit'] is True:
			clusterstackq.insert()

		### insert particle class & reference data
		clusterrefq = appiondata.ApClusteringReferenceData()
		clusterrefq['refnum'] = classnum
		clusterrefq['clusterrun'] = self.clusterrun
		clusterrefq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		clusterrefq['num_particles'] = len(partlist)
		if classnum in self.resdict:
			clusterrefq['ssnr_resolution'] = self.resdict[classnum]
		apDisplay.printColor("Inserting particle classification data, please wait", "cyan")
		for i,partnum in enumerate(partlist):
			cpartq = appiondata.ApClusteringParticleData()
			if self.runparams['align'] is True and self.params['commit'] is True:
				alignpartdata = self.getAlignParticleData(int(partnum)+1)
				cpartq['alignparticle'] = alignpartdata
			else:
				cpartq['alignparticle'] = None
			cpartq['clusterstack'] = clusterstackq
			cpartq['partnum'] = int(partnum)+1
			cpartq['refnum'] = classnum
			cpartq['clusterreference'] = clusterrefq
			# actual parameters
			if self.params['commit'] is True:
				cpartq.insert()
		return

	#=====================
	def start(self):
		### load parameters
		self.runparams = self.readRunParameters()
		self.apix = apStack.getStackPixelSizeFromStackId(self.runparams['stackid'])*self.runparams['bin']
		self.Nlevels=len(glob.glob("part"+self.params['timestamp']+"_level_??_.hed"))

		### create average of aligned stacks & insert aligned stack info
		lastLevelStack = "part"+self.params['timestamp']+"_level_%02d_.hed"%(self.Nlevels-1)
		self.boxsize = apFile.getBoxSize(lastLevelStack)[0]
		if self.runparams['align']:
			self.insertAlignStackRunIntoDatabase("alignedStack.hed")
			self.calcResolution(self.Nlevels-1)
			self.insertAlignParticlesIntoDatabase(level=self.Nlevels-1)
		
		### loop over each class average stack & insert as clustering stacks
		self.insertClusterRunIntoDatabase()
		for level in range(self.Nlevels):
			if self.runparams['align']:
				self.calcResolution(level)
			partdict = self.getClassificationAtLevel(level)
			for classnum in partdict: 
				self.insertClusterStackIntoDatabase(
					"part"+self.params['timestamp']+"_level_%02d_.hed"%level,
					classnum+1, partdict[classnum], len(partdict))

#=====================
if __name__ == "__main__":
	cl2d = UploadCL2DScript()
	cl2d.start()
	cl2d.close()
