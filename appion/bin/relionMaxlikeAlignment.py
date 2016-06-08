#!/usr/bin/env python
#
import os
import time
import glob
import math
import cPickle
import subprocess
from pyami import mrc
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apFile
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


	execFile = 'relion_refine_mpi'
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

		self.parser.add_option("--partDiam", dest="partdiam", type="int",
			help="Particle diameter in Angstroms", metavar="#")
		self.parser.add_option("--maxIter", "--max-iter", dest="maxiter", type="int", default=30,
			help="Maximum number of iterations", metavar="#")
		self.parser.add_option("--numRef", "--num-ref", dest="numrefs", type="int",
			help="Number of classes to create", metavar="#")
		self.parser.add_option("--angStep", "--angle-step", dest="psistep", type="int", default=5,
			help="In-plane rotation sampling step (degrees)", metavar="#")
		self.parser.add_option("--tau", dest="tau", type="float", default=1,
			help="Tau2 Fudge Factor (> 1)", metavar="#")
		self.parser.add_option("--correctnorm",dest="correctnorm",default=False,
			action="store_true", help="Perform normalisation error correction")

		self.parser.add_option("--invert", dest='invert', default=False,
			action="store_true", help="Invert before alignment")
		self.parser.add_option("--flat", "--flatten-solvent", dest='flattensolvent', default=False,
			action="store_true", help="Flatten Solvent in References")
		self.parser.add_option("--zero_mask", "--zero_mask", dest="zero_mask", default=False,
			action="store_true", help="Mask surrounding background in particles to zero (by default the solvent area is filled with random noise)", metavar="#")

		self.parser.add_option("--nompi", dest='usempi', default=True,
			action="store_false", help="Disable MPI and run on single host")
		# Job parameters that the remotehost need
		self.parser.add_option("--nodes", dest="nodes", type="int", default=1,
			help="Number of nodes requested for multi-node capable tasks", metavar="#")
		self.parser.add_option("--ppn", dest="ppn", type="int", default=1,
			help="Minimum Processors per node", metavar="#")
		self.parser.add_option("--mem", dest="mem", type="int", default=4,
			help="Maximum memory per node (in GB)", metavar="#")
		self.parser.add_option("--mpinodes", dest="mpinodes", type=int, default=2,
			help="Number of nodes used for the entire job.", metavar="#")
		self.parser.add_option("--mpiprocs", dest="mpiprocs", type=int, default=4,
			help="Number of processors allocated for a subjob. For memory intensive jobs, decrease this value.", metavar="#")
		self.parser.add_option("--mpithreads", dest="mpithreads", type=int, default=1,
			help="Number of threads to generate per processor. For memory intensive jobs, increase this value.", metavar="#")
		self.parser.add_option("--mpimem", dest="mpimem", type=int, default=4,
			help="Amount of memory (Gb) to allocate per thread. Increase this value for memory intensive jobs. ", metavar="#")
		self.parser.add_option("--walltime", dest="walltime", type="int", default=24,
			help="Maximum walltime in hours", metavar="#")
		self.parser.add_option('--cput', dest='cput', type='int', default=None)


	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		self.projectid = apProject.getProjectIdFromStackId(self.params['stackid'])
		if self.params['description'] is None:
			apDisplay.printError("run description was not defined")
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

		if self.params['usempi'] is True:
			self.mpirun = self.checkMPI()
			if self.mpirun is None:
				apDisplay.printError("There is no MPI installed")
			if self.params['nproc'] is None:
				self.params['nproc'] = self.params['mpinodes']*self.params['mpiprocs']

	#=====================
	def setRunDir(self):
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])

	#=====================
	def checkMPI(self):
		mpiexe = apParam.getExecPath("mpirun", die=True)
		if mpiexe is None:
			return None
		relionexe = apParam.getExecPath(self.execFile, die=True)
		if relionexe is None:
			return None
		lddcmd = "ldd "+relionexe+" | grep mpi"
		proc = subprocess.Popen(lddcmd, shell=True, stdout=subprocess.PIPE)
		proc.wait()
		lines = proc.stdout.readlines()
		print "lines=", lines
		if lines and len(lines) > 0:
			return mpiexe

	#=====================
	def dumpParameters(self):
		self.params['runtime'] = time.time() - self.t0
		self.params['timestamp'] = self.timestamp
		paramfile = "maxlike-"+self.timestamp+"-params.pickle"
		pf = open(paramfile, "w")
		newdict = self.params.copy()
		newdict.update(self.stack)
		cPickle.dump(newdict, pf)
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
		maxjobq['REF|projectdata|projects|project'] = self.projectid
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
	def runUploadScript(self):
		if self.params['commit'] is False:
			return
		uploadcmd = "uploadRelion2DMaxlikeAlign.py "
		uploadcmd += " -p %d "%(self.projectid)
		uploadcmd += " -j %s "%(self.params['maxlikejobid'])
		uploadcmd += " -R %s "%(self.params['rundir'])
		uploadcmd += " -n %s "%(self.params['runname'])
		print uploadcmd
		proc = subprocess.Popen(uploadcmd, shell=True)
		proc.communicate()

	#=====================
	def estimateIterTime(self, nprocs):
		##FIXME
		return 1
		secperiter = 0.12037
		### get num processors
		print '1. numprocs is = '+str(nproc)
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
	def estimateMemPerProc(self):
		classes = self.params['numrefs']
		boxsize = self.stack['boxsize']/self.params['bin']
		# bin 2 / 96 clip; angstep 5 ; numref 7 ; numpart 538 --> 0.108 Gb
		# bin 2 / 96 clip; angstep 5 ; numref 3 ; numpart 538 --> 0.104 Gb
		# bin 4 / 48 clip; angstep 5 ; numref 7 ; numpart 538 --> 0.107 Gb
		# bin 1 / 192 clip; angstep 15 ; numref 2 ; numpart 538 --> 0.104 Gb
		# bin 1 / 160 clip; angstep 15 ; numref 2 ; numpart 538 --> 0.104 Gb
		# bin 1 / 160 clip; angstep 15 ; numref 2 ; numpart 300 --> 0.103 Gb

	#=====================
	def writeRelionLog(self, text):
		f = open("relion.log", "a")
		f.write(apParam.getLogHeader())
		f.write(text+"\n\n")
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
		self.params['apix'] = self.stack['apix']
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])
		if self.params['virtualdata'] is not None:
			self.stack['file'] = self.params['virtualdata']['filename']
		else:
			self.stack['file'] = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])

		#self.estimateIterTime(nprocs)
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
			a.setValue('inverted',True) is True

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
			+" --particle_diameter %.1f "%(self.params['partdiam'])
			+" --dont_check_norm "
		)

		if self.params['flattensolvent'] is True:
			relionopts += " --flatten_solvent "
		if self.params['correctnorm'] is True:
			relionopts += " --norm "

		if self.params['usempi'] is True:
			relionexe = apParam.getExecPath("relion_refine_mpi", die=True)
			relionopts += " --j %d "%(self.params['mpithreads'])
			relionopts += " --memory_per_thread %d "%(self.params['mpimem'])
			print 'mpinodes is equal to '+str(self.params['mpinodes'])
			### find number of processors
			nproc = self.params['mpiprocs'] * self.params['mpinodes']
			print 'mpiprocs = '+str(self.params['mpiprocs'])
			print 'mpinodes = '+str(self.params['mpinodes'])
			apDisplay.printColor("Using "+str(nproc)+" processors!", "green")
			runcmd = self.mpirun+" -np "+str(nproc)+" "+relionexe+" "+relionopts
		else:
			relionexe = apParam.getExecPath("relion_refine", die=True)
			runcmd = relionexe+" "+relionopts
		#self.estimateIterTime(nprocs)

		self.writeRelionLog(runcmd)

		apParam.runCmd(runcmd, package="RELION", verbose=True, showcmd=True)
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		### minor post-processing
		self.createReferenceStack()
		self.dumpParameters()
		self.runUploadScript()

#=====================
if __name__ == "__main__":
	maxLike = RelionMaxLikeScript()
	maxLike.start()
	maxLike.close()



