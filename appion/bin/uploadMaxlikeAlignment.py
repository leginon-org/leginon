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
import appiondata
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
		self.parser.add_option("-t", "--timestamp", dest="timestamp",
			help="Timestamp of files, e.g. 08nov02b35", metavar="CODE")

		self.parser.add_option("--no-sort", dest="sort", default=True,
			action="store_false", help="Do not sort files into nice folders")


	#=====================
	def checkConflicts(self):
		if self.params['timestamp'] is None:
			self.params['timestamp'] = self.getTimestamp()
		return

	#=====================
	def setRunDir(self):
		if self.params["jobid"] is not None:
			jobdata = appiondata.ApMaxLikeJobData.direct_query(self.params["jobid"])
			self.params['rundir'] = jobdata['path']['path']
		else:
			self.params['rundir'] = os.path.abspath(".")

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
	def getTimestamp(self):
		if self.params["jobid"] is not None:
			jobdata = appiondata.ApMaxLikeJobData.direct_query(self.params["jobid"])
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
	def sortFolder(self):
		numsort = 0
		apDisplay.printMsg("Sorting files into clean folders")
		### move files for all particle iterations
		files = []
		for i in range(self.lastiter+1):
			iterdir = "iter%03d"%(i)
			apParam.createDirectory(iterdir, warning=False)
			wildcard = "part*_it*%03d_*.*"%(i)
			files.extend(glob.glob(wildcard))
			wildcard = "part*_it*%03d.*"%(i)
			files.extend(glob.glob(wildcard))
			for filename in files:
				if os.path.isfile(filename):
					numsort += 1
					shutil.move(filename,iterdir)
		if numsort < 3:
			apDisplay.printWarning("Problem in iteration file sorting, are they already sorted?")
		apDisplay.printMsg("Sorted "+str(numsort)+" iteration files")
		### move files for all reference iterations
		refsort = 0
		refdir = "refalign"
		apParam.createDirectory(refdir, warning=False)
		wildcard = "ref*_it*.*"
		files = glob.glob(wildcard)
		for filename in files:
			refsort += 1
			shutil.move(filename, refdir)
		#if refsort < 5:
		#	apDisplay.printError("Problem in reference file sorting")
		apDisplay.printMsg("Sorted "+str(refsort)+" reference files")
		return

	#=====================
	def readRefDocFile(self):
		reflist = []
		docfile = "ref"+self.params['timestamp']+".doc"
		if not os.path.isfile(docfile):
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
	def readPartDocFile(self, reflist):
		partlist = []
		docfile = "part"+self.params['timestamp']+".doc"
		if not os.path.isfile(docfile) or apFile.fileSize(docfile) < 50:
			apDisplay.printWarning("Could not find doc file "+docfile+" to read particle angles")
			lastdocfile = "iter%03d/part%s_it%06d.doc"%(self.lastiter, self.params['timestamp'], self.lastiter)
			if not os.path.isfile(lastdocfile) or apFile.fileSize(lastdocfile) < 50:
				apDisplay.printError("Could not find backup doc file")
			apDisplay.printColor("Found a backup copy of docfile", "green")
			shutil.copy(lastdocfile, docfile)
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
		if len(partlist) < 1:
			apDisplay.printError("Did not find any particles in doc file: "+docfile)
		return partlist

	#=====================
	def writePartDocFile(self, partlist):
		docfile = "finalshifts_"+self.params['timestamp']+".doc"
		f = open(docfile, "w")
		dlist = ['inplane', 'xshift', 'yshift', 'refnum', 'mirror', 'spread']
		f.write(" ; partnum ... "+str(dlist)+"\n")
		for partdict in partlist:
			floatlist = []
			for key in dlist:
				floatlist.append(partdict[key])
			line = operations.spiderOutLine(partdict['partnum'], floatlist)
			f.write(line)
		f.write(" ; partnum ... "+str(dlist)+"\n")
		f.close()
		apDisplay.printMsg("wrote rotation and shift parameters to "+docfile+" for "+str(len(partlist))+" particles")
		return

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
			'mirror': self.xor(origpartdict['mirror'],refdict['mirror']),
			'spread': origpartdict['spread'],
		}
		return newpartdict

	#=====================
	def xor(self, a ,b):
		xor = (a and not b) or (b and not a)
		return bool(xor)


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
		if not 'localstack' in runparams:
			runparams['localstack'] = self.params['timestamp']+".hed"
		return runparams

	#=====================
	def getMaxLikeJob(self, runparams):
		maxjobq = appiondata.ApMaxLikeJobData()
		maxjobq['runname'] = runparams['runname']
		maxjobq['path'] = appiondata.ApPathData(path=os.path.abspath(runparams['rundir']))
		maxjobq['project|projects|project'] = apProject.getProjectIdFromStackId(runparams['stackid'])
		maxjobq['timestamp'] = self.params['timestamp']
		maxjobdata = maxjobq.query(results=1)
		if not maxjobdata:
			return None
		return maxjobdata[0]

	#=====================
	def insertRunIntoDatabase(self, runparams):
		apDisplay.printMsg("Inserting MaxLike Run into DB")

		### setup alignment run
		alignrunq = appiondata.ApAlignRunData()
		alignrunq['runname'] = runparams['runname']
		alignrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+runparams['runname']+"' and path already exist in database")

		### setup max like run
		maxlikeq = appiondata.ApMaxLikeRunData()
		maxlikeq['runname'] = runparams['runname']
		maxlikeq['run_seconds'] = runparams['runtime']
		#maxlikeq['mask_diam'] = 2.0*runparams['maskrad']
		maxlikeq['fast'] = runparams['fast']
		maxlikeq['fastmode'] = runparams['fastmode']
		maxlikeq['mirror'] = runparams['mirror']
		maxlikeq['init_method'] = "xmipp default"
		maxlikeq['job'] = self.getMaxLikeJob(runparams)

		### finish alignment run
		alignrunq['maxlikerun'] = maxlikeq
		alignrunq['hidden'] = False
		alignrunq['runname'] = runparams['runname']
		alignrunq['description'] = runparams['description']
		alignrunq['lp_filt'] = runparams['lowpass']
		alignrunq['hp_filt'] = runparams['highpass']
		alignrunq['bin'] = runparams['bin']
		alignrunq['project|projects|project'] = apProject.getProjectIdFromStackId(runparams['stackid'])

		### setup alignment stack
		alignstackq = appiondata.ApAlignStackData()
		alignstackq['imagicfile'] = "alignstack.hed"
		alignstackq['avgmrcfile'] = "average.mrc"
		alignstackq['refstackfile'] = "part"+self.params['timestamp']+"_average.hed"
		alignstackq['iteration'] = self.lastiter
		alignstackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		alignstackq['alignrun'] = alignrunq
		### check to make sure files exist
		imagicfile = os.path.join(self.params['rundir'], alignstackq['imagicfile'])
		if not os.path.isfile(imagicfile):
			apDisplay.printError("could not find stack file: "+imagicfile)
		avgmrcfile = os.path.join(self.params['rundir'], alignstackq['avgmrcfile'])
		if not os.path.isfile(avgmrcfile):
			apDisplay.printError("could not find average mrc file: "+avgmrcfile)
		refstackfile = os.path.join(self.params['rundir'], alignstackq['refstackfile'])
		if not os.path.isfile(refstackfile):
			apDisplay.printError("could not find reference stack file: "+refstackfile)
		alignstackq['stack'] = apStack.getOnlyStackData(runparams['stackid'])
		alignstackq['boxsize'] = math.floor(apStack.getStackBoxsize(runparams['stackid'])/runparams['bin'])
		alignstackq['pixelsize'] = apStack.getStackPixelSizeFromStackId(runparams['stackid'])*runparams['bin']
		alignstackq['description'] = runparams['description']
		alignstackq['hidden'] =  False
		alignstackq['num_particles'] =  runparams['numpart']
		alignstackq['project|projects|project'] = apProject.getProjectIdFromStackId(runparams['stackid'])

		### insert
		if self.params['commit'] is True:
			alignstackq.insert()
		self.alignstackdata = alignstackq

		return

	#=====================
	def insertParticlesIntoDatabase(self, stackid, partlist):
		count = 0
		inserted = 0
		t0 = time.time()
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		for partdict in partlist:
			count += 1
			if count % 100 == 0:
				sys.stderr.write(".")

			### setup reference
			refq = appiondata.ApAlignReferenceData()
			refq['refnum'] = partdict['refnum']
			refq['iteration'] = self.lastiter
			refsearch = "part"+self.params['timestamp']+"_ref*"+str(partdict['refnum'])+"*"
			refbase = os.path.splitext(glob.glob(refsearch)[0])[0]
			refq['mrcfile'] = refbase+".mrc"
			refq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			refq['alignrun'] = self.alignstackdata['alignrun']
			reffile = os.path.join(self.params['rundir'], refq['mrcfile'])
			if not os.path.isfile(reffile):
				emancmd = "proc2d "+refbase+".xmp "+refbase+".mrc"
				apEMAN.executeEmanCmd(emancmd, verbose=False)
			if not os.path.isfile(reffile):
				apDisplay.printError("could not find reference file: "+reffile)

			### setup particle
			alignpartq = appiondata.ApAlignParticlesData()
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
	def createAlignedStacks(self, partlist, origstackfile):
		partperiter = 4096
		numpart = len(partlist)
		if numpart < partperiter:
			partperiter = numpart

		t0 = time.time()
		imgnum = 0
		stacklist = []
		apDisplay.printMsg("rotating and shifting particles at "+time.asctime())
		while imgnum < len(partlist):
			index = imgnum % partperiter
			if imgnum % 100 == 0:
				sys.stderr.write(".")
			if index == 0:
				### deal with large stacks
				if imgnum > 0:
					sys.stderr.write("\n")
					stackname = "alignstack%d.hed"%(imgnum)
					apDisplay.printMsg("writing aligned particles to file "+stackname)
					stacklist.append(stackname)
					apFile.removeStack(stackname, warn=False)
					apImagicFile.writeImagic(alignstack, stackname, msg=False)
					perpart = (time.time()-t0)/imgnum
					apDisplay.printColor("particle %d of %d :: %s per part :: %s remain"%
						(imgnum+1, numpart, apDisplay.timeString(perpart),
						apDisplay.timeString(perpart*(numpart-imgnum))), "blue")
				alignstack = []
				imagesdict = apImagicFile.readImagic(origstackfile, first=imgnum+1, last=imgnum+partperiter, msg=False)

			### align particles
			partimg = imagesdict['images'][index]
			partdict = partlist[imgnum]
			partnum = imgnum+1
			if partdict['partnum'] != partnum:
				apDisplay.printError("particle shifting "+str(partnum)+" != "+str(partdict))
			xyshift = (partdict['xshift'], partdict['yshift'])
			alignpartimg = apImage.xmippTransform(partimg, rot=partdict['inplane'],
				shift=xyshift, mirror=partdict['mirror'])
			alignstack.append(alignpartimg)
			imgnum += 1

		### write remaining particle to file
		sys.stderr.write("\n")
		stackname = "alignstack%d.hed"%(imgnum)
		apDisplay.printMsg("writing aligned particles to file "+stackname)
		stacklist.append(stackname)
		apImagicFile.writeImagic(alignstack, stackname, msg=False)

		### merge stacks
		self.alignimagicfile = "alignstack.hed"
		apFile.removeStack(self.alignimagicfile, warn=False)
		apImagicFile.mergeStacks(stacklist, self.alignimagicfile)
		#for stackname in stacklist:
		#	emancmd = "proc2d %s %s"%(stackname, self.alignimagicfile)
		#	apEMAN.executeEmanCmd(emancmd, verbose=False)
		filepart = apFile.numImagesInStack(self.alignimagicfile)
		if filepart != numpart:
			apDisplay.printError("number aligned particles (%d) not equal number expected particles (%d)"%
				(filepart, numpart))
		for stackname in stacklist:
			apFile.removeStack(stackname, warn=False)

		### summarize
		apDisplay.printMsg("rotated and shifted %d particles in %s"%(imgnum, apDisplay.timeString(time.time()-t0)))

		apStack.averageStack(self.alignimagicfile)

	#=====================
	def writeXmippLog(self, text):
		f = open("xmipp.log", "a")
		f.write(apParam.getLogHeader())
		f.write(text+"\n")
		f.close()

	#=====================
	def alignReferences(self, runparams):
		### align references
		xmippopts = ( " "
			+" -i "+os.path.join(self.params['rundir'], "part"+self.params['timestamp']+".sel")
			+" -nref 1 "
			+" -iter 20 "
			+" -o "+os.path.join(self.params['rundir'], "ref"+self.params['timestamp'])
			+" -psi_step 1 "
			#+" -fast -C 1e-18 "
			+" -eps 5e-8 "
		)
		if runparams['mirror'] is True:
			xmippopts += " -mirror "
		xmippexe = apParam.getExecPath("xmipp_ml_align2d")
		xmippcmd = xmippexe+" "+xmippopts
		self.writeXmippLog(xmippcmd)
		apEMAN.executeEmanCmd(xmippcmd, verbose=True, showcmd=True)

	#=====================
	def createAlignedReferenceStack(self):
		searchstr = "part"+self.params['timestamp']+"_ref0*.xmp"
		files = glob.glob(searchstr)
		files.sort()
		stack = []
		reflist = self.readRefDocFile()
		for i in range(len(files)):
			fname = files[i]
			refdict = reflist[i]
			if refdict['partnum'] != i+1:
				print i, refdict['partnum']
				apDisplay.printError("sorting error in reflist, see neil")
			refarray = spider.read(fname)
			xyshift = (refdict['xshift'], refdict['yshift'])
			alignrefarray = apImage.xmippTransform(refarray, rot=refdict['inplane'],
				shift=xyshift, mirror=refdict['mirror'])
			stack.append(alignrefarray)
		stackarray = numpy.asarray(stack, dtype=numpy.float32)
		#print stackarray.shape
		avgstack = "part"+self.params['timestamp']+"_average.hed"
		apFile.removeStack(avgstack, warn=False)
		apImagicFile.writeImagic(stackarray, avgstack)
		### create a average mrc
		avgdata = stackarray.mean(0)
		apImage.arrayToMrc(avgdata, "average.mrc")
		return

	#=====================
	def readRefDocFile(self):
		reflist = []
		docfile = "ref"+self.params['timestamp']+".doc"
		if not os.path.isfile(docfile):
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
	def start(self):
		### load parameters
		runparams = self.readRunParameters()

		### align references
		self.alignReferences(runparams)

		### create an aligned stack
		self.createAlignedReferenceStack()

		### read particles
		self.lastiter = self.findLastIterNumber()
		if self.params['sort'] is True:
			self.sortFolder()
		reflist = self.readRefDocFile()
		partlist = self.readPartDocFile(reflist)
		self.writePartDocFile(partlist)

		### create aligned stacks
		stackfile = self.createAlignedStacks(partlist, runparams['localstack'])

		### insert into databse
		self.insertRunIntoDatabase(runparams)
		self.insertParticlesIntoDatabase(runparams['stackid'], partlist)

		apFile.removeStack(runparams['localstack'], warn=False)
		rmcmd = "rm -fr partfiles/*"
		apEMAN.executeEmanCmd(rmcmd, verbose=False, showcmd=False)
		apFile.removeFilePattern("partfiles/*")

#=====================
if __name__ == "__main__":
	maxLike = UploadMaxLikeScript(True)
	maxLike.start()
	maxLike.close()



