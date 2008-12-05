#!/usr/bin/env python
#
import os
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
import appionData

#=====================
#=====================
class CoranClassifyScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --alignstack=ID --mask=# [ --num-part=# ]")

		### custom params
		self.parser.add_option("--num-factors", dest="numfactors", type="int", default=8,
			help="Number of factors to use in classification", metavar="#")
		self.parser.add_option("-s", "--alignstack", dest="alignstackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("-m", "--mask", "--maskrad", dest="maskrad", type="float",
			help="Mask radius for particle coran (in Angstoms)", metavar="#")

		### common params
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit stack to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit stack to database")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("-d", "--description", dest="description",
			help="Description of run", metavar="'TEXT'")
		self.parser.add_option("-n", "--runname", dest="runname",
			help="Name for this run", metavar="STR")

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
		if self.params['numfactors'] > 20:
			apDisplay.printError("too many factors defined: "+str(self.params['numfactors']))

	#=====================
	def setOutDir(self):
		alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
		path = self.alignstackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['outdir'] = os.path.join(uppath, "coran", self.params['runname'])

	#=====================
	def checkCoranRun(self):
		# create a norefParam object
		analysisq = appionData.ApAlignAnalysisRunData()
		analysisq['runname'] = self.params['runname']
		analysisq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		# ... path makes the run unique:
		uniquerun = analysisq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+self.params['runname']+"' for stackid="+\
				str(self.params['alignstackid'])+"\nis already in the database")

	#=====================
	def insertCoranRun(self, insert=False):
		# create a AlignAnalysisRun object
		analysisq = appionData.ApAlignAnalysisRunData()
		analysisq['runname'] = self.params['runname']
		analysisq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		# ... path makes the run unique:
		uniquerun = analysisq.query(results=1)
		if uniquerun and insert is True:
			apDisplay.printError("Run name '"+self.params['runname']+"' for align stack id="+\
				str(self.params['alignstackid'])+"\nis already in the database")

		coranq = appionData.ApCoranRunData()
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
			eigenq = appionData.ApCoranEigenImageData()
			eigenq['coranRun'] = coranq
			eigenq['factor_num'] = factnum
			path = os.path.join(self.params['outdir'], "coran")
			eigenq['path'] = appionData.ApPathData(path=os.path.abspath(path))
			imgname = ("eigenimg%02d.png" % (factnum))
			eigenq['image_name'] = imgname
			if insert is True:
				if not os.path.isfile(os.path.join(path, imgname)):
					apDisplay.printWarning(imgname+" does not exist")
					continue
				eigenq['percent_contrib'] = self.contriblist[i]
				eigenq.insert()

		return

	#=====================
	def getAlignedStack(self):
		return appionData.ApAlignStackData.direct_query(self.params['alignstackid'])

	#=====================
	def getNumAlignedParticles(self):
		t0 = time.time()
		partq = appionData.ApAlignParticlesData()
		alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
		partq['alignstack'] = alignstackdata
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
		maskpixrad = self.params['maskrad']/self.alignstackdata['pixelsize']
		clippixdiam = int(math.ceil(maskpixrad)+1)*2
		apDisplay.printMsg("Pixel mask radius="+str(maskpixrad)) 

		oldalignedstack = os.path.join(self.alignstackdata['path']['path'], self.alignstackdata['spiderfile'])
		alignedstack = os.path.join(self.params['outdir'], self.alignstackdata['spiderfile'])
		emancmd = "proc2d "+oldalignedstack+" "+alignedstack+" clip="+str(clippixdiam)+","+str(clippixdiam)
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		numpart = self.getNumAlignedParticles()

		esttime = apAlignment.estimateTime(numpart, maskpixrad)
		apDisplay.printColor("Running spider this can take awhile, estimated time: "+\
			apDisplay.timeString(esttime),"cyan")

		### do correspondence analysis
		corantime = time.time()
		self.contriblist = alignment.correspondenceAnalysis( alignedstack, 
			boxsize=clippixdiam, maskpixrad=maskpixrad, 
			numpart=numpart, numfactors=self.params['numfactors'])
		corantime = time.time() - corantime

		### make dendrogram
		alignment.makeDendrogram(alignedstack, numfactors=self.params['numfactors'])

		inserttime = time.time()
		if self.params['commit'] is True:
			self.runtime = corantime
			self.insertCoranRun(insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")
		inserttime = time.time() - inserttime

		apDisplay.printMsg("Correspondence Analysis time: "+apDisplay.timeString(corantime))
		apDisplay.printMsg("Database Insertion time: "+apDisplay.timeString(inserttime))

#=====================
if __name__ == "__main__":
	coranClass = CoranClassifyScript()
	coranClass.start()
	coranClass.close()

