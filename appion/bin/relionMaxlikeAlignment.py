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
import numpy
from pyami import mrc
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apTemplate
from appionlib import apStack
from appionlib import apParam
from appionlib import apImage
from appionlib import appiondata
from appionlib import apImagicFile
from appionlib import apProject
from appionlib import proc2dLib
import sinedon
import MySQLdb

#=====================
#=====================
class RelionMaxLikeScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):


		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("-N", "--numpart", dest="numpart", type="int",
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

		self.parser.add_option("--maxIter", "--max-iter", dest="maxiter", type="int", default=30,
			help="Maximum number of iterations", metavar="#")
		self.parser.add_option("--numRef", "--num-ref", dest="numrefs", type="int",
			help="Number of classes to create", metavar="#")
		self.parser.add_option("--angStep", "--angle-step", dest="psistep", type="int", default=5,
			help="In-plane rotation sampling step (degrees)", metavar="#")
		self.parser.add_option("--tau", dest="tau", type="float", default=1,
			help="Tau2 Fudge Factor (> 1)", metavar="#")
		
		# Job parameters that the remotehost need
		self.parser.add_option("--nodes", dest="nodes", type="int", default=1,
			help="Number of nodes requested for multi-node capable tasks", metavar="#")
		self.parser.add_option("--ppn", dest="ppn", type="int", default=1,
			help="Minimum Processors per node", metavar="#")
		self.parser.add_option("--mem", dest="mem", type="int", default=4,
			help="Maximum memory per node (in GB)", metavar="#")
		self.parser.add_option("--walltime", dest="walltime", type="int", default=24,
			help="Maximum walltime in hours", metavar="#")
		self.parser.add_option('--cput', dest='cput', type='int', default=None)

		self.parser.add_option("--invert", dest='invert', default=False,
			action="store_true", help="Invert before alignment")

		self.parser.add_option("--flat", "--flatten-solvent", dest='flattensolvent', default=False,
			action="store_true", help="Flatten Solvent in References")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		#if self.params['description'] is None:
		#	apDisplay.printError("run description was not defined")
		if self.params['numrefs'] is None:
			apDisplay.printError("a number of classes was not provided")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
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

	#=====================
	def setRunDir(self):
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
		##FIXME
		return 1
		secperiter = 0.12037
		### get num processors
		nproc = self.params['ppn']*self.params['nodes']

		calctime = (
			(self.params['numpart']/1000.0)
			*self.params['numrefs']
			*(self.stack['boxsize']/self.params['bin'])**2
			/self.params['psistep']
			/float(nproc)
			*secperiter
		)
		self.params['estimatedtime'] = calctime
		apDisplay.printColor("Estimated first iteration time: "+apDisplay.timeString(calctime), "purple")

	#=====================
	def writeRelionLog(self, text):
		f = open("relion.log", "a")
		f.write(apParam.getLogHeader())
		f.write(text+"\n")
		f.close()

	#=====================
	def createReferenceStack(self):
		avgstack = "part"+self.timestamp+"_average.hed"
		apFile.removeStack(avgstack, warn=False)
		searchstr = "part"+self.timestamp+"_it*_classes.mrcs"
		classStackFiles = glob.glob(searchstr)
		classStackFiles.sort()
		fname = classStackFiles[-1]
		print("reading class averages from file %s"%(fname))
		refarray = mrc.read(fname)
		apImagicFile.writeImagic(refarray, avgstack)
		### create a average mrc
		avgdata = refarray.mean(0)
		apImage.arrayToMrc(avgdata, "average.mrc")
		return

	#=====================
	def start(self):
		self.insertMaxLikeJob()
		self.stack = {}
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])
		if self.params['virtualdata'] is not None:
			self.stack['file'] = self.params['virtualdata']['filename']
		else:
			self.stack['file'] = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])

		self.estimateIterTime()
		self.dumpParameters()

		### process stack to local file
		self.params['localstack'] = os.path.join(self.params['rundir'], self.timestamp+".hed")

		a = proc2dLib.RunProc2d()
		a.setValue('infile',self.stack['file'])
		a.setValue('outfile',self.params['localstack'])
		a.setValue('apix',self.stack['apix'])
		a.setValue('bin',self.params['bin'])
		a.setValue('last',self.params['numpart']-1)
		a.setValue('append',False)
		### pixlimit and normalization are required parameters for RELION
		a.setValue('pixlimit',4.49)
		a.setValue('normalizemethod','edgenorm')

		if self.params['lowpass'] is not None and self.params['lowpass'] > 1:
			a.setValue('lowpass',self.params['lowpass'])
		if self.params['highpass'] is not None and self.params['highpass'] > 1:
			a.setValue('highpass',self.params['highpass'])
		if self.params['invert'] is True:
			a.setValue('invert') is True

		if self.params['virtualdata'] is not None:
			vparts = self.params['virtualdata']['particles']
			plist = [int(p['particleNumber'])-1 for p in vparts]
			a.setValue('list',plist)

		# clip not yet implemented
		if self.params['clipsize'] is not None:
			clipsize = int(self.clipsize)*self.params['bin']
			if clipsize % 2 == 1:
				clipsize += 1 ### making sure that clipped boxsize is even
			a.setValue('clip',clipsize)

		if self.params['virtualdata'] is not None:
			vparts = self.params['virtualdata']['particles']
			plist = [int(p['particleNumber'])-1 for p in vparts]
			a.setValue('list',plist)

		#run proc2d
		a.run()

		if self.params['numpart'] != apFile.numImagesInStack(self.params['localstack']):
			apDisplay.printError("Missing particles in stack")

		### setup Relion command
		aligntime = time.time()

		relionopts = ( " "
			+" --i %s "%(self.params['localstack'])
			+" --o %s "%(os.path.join(self.params['rundir'], "part"+self.timestamp))
			+" --angpix %.4f "%(self.stack['apix']*self.params['bin'])
			+" --iter %d "%(self.params['maxiter'])
			+" --K %d "%(self.params['numrefs'])
			+" --psi_step %d "%(self.params['psistep'])
			+" --tau2_fudge %.1f "%(self.params['tau'])
		)

		### find number of processors
		nproc = self.params['ppn'] * self.params['nodes']
		relionopts += " --j %d "%(nproc)

		if self.params['flattensolvent'] is True:
			relionopts += " --flatten_solvent "


		self.estimateIterTime()
		relionexe = apParam.getExecPath("relion_refine", die=True)
		relioncmd = relionexe+" "+relionopts
		self.writeRelionLog(relioncmd)
		apParam.runCmd(relioncmd, package="RELION", verbose=True, showcmd=True)
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		### minor post-processing
		self.createReferenceStack()
		self.readyUploadFlag()
		self.dumpParameters()

#=====================
if __name__ == "__main__":
	maxLike = RelionMaxLikeScript()
	maxLike.start()
	maxLike.close()



