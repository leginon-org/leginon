#!/usr/bin/env python

#python
import os
import time
import sys
import random
import math
import shutil
import glob
import cPickle
import subprocess
import numpy
import MySQLdb
#appion
import appionScript
import apDisplay
import apFile
import apTemplate
import apStack
import apParam
import apEMAN
import apXmipp
import appionData
import spyder
import apImagicFile
import apProject
from apSpider import alignment
from pyami import spider
import sinedon

"""
USE 
http://www.wadsworth.org/spider_doc/spider/docs/man/sy.html
to create SYMMETRY DOC files
"""

#=====================
#=====================
class MaximumLikelihoodScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")

		### integers
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("--cluster-id", dest="clusterid", type="int",
			help="clustering stack id", metavar="ID")
		self.parser.add_option("--align-id", dest="alignid", type="int",
			help="alignment stack id", metavar="ID")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int",
			help="Number of particles to use", metavar="#")
		self.parser.add_option("-m", "--model", dest="modelid", type="int",
			help="Initial model database id", metavar="ID#")
		self.parser.add_option("--nproc", dest="nproc", type="int",
			help="Number of processor to use", metavar="ID#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")
		self.parser.add_option("--numvol", dest="nvol", type="int", default=2,
			help="Number of volumes to create", metavar="#")
		self.parser.add_option("--max-iter", dest="maxiter", type="int", default=100,
			help="Maximum number of iterations", metavar="#")
		self.parser.add_option("--angle-interval", dest="psistep", type="int", default=5,
			help="In-plane rotation sampling interval (degrees)", metavar="#")

		### floats
		self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="float",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--highpass", "--hp", dest="highpass", type="float",
			help="High pass filter radius (in Angstroms)", metavar="#")

		### true/false
		self.parser.add_option("-F", "--fast", dest="fast", default=True,
			action="store_true", help="Use fast method")
		self.parser.add_option("--no-fast", dest="fast", default=True,
			action="store_false", help="Do NOT use fast method")
		self.parser.add_option("-M", "--mirror", dest="mirror", default=True,
			action="store_true", help="Use mirror method")
		self.parser.add_option("--no-mirror", dest="mirror", default=True,
			action="store_false", help="Do NOT use mirror method")
		self.parser.add_option("--norm", dest="norm", default=True,
			action="store_true", help="Use internal normalization for data with normalization errors")
		self.parser.add_option("--no-norm", dest="norm", default=True,
			action="store_false", help="Do NOT use internal normalization")

		### choices
		self.fastmodes = ( "normal", "narrow", "wide" )
		self.parser.add_option("--fast-mode", dest="fastmode",
			help="Search space reduction cutoff criteria", metavar="MODE", 
			type="choice", choices=self.fastmodes, default="normal" )
		self.convergemodes = ( "normal", "fast", "slow" )
		self.parser.add_option("--converge", dest="converge",
			help="Convergence criteria mode", metavar="MODE", 
			type="choice", choices=self.convergemodes, default="normal" )

	#=====================
	def checkConflicts(self):
		### check for missing and duplicate entries
		#if self.params['alignid'] is None and self.params['clusterid'] is None:
		#	apDisplay.printError("Please provide either --cluster-id or --align-id")
		if self.params['alignid'] is not None and self.params['clusterid'] is not None:
			apDisplay.printError("Please provide only one of either --cluster-id or --align-id")		

		### get the stack ID from the other IDs
		if self.params['alignid'] is not None:
			self.alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignid'])
			self.params['stackid'] = self.alignstackdata['stack'].dbid
		elif self.params['clusterid'] is not None:
			self.clusterstackdata = appionData.ApClusteringStackData.direct_query(self.params['clusterid'])
			self.alignstackdata = self.clusterstackdata['clusterrun']['alignstack']
			self.params['stackid'] = self.alignstackdata['stack'].dbid
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")


		#if self.params['description'] is None:
		#	apDisplay.printError("run description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
		if not self.params['fastmode'] in self.fastmodes:
			apDisplay.printError("fast mode must be on of: "+str(self.fastmodes))
		maxparticles = 150000
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
		paramfile = "maxlike-"+self.timestamp+"-params.pickle"
		pf = open(paramfile, "w")
		cPickle.dump(self.params, pf)
		pf.close()

	#=====================
	def insertMaxLikeJob(self):
		maxjobq = appionData.ApMaxLikeJobData()
		maxjobq['runname'] = self.params['runname']
		maxjobq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		maxjobdatas = maxjobq.query(results=1)
		if maxjobdatas:
			alignrunq = appionData.ApAlignRunData()
			alignrunq['runname'] = self.params['runname']
			alignrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
			alignrundata = alignrunq.query(results=1)
			if maxjobdatas[0]['finished'] is True or alignrundata:
				apDisplay.printError("This run name already exists as finished in the database, please change the runname")
		maxjobq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		maxjobq['timestamp'] = self.timestamp
		maxjobq['finished'] = False
		maxjobq['hidden'] = False
		#if self.params['commit'] is True:
		#	maxjobq.insert()
		self.params['maxlikejobid'] = maxjobq.dbid
		print "self.params['maxlikejobid']",self.params['maxlikejobid']
		return

	#=====================
	def readyUploadFlag(self):
		if self.params['commit'] is False:
			return
		config = sinedon.getConfig('appionData')
		dbc = MySQLdb.Connect(**config)
		cursor = dbc.cursor()
		query = (
			"  UPDATE ApMaxLikeJobData "
			+" SET `finished` = '1' "
			+" WHERE `DEF_id` = '"+str(self.params['maxlikejobid'])+"'"
		)
		cursor.execute(query)
		cursor.close()
		dbc.close()

	#=====================
	def estimateIterTime(self):
		secperiter = 0.12037
		### get num processors
		if self.params['nproc'] is None:
			nproc = nproc = apParam.getNumProcessors()
		else:
			nproc = self.params['nproc']

		calctime = (
			(self.params['numpart']/1000.0)
			*(self.stack['boxsize']/self.params['bin'])**2
			/self.params['psistep']
			/float(nproc)
			*secperiter
		)
		if self.params['mirror'] is True:
			calctime *= 2.0
		self.params['estimatedtime'] = calctime
		apDisplay.printColor("Estimated first iteration time: "+apDisplay.timeString(calctime), "purple")

	#=====================
	def createAverageStack(self):
		searchstr = "part"+self.timestamp+"_ref0*.xmp"
		files = glob.glob(searchstr)
		files.sort()
		stack = []
		for fname in files:
			refarray = spider.read(fname)
			stack.append(refarray)
		stackarray = numpy.asarray(stack, dtype=numpy.float32)
		print stackarray.shape
		apImagicFile.writeImagic(stackarray, "part"+self.timestamp+"_average.hed")
		return

	#=====================
	def checkMPI(self):
		mpiexe = apParam.getExecPath("mpirun")
		if mpiexe is None:
			return None
		xmippexe = apParam.getExecPath("xmipp_mpi_ml_refine3d")
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
	def createGaussianSphere(self, volfile, boxsize):
		stdev = boxsize/4.0
		halfbox = boxsize/2.0
		#width of Gaussian
		gaussstr = "%.3f,%.3f,%.3f"%(stdev+random.random(), stdev+random.random(), stdev+random.random())
		apDisplay.printMsg("Creating Gaussian volume with stdev="+gaussstr)
		mySpider = spyder.SpiderSession(logo=False)
		mySpider.toSpiderQuiet("MO 3",
			spyder.fileFilter(volfile),
			"%d,%d,%d"%(boxsize,boxsize,boxsize),
			"G", #G for Gaussian
			"%.3f,%.3f,%.3f"%(halfbox,halfbox,halfbox), #center of Gaussian
			gaussstr,
		)
		mySpider.close()
		return

	#=====================
	def setupVolumes(self, boxsize):
		voldocfile = "volumelist"+self.timestamp+".doc"
		f = open(voldocfile, "w")
		for i in range(self.params['nvol']):
			volfile = os.path.join(self.params['rundir'], "volume%s_%05d.spi"%(self.timestamp, i+1))
			self.createGaussianSphere(volfile, boxsize)
			f.write(volfile+" 1\n")
		f.close()
		return voldocfile

	#=====================
	def setupParticles(self):
		self.params['localstack'] = os.path.join(self.params['rundir'], self.timestamp+".hed")

		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])

		boxsize = int(math.floor(self.stack['boxsize']/float(self.params['bin'])))

		proccmd = "proc2d "+self.stack['file']+" "+self.params['localstack']+" apix="+str(self.stack['apix'])
		if self.params['bin'] > 1:
			clipsize = boxsize*self.params['bin']
			proccmd += " shrink=%d clip=%d,%d "%(self.params['bin'],clipsize,clipsize)
		if self.params['highpass'] > 1:
			proccmd += " hp="+str(self.params['highpass'])
		if self.params['lowpass'] > 1:
			proccmd += " lp="+str(self.params['lowpass'])
		proccmd += " last="+str(self.params['numpart'])
		apEMAN.executeEmanCmd(proccmd, verbose=True)

		### convert stack into single spider files
		self.partlistdocfile = apXmipp.breakupStackIntoSingleFiles(self.params['localstack'])
		return boxsize

	#=====================
	def runrefine(self):
		### setup Xmipp command
		recontime = time.time()

		xmippopts = ( " "
			+" -i "+os.path.join(self.params['rundir'], self.partlistdocfile)
			+" -vol "+os.path.join(self.params['rundir'], self.voldocfile)
			+" -iter "+str(self.params['maxiter'])
			+" -o "+os.path.join(self.params['rundir'], "part"+self.timestamp)
			+" -psi_step "+str(self.params['psistep'])
		)
		### fast mode
		if self.params['fast'] is True:
			xmippopts += " -fast "
			if self.params['fastmode'] == "narrow":
				xmippopts += " -C 1e-10 "
			elif self.params['fastmode'] == "wide":
				xmippopts += " -C 1e-18 "
		### convergence criteria
		if self.params['converge'] == "fast":
			xmippopts += " -eps 5e-3 "
		elif self.params['converge'] == "slow":
			xmippopts += " -eps 5e-8 "
		else:
			xmippopts += " -eps 5e-5 "
		### mirrors
		if self.params['mirror'] is True:
			xmippopts += " -mirror "
		### normalization
		if self.params['norm'] is True:
			xmippopts += " -norm "

		### find number of processors
		if self.params['nproc'] is None:
			nproc = nproc = apParam.getNumProcessors()
		else:
			nproc = self.params['nproc']
		mpirun = self.checkMPI()
		if nproc > 2 and mpirun is not None:
			### use multi-processor
			apDisplay.printColor("Using "+str(nproc-1)+" processors!", "green")
			xmippexe = apParam.getExecPath("xmipp_mpi_ml_refine3d", die=True)
			mpiruncmd = mpirun+" -np "+str(nproc-1)+" "+xmippexe+" "+xmippopts
			self.writeXmippLog(mpiruncmd)
			apEMAN.executeEmanCmd(mpiruncmd, verbose=True, showcmd=True)
		else:
			### use single processor
			xmippexe = apParam.getExecPath("xmipp_ml_refine3d", die=True)
			xmippcmd = xmippexe+" "+xmippopts
			self.writeXmippLog(xmippcmd)
			apEMAN.executeEmanCmd(xmippcmd, verbose=True, showcmd=True)
		apDisplay.printMsg("Reconstruction time: "+apDisplay.timeString(time.time() - recontime))

	#=====================
	def start(self):
		#self.insertMaxLikeJob()

		#self.estimateIterTime()
		self.dumpParameters()

		### set particles
		boxsize = self.setupParticles()

		### setup volumes

		self.voldocfile = self.setupVolumes(boxsize)

		### run the refinement
		self.dumpParameters()
		self.runrefine()

		self.readyUploadFlag()
		self.dumpParameters()

#=====================
if __name__ == "__main__":
	maxLike = MaximumLikelihoodScript(True)
	maxLike.start()
	maxLike.close()


