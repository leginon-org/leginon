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
import cPickle
#appion
import appionScript
import apDisplay
import apAlignment
import apFile
import apParam
import apTemplate
import apStack
import apEMAN
import apXmipp
from apSpider import operations
import appionData
import apProject

#=====================
#=====================
class UploadMaxLikeScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --jobid=ID [ --commit ]")
		self.parser.add_option("-j", "--jobid", dest="jobid", type="int",
			help="Maximum likelihood jobid", metavar="#")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("-t", "--timestamp", dest="timestamp",
			help="Timestamp of files, e.g. 08nov02b35", metavar="CODE")

		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit stack to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit stack to database")

	#=====================
	def checkConflicts(self):
		if self.params['timestamp'] is None:
			apDisplay.printError("Please enter the job timestamp, e.g. 08nov02b35")
		return

	#=====================
	def setOutDir(self):
		if self.params["jobid"] is not None:
			self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
			path = self.stackdata['path']['path']
			uppath = os.path.abspath(os.path.join(path, "../.."))
			self.params['outdir'] = os.path.join(uppath, "maxlike", self.params['runname'])
		else:
			self.params['outdir'] = os.path.abspath(".")

	#=====================
	def findLastIterNumber(self):
		lastiter = 0
		logfiles = glob.glob("*it*.log")
		for logfile in logfiles:
			m = re.search("it0*([0-9]*).log$", logfile)
			iternum = int(m.groups()[0])
			if iternum > lastiter:
				lastiter = iternum
		apDisplay.printMsg("Xmipp ran "+str(lastiter)+" iterations")
		return lastiter

	#=====================
	def sortFolder(self, lastiter):
		### move files for all iterations except last iter
		for i in range(lastiter):
			iterdir = "iter%03d"%(i)
			apParam.createDirectory(iterdir, warning=False)
			wildcard = "*_it%06d*.*"%(i)
			files = glob.glob(wildcard)
			for filename in files:
				shutil.move(filename,iterdir)
		return

	#=====================
	def readDocFile(self, iternum):
		partlist = []
		wildcard = "*_it%06d.doc"%(iternum)
		files = glob.glob(wildcard)
		if len(files) != 1:
			apDisplay.printError("could not find doc file to read angles")
		docfile = files[0]
		f = open(docfile, "r")
		for line in f:
			if line[:2] == ' ;':
				continue
			spidict = operations.spiderInLine(line)
			partdict = self.spidict2partdict(spidict)
			partlist.append(partdict)
		apDisplay.printMsg("read rotation and shift parameters for "+str(len(partlist))+" particles")
		return partlist

	#=====================
	def spidict2partdict(self, spidict):
		partdict = {
			'partnum': spidict['row'],
			'inplane': spidict['floatlist'][2],
			'xshift': spidict['floatlist'][3],
			'yshift': spidict['floatlist'][4],
			'refnum': spidict['floatlist'][5],
			'mirror': spidict['floatlist'][6],
			'spread': spidict['floatlist'][7],
		}
		return partdict

	#=====================
	def readRunParameters(self):
		paramfile = "maxlike-"+self.params['timestamp']+"-params.pickle"
		if not os.path.isfile(paramfile):
			apDisplay.printError("Could not find run parameters file: "+paramfile)
		f = open(paramfile, "r")
		runparams = cPickle.load(f)
		return runparams

	#=====================
	def insertRunIntoDatabase(self, runparams, lastiter):
		apDisplay.printMsg("Inserting MaxLike Run into DB")

		### setup max like run
		maxlikeq = appionData.ApMaxLikeRunData()
		maxlikeq['name'] = runparams['runname']
		maxlikeq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		uniquerun = maxlikeq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+runparams['runname']+"' and path already exist in database")

		maxlikeq['description'] = runparams['description']
		maxlikeq['run_seconds'] = runparams['runtime']
		#maxlikeq['mask_diam'] = 2.0*runparams['maskrad']
		maxlikeq['lp_filt'] = runparams['lowpass']
		maxlikeq['hp_filt'] = runparams['highpass']
		maxlikeq['num_particles'] =  runparams['numpart']
		maxlikeq['bin'] = runparams['bin']
		maxlikeq['fast'] = runparams['fast']
		maxlikeq['mirror'] = runparams['mirror']

		### setup alignment run
		alignrunq = appionData.ApAlignRunData()
		alignrunq['maxlikerun'] = maxlikeq
		alignrunq['hidden'] =  False
		alignrunq['project|projects|project'] = apProject.getProjectIdFromStackId(runparams['stackid'])

		### setup alignment stack
		alignstackq = appionData.ApAlignStackData()
#$$$		alignstackq['imagicfile', str),
#$$$		alignstackq['spiderfile', str),
		alignstackq['iteration'] = lastiter
		alignstackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		alignstackq['alignrun'] = alignrunq
		### check to make sure files exist
		#imagicfile = os.path.join(self.params['outdir'], alignstackq['imagicfile'])
		#if not os.path.isfile(imagicfile):
		#	apDisplay.printError("could not find stack file: "+imagicfile)
		#spiderfile = os.path.join(self.params['outdir'], alignstackq['spiderfile'])
		#if not os.path.isfile(spiderfile):
		#	apDisplay.printError("could not find stack file: "+spiderfile)
		alignstackq['stack'] = apStack.getOnlyStackData(runparams['stackid'])
		alignstackq['boxsize'] = math.floor(apStack.getStackBoxsize(runparams['stackid'])/runparams['bin'])
		alignstackq['pixelsize'] = apStack.getStackPixelSizeFromStackId(runparams['stackid'])*runparams['bin']
		alignstackq['description'] = runparams['description']
		alignstackq['hidden'] =  False
		alignstackq['project|projects|project'] = apProject.getProjectIdFromStackId(runparams['stackid'])

		### insert
		if self.params['commit'] is True:
			alignstackq.insert()
		self.alignstackdata = alignstackq

		return

	#=====================
	def insertParticlesIntoDatabase(self, stackid, partlist, lastiter):
		count = 0
		t0 = time.time()
		apDisplay.printMsg("Inserting MaxLike Particles into DB")
		for partdict in partlist:
			count += 1
			if count % 100 == 0:
				sys.stderr.write(".")

			### setup reference
			refq = appionData.ApAlignReferenceData()
			refq['refnum'] = partdict['refnum']
			refq['iteration'] = lastiter
			refbase = self.params['timestamp']+"_it%06d_ref%06d"%(lastiter,partdict['refnum'])
			refq['mrcfile'] = refbase+".mrc"
			refq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
			refq['alignrun'] = self.alignstackdata['alignrun']
			reffile = os.path.join(self.params['outdir'], refq['mrcfile'])
			if not os.path.isfile(reffile):
				emancmd = "proc2d "+refbase+".xmp "+refbase+".mrc"
				apEMAN.executeEmanCmd(emancmd, verbose=False)
			if not os.path.isfile(reffile):
				apDisplay.printError("could not find reference file: "+reffile)

			### setup particle
			alignpartq = appionData.ApAlignParticlesData()
			alignpartq['partnum'] = partdict['partnum']
			alignpartq['alignstack'] = self.alignstackdata
			stackpartdata = apStack.getStackParticle(stackid, partdict['partnum'])
			alignpartq['stackpart'] = stackpartdata
			alignpartq['xshift'] = partdict['xshift']
			alignpartq['yshift'] = partdict['yshift']
			alignpartq['rotation'] = partdict['inplane']
			alignpartq['mirror'] = partdict['mirror']
			alignpartq['ref'] = refq
			alignpartq['spread'] = partdict['spread']

			### insert
			if self.params['commit'] is True:
				alignpartq.insert()

		apDisplay.printColor("\ninserted "+str(count)+" particles into the database in "
			+apDisplay.timeString(time.time()-t0), "cyan")

		return

	#=====================
	def start(self):
		### load parameters
		runparams = self.readRunParameters()

		### read particles
		lastiter = self.findLastIterNumber()
		self.sortFolder(lastiter)
		partlist = self.readDocFile(lastiter)

		### insert into databse
		self.insertRunIntoDatabase(runparams, lastiter)
		self.insertParticlesIntoDatabase(runparams['stackid'], partlist, lastiter)

#=====================
if __name__ == "__main__":
	maxLike = UploadMaxLikeScript()
	maxLike.start()
	maxLike.close()


