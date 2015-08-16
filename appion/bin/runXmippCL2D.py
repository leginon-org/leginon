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
from appionlib import proc2dLib
from pyami import spider
import sinedon
import MySQLdb

#=====================
#=====================
class CL2D(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("-j", "--jobid", dest="jobid", type="int",
			help="CL2D jobid", metavar="#")
		self.parser.add_option("-t", "--timestamp", dest="timestamp",
			help="Timestamp of files, e.g. 08nov02b35", metavar="CODE")
						
		### filtering, clipping, etc.	
		self.parser.add_option("--clip", dest="clipsize", type="int",
			help="Clip size in pixels (reduced box size)", metavar="#")
		self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="int",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--highpass", "--hp", dest="highpass", type="int",
			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int",
			help="Number of particles to use", metavar="#")
		self.parser.add_option("--invert", default=False,
			action="store_true", help="Invert before alignment")
			
		### CL2D params
		self.parser.add_option("--max-iter", dest="maxiter", type="int", default=20,
			help="Maximum number of iterations", metavar="#")
		self.parser.add_option("--num-ref", dest="numrefs", type="int",
			help="Number of classes to create", metavar="#")
		self.parser.add_option("-F", "--fast", dest="fast", default=False,
			action="store_true", help="Use fast method")
		self.parser.add_option("--correlation", dest="correlation", default=False,
			action="store_true", help="Use correlation")
		self.parser.add_option("--classical_multiref", dest="classical", default=False,
			action="store_true", help="Use classical multireference alignment")
		self.parser.add_option("--dontAlignImages", dest="align", default=True,
			action="store_false", help="Do not produce an aligned stack")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['numrefs'] is None:
			apDisplay.printError("a number of classes was not provided")
		maxparticles = 500000
		if self.params['numpart'] > maxparticles:
			apDisplay.printError("too many particles requested, max: "
				+ str(maxparticles) + " requested: " + str(self.params['numpart']))
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])
		# check for virtual stack
		self.params['virtualdata'] = None
		if not os.path.isfile(stackfile):
			vstackdata = apStack.getVirtualStackParticlesFromId(self.params['stackid'])
			npart = len(vstackdata['particles'])
			self.params['virtualdata'] = vstackdata
		else:
			npart = apFile.numImagesInStack(stackfile)

		if self.params['numpart'] > npart:
			apDisplay.printError("trying to use more particles "+str(self.params['numpart'])
				+" than available "+str(apFile.numImagesInStack(stackfile)))

		boxsize = apStack.getStackBoxsize(self.params['stackid'])
		self.clipsize = int(math.floor(boxsize/float(self.params['bin']*2)))*2
		if self.params['clipsize'] is not None:
			if self.params['clipsize'] > self.clipsize:
				apDisplay.printError("requested clipsize is too big %d > %d"
					%(self.params['clipsize'],self.clipsize))
			self.clipsize = self.params['clipsize']
		if self.params['numpart'] is None:
			self.params['numpart'] = apFile.numImagesInStack(stackfile)
		self.mpirun = self.checkMPI()
		if self.mpirun is None:
			apDisplay.printError("There is no MPI installed")
		if self.params['nproc'] is None:
			self.params['nproc'] = apParam.getNumProcessors()
		if self.params['nproc'] < 2:
			apDisplay.printError("Only the MPI version of CL2D is currently supported, must run with > 1 CPU")

	#=====================
	def setRunDir(self):
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])

	#=====================
	#=====================		RUNNING CL2D JOB
	#=====================

	'''
	#=====================
	def dumpParameters(self):
		self.params['runtime'] = time.time() - self.t0
		self.params['timestamp'] = self.params['timestamp']
		paramfile = "cl2d-"+self.params['timestamp']+"-params.pickle"
		pf = open(paramfile, "w")
		cPickle.dump(self.params, pf)
		pf.close()
		
	#=====================

	def insertCL2DJob(self):
		cl2dq = appiondata.ApCL2DRunData()
		cl2dq['runname'] = self.params['runname']
		cl2dq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		maxjobdatas = cl2dq.query(results=1)
		if maxjobdatas:
			alignrunq = appiondata.ApAlignRunData()
			alignrunq['runname'] = self.params['runname']
			alignrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			alignrundata = alignrunq.query(results=1)
			if maxjobdatas[0]['finished'] is True or alignrundata:
				apDisplay.printError("This run name already exists as finished in the database, please change the runname")
		cl2dq['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		cl2dq['timestamp'] = self.params['timestamp']
		cl2dq['finished'] = False
		if self.params['commit'] is True:
			cl2dq.insert()
			print "******************",cl2dq
		self.params['cl2djobid'] = cl2dq.dbid
		print "self.params['cl2djobid']",self.params['cl2djobid']
		return

	#=====================
	def readyUploadFlag(self):
		if self.params['commit'] is False:
			return
		config = sinedon.getConfig('appiondata')
		dbc = MySQLdb.Connect(**config)
		cursor = dbc.cursor()
		query = (
			"  UPDATE ApCL2DRunData "
			+" SET `finished` = '1' "
			+" WHERE `DEF_id` = '"+str(self.params['cl2djobid'])+"'"
		)
		cursor.execute(query)
		cursor.close()
		dbc.close()
	'''
	
	#=====================
	def checkMPI(self):
		mpiexe = apParam.getExecPath("mpirun")
		if mpiexe is None:
			return None
		xmippexe = apParam.getExecPath("xmipp_mpi_class_averages")
		if xmippexe is None:
			return None
		lddcmd = "ldd "+xmippexe+" | grep mpi"
		proc = subprocess.Popen(lddcmd, shell=True, stdout=subprocess.PIPE)
		proc.wait()
		lines = proc.stdout.readlines()
		print "lines=", lines
		if lines and len(lines) > 0:
			return mpiexe

	#=====================
	def writeXmippLog(self, text):
		f = open("xmipp.log", "a")
		f.write(apParam.getLogHeader())
		f.write(text+"\n")
		f.close()

	#=====================
	def clearIntermediateFiles(self):
		os.system("rm -rf partfiles *.xmp *.doc "+self.params['timestamp']+".* "+\
			  "part"+self.params['timestamp']+"0*.sel part*_.sel partlist.sel "+\
			  "part"+self.params['timestamp']+".sel")

	#=====================
	def createReferenceStack(self):
		# Create a stack for the class averages at each level
		Nlevels=len(glob.glob("part"+self.params['timestamp']+"_level_??_.sel"))
		for level in range(Nlevels):
			stack=[]
			files = glob.glob("part"+self.params['timestamp']+"_level_%02d_[0-9]*.xmp"%level)
			files.sort()
			for f in files:
				stack.append(spider.read(f))
			apImagicFile.writeImagic(stack, "part"+self.params['timestamp']+"_level_%02d_.hed"%level)
		if self.params['align']:
			apXmipp.gatherSingleFilesIntoStack("partlist.sel","alignedStack.hed")
		return

	#=====================
	def parseOutput(self):
		fh=open("xmipp.std","r")
		level=-1
		fhOut=None
		for line in fh:
			tokens=line.split(" ")
			if tokens[0]=="Quantizing":
				level+=1
				if not fhOut is None:
					fhOut.close()
				fhOut=open("part"+self.params['timestamp']+"_level_%02d_convergence.txt"%level,"w")
			elif tokens[0]=="Number":
				print >>fhOut, tokens[3].split("=")[1].rstrip()
		if not fhOut is None:
			fhOut.close()
		fh.close()		

	
	#=====================
	#=====================		UPLOADING RESULTS
	#=====================

	'''
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
	'''
		
	#=====================
	def calcResolution(self, level):
		self.resdict = {}
		D=self.getClassificationAtLevel(level)
		for classref in D:
			stack=[]
			for partnum in D[classref]:
				### NOTE: RESOLUTION WILL NOT BE CALCULATED IF ALIGNED STACK IS NOT CREATED
				stack.append(apImagicFile.readSingleParticleFromStack("alignedStack.hed",int(partnum)+1,msg=False))
			apImagicFile.writeImagic(stack,"tmp.hed")

			frcdata = apFourier.spectralSNRStack("tmp.hed", self.apix)
			self.resdict[classref] = apFourier.getResolution(frcdata, self.apix, self.boxsize)
		apFile.removeStack("tmp.hed")

	#=====================
	def getClassificationAtLevel(self,level):
		D={}
		xmipplist = []
		for classSel in glob.glob("part"+self.params['timestamp']+"_level_%02d_[0-9]*.sel"%level):
				fh=open(classSel)
				listOfParticles=[]
				for line in fh:
						fileName=line.split(" ")[0]
						### particle numbering starts at 0
						particleNumber=os.path.split(fileName)[1][4:10]
						listOfParticles.append(particleNumber)
						xmipplist.append(int(particleNumber))
				classNumber=int(os.path.splitext(classSel.split("_")[-1])[0])
				D[classNumber]=listOfParticles
				fh.close()
	
		### I've noticed that some particles do not get aligned by CL2D, and are therefore not saved in the selfiles.  
		### This is a workaround to make sure that all particles, aligned & not aligned, get saved to the database - Dmitry
		self.badpartlist = []
		partlist = []
		for i in range(self.params['numpart']):
			partlist.append(i)
		missingcount = 0
		for p in partlist:
			if p not in xmipplist:
				apDisplay.printWarning("particle %d was not aligned by CL2D at level %d, appending as bad particle" % (p, level))
				self.badpartlist.append(p)
				missingcount += 1
		if missingcount > 0:
			apDisplay.printWarning("total number of missing particles: %d" % missingcount)
	
		return D	

	#=====================
	def insertCL2DParamsIntoDatabase(self):
		### setup cl2d run
		cl2dq = appiondata.ApCL2DRunData()
		cl2dq['runname'] = self.runparams['runname']
		cl2dq['run_seconds'] = self.runparams['runtime']
		cl2dq['fast'] = self.runparams['fast']
		cl2dq['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		cl2dq['timestamp'] = self.params['timestamp']
		cl2dq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		cl2dq['finished'] = True
		cl2dq['max-iter'] = self.params['maxiter']
		cl2dq['num-ref'] = self.params['numrefs']
		if self.params['correlation'] is True:
			cl2dq['correlation'] = True
			cl2dq['correntropy'] = False
		else:
			cl2dq['correlation'] = False
			cl2dq['correntropy'] = True
		if self.params['classical'] is True:
			cl2dq['classical_multiref'] = True
			cl2dq['intracluster_multiref'] = False
		else:
			cl2dq['classical_multiref'] = False
			cl2dq['intracluster_multiref'] = True
	
		### insert if commit is true
		if self.params['commit'] is True:
			cl2dq.insert()	
		self.cl2dqdata=cl2dq

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

		### finish alignment run
		alignrunq['cl2drun'] = self.cl2dqdata
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
				apDisplay.printWarning("could not find average mrc file: "+avgmrcfile)
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
			refq['iteration'] = self.params['maxiter']
			if ref in self.resdict:
				refq['ssnr_resolution'] = self.resdict[ref]

			### setup particle info ... NOTE: ALIGNMENT PARAMETERS ARE NOT SAVED IN XMIPP 2.4
			for partnum in D[ref]: # particle numbering in D[ref] starts with 0
				alignpartq = appiondata.ApAlignParticleData()
				alignpartq['partnum'] = int(partnum)+1
				alignpartq['alignstack'] = self.alignstackdata
				### particle numbering in Appion db starts with 1
				stackpartdata = apStack.getStackParticle(self.runparams['stackid'], int(partnum)+1)
				alignpartq['stackpart'] = stackpartdata
				alignpartq['ref'] = refq
				### insert
				if self.params['commit'] is True:
					inserted += 1
					alignpartq.insert()

		### insert bad particles
		if len(self.badpartlist) > 0:
			for p in self.badpartlist: # particle numbering in badpartlist starts with 0
				refq = appiondata.ApAlignReferenceData()
				refq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
				refq['alignrun'] = self.alignstackdata['alignrun']
				refq['iteration'] = self.params['maxiter']
				alignpartq = appiondata.ApAlignParticleData()
				alignpartq['partnum'] = int(p)+1
				alignpartq['alignstack'] = self.alignstackdata
				### particle numbering in Appion db starts with 1
				stackpartdata = apStack.getStackParticle(self.runparams['stackid'], int(p)+1)
				alignpartq['stackpart'] = stackpartdata
				alignpartq['bad'] = 1
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
		if self.params['align'] is True:
			if (classnum-1) in self.resdict:
				clusterrefq['ssnr_resolution'] = self.resdict[classnum-1]
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
#		self.insertCL2DJob()
		self.stack = {}
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])

		if self.params['virtualdata'] is not None:
			self.stack['file'] = self.params['virtualdata']['filename']
		else:
			self.stack['file'] = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])

		### process stack to local file
		if self.params['timestamp'] is None:
			apDisplay.printMsg("creating timestamp")
			self.params['timestamp'] = self.timestamp
		self.params['localstack'] = os.path.join(self.params['rundir'], self.params['timestamp']+".hed")
		if os.path.isfile(self.params['localstack']):
			apFile.removeStack(self.params['localstack'])

		a = proc2dLib.RunProc2d()
		a.setValue('infile',self.stack['file'])
		a.setValue('outfile',self.params['localstack'])
		a.setValue('apix',self.stack['apix'])
		a.setValue('bin',self.params['bin'])
		a.setValue('last',self.params['numpart']-1)

		if self.params['lowpass'] is not None and self.params['lowpass'] > 1:
			a.setValue('lowpass',self.params['lowpass'])
		if self.params['highpass'] is not None and self.params['highpass'] > 1:
			a.setValue('highpass',self.params['highpass'])
		if self.params['invert'] is True:
			a.setValue('invert',True)

		# clip not yet implemented
#		if self.params['clipsize'] is not None:
#			clipsize = int(self.clipsize)*self.params['bin']
#			if clipsize % 2 == 1:
#				clipsize += 1 ### making sure that clipped boxsize is even
#			a.setValue('clip',clipsize)

		if self.params['virtualdata'] is not None:
			vparts = self.params['virtualdata']['particles']
			plist = [int(p['particleNumber'])-1 for p in vparts]
			a.setValue('list',plist)

		#run proc2d
		a.run()

		if self.params['numpart'] != apFile.numImagesInStack(self.params['localstack']):
			apDisplay.printError("Missing particles in stack")

		### convert stack into single spider files
		self.partlistdocfile = apXmipp.breakupStackIntoSingleFiles(self.params['localstack'])

		### setup Xmipp command
		aligntime = time.time()
		xmippopts = ( " "
			+" -i "+os.path.join(self.params['rundir'], self.partlistdocfile)
			+" -codes "+str(self.params['numrefs'])
			+" -iter "+str(self.params['maxiter'])
			+" -o "+os.path.join(self.params['rundir'], "part"+self.params['timestamp'])
		)
		if self.params['fast']:
			xmippopts += " -fast "
		if self.params['correlation']:
			xmippopts += " -useCorrelation "
		if self.params['classical']:
			xmippopts += " -classicalMultiref "		
		if self.params['align']:
			xmippopts += " -alignImages "

		### use multi-processor command
		apDisplay.printColor("Using "+str(self.params['nproc'])+" processors!", "green")
		xmippexe = apParam.getExecPath("xmipp_mpi_class_averages", die=True)
		mpiruncmd = self.mpirun+" -np "+str(self.params['nproc'])+" "+xmippexe+" "+xmippopts
		self.writeXmippLog(mpiruncmd)
		apParam.runCmd(mpiruncmd, package="Xmipp", verbose=True, showcmd=True, logfile="xmipp.std")
		self.params['runtime'] = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(self.params['runtime']))

		### minor post-processing
		self.createReferenceStack()
		self.parseOutput()
		self.clearIntermediateFiles()
#		self.readyUploadFlag()
		apParam.dumpParameters(self.params, "cl2d-"+self.params['timestamp']+"-params.pickle")

		### upload results ... this used to be two separate operations, I'm combining into one
		self.runparams = apParam.readRunParameters("cl2d-"+self.params['timestamp']+"-params.pickle")
		self.apix = apStack.getStackPixelSizeFromStackId(self.runparams['stackid'])*self.runparams['bin']
		self.Nlevels=len(glob.glob("part"+self.params['timestamp']+"_level_??_.hed"))

		### create average of aligned stacks & insert aligned stack info
		lastLevelStack = "part"+self.params['timestamp']+"_level_%02d_.hed"%(self.Nlevels-1)
		apStack.averageStack(lastLevelStack)
		self.boxsize = apFile.getBoxSize(lastLevelStack)[0]
		self.insertCL2DParamsIntoDatabase()
		if self.runparams['align'] is True:
			self.insertAlignStackRunIntoDatabase("alignedStack.hed")
			self.calcResolution(self.Nlevels-1)
			self.insertAlignParticlesIntoDatabase(level=self.Nlevels-1)
		
		### loop over each class average stack & insert as clustering stacks
		self.insertClusterRunIntoDatabase()
		for level in range(self.Nlevels):
			### NOTE: RESOLUTION CAN ONLY BE CALCULATED IF ALIGNED STACK EXISTS TO EXTRACT / READ THE PARTICLES
			if self.params['align'] is True:
				self.calcResolution(level)
			partdict = self.getClassificationAtLevel(level)
			for classnum in partdict: 
				self.insertClusterStackIntoDatabase(
					"part"+self.params['timestamp']+"_level_%02d_.hed"%level,
					classnum+1, partdict[classnum], len(partdict))
					
#=====================
if __name__ == "__main__":
	cl2d = CL2D()
	cl2d.start()
	cl2d.close()
