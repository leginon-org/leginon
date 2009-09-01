#!/usr/bin/env python
#
import os
import re
import time
import sys
import random
import math
import shutil
#appion
import appionScript
import apDisplay
import apAlignment
import apFile
import apTemplate
import apStack
import apProject
import apEMAN
from apSpider import alignment
import appiondata

#=====================
#=====================
class CoranClassifyScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --alignstack=ID --mask=# [ --num-part=# ]")

		### custom params
		self.parser.add_option("--num-factors", dest="numfactors", type="int", default=20,
			help="Number of factors to use in classification", metavar="#")
		self.parser.add_option("-s", "--alignstack", dest="alignstackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("-m", "--mask", "--maskrad", dest="maskrad", type="float",
			help="Mask radius for particle coran (in Angstoms)", metavar="#")
		self.parser.add_option("--num-part", dest="numpart", type="int",
			help="Number of particles to use in classification", metavar="#")
		self.parser.add_option("-b", "--bin", dest="bin", type="int", default=2,
			help="Particle binning", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['alignstackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['description'] is None:
			apDisplay.printError("run description was not defined")
		if self.params['maskrad'] is None:
			apDisplay.printError("a mask radius was not provided")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
		if self.params['numfactors'] > 60:
			apDisplay.printError("too many factors defined: "+str(self.params['numfactors']))

	#=====================
	def setRunDir(self):
		self.alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])
		path = self.alignstackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "coran", self.params['runname'])

	#=====================
	def checkCoranRun(self):
		# create a norefParam object
		analysisq = appiondata.ApAlignAnalysisRunData()
		analysisq['runname'] = self.params['runname']
		analysisq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		# ... path makes the run unique:
		uniquerun = analysisq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+self.params['runname']+"' for stackid="+\
				str(self.params['alignstackid'])+"\nis already in the database")

	#=====================
	def insertCoranRun(self, insert=False):
		# create a AlignAnalysisRun object
		analysisq = appiondata.ApAlignAnalysisRunData()
		analysisq['runname'] = self.params['runname']
		analysisq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		# ... path makes the run unique:
		uniquerun = analysisq.query(results=1)
		if uniquerun and insert is True:
			apDisplay.printError("Run name '"+self.params['runname']+"' for align stack id="+\
				str(self.params['alignstackid'])+"\nis already in the database")

		coranq = appiondata.ApCoranRunData()
		coranq['num_factors'] = self.params['numfactors']
		coranq['mask_diam'] = 2.0*self.params['maskrad']
		coranq['run_seconds'] = self.runtime

		# finish AlignAnalysisRun object
		analysisq['description'] = self.params['description']
		analysisq['alignstack'] = self.alignstackdata
		analysisq['hidden'] = False
		analysisq['project|projects|project'] = apProject.getProjectIdFromAlignStackId(self.params['alignstackid'])
		analysisq['coranrun'] = coranq

		apDisplay.printMsg("inserting Align Analysis Run parameters into database")
		if insert is True:
			analysisq.insert()

		### eigen data
		for i in range(self.params['numfactors']):
			factnum = i+1
			eigenq = appiondata.ApCoranEigenImageData()
			eigenq['coranRun'] = coranq
			eigenq['factor_num'] = factnum
			path = os.path.join(self.params['rundir'], "coran")
			eigenq['path'] = appiondata.ApPathData(path=os.path.abspath(path))
			imgname = ("eigenimg%02d.png" % (factnum))
			eigenq['image_name'] = imgname
			if not os.path.isfile(os.path.join(path, imgname)):
				apDisplay.printWarning(imgname+" does not exist")
				continue
			if insert is True:
				eigenq['percent_contrib'] = self.contriblist[i]
				eigenq.insert()

		return

	#=====================
	def getAlignedStack(self):
		return appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])

	#=====================
	def getNumAlignedParticles(self):
		t0 = time.time()
		partq = appiondata.ApAlignParticlesData()
		self.alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])
		partq['alignstack'] = self.alignstackdata
		partdata = partq.query()
		numpart = len(partdata)
		del partdata
		apDisplay.printMsg("numpart="+str(numpart)+" in "+apDisplay.timeString(time.time()-t0))
		return numpart

	#=====================
	def start(self):
		self.runtime = 0

		self.checkCoranRun()

		### convert stack to spider
		self.alignstackdata = self.getAlignedStack()
		maskpixrad = self.params['maskrad']/self.alignstackdata['pixelsize']/self.params['bin']
		boxpixdiam = int(math.ceil(maskpixrad)+1)*2
		if boxpixdiam*self.params['bin'] > self.alignstackdata['boxsize']:
			boxpixdiam = math.floor(self.alignstackdata['boxsize']/self.params['bin'])
		clippixdiam = boxpixdiam*self.params['bin']
		apDisplay.printMsg("Pixel mask radius="+str(maskpixrad))

		oldalignedstack = os.path.join(self.alignstackdata['path']['path'], self.alignstackdata['imagicfile'])
		alignedstackname = re.sub("\.", "_", self.alignstackdata['imagicfile'])+".spi"
		alignedstack = os.path.join(self.params['rundir'], alignedstackname)
		apFile.removeFile(alignedstack)
		emancmd = ("proc2d %s %s spiderswap shrink=%d clip=%d,%d"
			%(oldalignedstack,alignedstack,self.params['bin'],clippixdiam,clippixdiam))
		if self.params['numpart'] is not None:
			emancmd += " last=%d"%(self.params['numpart']-1)
			numpart = self.params['numpart']
		else:
			numpart = self.getNumAlignedParticles()
		apEMAN.executeEmanCmd(emancmd, verbose=True)

		esttime = apAlignment.estimateTime(numpart, maskpixrad)
		apDisplay.printColor("Running spider this can take awhile, estimated time: "+\
			apDisplay.timeString(esttime),"cyan")

		### do correspondence analysis
		corantime = time.time()
		self.contriblist = alignment.correspondenceAnalysis( alignedstack,
			boxsize=boxpixdiam, maskpixrad=maskpixrad,
			numpart=numpart, numfactors=self.params['numfactors'])
		corantime = time.time() - corantime

		### make dendrogram
		dendrotime = time.time()
		alignment.makeDendrogram(numfactors=min(3,self.params['numfactors']))
		dendrotime = time.time() - dendrotime

		inserttime = time.time()
		if self.params['commit'] is True:
			self.runtime = corantime
			self.insertCoranRun(insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")
		inserttime = time.time() - inserttime

		apFile.removeFile(alignedstack, warn=True)

		apDisplay.printMsg("Correspondence Analysis time: "+apDisplay.timeString(corantime))
		apDisplay.printMsg("Make Dendrogram time: "+apDisplay.timeString(dendrotime))
		apDisplay.printMsg("Database Insertion time: "+apDisplay.timeString(inserttime))

#=====================
if __name__ == "__main__":
	coranClass = CoranClassifyScript(True)
	coranClass.start()
	coranClass.close()


