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
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit stack to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit stack to database")

	#=====================
	def checkConflicts(self):
		return

	#=====================
	def setOutDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['outdir'] = os.path.join(uppath, "maxlike", self.params['runname'])

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
			'prob_spread': spidict['floatlist'][7],
		}
		return partdict


	#=====================
	def readRunParameters(self):
		paramfile = "maxlike-params.pickle"
		if not os.path.isfile(paramfile):
			apDisplay.printError("Could not find run parameters file")
		runparams = cPickle.load(paramfile)
		return runparams

	#=====================
	def insertRunIntoDatabase(self, runparams):
		maxlikeq = appionData.ApMaxLikeRunData()
		maxlikeq['name'] = runparams['runname']
		maxlikeq['stack'] = apStack.getOnlyStackData(runparams['stackid'])
		maxlikeq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		maxlikeq['description'] = runparams['description']
		maxlikeq['run_seconds'] = runparams['runtime']
		maxlikeq['hidden'] =  False
		maxlikeq['mask_diam'] = 2.0*runparams['maskrad']
		maxlikeq['lp_filt'] = runparams['lowpass']
		maxlikeq['hp_filt'] = runparams['highpass']
		maxlikeq['num_particles'] =  runparams['numpart']
		maxlikeq['bin'] = runparams['bin']
		maxlikeq['fast'] = runparams['fast']
		maxlikeq['mirror'] = runparams['mirror']

		if self.params['commit'] is True:
			maxlikeq.insert()

		return

	#=====================
	def insertParticlesIntoDatabase(self, partlist):
		for partdict in partlist:
			mlpartq = appionData.ApMaxLikeAlignParticlesData()


			if self.params['commit'] is True:
				mlpartq.insert()

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
		self.insertRunIntoDatabase(runparams)
		self.insertRunIntoDatabase(partlist)

#=====================
if __name__ == "__main__":
	maxLike = UploadMaxLikeScript()
	maxLike.start()
	maxLike.close()


