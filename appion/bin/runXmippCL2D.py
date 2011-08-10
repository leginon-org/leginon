#!/usr/bin/env python
#
import os
import time
import sys
import random
import math
import shutil
import glob
import cPickle
import subprocess
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apFile
import numpy
from appionlib import apTemplate
from appionlib import apStack
from appionlib import apParam
from appionlib import apXmipp
from appionlib import apImage
from pyami import spider
from appionlib import appiondata
from appionlib import apImagicFile
from appionlib import apProject
import sinedon
import MySQLdb

#=====================
#=====================
class CL2D(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int",
			help="Number of particles to use", metavar="#")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")

		self.parser.add_option("--nproc", dest="nproc", type="int",
			help="Number of processors to use", metavar="ID#")

		self.parser.add_option("--clip", dest="clipsize", type="int",
			help="Clip size in pixels (reduced box size)", metavar="#")
		self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="int",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--highpass", "--hp", dest="highpass", type="int",
			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")

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
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		if self.params['numpart'] > apFile.numImagesInStack(stackfile):
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
		if self.checkMPI() is None:
			apDisplay.printError("There is no MPI installed")

	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])

	#=====================
	def dumpParameters(self):
		self.params['runtime'] = time.time() - self.t0
		self.params['timestamp'] = self.timestamp
		paramfile = "cl2d-"+self.timestamp+"-params.pickle"
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
		cl2dq['timestamp'] = self.timestamp
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
		os.system("rm -rf partfiles *.xmp *.doc "+self.timestamp+".* "+\
		          "part"+self.timestamp+"0*.sel part*_.sel partlist.sel "+\
			  "part"+self.timestamp+".sel xmipp.std")

	#=====================
	def createReferenceStack(self):
		# Create a stack for the class averages at each level
		Nlevels=len(glob.glob("part"+self.timestamp+"_level_??_.sel"))
		for level in range(Nlevels):
			stack=[]
			for f in glob.glob("part"+self.timestamp+"_level_%02d_[0-9]*.xmp"%level):
				stack.append(spider.read(f))
			apImagicFile.writeImagic(stack, "part"+self.timestamp+"_level_%02d_.hed"%level)
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
				fhOut=open("part"+self.timestamp+"_level_%02d_convergence.txt"%level,"w")
			elif tokens[0]=="Number":
				print >>fhOut, tokens[3].split("=")[1].rstrip()
		if not fhOut is None:
			fhOut.close()
		fh.close()		

	#=====================
	def start(self):
		self.insertCL2DJob()
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])
		self.dumpParameters()

		### process stack to local file
		self.params['localstack'] = os.path.join(self.params['rundir'], self.timestamp+".hed")
		proccmd = "proc2d "+self.stack['file']+" "+self.params['localstack']+" apix="+str(self.stack['apix'])
		if self.params['bin'] > 1 or self.params['clipsize'] is not None:
			clipsize = int(self.clipsize)*self.params['bin']
			if clipsize % 2 == 1:
				clipsize += 1 ### making sure that clipped boxsize is even
			proccmd += " shrink=%d clip=%d,%d "%(self.params['bin'],clipsize,clipsize)
		proccmd += " last="+str(self.params['numpart']-1)
		if self.params['highpass'] is not None and self.params['highpass'] > 1:
			proccmd += " hp="+str(self.params['highpass'])
		if self.params['lowpass'] is not None and self.params['lowpass'] > 1:
			proccmd += " lp="+str(self.params['lowpass'])
		apParam.runCmd(proccmd, "EMAN", verbose=True)
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
			+" -o "+os.path.join(self.params['rundir'], "part"+self.timestamp)
		)
		if self.params['fast']:
			xmippopts += " -fast "
		if self.params['correlation']:
			xmippopts += " -useCorrelation "
		if self.params['classical']:
			xmippopts += " -classicalMultiref "		
		if self.params['align']:
			xmippopts += " -alignImages "

		### find number of processors
		if self.params['nproc'] is None:
			nproc = nproc = apParam.getNumProcessors()
		else:
			nproc = self.params['nproc']
		mpirun = self.checkMPI()
		if nproc > 2 and mpirun is not None:
			### use multi-processor
			apDisplay.printColor("Using "+str(nproc)+" processors!", "green")
			xmippexe = apParam.getExecPath("xmipp_mpi_class_averages", die=True)
			mpiruncmd = mpirun+" -np "+str(nproc)+" "+xmippexe+" "+xmippopts
			self.writeXmippLog(mpiruncmd)
			apParam.runCmd(mpiruncmd, package="Xmipp", verbose=True, showcmd=True, logfile="xmipp.std")
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		### minor post-processing
		self.createReferenceStack()
		self.parseOutput()
		self.clearIntermediateFiles()
		self.readyUploadFlag()
		self.dumpParameters()

#=====================
if __name__ == "__main__":
	cl2d = CL2D(True)
	cl2d.start()
	cl2d.close()
