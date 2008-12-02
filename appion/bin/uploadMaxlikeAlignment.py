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
import appionScript
import apDisplay
import apFile
import apParam
import apStack
import apImage
import apEMAN
import apImagicFile
from apSpider import operations
import appionData
import apProject
from pyami import spider

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

		self.parser.add_option("--no-sort", dest="sort", default=True,
			action="store_false", help="Do not sort files into nice folders")

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
		for i in range(lastiter+1):
			iterdir = "iter%03d"%(i)
			apParam.createDirectory(iterdir, warning=False)
			wildcard = "*_it%06d*.*"%(i)
			files = glob.glob(wildcard)
			for filename in files:
				shutil.move(filename,iterdir)
		return

	#=====================
	def readRefDocFile(self, iternum):
		reflist = []
		docfile = "ref"+self.params['timestamp']+".doc"
		if os.path.isfile(docfile):
			apDisplay.printError("could not find doc file "+docfile+" to read reference angles")
		f = open(docfile, "r")
		mininplane = 360.0
		for line in f:
			if line[:2] == ' ;':
				continue
			spidict = operations.spiderInLine(line)
			refdict = self.spidict2partdict(spidict)
			if refdict['inplane'] < mininplane:
				mininplane = refdict['inplane']
			reflist.append(refdict)
		for refdict in reflist:
			refdict['inplane'] = refdict['inplane']-mininplane
		apDisplay.printMsg("read rotation and shift parameters for "+str(len(reflist))+" references")
		return reflist

	#=====================
	def readPartDocFile(self, iternum, reflist):
		partlist = []
		docfile = "part"+self.params['timestamp']+".doc"
		if os.path.isfile(docfile):
			apDisplay.printError("could not find doc file "+docfile+" to read particle angles")
		f = open(docfile, "r")
		mininplane = 360.0
		for line in f:
			if line[:2] == ' ;':
				continue
			spidict = operations.spiderInLine(line)
			origpartdict = self.spidict2partdict(spidict)
			partdict = self.adjustPartDict(origpartdict, reflist)
			if partdict['inplane'] < mininplane:
				mininplane = partdict['inplane']
			partlist.append(partdict)
		apDisplay.printMsg("minimum inplane: "+str(mininplane))
		for partdict in partlist:
			partdict['inplane'] = partdict['inplane']-mininplane
		apDisplay.printMsg("read rotation and shift parameters for "+str(len(partlist))+" particles")
		return partlist

	#=====================
	def spidict2partdict(self, spidict):
		partdict = {
			'partnum': int(spidict['row']),
			'inplane': float(spidict['floatlist'][2]),
			'xshift': float(spidict['floatlist'][3]),
			'yshift': float(spidict['floatlist'][4]),
			'refnum': int(spidict['floatlist'][5]),
			'mirror': bool(spidict['floatlist'][6]),
			'spread': float(spidict['floatlist'][7]),
		}
		return partdict

	#=====================
	def adjustPartDict(self, origpartdict, reflist):
		refdict = reflist[origpartdict['refnum']-1]
		if refdict['partnum'] != origpartdict['refnum']:
			apDisplay.printError("sorting error in reflist, see neil")
		newpartdict = {
			'partnum': origpartdict['partnum'],
			'inplane': self.wrap360(origpartdict['inplane']+refdict['inplane']),
			'xshift': origpartdict['xshift']+refdict['xshift'],
			'yshift': origpartdict['yshift']+refdict['yshift'],
			'refnum': origpartdict['refnum'],
			'mirror': origpartdict['mirror']*refdict['mirror'],
			'spread': origpartdict['spread'],
		}
		return newpartdict

	#=====================
	def wrap360(self, theta):
		f = theta % 360
		if f > 180:
			f = f - 360.0
		return f

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

		### setup alignment run
		alignrunq = appionData.ApAlignRunData()
		alignrunq['runname'] = runparams['runname']
		alignrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		uniquerun = alignrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+runparams['runname']+"' and path already exist in database")

		### setup max like run
		maxlikeq = appionData.ApMaxLikeRunData()
		maxlikeq['runname'] = runparams['runname']
		maxlikeq['run_seconds'] = runparams['runtime']
		#maxlikeq['mask_diam'] = 2.0*runparams['maskrad']
		maxlikeq['fast'] = runparams['fast']
		maxlikeq['mirror'] = runparams['mirror']

		### finish alignment run
		alignrunq['maxlikerun'] = maxlikeq
		alignrunq['hidden'] = False
		alignrunq['runname'] = runparams['runname']
		alignrunq['description'] = runparams['description']
		alignrunq['lp_filt'] = runparams['lowpass']
		alignrunq['hp_filt'] = runparams['highpass']
		alignrunq['num_particles'] =  runparams['numpart']
		alignrunq['bin'] = runparams['bin']
		alignrunq['project|projects|project'] = apProject.getProjectIdFromStackId(runparams['stackid'])

		### setup alignment stack
		alignstackq = appionData.ApAlignStackData()
		alignstackq['imagicfile'] = "alignstack.hed"
		alignstackq['spiderfile'] = "alignstack.spi"
		alignstackq['avgmrcfile'] = "average.mrc"
		alignstackq['iteration'] = lastiter
		alignstackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		alignstackq['alignrun'] = alignrunq
		### check to make sure files exist
		imagicfile = os.path.join(self.params['outdir'], alignstackq['imagicfile'])
		if not os.path.isfile(imagicfile):
			apDisplay.printError("could not find stack file: "+imagicfile)
		spiderfile = os.path.join(self.params['outdir'], alignstackq['spiderfile'])
		if not os.path.isfile(spiderfile):
			apDisplay.printError("could not find stack file: "+spiderfile)
		averagefile = os.path.join(self.params['outdir'], alignstackq['avgmrcfile'])
		if not os.path.isfile(averagefile):
			apDisplay.printError("could not find average stack file: "+averagefile)
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
		inserted = 0
		t0 = time.time()
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		for partdict in partlist:
			count += 1
			if count % 100 == 0:
				sys.stderr.write(".")

			### setup reference
			refq = appionData.ApAlignReferenceData()
			refq['refnum'] = partdict['refnum']
			refq['iteration'] = lastiter
			refbase = self.params['timestamp']+"_ref%06d"%(partdict['refnum'])
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
				inserted += 1
				alignpartq.insert()

		apDisplay.printColor("\ninserted "+str(inserted)+" of "+str(count)+" particles into the database in "
			+apDisplay.timeString(time.time()-t0), "cyan")

		return

	#=====================
	def convertStackToSpider(self, imagicstack, spiderstack):
		"""
		takes the stack file and creates a spider file ready for processing
		"""
		if not os.path.isfile(imagicstack):
			apDisplay.printError("stackfile does not exist: "+imagicstack)

		### convert imagic stack to spider
		emancmd  = "proc2d "
		emancmd += imagicstack+" "
		apFile.removeFile(spiderstack, warn=True)
		emancmd += spiderstack+" "
		emancmd += "spiderswap"
		starttime = time.time()
		apDisplay.printColor("Running spider stack conversion this can take a while", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return

	#=====================
	def createAlignedStacks(self, stackid, partlist):
		stackdata = apStack.getOnlyStackData(stackid)
		origstackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		imagesdict = apImagicFile.readImagic(origstackfile)
		spiderstackfile = os.path.join(self.params['outdir'], "alignstack.spi")
		apFile.removeFile(spiderstackfile)

		i = 0
		t0 = time.time()
		apDisplay.printMsg("rotating and shifting particles at "+time.asctime())
		alignstack = []
		while i < len(partlist):
			partimg = imagesdict['images'][i]
			partdict = partlist[i]
			partnum = i+1
			#print partnum, partdict, partimg.shape
			if partdict['partnum'] != partnum:
				apDisplay.printError("particle shifting "+str(partnum)+" != "+str(partdict))
			xyshift = (partdict['xshift'], partdict['yshift'])
			alignpartimg = apImage.rotateThenShift(partimg, rot=partdict['inplane'], shift=xyshift)
			alignstack.append(alignpartimg)
			#partfile = "partimg%06d.spi"%(partnum)
			#spider.write(alignpartimg, partfile)
			#operations.addParticleToStack(partnum, partfile, spiderstackfile)
			#apFile.removeFile(partfile)
			i += 1
		apDisplay.printMsg("rotate then shift %d particles in %s"%(i,apDisplay.timeString(time.time()-t0)))
		alignstackarray = numpy.asarray(alignstack)
		self.alignimagicfile = "alignstack.hed"
		self.alignspiderfile = "alignstack.spi"
		apImagicFile.writeImagic(alignstackarray, self.alignimagicfile)
		self.convertStackToSpider(self.alignimagicfile, self.alignspiderfile)
		apStack.averageStack(self.alignimagicfile)

	#=====================
	def start(self):
		### load parameters
		runparams = self.readRunParameters()

		### read particles
		lastiter = self.findLastIterNumber()
		if self.params['sort'] is True:
			self.sortFolder(lastiter)
		reflist = self.readRefDocFile(lastiter)
		partlist = self.readPartDocFile(lastiter, reflist)

		### create aligned stacks
		stackfile = self.createAlignedStacks(runparams['stackid'], partlist)

		### insert into databse
		self.insertRunIntoDatabase(runparams, lastiter)
		self.insertParticlesIntoDatabase(runparams['stackid'], partlist, lastiter)

#=====================
if __name__ == "__main__":
	maxLike = UploadMaxLikeScript()
	maxLike.start()
	maxLike.close()


