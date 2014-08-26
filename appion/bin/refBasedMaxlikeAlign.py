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
from appionlib import apEMAN
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
class MaximumLikelihoodScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):


		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int",
			help="Number of particles to use", metavar="#")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")

		self.parser.add_option("--clip", dest="clipsize", type="int",
			help="Clip size in pixels (reduced box size)", metavar="#")
		self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="int",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--highpass", "--hp", dest="highpass", type="int",
			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")

		self.parser.add_option("--max-iter", dest="maxiter", type="int", default=30,
			help="Maximum number of iterations", metavar="#")
		self.parser.add_option("--angle-interval", dest="psistep", type="int", default=5,
			help="In-plane rotation sampling interval (degrees)", metavar="#")

		self.parser.add_option("--template-list", dest="templatelist",
			help="Template Id for template init method", metavar="56,12,34")

		### true/false
		self.parser.add_option("-F", "--fast", dest="fast", default=True,
			action="store_true", help="Use fast method")
		self.parser.add_option("--no-fast", dest="fast", default=True,
			action="store_false", help="Do NOT use fast method")

		self.parser.add_option("-M", "--mirror", dest="mirror", default=True,
			action="store_true", help="Use mirror method")
		self.parser.add_option("--no-mirror", dest="mirror", default=True,
			action="store_false", help="Do NOT use mirror method")

		self.parser.add_option("--norm", dest="norm", default=False,
			action="store_true", help="Use internal normalization for data with normalization errors")
		self.parser.add_option("--no-norm", dest="norm", default=False,
			action="store_false", help="Do NOT use internal normalization")

		self.parser.add_option("--invert-templates", dest="inverttemplates", default=False,
			action="store_true", help="Invert the density of all the templates")


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
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['description'] is None:
			apDisplay.printError("run description was not defined")

		### convert / check template data
		if self.params['templatelist'] is None:
			apDisplay.printError("template list was not provided")
		self.templatelist = self.params['templatelist'].strip().split(",")
		if not self.templatelist or type(self.templatelist) != type([]):
			apDisplay.printError("could not parse template list="+self.params['templatelist'])
		self.params['numtemplate'] = len(self.templatelist)
		apDisplay.printMsg("Found "+str(self.params['numtemplate'])+" templates")

		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
		if not self.params['fastmode'] in self.fastmodes:
			apDisplay.printError("fast mode must be on of: "+str(self.fastmodes))
		if not self.params['converge'] in self.convergemodes:
			apDisplay.printError("converge mode must be on of: "+str(self.convergemodes))
		maxparticles = 150000
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
			if self.params['clipsize'] >= self.clipsize:
				apDisplay.printError("requested clipsize is too big %d > %d"
					%(self.params['clipsize'],self.clipsize))
			self.clipsize = self.params['clipsize']
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
		maxjobq = appiondata.ApMaxLikeJobData()
		maxjobq['runname'] = self.params['runname']
		maxjobq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		maxjobdatas = maxjobq.query(results=1)
		if maxjobdatas:
			alignrunq = appiondata.ApAlignRunData()
			alignrunq['runname'] = self.params['runname']
			alignrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			alignrundata = alignrunq.query(results=1)
			if maxjobdatas[0]['finished'] is True or alignrundata:
				apDisplay.printError("This run name already exists as finished in the database, please change the runname")
		maxjobq['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		maxjobq['timestamp'] = self.timestamp
		maxjobq['finished'] = False
		maxjobq['hidden'] = False
		if self.params['commit'] is True:
			maxjobq.insert()
		self.params['maxlikejobid'] = maxjobq.dbid
		print "self.params['maxlikejobid']",self.params['maxlikejobid']
		return

	#=====================
	def readyUploadFlag(self):
		if self.params['commit'] is False:
			return
		config = sinedon.getConfig('appiondata')
		dbc = MySQLdb.Connect(**config)
		dbc.autocommit(True)
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
			nproc = apParam.getNumProcessors()
		else:
			nproc = self.params['nproc']

		calctime = (
			(self.params['numpart']/1000.0)
			*self.params['numtemplate']
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
	def checkMPI(self):
		mpiexe = apParam.getExecPath("mpirun")
		if mpiexe is None:
			return None
		xmippexe = apParam.getExecPath("xmipp_mpi_ml_align2d")
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
	def createReferenceStack(self):
		avgstack = "part"+self.timestamp+"_average.hed"
		apFile.removeStack(avgstack, warn=False)
		searchstr = "part"+self.timestamp+"_ref0*.xmp"
		files = glob.glob(searchstr)
		if len(files) == 0:
			apDisplay.printError("Xmipp did not run")
		files.sort()
		stack = []
		for i in range(len(files)):
			fname = files[i]
			refarray = spider.read(fname)
			stack.append(refarray)
		apImagicFile.writeImagic(stack, avgstack)
		### create a average mrc
		stackarray = numpy.asarray(stack, dtype=numpy.float32)
		avgdata = stackarray.mean(0)
		apImage.arrayToMrc(avgdata, "average.mrc")
		return

	#=====================
	def initializeTemplates(self):
		"""
		creates initial templates
		"""
		templatetime = time.time()

		templatedir = os.path.join(self.params['rundir'], "templates")
		apParam.createDirectory(templatedir)

		### hack to use standard filtering library
		templateparams = {}
		templateparams['apix'] = self.stack['apix']
		templateparams['rundir'] = templatedir
		templateparams['templateIds'] = self.templatelist
		templateparams['bin'] = self.params['bin']
		templateparams['lowpass'] = self.params['lowpass']
		templateparams['median'] = None
		templateparams['pixlimit'] = None
		filelist = apTemplate.getTemplates(templateparams)

		templateselfile = os.path.join(self.params['rundir'], "templates.sel")
		f = open(templateselfile, "w")
		for mrcfile in filelist:
			spifile = mrcfile[:-4]+".xmp"
			emancmd  = ("proc2d templates/"+mrcfile+" templates/"+spifile
				+" clip="+str(self.clipsize)+","+str(self.clipsize)
				+" spiderswap-single ")
			if self.params['inverttemplates'] is True:
				emancmd += " invert "
			apEMAN.executeEmanCmd(emancmd, showcmd=False)
			if not os.path.isfile("templates/"+spifile):
				apDisplay.printError("Template conversion failed")
			temppath = os.path.join(self.params['rundir'], "templates/"+spifile)
			f.write(temppath+" 1\n")
		f.close()

		templatetime = time.time() - templatetime
		apDisplay.printMsg("Template time: "+apDisplay.timeString(templatetime))
		return templateselfile

	#=====================
	def start(self):
		self.insertMaxLikeJob()
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])
		self.estimateIterTime()
		self.dumpParameters()

		### process stack to local temp file

		proccmd = "proc2d "+self.stack['file']+" temp.hed apix="+str(self.stack['apix'])
		if self.params['bin'] > 1 or self.params['clipsize'] is not None:
			clipsize = int(self.clipsize)*self.params['bin']
			proccmd += " shrink=%d clip=%d,%d "%(self.params['bin'],clipsize,clipsize)
		proccmd += " last="+str(self.params['numpart']-1)
		apEMAN.executeEmanCmd(proccmd, verbose=True)

		### process stack to final file
		self.params['localstack'] = os.path.join(self.params['rundir'], self.timestamp+".hed")
		proccmd = "proc2d temp.hed "+self.params['localstack']+" apix="+str(self.stack['apix']*self.params['bin'])
		if self.params['highpass'] is not None and self.params['highpass'] > 1:
			proccmd += " hp="+str(self.params['highpass'])
		if self.params['lowpass'] is not None and self.params['lowpass'] > 1:
			proccmd += " lp="+str(self.params['lowpass'])
		apEMAN.executeEmanCmd(proccmd, verbose=True)
		apFile.removeStack("temp.hed")

		### convert stack into single spider files
		self.partlistdocfile = apXmipp.breakupStackIntoSingleFiles(self.params['localstack'])

		### convert stack into single spider files
		templateselfile = self.initializeTemplates()

		### setup Xmipp command
		aligntime = time.time()

		xmippopts = ( " "
			+" -i "+os.path.join(self.params['rundir'], self.partlistdocfile)
			+" -iter "+str(self.params['maxiter'])
			+" -ref "+templateselfile
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
			xmippexe = apParam.getExecPath("xmipp_mpi_ml_align2d", die=True)
			mpiruncmd = mpirun+" -np "+str(nproc-1)+" "+xmippexe+" "+xmippopts
			self.writeXmippLog(mpiruncmd)
			apEMAN.executeEmanCmd(mpiruncmd, verbose=True, showcmd=True)
		else:
			### use single processor
			xmippexe = apParam.getExecPath("xmipp_ml_align2d", die=True)
			xmippcmd = xmippexe+" "+xmippopts
			self.writeXmippLog(xmippcmd)
			apEMAN.executeEmanCmd(xmippcmd, verbose=True, showcmd=True)
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		### minor post-processing
		self.createReferenceStack()
		self.readyUploadFlag()
		self.dumpParameters()

#=====================
if __name__ == "__main__":
	maxLike = MaximumLikelihoodScript()
	maxLike.start()
	maxLike.close()



