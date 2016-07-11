#!/usr/bin/env python
#
import os
import re
import sys
import time
import glob
import numpy
import shutil
import cPickle
#appion
from appionlib import appionScript
from appionlib import apFile
from appionlib import apEMAN
from appionlib import apParam
from appionlib import apStack
from appionlib import apImage
from appionlib import starFile
from appionlib import apDisplay
from appionlib import apProject
from appionlib import apFourier
from appionlib import appiondata
from appionlib import apImagicFile
#pyami
from pyami import mrc

#=====================
#=====================
#FIXME: appionScript.AppionScript
class UploadRelionMaxLikeScript(appionScript.AppionScript):
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
		logfiles = glob.glob("*_it*_data.star")
		for logfile in logfiles:
			m = re.search("it([0-9]+)_data\.star$", logfile)
			if not m: #handle a case when logfile is like blahmaskitonmaxlike7.appionsub.log
			 	apDisplay.printWarning('No match for re.search("it0*([0-9]*).log$" in '+logfile)
			 	continue
			iternum = int(m.groups()[0])
			if iternum > lastiter:
				lastiter = iternum
		apDisplay.printMsg("RELION ran "+str(lastiter)+" iterations")
		return lastiter

	#=====================
	def getTimestamp(self):
		timestamp = None
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
			wildcard = "part*_it%03d_*.*"%(i)
			files.extend(glob.glob(wildcard))
			wildcard = "part*_it%03d.*"%(i)
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
	def readRefStarFile(self):
		reflist = []
		#ref16may17u43_it030_data.star
		inputfile = "ref%s_final_data.star"%(self.params['timestamp'])
		lastiterfile = "ref%s_it%03d_data.star"%(self.params['timestamp'], self.lastiter)
		if not os.path.isfile(lastiterfile):
			lastiterfile = os.path.join("refalign", lastiterfile)
		shutil.copy(lastiterfile, inputfile)

		starData = starFile.StarFile(inputfile)
		starData.read()
		dataBlock = starData.getDataBlock('data_images')
		particleTree = dataBlock.getLoopDict()

		fakereflist = [{ 'xshift': 0, 'yshift':0, 'inplane':0}]
		for relionpartdict in particleTree:
			refdict = self.adjustPartDict(relionpartdict, fakereflist)
			reflist.append(refdict)
		apDisplay.printMsg("read rotation and shift parameters for "+str(len(reflist))+" references")
		if len(reflist) < 1:
			apDisplay.printError("Did not find any particles in star file: "+inputfile)
		return reflist

	#=====================
	def readPartStarFile(self, reflist):
		partlist = []
		#part16may17u43_it030_data.star
		inputfile = "part%s_final_data.star"%(self.params['timestamp'])
		lastiterfile = "part%s_it%03d_data.star"%(self.params['timestamp'], self.lastiter)
		if self.params['sort'] is True:
			lastiterfile = os.path.join("iter%03d"%(self.lastiter), lastiterfile)
		shutil.copy(lastiterfile, inputfile)

		starData = starFile.StarFile(inputfile)
		starData.read()
		#print starData.getHeader()
		dataBlock = starData.getDataBlock('data_images')
		particleTree = dataBlock.getLoopDict()
		#for i in range(10):
		#	print particleTree[i]
		for relionpartdict in particleTree:
			partdict = self.adjustPartDict(relionpartdict, reflist)
			partlist.append(partdict)
		apDisplay.printMsg("read rotation and shift parameters for "+str(len(partlist))+" particles")
		if len(partlist) < 1:
			apDisplay.printError("Did not find any particles in star file: "+inputfile)
		return partlist

	#=====================
	def adjustPartDict(self, relionpartdict, reflist):
		refnum = int(relionpartdict['_rlnClassNumber'])
		refdict = reflist[refnum-1]
		#APPION uses shift, mirror, clockwise rotate system for 2D alignment
		#In order for Appion to get the parameters right, we have to do the mirror operation first.
		particleNumber = int(re.sub("\@.*$", "", relionpartdict['_rlnImageName']))
		xshift = 1.0*float(relionpartdict['_rlnOriginX'])+refdict['xshift']
		yshift = -1.0*float(relionpartdict['_rlnOriginY'])+refdict['yshift']
		inplane = self.wrap360(float(relionpartdict['_rlnAnglePsi'])+refdict['inplane'])
		newpartdict = {
			'partnum': particleNumber,
			'xshift': xshift,
			'yshift': yshift,
			'inplane': inplane,
			'refnum': refnum,
			'mirror': True, #not available in RELION, but must be True to correct alignments
			'spread': float(relionpartdict['_rlnMaxValueProbDistribution']), #check for better
		}
		if particleNumber < 10:
			print "%03d -- %.1f -- %s"%(particleNumber, newpartdict['inplane'], relionpartdict['_rlnAnglePsi'])
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
		apDisplay.printMsg("Reading old parameter file: %s"%(paramfile))
		f = open(paramfile, "r")
		runparams = cPickle.load(f)
		if not 'localstack' in runparams:
			runparams['localstack'] = self.params['timestamp']+".hed"
		if not 'student' in runparams:
			runparams['student'] = 0
		apDisplay.printMsg("Read %d old parameters"%(len(runparams)))
		return runparams

	#=====================
	def getMaxLikeJob(self, runparams):
		maxjobq = appiondata.ApMaxLikeJobData()
		maxjobq['runname'] = runparams['runname']
		maxjobq['path'] = appiondata.ApPathData(path=os.path.abspath(runparams['rundir']))
		maxjobq['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(runparams['stackid'])
		maxjobq['timestamp'] = self.params['timestamp']
		maxjobdata = maxjobq.query(results=1)
		if not maxjobdata:
			return None
		return maxjobdata[0]

	#=====================
	def insertRunIntoDatabase(self, alignimagicfile, runparams):
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
		maxlikeq['job'] = self.getMaxLikeJob(runparams)

		### finish alignment run
		alignrunq['maxlikerun'] = maxlikeq
		alignrunq['hidden'] = False
		alignrunq['runname'] = runparams['runname']
		alignrunq['description'] = runparams['description']
		alignrunq['lp_filt'] = runparams['lowpass']
		alignrunq['hp_filt'] = runparams['highpass']
		alignrunq['bin'] = runparams['bin']

		### setup alignment stack
		alignstackq = appiondata.ApAlignStackData()
		alignstackq['imagicfile'] = alignimagicfile
		alignstackq['avgmrcfile'] = "average.mrc"
		alignstackq['refstackfile'] = "part"+self.params['timestamp']+"_average.hed"
		alignstackq['iteration'] = self.lastiter
		alignstackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		alignstackq['alignrun'] = alignrunq
		### check to make sure files exist
		alignimagicfilepath = os.path.join(self.params['rundir'], alignstackq['imagicfile'])
		if not os.path.isfile(alignimagicfilepath):
			apDisplay.printError("could not find stack file: "+alignimagicfilepath)
		avgmrcfile = os.path.join(self.params['rundir'], alignstackq['avgmrcfile'])
		if not os.path.isfile(avgmrcfile):
			apDisplay.printError("could not find average mrc file: "+avgmrcfile)
		refstackfile = os.path.join(self.params['rundir'], alignstackq['refstackfile'])
		if not os.path.isfile(refstackfile):
			apDisplay.printError("could not find reference stack file: "+refstackfile)
		alignstackq['stack'] = apStack.getOnlyStackData(runparams['stackid'])
		alignstackq['boxsize'] = apFile.getBoxSize(alignimagicfilepath)[0]
		alignstackq['pixelsize'] = apStack.getStackPixelSizeFromStackId(runparams['stackid'])*runparams['bin']
		alignstackq['description'] = runparams['description']
		alignstackq['hidden'] =  False
		alignstackq['num_particles'] =  runparams['numpart']

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
			refmrc = "ref%03d-average.mrc"%(partdict['refnum'])
			if os.path.exists(refmrc):
				refq['mrcfile'] = refmrc
			refq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			refq['alignrun'] = self.alignstackdata['alignrun']
			if partdict['refnum']  in self.resdict:
				refq['ssnr_resolution'] = self.resdict[partdict['refnum']]

			### setup particle
			alignpartq = appiondata.ApAlignParticleData()
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
	def createAlignedStacks(self, partlist, origstackfile):
		partperiter = min(4096,apImagicFile.getPartSegmentLimit(origstackfile))
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
				imagesdict = apImagicFile.readImagic(origstackfile, first=imgnum+1,
					last=imgnum+partperiter, msg=False)

			### align particles
			partimg = imagesdict['images'][index]
			partdict = partlist[imgnum]
			partnum = imgnum+1
			if partdict['partnum'] != partnum:
				apDisplay.printError("particle shifting "+str(partnum)+" != "+str(partdict['partnum']))
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
		alignimagicfile = "alignstack.hed"
		apFile.removeStack(alignimagicfile, warn=False)
		apImagicFile.mergeStacks(stacklist, alignimagicfile)
		#for stackname in stacklist:
		#	emancmd = "proc2d %s %s"%(stackname, alignimagicfile)
		#	apEMAN.executeEmanCmd(emancmd, verbose=False)
		filepart = apFile.numImagesInStack(alignimagicfile)
		if filepart != numpart:
			apDisplay.printError("number aligned particles (%d) not equal number expected particles (%d)"%
				(filepart, numpart))
		for stackname in stacklist:
			apFile.removeStack(stackname, warn=False)

		### summarize
		apDisplay.printMsg("rotated and shifted %d particles in %s"
			%(imgnum, apDisplay.timeString(time.time()-t0)))

		return alignimagicfile


	#=====================
	def writeRelionLog(self, text):
		f = open("relion.log", "a")
		f.write(apParam.getLogHeader())
		f.write(text+"\n\n")
		f.close()

	#=====================
	def alignReferences(self, runparams):
		### align references
		# ref16may19v36_it010_classes.mrcs
		finalreffile = "part%s_it%03d_classes.mrcs"%(runparams['timestamp'], runparams['maxiter'])
		apix = apStack.getStackPixelSizeFromStackId(runparams['stackid'])*runparams['bin']
		relionopts = ( " "
			+" --i %s "%(finalreffile)
			+" --o %s "%(os.path.join(runparams['rundir'], "ref"+self.params['timestamp']))
			+" --angpix %.4f "%(apix)
			+" --iter %d "%(runparams['maxiter'])
			+" --K %d "%(1)
			+" --psi_step %d "%(runparams['psistep'])
			+" --tau2_fudge %.1f "%(runparams['tau'])
			+" --particle_diameter %.1f "%(runparams['partdiam'])
			+" --j %d "%(1)
			+" --dont_check_norm "
		)
		relionexe = apParam.getExecPath("relion_refine", die=True)
		relioncmd = relionexe+" "+relionopts
		self.writeRelionLog(relioncmd)
		apEMAN.executeEmanCmd(relioncmd, verbose=True, showcmd=True)

	#=====================
<<<<<<< HEAD
	def createAlignedReferenceStack(self, runparams):
		searchstr = "part"+self.params['timestamp']+"_ref0*.xmp"
		files = glob.glob(searchstr)
		if len(files) < 1:
			apDisplay.printError("reference images not found")
		refarray = mrc.read(files[0])
		refshape = refarray.shape

		stack = []
		for i in range(runparams['numrefs']):
			fname = ("ref%03d-average.mrc"%(i+1))
			if os.path.isfile(fname):
				refarray = mrc.read(fname)
			else:
				apDisplay.printWarning("no particles for reference %d"%(i+1))
				refarray = numpy.zeros(refshape)
=======
	def createAlignedReferenceStack(self):
		"""
		must be run after calc resolution
		"""
		files = glob.glob("ref*-average.mrc")
		files.sort()
		stack = []
		if len(files) < 1:
			apDisplay.printError("reference images not found")
		for fname in files:
			refarray = mrc.read(fname)
>>>>>>> 314ffaf... final version of upload RELION 2D alignment, need to work on the webpage stuff, refs #3971
			stack.append(refarray)
		stackarray = numpy.asarray(stack, dtype=numpy.float32)
		#print stackarray.shape
		avgstack = "part"+self.params['timestamp']+"_average.hed"
		apFile.removeStack(avgstack, warn=False)
		apImagicFile.writeImagic(stackarray, avgstack)
		return

	#=====================
	def calcResolution(self, partlist, alignimagicfile, apix):
		### group particles by refnum
		reflistsdict = {}
		for partdict in partlist:
			refnum = partdict['refnum']
			partnum = partdict['partnum']
			if not refnum in reflistsdict:
					reflistsdict[refnum] = []
			reflistsdict[refnum].append(partnum)
		### get resolution
		self.resdict = {}
		boxsizetuple = apFile.getBoxSize(alignimagicfile)
		boxsize = boxsizetuple[0]
		for refnum in reflistsdict.keys():
			partlist = reflistsdict[refnum]
			esttime = 3e-6 * len(partlist) * boxsize**2
			apDisplay.printMsg("? Ref num %d; %d parts; est time %s"
				%(refnum, len(partlist), apDisplay.timeString(esttime)))
			refavgfile = "ref%03d-average.mrc"%(refnum)
			apStack.averageStack(stack=alignimagicfile, outfile=refavgfile, partlist=partlist, msg=False)
			frcdata = apFourier.spectralSNRStack(alignimagicfile, apix, partlist, msg=False)
			frcfile = "frcplot-%03d.dat"%(refnum)
			apFourier.writeFrcPlot(frcfile, frcdata, apix, boxsize)
			res = apFourier.getResolution(frcdata, apix, boxsize)
			apDisplay.printMsg("* Ref num %d; %d parts; final resolution %.1f Angstroms"
				%(refnum, len(partlist), res))
			self.resdict[refnum] = res
		return

	#=====================
	def start(self):
		### load parameters
		runparams = self.readRunParameters()
		apDisplay.printColor("going to directory %s"%(runparams['rundir']), "green")
		os.chdir(runparams['rundir'])
		self.lastiter = runparams['maxiter'] #self.findLastIterNumber()

		#import pprint
		#pprint.pprint( runparams)

		### align references
		self.alignReferences(runparams)

		### read particles
		if self.params['sort'] is True:
			self.sortFolder()
		reflist = self.readRefStarFile()
		partlist = self.readPartStarFile(reflist)
		#self.writePartDocFile(partlist)

		### create aligned stacks
		alignimagicfile = self.createAlignedStacks(partlist, runparams['localstack'])

		#create average image for web
		apStack.averageStack(alignimagicfile, msg=False)

		### calculate resolution for each reference
		apix = apStack.getStackPixelSizeFromStackId(runparams['stackid'])*runparams['bin']
		self.calcResolution(partlist, alignimagicfile, apix)
<<<<<<< HEAD
		self.createAlignedReferenceStack(runparams)
=======
		self.createAlignedReferenceStack()
>>>>>>> 314ffaf... final version of upload RELION 2D alignment, need to work on the webpage stuff, refs #3971

		### insert into databse
		self.insertRunIntoDatabase(alignimagicfile, runparams)
		self.insertParticlesIntoDatabase(runparams['stackid'], partlist)

		apFile.removeStack(runparams['localstack'], warn=False)

#=====================
if __name__ == "__main__":
	maxLike = UploadRelionMaxLikeScript()
	maxLike.start()
	maxLike.close()



