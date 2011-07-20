import sys
import time
import subprocess
import math
import os

from appionlib import basicScript
from appionlib import apParam
from appionlib import apDisplay

class RefineJob(basicScript.BasicScript):
	'''
	Refine Job is run on a remotehost, normally a big cluster that does
	not have access to local disk.  By the time this script is run, the
  require data files should already reside on the remotehost in remoterundir.
	If remotehost has the same access to local disk as localhost, then
	remoterundir is identical to standard appion rundir.
	At the last part of the job, the results are pushed to localhost using
	rsync if remoterundir is not the same as rundir.
	'''
	def __init__(self,optlist=[]):
		super(RefineJob,self).__init__(optlist)
		self.tasks = {}
		self.setAttributes()
		self.start()

	#=====================
	def setupParserOptions(self):
		# Agent class uses this to choose the RefineJob subclass
		self.parser.add_option("--jobtype", dest="jobtype",
			help="Job Type of processing run, e.g., emanrecon", metavar="X")
		# Parameters that the agent need
		self.parser.add_option("--jobid", dest="jobid", type="int", default=1,
			help="ApAppionJobId for updating job status", metavar="#")
		# Job parameters that the remotehost need
		self.parser.add_option("--rpn", dest="rpn", type="int", default=4,
			help="Number of processors used per node", metavar="#")
		self.parser.add_option("--nodes", dest="nodes", type="int", default=1,
			help="Number of nodes requested for multi-node capable tasks", metavar="#")
		self.parser.add_option("--ppn", dest="ppn", type="int", default=4,
			help="Minimum Processors per node", metavar="#")
		self.parser.add_option("--mem", dest="mem", type="int", default=4,
			help="Maximum memory per node", metavar="#")
		self.parser.add_option("--walltime", dest="walltime", type="int", default=24,
			help="Maximum walltime in hours", metavar="#")
		self.parser.add_option('--cput', dest='cput', type='int', default=None)
		# Parameters used to bring results back from the remotehost
		self.parser.add_option("--localhost", dest="localhost", type="str", default='',
			help="Name of a localhost that the remotehost user can do rsync to transfer the result files", metavar="text")
		self.parser.add_option("--rundir", dest="rundir", default='./',
			help="Path for the local run directory that is accessable by localhost and general data files e.g. --rundir=/data/appion/sessionname/recon/runname", metavar="PATH")
		self.parser.add_option("--remoterundir", dest="remoterundir", default='./',
			help="Path for the remote run directory accessable by remotehost and will not be erased at the beginning of the run, e.g. --recondir=/home/you/sessionname/rundir/", metavar="PATH")
		self.parser.add_option('--runname', dest='runname')
		self.parser.add_option("--expId", dest="expid", type="int",
			help="Experiment session id standard from web form.  Not used here", metavar="#")
		self.parser.add_option("-p", "--projectid", dest="projectid", type="int",
			help="Project id associated with processing run, e.g. --projectid=159", metavar="#")

		# ReconJob parameters
		self.parser.add_option("--description", dest="description", type="str", default='',
			help="Description of the run", metavar="text")
		self.parser.add_option("--appionwrap", dest="appionwrapper", default='',
			help="Path for Appion bin directory if needed e.g. --appionwrap=/home/you/appion/bin", metavar="PATH")
		self.parser.add_option("--recondir", dest="recondir", default='recon',
			help="Path of the Scratch directory for processing that will be erased if start from iteration 1, e.g. --recondir=/home/you/sessionname/rundir/recon", metavar="PATH")
		self.parser.add_option("-s", "--stackname", dest="stackname",
			help="Particle stack path", metavar="FILENAME")
		self.parser.add_option("--modelnames", dest="modelnames",
			help="Initial Model volume path", metavar="FILENAME")
		self.parser.add_option("-N", "--totalpart", dest="totalpart", type="int", default=None,
			help="Number of particles in the particle stack", metavar="#")
		self.parser.add_option("--boxsize", dest="boxsize", type="int", default=None,
			help="Boxsize in the particle stack", metavar="#")
		self.parser.add_option("--apix", dest="apix", type="float",
			help="Pixel size (Angstrom per pixel/voxel)", metavar="#")
		self.parser.add_option("--startiter", dest="startiter", type="int", default=1,
			help="Begin refine from this iteration", metavar="INT")
		self.parser.add_option("--enditer", dest="enditer", type="int",
			help="End refine at this iteration", metavar="INT")
		self.parser.add_option('--setuponly', dest='setuponly', default=False, action='store_true',
			help="setup without executing, for testing purpose")
			# Refinement Iteration parameters
		self.setIterationParamList()
		for param in self.iterparams:
			example = ''
			if 'default' in param.keys() and param['default']:
				example = ", e.g. --%s=%s" % (param['name'],param['default'])

			self.parser.add_option('--%s' % param['name'], dest="%s" % param['name'], default= param['default'],
				type="str", help="iteration parameter: %s%s" % (param['help'],example), metavar="#x##")
		
	#=====================
	def checkConflicts(self):
		if self.params['modelnames'] is None:
			apDisplay.printError("enter at least one 3D initial model volume file, e.g. --modelnames=initial.mrc")
		if self.params['stackname'] is None:
			apDisplay.printError("enter a particle stack file, e.g. --stackname=start.hed")
		if self.params['boxsize'] is None:
			apDisplay.printError("enter the stack boxsize, e.g. --boxsize=64")
		if self.params['stackname'] is None:
			apDisplay.printError("enter the pixel size, e.g. --apix=1.5")
		self.params['numiter'] = self.params['enditer'] - self.params['startiter'] + 1
		self.params['remotedir'] = os.path.abspath(self.params['remoterundir'])
		if self.params['recondir'][0] != '/':
			# assumes relative recondir is under the safe remotedir
			self.params['recondir'] = os.path.join(self.params['remoterundir'],self.params['recondir'])
		self.params['nproc'] = self.params['rpn'] * self.params['nodes']
		self.checkPackageConflicts()
		### convert iteration parameters first before its confict checking
		self.convertIterationParams()
		self.checkIterationConflicts()

	def checkPackageConflicts(self):
		pass

	def setIterationParamList(self):
		self.iterparams = [
				{'name':'symmetry','default':'','help':'symmetry name (i.e. c1 or C1)'},
				{'name':'angSampRate','default':'5.0','help':'angular increment (degrees)'},
				{'name':'outerMaskRadius','default':'0','help':'mask radius (pixels) autoset if 0'},
				{'name':'innerMaskRadius','default':'0','help':'mask radius (pixels) autoset if 0'},
				]

	def convertIterationParams(self):
		iterparam_names = map((lambda x: x['name']),self.iterparams)
		self.params = apParam.convertIterationParams(iterparam_names,self.params,self.params['numiter'])

	def checkIterationConflicts(self):
		''' 
		Conflict checking of per-iteration parameters
		'''
		for paraminfo in self.iterparams:
			key = paraminfo['name']
			if key in self.params:
				try:
					number = eval(paraminfo['default'])
				except:
					continue
				if type(number) == type(0):
					apDisplay.printWarning("%s is converted to next integer above if entered as float" % key)
					self.params[key] = map((lambda x: int(math.ceil(x))),self.params[key])
		#
		maxmask = int(math.floor((self.params['boxsize'])/2.0))-2
		for iter in range(self.params['numiter']):
			if 'symmetry' not in self.params.keys() or self.params['symmetry'][iter] == '':
				apDisplay.printError("Symmetry was not defined")

			if self.params['outerMaskRadius'][iter] == 0:
				apDisplay.printWarning("mask was not defined, setting to boxsize: %d"%(maxmask))
				self.params['outerMaskRadius'][iter] = maxmask
			if self.params['outerMaskRadius'][iter] > maxmask:
				apDisplay.printWarning("mask was too big, setting to boxsize: %d"%(maxmask))
				self.params['outerMaskRadius'][iter] = maxmask
			self.params['symmetry'][iter] = self.convertSymmetryNameForPackage(self.params['symmetry'][iter])

	def convertSymmetryNameForPackage(self,symm_name):
		return symm_name.replace(' (z)','')

	def setupMPIRun(self,iter,procscripts,nproc,iterpath):
		mpi_script = 'mpirun -np %d ' % (nproc)
		if len(procscripts) > 1:
			masterfile = os.path.join(iterpath,'mpi.iter%03d.run.sh' % (iter))
			self.makeMPIMasterScript(procscripts,masterfile)
			mpi_script += masterfile
		elif len(procscripts) == 1:
			mpi_script += procscripts[0]
		else:
			apDisplay.printError('no processes to make mpirun command line')
		return mpi_script

	def makeMPIMasterScript(self,shellscripts,masterfile):
		lines = map((lambda x:'-np 1 '+x),shellscripts)
		f = open(masterfile,'w')
		f.writelines(map((lambda x: x+'\n'),lines))
		f.close()
		os.chmod(masterfile, 0755)
	
	def makePreIterationScript(self):
		pretasks = {}
		pretasks = self.addToTasks(pretasks,'# setup directory')
		pretasks = self.addToTasks(pretasks,'/bin/rm -rf %s' % self.params['recondir'])
		pretasks = self.addToTasks(pretasks,'mkdir -p %s' % self.params['recondir'])
		pretasks = self.addToTasks(pretasks,'cd %s' % self.params['recondir'])
		pretasks = self.addToTasks(pretasks,'')
		# link the required files to scratch dir
		f = open(os.path.join(self.params['remoterundir'],'files_to_remote_host'))
		lines = f.readlines()
		pretasks = self.addToTasks(pretasks,'# link needed files into recondir')
		for line in lines:
			filename = os.path.basename(line.replace('\n',''))
			sourcepath = os.path.join(self.params['remoterundir'],filename)
			pretasks = self.addToTasks(pretasks,'ln -s  %s %s' % (sourcepath,filename))
			pretasks = self.addToTasks(pretasks,'test -s  %s || ( echo %s not found && exit )' % (sourcepath,filename))
		pretasks = self.addToTasks(pretasks,'/bin/rm -fv resolution.txt')
		pretasks = self.addToTasks(pretasks,'touch resolution.txt')
		self.addJobCommands(pretasks)

	def makePostIterationScript(self):
		pass

	def makeRefineScript(self,iter):
			print 'make refine script in RefineJob'
			'''
			Need to be implemented in the subclass
			'''
			return [[]]

	def setAttributes(self):
		self.ppn = self.params['ppn']
		self.nodes = self.params['nodes']
		self.walltime = self.params['walltime']
		self.mem = self.params['mem']
		self.nproc = self.params['nproc']
		self.setuponly = self.params['setuponly']
		self.jobtype = self.params['jobtype']
		self.jobid = self.params['jobid']
		self.command_list = []
		self.min_mem_list = []
		self.nproc_list = []
		self.remoterundir = self.params['remoterundir']
		self.runname = self.params['runname']
		self.cpuTime = self.params['cput']
		
	def addParallelsToTasks(self,tasks,scripts,mem=2,nproc=1):
		if len(tasks) == 0:
			for key in ('scripts','mem','nproc','file'):
				tasks[key] = []
		length = len(scripts)
		tasks['scripts'].append(scripts)
		tasks['mem'].append(map((lambda x:mem),range(length)))
		tasks['nproc'].append(map((lambda x:nproc),range(length)))
		return tasks

	def addToTasks(self,tasks,script,mem=2,nproc=1):
		if len(tasks) == 0:
			for key in ('scripts','mem','nproc','file'):
				tasks[key] = []
		tasks['scripts'].append([script])
		tasks['mem'].append([mem])
		tasks['nproc'].append([nproc])
		return tasks

	def addJobCommands(self,tasks):
		self.command_list.extend(map((lambda x:x[0]),tasks['scripts']))
		self.min_mem_list.extend(tasks['mem'])
		self.nproc_list.extend(tasks['nproc'])

	def start(self):
		if self.params['startiter'] == 1:
			self.makePreIterationScript()
		self.addJobCommands(self.addToTasks({},''))
		self.addJobCommands(self.addToTasks({},''))
		for iter in range(self.params['startiter'],self.params['enditer']+1):
			self.addJobCommands(self.makeRefineScript(iter))
		self.makePostIterationScript()

	def getWalltime(self):
		return self.wallTime
	def getName(self):
		return self.runname                   
	def getNodes(self):
		return self.nodes
	def getPPN(self):
		return self.ppn
	def getCpuTime(self):
		return self.cpuTime
	def getMem(self):
		return  self.mem
	def getPmem(self):
		return None
	def getQueue(self):
		return None
	def getAccount(self):
		return None
	def getOutputDir(self):   	
		return self.remoterundir
	def getCommandList(self):
		return self.command_list
	def getJobId(self):
		return self.jobid
	
class Tester(RefineJob):
	def makeRefineScript(self,iter):
			print 'make refine script in Tester'
			tasks = {
					'mem':[[2,2,2,2],[47,]],
					'scripts':[['echo "doing proc000"\n',
								'echo "doing proc001"\n',
								'echo "doing proc002"\n',
								'echo "doing proc003"\n',
								],
								['frealign.exe combine%d\n' % iter],],
					'nproc':[[1,1,1,1],[self.ppn]],
					}
			return tasks
       

if __name__ == '__main__':
	testscript = Tester()
