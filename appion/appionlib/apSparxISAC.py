#!/usr/bin/env python
#
import os
import time
import sys
import math
import subprocess
import re
#appion
from appionlib import apRemoteJob
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apStack
from appionlib import apParam
from appionlib import apProject
from appionlib import appiondata
from appionlib import processingHost
from appionlib import apRecon
import sinedon
import MySQLdb

#=====================
#=====================
class ISACJob(apRemoteJob.RemoteJob): # technically not a refine job, but a big job run on a remote cluster

	#=====================
	def setupParserOptions(self):
		super(ISACJob,self).setupParserOptions()
		### basic params
		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("--alignstack", dest="alignstackid", type="int",
			help="Align stack database id", metavar="ID#")
		self.parser.add_option("--timestamp", dest="timestamp",
			help="Timestamp of files, e.g. 08nov02b35", metavar="CODE")
		self.parser.add_option("--nproc", dest="nproc",
			help="number of processors", metavar="#")
#		self.parser.add_option("--projectid", dest="projectid", type="int",
#			help="Project id associated with processing run, e.g. --projectid=159", metavar="#")
		
		### filtering, clipping, etc.	
		self.parser.add_option("--clip", dest="clipsize", type="int",
			help="Clip size in pixels (reduced box size)", metavar="#")
		self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="int",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--highpass", "--hp", dest="highpass", type="int",
			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")
		self.parser.add_option("--num-part", dest="numpart", type="int",
			help="Number of particles to use", metavar="#")
			
		### ISAC params
		self.parser.add_option("--generations", dest="generations", type="int", 
			help="number of approaches on the dataset", metavar="#") 

		'''

		self.parser.add_option("--ir", dest="ir", type="str", 
			help="Inner radius of the resampling to polar coordinate, colon separate for different generations, \
			e.g. 4x1:2x5 means ir=0 for 4 generations and ir=5 for 2 generations (default 1)", metavar="# or STR")
		self.parser.add_option("--ou", dest="ou", type="str", 
			help="Outer radius of the resampling to polar coordinate, colon separate for different generations, \
			e.g. 4x24:2x20 means ou=24 for 4 generations and ou=20 for 2 generations (default box/2-2", metavar="# or STR")
		self.parser.add_option("--rs", dest="rs", type="str", 
			help="Ring step of the resampling to polar coordinate, colon separate for different generations, \
			e.g. 4x1:2x2 means rs=1 for 4 generations and rs=2 for 2 generations (default 1)", metavar="# or STR")
		self.parser.add_option("--ts", dest="ts", type="str", 
			help="Search step of translational search, colon separate for different generations, \
			e.g. 4x1:2x2 means ts=1 for 4 generations and ts=2 for 2 generations (default 1)", metavar="# or STR")
		self.parser.add_option("--xr", dest="xr", type="str",
			help="x range of translational search, colon separate for different generations, \
			e.g. 4x1:2x2 means xr=1 for 4 generations and xr=2 for 2 generations (default 1)", metavar="# or STR")
		self.parser.add_option("--yr", dest="yr", type="str", 
			help="y range of translational search, colon separate for different generations, \
			e.g. 4x1:2x2 means yr=1 for 4 generations and yr=2 for 2 generations (default 1)", metavar="# or STR")
		self.parser.add_option("--maxit", dest="maxit", type="str",
			help="number of iterations for reference-free alignment, colon separate for different generations, \
			e.g. 4x30:2x20 means maxit=30 for 4 generations and maxit=20 for 2 generations (default 30)", metavar="# or STR")
		self.parser.add_option("--FL", dest="FL", type="str",
			help="lowest stopband frequency used in the tangent filter, colon separate for different generations, \
			e.g. 4x0.1:2x0.08 means FL=0.1 for 4 generations and FL=0.08 for 2 generations (default 0.1)", metavar="# or STR")
		self.parser.add_option("--FH", dest="FH", type="str", 
			help="highest stopband frequency used in the tangent filter, colon separate for different generations, \
			e.g. 4x0.3:2x0.4 means FH=0.3 for 4 generations and FH=0.4 for 2 generations (default 0.3)", metavar="# or STR")
		self.parser.add_option("--FF", dest="FF", type="str", 
			help="falloff of the tangent filter, colon separate for different generations, \
			e.g. 4x0.2:2x0.3 means FF=0.2 for 4 generations and FF=0.3 for 2 generations (default 0.2)", metavar="# or STR")
		self.parser.add_option("--init_iter", dest="init_iter", type="str",
			help="number of runs of ab-initio within-cluster alignment for stability evaluation in SAC initialization, \
			colon separate for different generations, e.g. 4x3:2x2 means init_iter=3 for 4 generations and init_iter=2 \
			for 2 generations (default 3)", metavar="# or STR")
		self.parser.add_option("--main_iter", dest="main_iter", type="str",
			help="number of runs of ab-initio within-cluster alignment for stability evaluation in SAC, \
			colon separate for different generations, e.g. 4x3:2x2 means main_iter=3 for 4 generations and main_iter=2 \
			for 2 generations (default 3)", metavar="# or STR")
		self.parser.add_option("--iter_reali", dest="iter_reali", type="str",
			help="every iter_reali iterations of SAC stability checking is performed, colon separate for different generations, \
			e.g. 4x1:2x2 means iter_reali=1 for 4 generations and iter_reali=2 for 2 generations (default 1)", metavar="# or STR")
		self.parser.add_option("--match_first", dest="match_first", type="str",
			help="number of iterations to run 2-way matching in the first phase, colon separate for different generations, \
			e.g. 4x2:2x1 means match_first=2 for 4 generations and match_first=1 for 2 generations (default 1)", metavar="# or STR")
		self.parser.add_option("--max_round", dest="max_round", type="str",
			help="maximum rounds of generating candidate class averages in the first phase, colon separate for \
			different generations, e.g. 4x20:2x10 means max_round=20 for 4 generations and max_round=10 for 2 \
			generations (default 20)", metavar="# or STR")
		self.parser.add_option("--match_second", dest="match_second", type="str",
			help="number of iterations to run 2-way (or 3-way) matching in the second phase, colon separate for different \
			generations, e.g. 4x5:2x3 means match_second=5 for 4 generations and match_second=3 for 2 generations \
			(default 5)", metavar="# or STR")
		self.parser.add_option("--stab_ali", dest="stab_ali", type="str",
			help="number of alignments when checking stability, colon separate for different generations, \
			e.g. 4x5:2x3 means stab_ali=5 for 4 generations and stab_ali=3 for 2 generations (default 5)", metavar="# or STR")
		self.parser.add_option("--thld_err", dest="thld_err", type="str", 
			help="the threshold of pixel error when checking stability, equals root mean square of distances \
			between corresponding pixels from set of found transformations and theirs average transformation, \
			depends linearly on square of radius (parameter ou), colon separate for different generations, \
			e.g. 4x1:2x3 means thld_err=1 for 4 generations and thld_err=3 for 2 generations (default 0.7)", metavar="# or STR")
		self.parser.add_option("--indep_run", dest="indep_run", type="str",
			help="specifies the level of m-way matching for reproducibility tests. The default = 4 will perform \
			full ISAC to 4-way matching. Value indep_run=2 will restrict ISAC to 2-way matching and 3 to 3-way \
			matching. Note the number of used MPI processes requested in mpirun must be a multiplicity of indep_run, \
			colon separate for different generations, e.g. 4x4:2x2 means indep_run=4 for 4 generations and indep_run=2 \
			for 2 generations (default 4)", metavar="# or STR")
		self.parser.add_option("--thld_grp", dest="thld_grp", type="str", 
			help="the threshold of the size of reproducible class (essentially minimum size of class), \
			colon separate for different generations, e.g. 4x10:2x5 means thld_grp=10 for 4 generations and thld_grp=5 for 2 \
			generations (default 10)", metavar="# or STR")
		self.parser.add_option("--img_per_grp", dest="img_per_grp", type="str",
			help="number of images per class in the ideal case (essentially maximum size of class), \
			colon separate for different generations, e.g. 4x100:2x50 means thld_grp=100 for 4 generations and thld_grp=50 for 2 \
			generations (default 100)", metavar="# or STR")
		'''

		# Refinement Iteration parameters
		self.setIterationParamList()
		for param in self.iterparams:
			example = ''
			if 'default' in param.keys() and param['default']:
				example = ", e.g. --%s=%s" % (param['name'],param['default'])
			else:
				example = ", e.g. --%s=<value>" % (param['name'])
				param['default'] = None
			if 'action' in param.keys() and param['action']:
				self.parser.add_option('--%s' % param['name'], dest="%s" % param['name'], default=param['default'], action="%s" % param['action'] ,
				help="iteration parameter: %s%s" % (param['help'],example))
			else:
				self.parser.add_option('--%s' % param['name'], dest="%s" % param['name'], default=param['default'],
				type="str", help="iteration parameter: %s%s" % (param['help'],example), metavar=param['metavar'])

		print "*****", self.listparams, "******"

#		'''
	#=====================
	def setIterationParamList(self):
#		super(ISACJob,self).setIterationParamList()		
		self.iterparams = ([		
			{'name':"ir", 
				'help':"Inner radius of the resampling to polar coordinate, colon separate for different generations, \
				e.g. 4x1:2x5 means ir=0 for 4 generations and ir=5 for 2 generations (default 1)", 'metavar':"# or STR"},
			{'name':"ou", 
				'help':"Outer radius of the resampling to polar coordinate, colon separate for different generations, \
				e.g. 4x24:2x20 means ou=24 for 4 generations and ou=20 for 2 generations (default box/2-2", 'metavar':"# or STR"},
			{'name':"rs", 
				'help':"Ring step of the resampling to polar coordinate, colon separate for different generations, \
				e.g. 4x1:2x2 means rs=1 for 4 generations and rs=2 for 2 generations (default 1)", 'metavar':"# or STR"},
			{'name':"ts", 
				'help':"Search step of translational search, colon separate for different generations, \
				e.g. 4x1:2x2 means ts=1 for 4 generations and ts=2 for 2 generations (default 1)", 'metavar':"# or STR"},
			{'name':"xr", 
				'help':"x range of translational search, colon separate for different generations, \
				e.g. 4x1:2x2 means xr=1 for 4 generations and xr=2 for 2 generations (default 1)", 'metavar':"# or STR"},
			{'name':"yr", 
				'help':"y range of translational search, colon separate for different generations, \
				e.g. 4x1:2x2 means yr=1 for 4 generations and yr=2 for 2 generations (default 1)", 'metavar':"# or STR"},
			{'name':"maxit", 
				'help':"number of iterations for reference-free alignment, colon separate for different generations, \
				e.g. 4x30:2x20 means maxit=30 for 4 generations and maxit=20 for 2 generations (default 30)", 'metavar':"# or STR"},
			{'name':"FL", 
				'help':"lowest stopband frequency used in the tangent filter, colon separate for different generations, \
				e.g. 4x0.1:2x0.08 means FL=0.1 for 4 generations and FL=0.08 for 2 generations (default 0.1)", 'metavar':"# or STR"},
			{'name':"FH", 
				'help':"highest stopband frequency used in the tangent filter, colon separate for different generations, \
				e.g. 4x0.3:2x0.4 means FH=0.3 for 4 generations and FH=0.4 for 2 generations (default 0.3)", 'metavar':"# or STR"},
			{'name':"FF", 
				'help':"falloff of the tangent filter, colon separate for different generations, \
				e.g. 4x0.2:2x0.3 means FF=0.2 for 4 generations and FF=0.3 for 2 generations (default 0.2)", 'metavar':"# or STR"},
			{'name':"init_iter", 
				'help':"number of runs of ab-initio within-cluster alignment for stability evaluation in SAC initialization, \
				colon separate for different generations, e.g. 4x3:2x2 means init_iter=3 for 4 generations and init_iter=2 \
				for 2 generations (default 3)", 'metavar':"# or STR"},
			{'name':"main_iter", 
				'help':"number of runs of ab-initio within-cluster alignment for stability evaluation in SAC, \
				colon separate for different generations, e.g. 4x3:2x2 means main_iter=3 for 4 generations and main_iter=2 \
				for 2 generations (default 3)", 'metavar':"# or STR"},
			{'name':"iter_reali", 
				'help':"every iter_reali iterations of SAC stability checking is performed, colon separate for different generations, \
				e.g. 4x1:2x2 means iter_reali=1 for 4 generations and iter_reali=2 for 2 generations (default 1)", 'metavar':"# or STR"},
			{'name':"match_first", 
				'help':"number of iterations to run 2-way matching in the first phase, colon separate for different generations, \
				e.g. 4x2:2x1 means match_first=2 for 4 generations and match_first=1 for 2 generations (default 1)", 'metavar':"# or STR"},
			{'name':"max_round", 
				'help':"maximum rounds of generating candidate class averages in the first phase, colon separate for \
				different generations, e.g. 4x20:2x10 means max_round=20 for 4 generations and max_round=10 for 2 \
				generations (default 20)", 'metavar':"# or STR"},
			{'name':"match_second", 
				'help':"number of iterations to run 2-way (or 3-way) matching in the second phase, colon separate for different \
				generations, e.g. 4x5:2x3 means match_second=5 for 4 generations and match_second=3 for 2 generations \
				(default 5)", 'metavar':"# or STR"},
			{'name':"stab_ali", 
				'help':"number of alignments when checking stability, colon separate for different generations, \
				e.g. 4x5:2x3 means stab_ali=5 for 4 generations and stab_ali=3 for 2 generations (default 5)", 'metavar':"# or STR"},
			{'name':"thld_err", 
				'help':"the threshold of pixel error when checking stability, equals root mean square of distances \
				between corresponding pixels from set of found transformations and theirs average transformation, \
				depends linearly on square of radius (parameter ou), colon separate for different generations, \
				e.g. 4x1:2x3 means thld_err=1 for 4 generations and thld_err=3 for 2 generations (default 0.7)", 'metavar':"# or STR"},
			{'name':"indep_run", 
				'help':"specifies the level of m-way matching for reproducibility tests. The default = 4 will perform \
				full ISAC to 4-way matching. Value indep_run=2 will restrict ISAC to 2-way matching and 3 to 3-way \
				matching. Note the number of used MPI processes requested in mpirun must be a multiplicity of indep_run, \
				colon separate for different generations, e.g. 4x4:2x2 means indep_run=4 for 4 generations and indep_run=2 \
				for 2 generations (default 4)", 'metavar':"# or STR"},
			{'name':"thld_grp", 
				'help':"the threshold of the size of reproducible class (essentially minimum size of class), \
				colon separate for different generations, e.g. 4x10:2x5 means thld_grp=10 for 4 generations and thld_grp=5 for 2 \
				generations (default 10)", 'metavar':"# or STR"},
			{'name':"img_per_grp", 
				'help':"number of images per class in the ideal case (essentially maximum size of class), \
				colon separate for different generations, e.g. 4x100:2x50 means thld_grp=100 for 4 generations \
				 and thld_grp=50 for 2 generations (default 100)", 'metavar':"# or STR"}
			])

	#=====================
	def checkConflicts(self):

		### setup correct database after we have read the project id
		if 'projectid' in self.params and self.params['projectid'] is not None:
			apDisplay.printMsg("Using split database")
			# use a project database
			newdbname = apProject.getAppionDBFromProjectId(self.params['projectid'])
			sinedon.setConfig('appiondata', db=newdbname)
			apDisplay.printColor("Connected to database: '"+newdbname+"'", "green")
		
		### get stack data
		self.stack = {}
		if self.params['stackid'] is not None:
			self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
			self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
			self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
			self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])
		else:
			self.stack['data'] = appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])
			self.stack['apix'] = self.stack['pixelsize']
			self.stack['boxsize'] = self.stack['boxsize']
			self.stack['file'] = self.stack['imagicfile']

		### check conflicts
		if self.params['stackid'] is None and self.params['alignstackid'] is None:
			apDisplay.printError("stack id OR alignstack id was not defined")
		if self.params['stackid'] is not None and self.params['alignstackid'] is not None:
			apDisplay.printError("either specify stack id OR alignstack id, not both")
		if self.params['generations'] is None:
			apDisplay.printError("number of generations was not provided")
		maxparticles = 500000
		if self.params['numpart'] > maxparticles:
			apDisplay.printError("too many particles requested, max: "
				+ str(maxparticles) + " requested: " + str(self.params['numpart']))
		if self.params['numpart'] > apFile.numImagesInStack(self.stack['file']):
			apDisplay.printError("trying to use more particles "+str(self.params['numpart'])
				+" than available "+str(apFile.numImagesInStack(self.stack['file'])))
		if self.params['numpart'] is None:
			self.params['numpart'] = apFile.numImagesInStack(self.stack['file'])

		boxsize = apStack.getStackBoxsize(self.params['stackid'])
		if self.params['ou'] is None:
			self.params['ou'] = (boxsize / 2.0) - 2
		self.clipsize = int(math.floor(boxsize/float(self.params['bin']*2)))*2
		if self.params['clipsize'] is not None:
			if self.params['clipsize'] > self.clipsize:
				apDisplay.printError("requested clipsize is too big %d > %d"
					%(self.params['clipsize'],self.clipsize))
			self.clipsize = self.params['clipsize']
		self.mpirun = self.checkMPI()
		if self.mpirun is None:
			apDisplay.printError("There is no MPI installed")
#		if self.params['nproc'] is None:
#			self.params['nproc'] = apParam.getNumProcessors()
#		if self.params['nproc'] < 2:
#			apDisplay.printError("Only the MPI version of ISAC is currently supported, must run with > 1 CPU")


	#=====================
	#=====================		RUNNING ISAC JOB
	#=====================

	#=====================
	'''
	def readyUploadFlag(self):
		if self.params['commit'] is False:
			return
		config = sinedon.getConfig('appiondata')
		dbc = MySQLdb.Connect(**config)
		cursor = dbc.cursor()
		query = (
			"  UPDATE ApISACRunData "
			+" SET `finished` = '1' "
			+" WHERE `DEF_id` = '"+str(self.params['isacjobid'])+"'"
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
		return mpiexe
#		sparxexe = apParam.getExecPath("sxisac.py")
#		if sparxexe is None:
#			return None
#		lddcmd = "ldd "+sparxexe+" | grep mpi"
#		proc = subprocess.Popen(lddcmd, shell=True, stdout=subprocess.PIPE)
#		proc.wait()
#		lines = proc.stdout.readlines()
#		print "lines=", lines
#		if lines and len(lines) > 0:
#			return mpiexe

	#=====================
	def writeSparxLog(self, text):
		f = open("isac.log", "a")
		f.write(apParam.getLogHeader())
		f.write(text+"\n")
		f.close()
	
	#=====================
#	def clearIntermediateFiles(self):
#		for i in range(self.params['generations']):
#			os.system("rm -rf start%d.hdf" % i)

	#=====================
	def start(self):
		self.addToLog('.... Setting up new ISAC job ....')
		self.addToLog('.... Making command for stack pre-processing ....')
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])

		### send file to remotehost
		tasks = {}
		sfhed = self.stack['file'][:-4]+".hed"
		sfimg = self.stack['file'][:-4]+".img"
		tasks = self.addToTasks(tasks,"rsync -e 'ssh -o StrictHostKeyChecking=no' -rotouv --partial %s %s:%s/%s" % (sfhed,self.params['localhost'],self.params['remoterundir'],"start1.hed"))
		tasks = self.addToTasks(tasks,"rsync -e 'ssh -o StrictHostKeyChecking=no' -rotouv --partial %s %s:%s/%s" % (sfimg,self.params['localhost'],self.params['remoterundir'],"start1.img"))

		### write Sparx jobfile: process stack to local file
		if self.params['timestamp'] is None:
			apDisplay.printMsg("creating timestamp")
			self.params['timestamp'] = self.timestamp
		self.params['localstack'] = os.path.join(self.params['rundir'], self.params['timestamp']+".hed")
		if os.path.isfile(self.params['localstack']):
			apFile.removeStack(self.params['localstack'])
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
#		apParam.runCmd(proccmd, "EMAN", verbose=True)
		self.addSimpleCommand('cd %s' % self.params['rundir'])
		self.addSimpleCommand(proccmd)
		sparxcmd = "sxcpy.py %s %s_1.hdf" % (self.params['localstack'], self.params['localstack'][:-4])
#		apParam.runCmd(sparxcmd, "SPARX", verbose=True)
		self.addSimpleCommand(sparxcmd)
		self.addSimpleCommand("")

		### write Sparx jobfile: run ISAC
		for i in range(self.params['generations']):
			sparxopts = " %s_%d.hdf" % (os.path.join(self.params['localstack'][:-4]), (i+1))
			if self.params['ir'] is not None:
				sparxopts += " --ir %d" % int(float(apRecon.getComponentFromVector(self.params['ir'], i, splitter=":")))
			if self.params['ou'] is not None:
				sparxopts += " --ou %d" % int(float(apRecon.getComponentFromVector(self.params['ou'], i, splitter=":")))
			if self.params['rs'] is not None:
				sparxopts += " --rs %d" % int(float(apRecon.getComponentFromVector(self.params['rs'], i, splitter=":")))
			if self.params['ts'] is not None:
				sparxopts += " --ts %.1f" % int(float(apRecon.getComponentFromVector(self.params['ts'], i, splitter=":")))
			if self.params['xr'] is not None:
				sparxopts += " --xr %.1f" % int(float(apRecon.getComponentFromVector(self.params['xr'], i, splitter=":")))
			if self.params['yr'] is not None:
				sparxopts += " --yr %.1f" % int(float(apRecon.getComponentFromVector(self.params['yr'], i, splitter=":")))
			if self.params['maxit'] is not None:
				sparxopts += " --maxit %d" % int(float(apRecon.getComponentFromVector(self.params['maxit'], i, splitter=":")))
			if self.params['FL'] is not None:
				sparxopts += " --FL %.2f" % int(float(apRecon.getComponentFromVector(self.params['FL'], i, splitter=":")))
			if self.params['FH'] is not None:
				sparxopts += " --FH %.2f" % int(float(apRecon.getComponentFromVector(self.params['FH'], i, splitter=":")))
			if self.params['FF'] is not None:
				sparxopts += " --FF %.2f" % int(float(apRecon.getComponentFromVector(self.params['FF'], i, splitter=":")))
			if self.params['init_iter'] is not None:
				sparxopts += " --init_iter %d" % int(float(apRecon.getComponentFromVector(self.params['init_iter'], i, splitter=":")))
			if self.params['main_iter'] is not None:
				sparxopts += " --main_iter %d" % int(float(apRecon.getComponentFromVector(self.params['main_iter'], i, splitter=":")))
			if self.params['iter_reali'] is not None:
				sparxopts += " --iter_reali %d" % int(float(apRecon.getComponentFromVector(self.params['iter_reali'], i, splitter=":")))
			if self.params['match_first'] is not None:
				sparxopts += " --match_first %d" % int(float(apRecon.getComponentFromVector(self.params['match_first'], i, splitter=":")))
			if self.params['max_round'] is not None:
				sparxopts += " --max_round %d" % int(float(apRecon.getComponentFromVector(self.params['max_round'], i, splitter=":")))
			if self.params['match_second'] is not None:
				sparxopts += " --match_second %d" % int(float(apRecon.getComponentFromVector(self.params['match_second'], i, splitter=":")))
			if self.params['stab_ali'] is not None:
				sparxopts += " --stab_ali %d" % int(float(apRecon.getComponentFromVector(self.params['stab_ali'], i, splitter=":")))
			if self.params['thld_err'] is not None:
				sparxopts += " --thld_err %.2f" % int(float(apRecon.getComponentFromVector(self.params['thld_err'], i, splitter=":")))
			if self.params['indep_run'] is not None:
				sparxopts += " --indep_run %d" % int(float(apRecon.getComponentFromVector(self.params['indep_run'], i, splitter=":")))
			if self.params['thld_grp'] is not None:
				sparxopts += " --thld_grp %d" % int(float(apRecon.getComponentFromVector(self.params['thld_grp'], i, splitter=":")))
			if self.params['img_per_grp'] is not None:
				sparxopts += " --img_per_grp %d" % int(apRecon.getComponentFromVector(self.params['img_per_grp'], i))
			sparxopts += " --generation %d" % (i+1)
			
			sparxexe = apParam.getExecPath("sxisac.py", die=True)
			mpiruncmd = self.mpirun+" -np "+str(self.params['nproc'])+" "+sparxexe+" "+sparxopts
			bn = os.path.basename(self.params['localstack'])[:-4]
			e2cmd = "e2proc2d.py %s_%d.hdf %s_%d.hdf --list=\"generation_%d_unaccounted.txt\"" % \
				(bn, i+1, bn, i+2, i+1)
			self.addSimpleCommand(mpiruncmd)
			self.addSimpleCommand(e2cmd)

#		print self.tasks
#		print self.command_list
#		self.writeCommandListToFile()
		apParam.dumpParameters(self.params, "isac-"+self.params['timestamp']+"-params.pickle")
					
#=====================
if __name__ == "__main__":
	isac = ISACJob()
#	isac.start()
#	isac.close()
