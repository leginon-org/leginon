#!/usr/bin/env python
#
import os
import time
import sys
import math
import glob
import cPickle
import subprocess
import re
import numpy
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apStack
from appionlib import apParam
from appionlib import apXmipp
from appionlib import appiondata
from appionlib import apImagicFile
from appionlib import apProject
from appionlib import apFourier
from pyami import spider
import sinedon
import MySQLdb

#=====================
#=====================
class SIMPLE(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
#		self.parser.add_option("-j", "--jobid", dest="jobid", type="int",
#			help="SIMPLE jobid", metavar="#")
		self.parser.add_option("-t", "--timestamp", dest="timestamp",
			help="Timestamp of files, e.g. 08nov02b35", metavar="CODE")
						
		### filtering, clipping, centering, etc.	
		self.parser.add_option("--clip", dest="clipsize", type="int",
			help="Clip size in pixels (reduced box size)", metavar="#")
#		self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="int",
#			help="Low pass filter radius (in Angstroms)", metavar="#")
#		self.parser.add_option("--highpass", "--hp", dest="highpass", type="int",
#			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")
		self.parser.add_option("-N", "--numpart", dest="numpart", type="int",
			help="Number of particles to use", metavar="#")
		self.parser.add_option("--no_center", "--no_center", default=False,
			action="store_true", help="dont center particles using cenalignint prior to input to SIMPLE")

		### SIMPLE clustering params
		self.parser.add_option("--ring2", dest="ring2", type="int",
			help="last ring for alignment (in pixels)", metavar="#")
		self.parser.add_option("--ncls", dest="ncls", type="int",
			help="Number of classes to create", metavar="#")
		self.parser.add_option("--minp", dest="minp", type="int", default=10,
			help="minimum number of particles per class", metavar="#")
		self.parser.add_option("--nvars", dest="nvars", type="int", default=30,
			help="number of eigenvectors", metavar="#")
		self.parser.add_option("--nran", dest="nran", type="int", 
			help="size of random sample (depends on the memory of the machine)", metavar="#")
		self.parser.add_option("--no_kmeans", dest="no_kmeans", default=False,
			action="store_true", help="don't use kmeans for refinement")
		self.parser.add_option("--mask", dest="mask", type="int", 
			help="radius of mask (in pixels)", metavar="#")

		### SIMPLE origami reconstruction params
		self.parser.add_option("--lp", dest="lp", type="int", default=20,
			help="low-pass limit for origami reconstruction (in Angstroms)", metavar="#")
		self.parser.add_option("--hp", dest="hp", type="int", default=100,
			help="high-pass limit for origami reconstruction (in Angstroms). If you work with really large \
				compelxes (lots of inelastic scattering), you may want to change this value", metavar="#")
		self.parser.add_option("--froms", dest="froms", type="int", default=2,
			help="starting number of conformational states to classify. (note: if you have 1 conformational \
				state, you may still wish to use 2 in order to suck up bad particles) ", metavar="#")
		self.parser.add_option("--tos", dest="tos", type="int", default=2,
			help="ending number of conformational states to classify. (note: if you have 1 conformational \
				state, you may still wish to use 2 in order to suck up bad particles) ", metavar="#")
		self.parser.add_option("--maxits", dest="maxits", type="int", default=5,
			help="maximum number of rounds for refinement", metavar="#")
		self.parser.add_option("--mw", dest="mw", type="int",
			help="molecular weight (in KDa)", metavar="#")
		self.parser.add_option("--frac", dest="frac", type="float", default=0.8,
			help="fraction of particles to include", metavar="FLOAT")
		self.parser.add_option("--amsklp", dest="amsklp", type="int", default=40,
			help="auto-masking parameter - low-pass filter value of the mask", metavar="#")
		self.parser.add_option("--edge", dest="edge", type="int", default=3,
			help="size of softening of the molecular envelope (in pixels)", metavar="#")
		self.parser.add_option("--trs", dest="trs", type="int", default=5,
			help="origin shift (in pixels)", metavar="#")
		self.parser.add_option("--pgrp", dest="pgrp", type="str", default="C1",
			help="point-group symmetry (currently only C and D symmetry is supported)", metavar="STR")

	#=====================
	def checkConflicts(self):
		### first get all stack data
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])

		### modify boxsize and pixelsize according to binning
		self.boxsize = self.stack['boxsize']
		self.clipsize = int(math.floor(self.boxsize/float(self.params['bin']*2)))*2
		if self.params['clipsize'] is not None:
			if self.params['clipsize'] > self.clipsize:
				apDisplay.printError("requested clipsize is too big %d > %d"
					%(self.params['clipsize'],self.clipsize))
			self.clipsize = self.params['clipsize']

		self.apix = self.stack['apix']
		if self.params['bin'] > 1 or self.params['clipsize'] is not None:
			clipsize = int(self.clipsize)*self.params['bin']
			if clipsize % 2 == 1:
				clipsize += 1 ### making sure that clipped boxsize is even
			self.boxsize = clipsize
			self.apix = self.apix * self.params['bin']

		### basic error checking
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['ncls'] is None:
			apDisplay.printError("a number of classes was not provided")
		maxparticles = 1000000
		if self.params['numpart'] > maxparticles:
			apDisplay.printError("too many particles requested, max: "
				+ str(maxparticles) + " requested: " + str(self.params['numpart']))
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		if self.params['numpart'] > apFile.numImagesInStack(stackfile):
			apDisplay.printError("trying to use more particles "+str(self.params['numpart'])
				+" than available "+str(apFile.numImagesInStack(stackfile)))
		if self.params['numpart'] is None:
			self.params['numpart'] = apFile.numImagesInStack(stackfile)
		if self.params['numpart'] > 5000:
			apDisplay.printWarning("initial model calculation may not work with less than 5000 particles")
		self.mpirun = self.checkMPI()
#		if self.mpirun is None:
#			apDisplay.printError("There is no MPI installed")
		if self.params['nproc'] is None:
			self.params['nproc'] = apParam.getNumProcessors()

		### SIMPLE defaults and error checking
		if self.params['ring2'] is None:
			self.params['ring2'] = (self.boxsize/2) - 2
		if self.params['ncls'] > 2000:
			apDisplay.printError("number of classes should be less than 2000 for subsequent ORIGAMI run to work")
		if self.params['ncls'] > self.params['numpart']:
			self.params['ncls'] = self.params['numpart'] / self.params['minp']
		if self.params['mask'] is None:
			self.params['mask'] = (self.boxsize/2) - 2 
		if self.params['mw'] is None:
			apDisplay.printError("please specify the molecular weight (in kDa)")


	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])

	#=====================
	#=====================		RUNNING SIMPLE JOB
	#=====================
	
	def checkMPI(self):
		mpiexe = apParam.getExecPath("mpirun")
		if mpiexe is None:
			return None
		simpleexe = apParam.getExecPath("simple_mpi_class_averages")
		if simpleexe is None:
			return None
		lddcmd = "ldd "+simpleexe+" | grep mpi"
		proc = subprocess.Popen(lddcmd, shell=True, stdout=subprocess.PIPE)
		proc.wait()
		lines = proc.stdout.readlines()
		print "lines=", lines
		if lines and len(lines) > 0:
			return mpiexe

	#=====================
	def writeSimpleLog(self, text):
		f = open("simple.log", "a")
		f.write(apParam.getLogHeader())
		f.write(text+"\n")
		f.close()

	#=====================
	def clearIntermediateFiles(self):
		os.system("rm -rf pdfile.bin ali.* %s" % (self.params['localstack']))

	
	#=====================
	#=====================		UPLOADING RESULTS
	#=====================

	#=====================
	def getTimestamp(self):
		if self.params["jobid"] is not None:
			jobdata = appiondata.ApSIMPLERunData.direct_query(self.params["jobid"])
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
		paramfile = "simple-"+self.params['timestamp']+"-params.pickle"
		if not os.path.isfile(paramfile):
			apDisplay.printError("Could not find run parameters file: "+paramfile)
		f = open(paramfile, "r")
		runparams = cPickle.load(f)
		return runparams
		
	#=====================
	def calcResolution(self, alignedStack):
		self.resdict = {}
		for classref, partlist in self.classD.iteritems():
			if len(partlist) == 0:
				continue
			stack=[]
			for partnum in partlist:
				### NOTE: RESOLUTION WILL NOT BE CALCULATED IF ALIGNED STACK IS NOT CREATED
				stack.append(apImagicFile.readSingleParticleFromStack(alignedStack,int(partnum),msg=False))
			apImagicFile.writeImagic(stack,"tmp.hed")

			frcdata = apFourier.spectralSNRStack("tmp.hed", self.apix)
			self.resdict[classref] = apFourier.getResolution(frcdata, self.apix, self.boxsize)
		apFile.removeStack("tmp.hed")

	#=====================
	def getClassification(self, classdoc, classname):
		D = {}
		tmp = {}
		fh = open(classdoc)
		nclasses = apFile.numImagesInStack(classname)
	
		### all classes, assuming that some of them were discarded by the minp parameter
		for i in range(self.params['ncls']):
			tmp[(i+1)] = []
		for line in fh:
			params = line.strip().split()
			particleNumber = int(params[0])
			classNumber = int(float(params[2]))
			tmp[classNumber].append(particleNumber)
		fh.close()	

		### rename the dictionary
		i = 1
		for oldkey, val in tmp.iteritems(): ### ascending order
			if len(val) > 0:
				D[i] = val
#				print oldkey, i, val
				i += 1

		return D	
	
	#=====================
	def getAlignParameters(self, alignparams="cluster_algndoc.dat", centparams=None):
		D = {}
		if centparams is not None:
			cp = open(centparams, "r")
			cplines = cp.readlines()
			cp.close()
		ap = open(alignparams, "r")
		aplines = ap.readlines()
		ap.close()

		### read centering parameters
		for i in range(self.params['numpart']):
			D[i] = {}
		if centparams is not None:
			for cline in cplines:
				try: 
					partnum = int(float(cline.strip().split()[0]))
				except:
					partnum = None
					continue
				try:
					shx = float(cline.strip().split()[1])
				except:
					shx = None
					continue
				try:
					shy = float(cline.strip().split()[2])
				except:
					shy = None
					continue
				try:
					mir = bool(float(cline.strip().split()[3]))
				except:
					mir = None
					continue
				if type(partnum) is int and type(shx) is float and type(shy) is float and type(mir) is bool:
					D[partnum] = {"shx":shx, "shy":shy, "mirror":mir}

		for i, aline in enumerate(aplines):
			rot = float(aline.strip().split()[2])
			D[i]["rot"] = rot

		return D


	#=====================
	def insertSIMPLEAlignParamsIntoDatabase(self):
		### setup simple run
		simpleq = appiondata.ApSIMPLEClusterRunData()
		simpleq['runname'] = self.runparams['runname']
		simpleq['run_seconds'] = self.runparams['runtime']
		simpleq['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		simpleq['timestamp'] = self.params['timestamp']
		simpleq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		simpleq['finished'] = True
		simpleq['num-ref'] = self.params['ncls']
		if self.params['no_kmeans'] is False:
			simpleq['kmeans'] = True
		else:
			simpleq['kmeans'] = False
		if self.params['no_center'] is False:
			simpleq['center'] = True
		else:
			simpleq['center'] = False
	
		### insert if commit is true
		if self.params['commit'] is True:
			simpleq.insert()	
		self.simpleqdata=simpleq

	#=====================
	def insertSIMPLEOrigamiParamsIntoDatabase(self):
		### setup simple run	
		simpleq = appiondata.ApSIMPLEOrigamiRunData()
		simpleq['runname'] = self.runparams['runname']
		simpleq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
#		### check unique run
#		uniquerun = simpleq.query(results=1)
#		if uniquerun:
#			apDisplay.printError("runname already exists in the database")

		paramsq = appiondata.ApSIMPLEOrigamiParamsData()
		paramsq['lp'] = self.params['lp']
		paramsq['hp'] = self.params['hp']
		paramsq['froms'] = self.params['froms']
		paramsq['tos'] = self.params['tos']
		paramsq['maxits'] = self.params['maxits']
		paramsq['msk'] = self.params['mask']
		paramsq['mw'] = self.params['mw']
		paramsq['amsklp'] = self.params['amsklp']
		paramsq['edge'] = self.params['edge']
		paramsq['trs'] = self.params['trs']
		paramsq['pgrp'] = self.params['pgrp']

		simpleq['description'] = self.params['description']
		simpleq['box'] = self.boxsize
		simpleq['apix'] = self.apix
		simpleq['simple_params'] = paramsq
		simpleq['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		simpleq['timestamp'] = self.params['timestamp']
		simpleq['stack'] = apStack.getOnlyStackData(self.runparams['stackid'])
		simpleq['alignstack'] = self.alignstackdata
		simpleq['clusteringstack'] = self.clusterstackq

		if self.params['commit'] is True:
			simpleq.insert()
	
		return

	#=====================
	def insertAlignStackRunIntoDatabase(self, alignimagicfile, refstackfile):
		apDisplay.printMsg("Inserting SIMPLE Run into DB")

		### setup alignment run
		alignrunq = appiondata.ApAlignRunData()
		alignrunq['runname'] = self.runparams['runname']
		alignrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
#		if uniquerun:
#			apDisplay.printError("Run name '"+self.runparams['runname']+"' and path already exist in database")

		### finish alignment run
		alignrunq['simplerun'] = self.simpleqdata
		alignrunq['hidden'] = False
		alignrunq['runname'] = self.runparams['runname']
		alignrunq['description'] = self.runparams['description']
#		alignrunq['lp_filt'] = self.runparams['lowpass']
#		alignrunq['hp_filt'] = self.runparams['highpass']
		alignrunq['bin'] = self.runparams['bin']

		### setup alignment stack
		alignstackq = appiondata.ApAlignStackData()
		alignstackq['imagicfile'] = alignimagicfile
		alignstackq['avgmrcfile'] = "average.mrc"
		alignstackq['refstackfile'] = refstackfile
		alignstackq['iteration'] = 10 ### hardcoded in SIMPLE
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
		alignstackq['stack'] = apStack.getOnlyStackData(self.runparams['stackid'])
		alignstackq['boxsize'] = self.boxsize
		alignstackq['pixelsize'] = self.apix
		alignstackq['description'] = self.runparams['description']
		alignstackq['hidden'] =  False
		alignstackq['num_particles'] =  self.runparams['numpart']

		### insert
		if self.params['commit'] is True:
			alignstackq.insert()
		self.alignstackdata = alignstackq

		return

	#=====================
	def insertAlignParticlesIntoDatabase(self):
		count = 0
		inserted = 0
		t0 = time.time()
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		for ref in self.classD:
			### setup reference
			refq = appiondata.ApAlignReferenceData()
			refq['refnum'] = ref
			refq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			refq['alignrun'] = self.alignstackdata['alignrun']
			refq['iteration'] = 10
#			if ref in self.resdict:
#				refq['ssnr_resolution'] = self.resdict[ref]

			### setup particle info 
			for partnum in self.classD[ref]:
				alignpartq = appiondata.ApAlignParticleData()
				alignpartq['partnum'] = int(partnum)
				alignpartq['alignstack'] = self.alignstackdata
				### particle numbering starts with 1 in SIMPLE
				stackpartdata = apStack.getStackParticle(self.runparams['stackid'], int(partnum))
				alignpartq['stackpart'] = stackpartdata
				alignpartq['ref'] = refq
				try:
					alignpartq['xshift'] = self.alignD[partnum-1]['shx']
				except:
					pass
				try:
					alignpartq['yshift'] = self.alignD[partnum-1]['shy']
				except:
					pass
				try:
					alignpartq['mirror'] = self.alignD[partnum-1]['mirror']
				except:
					pass
				alignpartq['rotation'] = self.alignD[partnum-1]['rot']
				### insert
				if self.params['commit'] is True:
					inserted += 1
					alignpartq.insert()

		apDisplay.printColor("\ninserted "+str(inserted)+" of "+str(self.params['numpart'])+" particles into the database in "
			+apDisplay.timeString(time.time()-t0), "cyan")

		return

	#=====================
	def insertClusterRunIntoDatabase(self):
		# create a Clustering Run object
		clusterrunq = appiondata.ApClusteringRunData()
		clusterrunq['runname'] = self.params['runname']
		clusterrunq['description'] = self.params['description']
		clusterrunq['simpleparams'] = self.simpleqdata
		clusterrunq['boxsize'] = self.boxsize
		clusterrunq['pixelsize'] = self.apix
		clusterrunq['num_particles'] = self.runparams['numpart']
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
	def insertClusterStackIntoDatabase(self, clusterstackfile, num_classes):
		clusterstackq = appiondata.ApClusteringStackData()
		clusterstackq['avg_imagicfile'] = clusterstackfile
		clusterstackq['var_imagicfile'] = None
		clusterstackq['num_classes'] = num_classes
		clusterstackq['clusterrun'] = self.clusterrun
		clusterstackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		clusterstackq['hidden'] = False
		self.clusterstackq = clusterstackq

		if not os.path.isfile(clusterstackfile):
			apDisplay.printError("could not find average stack file: "+clusterstackfile)

		apDisplay.printMsg("inserting clustering stack into database")
		if self.params['commit'] is True:
			clusterstackq.insert()

		### insert particle class & reference data
#		print self.classD
		for i in self.classD:
			clusterrefq = appiondata.ApClusteringReferenceData()
			clusterrefq['refnum'] = i
			clusterrefq['clusterrun'] = self.clusterrun
			clusterrefq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			clusterrefq['num_particles'] = len(self.classD[i])
			if i in self.resdict:
				clusterrefq['ssnr_resolution'] = self.resdict[i]
	
#			apDisplay.printColor("Inserting particle classification data, please wait", "cyan")
			for partnum in self.classD[i]: ### simple references start with 1
				cpartq = appiondata.ApClusteringParticleData()
				if self.params['commit'] is True:
					alignpartdata = self.getAlignParticleData(int(partnum))
					cpartq['alignparticle'] = alignpartdata
				else:
					cpartq['alignparticle'] = None
				cpartq['clusterstack'] = clusterstackq
				cpartq['partnum'] = int(partnum)
				cpartq['refnum'] = i
				cpartq['clusterreference'] = clusterrefq
				# actual parameters
				if self.params['commit'] is True:
					cpartq.insert()
		return

	#=====================
	def start(self):
		### simple is written in Fortran, which cannot take inputs of certain length, therefore one needs
		### to change to the directory to minimize the filename length, in particular for the stack
		os.chdir(self.params['rundir'])

		### stack needs to be centered
		if self.params['no_center'] is False:
			if os.path.isfile(os.path.join(self.params['rundir'], "ali.hed")):
				apFile.removeStack(os.path.join(self.params['rundir'], "ali.hed"))
			centstack = os.path.join(self.params['rundir'], "ali.hed")
			centcmd = "cenalignint %s > cenalignint.log" % (self.stack['file'])
			apParam.runCmd(centcmd, "EMAN")

		### process stack to local file
		if self.params['timestamp'] is None:
			apDisplay.printMsg("creating timestamp")
			self.params['timestamp'] = self.timestamp
		self.params['localstack'] = os.path.join(self.params['rundir'], self.params['timestamp']+".spi")

		if os.path.isfile(self.params['localstack']):
			apFile.removeFile(self.params['localstack'])
		if self.params['no_center'] is False:
			proccmd = "proc2d "+centstack+" "+self.params['localstack']+" apix="+str(self.stack['apix'])
		else:
			proccmd = "proc2d "+self.stack['file']+" "+self.params['localstack']+" apix="+str(self.stack['apix'])
		if self.params['bin'] > 1 or self.params['clipsize'] is not None:
			proccmd += " shrink=%d clip=%d,%d " % (self.params['bin'], self.boxsize, self.boxsize)
		proccmd += " last="+str(self.params['numpart']-1)
		proccmd += " spiderswap"
#		if self.params['highpass'] is not None and self.params['highpass'] > 1:
#			proccmd += " hp="+str(self.params['highpass'])
#		if self.params['lowpass'] is not None and self.params['lowpass'] > 1:
#			proccmd += " lp="+str(self.params['lowpass'])
		apParam.runCmd(proccmd, "EMAN", verbose=True)

#		if self.params['numpart'] != int(spider.getSpiderHeader(self.params['localstack'])[-2]):
#			apDisplay.printError("Missing particles in stack")

		### setup Simple command
		aligntime = time.time()
		simpleopts = (""
			+" stk=%s" % os.path.basename(self.params['localstack'])
			+" box=%d" % self.boxsize
			+" nptcls=%d" % self.params['numpart']
			+" smpd=%.3f" % self.apix
			+" ring2=%d" % self.params['ring2']
			+" ncls=%d" % self.params['ncls']	
			+" minp=%d" % self.params['minp']
			+" nvars=%d" % self.params['nvars']
			+" nthr=%d" % self.params['nproc']
		)
		if self.params['no_kmeans'] is True:
			simpleopts += " kmeans=off"
		if self.params['nran'] is not None:
			simpleopts += "nran=%d" % self.params['nran']

		### SIMPLE 2D clustering
		apDisplay.printColor("Using "+str(self.params['nproc'])+" processors!", "green")
		simpleexe = apParam.getExecPath("cluster", die=True)
		simplecmd = "%s %s" % (simpleexe, simpleopts)
		self.writeSimpleLog(simplecmd)
		apParam.runCmd(simplecmd, package="SIMPLE", verbose=True, showcmd=True, logfile="cluster.std")
		self.params['runtime'] = time.time() - aligntime
		apDisplay.printMsg("Alignment & Classification time: "+apDisplay.timeString(self.params['runtime']))

		### SIMPLE spider to Fourier format
		clsavgs = "cavgstk.spi"
		if not os.path.isfile(os.path.join(self.params['rundir'], clsavgs)):
			apDisplay.printError("class averages were not created! try rerunning with centering, more particles, or less ppc")
		try:
			nptcls = spider.getSpiderHeader(clsavgs)[-2]
		except:
			nptcls = self.params['ncls']
			apDisplay.printWarning("class average file may not have been created! Please check existence of file cavgstk.spi")
		projfile = "projs"
		projext = ".fim"
		simpleexe = apParam.getExecPath("spi_to_fim", die=True)
		simpleopts = (""
			+" stk=%s" % clsavgs
			+" box=%d" % self.boxsize
			+" nptcls=%d" % nptcls
			+" smpd=%.3f" % self.apix
			+" outbdy=%s" % projfile
			+" msk=%d" % self.params['mask']
		)
		simplecmd = "%s %s" % (simpleexe, simpleopts)
		self.writeSimpleLog(simplecmd)
		apParam.runCmd(simplecmd, package="SIMPLE", verbose=True, showcmd=True, logfile="spi_to_fim.std")

		### SIMPLE origami, ab initio 3D reconstruction
		refinetime = time.time()
		simpleexe = apParam.getExecPath("origami", die=True)
		simpleopts = (""
			+" fstk=%s" % projfile+projext
			+" froms=%d" % self.params['froms']
			+" tos=%d" % self.params['tos']
			+" lp=%d" % self.params['lp']
			+" hp=%d" % self.params['hp']
			+" maxits=%d" % self.params['maxits']
			+" msk=%d" % self.params['mask']	
			+" mw=%d" % self.params['mw']
			+" frac=%.3f" % self.params['frac']
			+" amsklp=%d" % self.params['amsklp']
			+" edge=%d" % self.params['edge']
			+" trs=%d" % self.params['trs']
			+" nthr=%d" % self.params['nproc']
		)
		simplecmd = "%s %s" % (simpleexe, simpleopts)
		self.writeSimpleLog(simplecmd)
		apParam.runCmd(simplecmd, package="SIMPLE", verbose=True, showcmd=True, logfile="origami.std")
		refinetime = time.time() - refinetime
		apDisplay.printMsg("Origami reconstruction time: "+apDisplay.timeString(refinetime))

#		'''

		### minor post-processing
		self.clearIntermediateFiles()
		apParam.dumpParameters(self.params, "simple-"+self.params['timestamp']+"-params.pickle")

		### upload results
		self.runparams = apParam.readRunParameters("simple-"+self.params['timestamp']+"-params.pickle")

		### create average of aligned and clustered stacks, convert to IMAGIC
		alignedStackSpi = "inplalgnstk.spi"
		alignedStack = "inplalgnstk.hed"
		if os.path.isfile(alignedStack):
			apFile.removeStack(alignedStack)
		emancmd = "proc2d %s %s flip" % (alignedStackSpi, alignedStack)
		apParam.runCmd(emancmd, "EMAN")
		clusterStackSpi = "cavgstk.spi"
		clusterStack = "cavgstk.hed"
		if os.path.isfile(clusterStack):
			apFile.removeStack(clusterStack)
		emancmd = "proc2d %s %s flip" % (clusterStackSpi, clusterStack)
		apParam.runCmd(emancmd, "EMAN")
#		apStack.averageStack(alignedStack)

		### parse alignment and classification results
		if self.params['no_center'] is False:
			self.alignD = self.getAlignParameters(centparams="cenalignint.log")
		else:
			self.alignD = self.getAlignParameters()
		if self.params['no_kmeans'] is False:
			self.classD = self.getClassification("kmeans.spi", clusterStack)
		else:
			self.classD = self.getClassification("hcl.spi", clusterStack)	

		### upload to database
		self.insertSIMPLEAlignParamsIntoDatabase()
		self.insertAlignStackRunIntoDatabase(alignedStack, clusterStack)
		self.calcResolution(alignedStack)
		self.insertAlignParticlesIntoDatabase()
		self.insertClusterRunIntoDatabase()
		self.insertClusterStackIntoDatabase(clusterStack, len(self.classD))
		self.insertSIMPLEOrigamiParamsIntoDatabase()

#		'''	
				
#=====================
if __name__ == "__main__":
	simple = SIMPLE()
	simple.start()
	simple.close()
