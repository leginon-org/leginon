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
from appionlib import apStackFile
from appionlib import apImage
from appionlib import starFile
from appionlib import apDisplay
from appionlib import apProject
from appionlib import apFourier
from appionlib import appiondata
from appionlib import apImagicFile
from appionlib import apRelion
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
	def adjustPartDict(self, relionpartdict, reflist):
		return apRelion.adjustPartDict(relionpartdict, reflist)

	#=====================
	def readRefStarFile(self):
		reflist = []
		#ref16may17u43_it030_data.star
		inputfile = "ref%s_final_data.star"%(self.params['timestamp'])
		lastiterfile = "ref%s_it%03d_data.star"%(self.params['timestamp'], self.lastiter)
		if not os.path.isfile(lastiterfile):
			# may be in refalign after file sorting but did not upload properly
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
		dataBlock = starData.getDataBlock('data_images')
		particleTree = dataBlock.getLoopDict()
		self.class_count = {}
		for relionpartdict in particleTree:
			partdict = self.adjustPartDict(relionpartdict, reflist)
			refnum = partdict['refnum']
			self.class_count[refnum] = self.class_count.get(refnum, 0) + 1
			partlist.append(partdict)
		apDisplay.printMsg("read rotation and shift parameters for "+str(len(partlist))+" particles")
		apDisplay.printMsg("Class counts: %s"%(str(self.class_count)))
		if len(partlist) < 1:
			apDisplay.printError("Did not find any particles in star file: "+inputfile)
		return partlist

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
	def insertRunIntoDatabase(self, alignref_imagicfile, alignimagicfile, runparams):
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
		alignstackq['refstackfile'] = alignref_imagicfile
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
	def createAlignedStack(self, partlist, origstackfile):
		### this is redundant...
		return apStackFile.createAlignedStack(partlist, origstackfile)

	#=====================
	def writeRelionLog(self, text):
		f = open("relion.log", "a")
		f.write(apParam.getLogHeader())
		f.write(text+"\n\n")
		f.close()

	#=====================
	def replaceNaNImageInReferenceStack(self, runparams):
		apDisplay.printMsg('Checking reference stack for NaN data....')
		finalreffile = "part%s_it%03d_classes.mrcs"%(runparams['timestamp'], runparams['maxiter'])
		number_of_replacement = apRelion.replaceNaNImageInStack(finalreffile)
		apDisplay.printMsg('Replaced %d bad images in stack' % number_of_replacement)

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
	def createAlignedReferenceStack(self, runparams):
		"""
		must be run after calc resolution
		"""
		files = glob.glob("ref*-average.mrc")
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
		# initialize variables
		self.resdict = {}

		### load parameters
		runparams = self.readRunParameters()
		apDisplay.printColor("going to directory %s"%(runparams['rundir']), "green")
		os.chdir(runparams['rundir'])
		self.lastiter = runparams['maxiter'] #self.findLastIterNumber()

		#import pprint
		#pprint.pprint( runparams)

		### refs #4396 Relion sometimes gives NaN image that it can not use for alignment
		self.replaceNaNImageInReferenceStack(runparams)

		### align references, output to rundir
		self.alignReferences(runparams)

		### organize refinement results into folders
		if self.params['sort'] is True:
			self.sortFolder()

		# create aligned reference stack
		reflist = self.readRefStarFile()
		alignref_imagicfile = "part"+self.params['timestamp']+"_average.hed"

		### create aligned stacks
		partlist = self.readPartStarFile(reflist)
		#self.writePartDocFile(partlist)
		alignimagicfile = self.createAlignedStack(partlist, runparams['localstack'])

		# convert unaligned weighted refstack from mrc to imagic format
		unaligned_refstack_mrc = os.path.join('iter%03d' % self.lastiter,'part%s_it%03d_classes.mrcs' % (self.params['timestamp'], self.lastiter))
		unaligned_refstack_imagic = 'part%s_it%03d_classes.hed' % (self.params['timestamp'], self.lastiter)
		## hopefully this reference stack is not too big to cause memory error
		stackarray = mrc.read(unaligned_refstack_mrc)
		## blank out empty classes
		print stackarray.shape
		blank_classes = []
		for refnum in range(len(stackarray)):
			if self.class_count.get(refnum, 0) == 0:
				blank_classes.append(refnum)
				stackarray[refnum,:,:] = 0
		if len(blank_classes) > 0:
			apDisplay.printWarning("%d of %d classes were empty and set to black: %s"
				%(len(blank_classes), len(stackarray), str(blank_classes)))
		apImagicFile.writeImagic(stackarray, unaligned_refstack_imagic)

		# createAlignedStack
		temp_imagicfile = apStackFile.createAlignedStack(reflist, unaligned_refstack_imagic, 'temp_aligned_ref')
		apFile.moveStack(temp_imagicfile, alignref_imagicfile)
		#sys.exit(1)

		#create average image for web
		apStack.averageStack(alignimagicfile, msg=False)

		### calculate resolution for each reference
		### The way the function average particles in each class
		### without weighting causes Issue #4566.
		#apix = apStack.getStackPixelSizeFromStackId(runparams['stackid'])*runparams['bin']
		#self.calcResolution(partlist, alignimagicfile, apix)
		#self.createAlignedReferenceStack(runparams)

		### insert into databse
		self.insertRunIntoDatabase(alignref_imagicfile, alignimagicfile, runparams)
		self.insertParticlesIntoDatabase(runparams['stackid'], partlist)

		apFile.removeStack(runparams['localstack'], warn=False)

#=====================
if __name__ == "__main__":
	maxLike = UploadRelionMaxLikeScript()
	maxLike.start()
	maxLike.close()



