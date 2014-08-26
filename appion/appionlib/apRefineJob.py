import sys
import time
import subprocess
import math
import os
import glob

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
		self.listparams = []
		super(RefineJob,self).__init__(optlist)
		self.__gotoRemoteRunDir()
		self.setAttributes()
		self.launch_as_shell = False
		self.__initializeLog()
		self.start()
		self.close()

	#=====================
	def setupParserOptions(self):
		# Agent class uses this to choose the RefineJob subclass
		self.parser.add_option("--jobtype", dest="jobtype",
			help="Job Type of processing run, e.g., emanrecon", metavar="X")
		# Parameters that the agent need
		self.parser.add_option("--jobid", dest="jobid", type="int", default=0,
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
		self.parser.add_option("--queue", dest="queue", type="str", default='',
			help="Name of the queue on the processing host to submit this job to.", metavar="text")
		# Parameters used to bring results back from the remotehost
		self.parser.add_option("--localhost", dest="localhost", type="str", default='',
			help="Name of a localhost that the remotehost user can do rsync to transfer the result files", metavar="text")
		self.parser.add_option("--rundir", dest="rundir", default='./',
			help="Path for the local run directory that is accessable by localhost and general data files e.g. --rundir=/data/appion/sessionname/recon/runname", metavar="PATH")
		self.parser.add_option("--remoterundir", dest="remoterundir", default='./',
			help="Path for the remote run directory accessable by remotehost and will not be erased at the beginning of the run, e.g. --remoterundir=/home/you/sessionname/rundir/", metavar="PATH")
		# Standard Web Form Appion parameters
		self.parser.add_option('--runname', dest='runname')
		self.parser.add_option("--expid", dest="expid", type="int",
			help="Experiment session id standard from web form.  Not used here", metavar="#")
		self.parser.add_option("-p", "--projectid", dest="projectid", type="int",
			help="Project id associated with processing run. Used for updating run status in the database", metavar="#")

		# ReconJob parameters
		self.parser.add_option("--description", dest="description", type="str", default='',
			help="Description of the run", metavar="text")
		self.parser.add_option("--appionwrapper", dest="appionwrapper", default='',
			help="Path for Appion bin directory if needed e.g. --appionwrap=/home/you/appion/bin", metavar="PATH")
		self.parser.add_option("--recondir", dest="recondir", default='recon',
			help="Path of the Scratch directory for processing that will be erased if start from iteration 1, e.g. --recondir=/home/you/sessionname/rundir/recon", metavar="PATH")
		self.parser.add_option("-s", "--stackname", dest="stackname",
			help="Particle stack path", metavar="FILENAME")
		self.parser.add_option("--modelnames", dest="modelnames",
			help="Initial Model volume path", metavar="FILENAME")
		self.parser.add_option("--symmetry", dest="symmetry", default='',
			help='symmetry name (i.e. c1 or C1)', metavar="text")
		self.parser.add_option("-N", "--totalpart", dest="totalpart", type="int", default=None,
			help="Number of particles in the particle stack", metavar="#")
		self.parser.add_option("--boxsize", dest="boxsize", type="int", default=None,
			help="Boxsize in the particle stack", metavar="#")
		self.parser.add_option("--phaseflipped", dest="phaseflipped", default=False, action='store_true',
			help="Indicates that the stack data have been phase flipped")
		self.parser.add_option("--apix", dest="apix", type="float",
			help="Pixel size (Angstrom per pixel/voxel)", metavar="#")
		self.parser.add_option("--startIter", dest="startiter", type="int", default=1,
			help="Begin refine from this iteration", metavar="INT")
		self.parser.add_option("--endIter", dest="enditer", type="int",
			help="End refine at this iteration", metavar="INT")
		self.parser.add_option('--setuponly', dest='setuponly', default=False, action='store_true',
			help="setup without executing, for testing purpose")
		self.parser.add_option('--refineonly', dest='refineonly', default=False, action='store_true',
			help="always refine angles against the original initial model")
		self.parser.add_option("--cs", dest="cs", type="float", default=2.0,
			help="Spherical Aboration", metavar="#")
		self.parser.add_option("--kv", dest="kv", type="int", default=200,
			help="High Tension value of scope in Kv", metavar="INT")
		# set non-iteration list parameters that are separated by ','
		self.setListParams()
			# Refinement Iteration parameters
		self.setIterationParamList()
		for param in self.iterparams:
			example = ''
			if 'default' in param.keys() and param['default']:
				example = ", e.g. --%s=%s" % (param['name'],param['default'])

			if 'action' in param.keys() and param['action']:
				self.parser.add_option('--%s' % param['name'], dest="%s" % param['name'], default= param['default'], action="%s" % param['action'] ,
				help="iteration parameter: %s%s" % (param['help'],example))
			else:
				self.parser.add_option('--%s' % param['name'], dest="%s" % param['name'], default= param['default'],
				type="str", help="iteration parameter: %s%s" % (param['help'],example), metavar="#x##")
		
	#=====================
	def checkConflicts(self):
		if self.params['modelnames'] is None:
			apDisplay.printError("enter at least one 3D initial model volume file, e.g. --modelnames=initial.mrc")
		if self.params['stackname'] is None:
			apDisplay.printError("enter a particle stack file, e.g. --stackname=start.hed")
		if 'symmetry' not in self.params.keys() or self.params['symmetry'] == '':
			apDisplay.printError("Symmetry was not defined")
		self.params['symmetry'] = self.convertSymmetryNameForPackage(self.params['symmetry'])

		if self.params['boxsize'] is None:
			apDisplay.printError("enter the stack boxsize, e.g. --boxsize=64")
		if self.params['stackname'] is None:
			apDisplay.printError("enter the pixel size, e.g. --apix=1.5")
		self.params['numiter'] = self.params['enditer'] - self.params['startiter'] + 1
		self.params['remoterundir'] = os.path.abspath( os.path.expanduser(self.params['remoterundir']) )
		if self.params['recondir'][0] != '/':
			# assumes relative recondir is under the safe remoterundir
			self.params['recondir'] = os.path.join(self.params['remoterundir'],self.params['recondir'])
		self.params['recondir'] = os.path.abspath(self.params['recondir'])
		if self.params['rundir'] != self.params['remoterundir'] and not self.params['localhost']:
			apDisplay.printError('local host not defined for result transfer')
		self.params['nproc'] = self.params['rpn'] * self.params['nodes']
		self.checkPackageConflicts()
		self.__convertListParams()
		### convert iteration parameters first before its confict checking
		self.__convertIterationParams()
		self.checkIterationConflicts()

	def setListParams(self):
		self.listparams.append('modelnames')

	def __convertListParams(self):
		for paramkey in self.listparams:
			if paramkey in self.params.keys():
				self.params[paramkey] = self.params[paramkey].split(',')

	def checkPackageConflicts(self):
		pass

	def setIterationParamList(self):
		self.iterparams = [
				{'name':'angSampRate','default':'5.0','help':'angular increment (degrees)'},
				{'name':'outerMaskRadius','default':'0','help':'mask radius (angstroms) autoset if 0'},
				{'name':'innerMaskRadius','default':'0','help':'mask radius (angstroms) autoset if 0'},
				]

	def __convertIterationParams(self):
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
		# mask size in pixels has to be 2 pixels less than half the box size
		maxmaskPixels = int(math.floor(self.params['boxsize']/2.0)) - 2
		# convert to angstroms to find the max outer mask radius
		maxmaskAngstrom = maxmaskPixels * self.params['apix']
		for iter in range(self.params['numiter']):
			if self.params['outerMaskRadius'][iter] == 0:
				apDisplay.printWarning("mask was not defined, setting to boxsize: %.1f"%(maxmaskAngstrom))
				self.params['outerMaskRadius'][iter] = maxmaskAngstrom
			if self.params['outerMaskRadius'][iter] > maxmaskAngstrom:
				apDisplay.printWarning("mask was too big, setting to boxsize: %.1f"%(maxmaskAngstrom))
				self.params['outerMaskRadius'][iter] = maxmaskAngstrom

	def convertSymmetryNameForPackage(self,symm_name):
		return symm_name.replace(' (z)','')

	def __gotoRemoteRunDir(self):
		os.chdir(self.params['remoterundir'])

	def setupMPIRun(self,procscripts,nproc,masterfile_dir,masterfile_name):
		'''
		setupMPI run by making a master script in the designated path
		'''
		mpi_script = 'mpirun -np %d ' % (nproc)
		if len(procscripts) > 1:
			masterfile = os.path.join(masterfile_dir,masterfile_name)
			self.__makeMPIMasterScript(procscripts,masterfile)
			mpi_script += '-app '
			mpi_script += masterfile
		elif len(procscripts) == 1:
			mpi_script += procscripts[0]
		else:
			apDisplay.printError('no processes to make mpirun command line')
		return mpi_script

	def __makeMPIMasterScript(self,shellscripts,masterfile):
		lines = map((lambda x:'-np 1 '+x),shellscripts)
		f = open(masterfile,'w')
		f.writelines(map((lambda x: x+'\n'),lines))
		f.close()
		os.chmod(masterfile, 0755)
	def wrapScript(self,scriptname):	
		if self.params['appionwrapper'] != '':
			return self.params['appionwrapper']+' '+scriptname
		else:
			return scriptname

	def setupMPIRun(self,procscripts,nproc,masterfile_dir,masterfile_name):
		'''
		setupMPI run by making a master script in the designated path
		'''
		mpi_script = ''
		wrapper_tasksender = self.wrapScript('taskSender.py')
		subp_nproc = max(nproc / len(procscripts), 1)
		for index, procscript in enumerate(procscripts):
			ppn = min(subp_nproc,self.ppn)
			nodes = subp_nproc * ppn
			mpi_script += '%s %s %03d %d %d %d %s\n' % (wrapper_tasksender,self.params['remoterundir'],index,ppn,nodes,self.mem,procscript)
		mpi_script += '%s %s\n' % (self.wrapScript('taskMonitor.py'),self.params['remoterundir'])
		self.launch_as_shell = True
		return mpi_script

	def setupMPRun(self,procscript,mem,nproc):
		'''
		setup single node MP run
		'''
		mp_script = ''
		wrapper_tasksender = self.wrapScript('taskSender.py')
		ppn = nproc
		mp_script += '%s %s %03d %d %d %d %s\n' % (wrapper_tasksender,self.params['remoterundir'],0,ppn,1,mem,procscript)
		mp_script += '%s %s\n' % (self.wrapScript('taskMonitor.py'),self.params['remoterundir'])
		self.launch_as_shell = True
		return mp_script

	def makePreIterationScript(self):
		'''
		Package-specific function to make job script for setup tasks to do before
		performing iterated tasks even if it is a continuation of a trial
		'''
		pass

	def __makePreIterationScript(self):
		'''
		Function to make job script for setup tasks to do before performing iterated tasks
		even if it is a continuation of a trial
		'''
		self.addSimpleCommand('# work in the recondir')
		self.addSimpleCommand('cd %s' % self.params['recondir'])
		self.addSimpleCommand('')
		pretasks = {}
		# link the required files to scratch recondir in case they are removed in previous cleanup
		f = open(os.path.join(self.params['remoterundir'],'files_to_remote_host'))
		lines = f.readlines()
		pretasks = self.addToTasks(pretasks,'# link needed files into recondir')
		for line in lines:
			filename = os.path.basename(line.replace('\n',''))
			sourcepath = os.path.join(self.params['remoterundir'],filename)
			pretasks = self.addToTasks(pretasks,'ln -s  ../%s %s' % (filename,filename))
			pretasks = self.addToTasks(pretasks,'test -s  %s || ( echo %s not found && exit )' % (sourcepath,filename))
		self.addJobCommands(pretasks)
		self.addSimpleCommand('')

	def __createReconDir(self):
		apParam.createDirectory(self.params['recondir'], warning=(not self.quiet))

	def __removeReconDir(self):
		apParam.removeDirectory(self.params['recondir'], warning=(not self.quiet))

	def makeNewTrialScript(self):
		'''
		Package-specific function to make job script for tasks that set up files required to start a
		clean refine/reconstruction trial, including removal of the old trial. The job script starts
		at recondir
		'''
		pass

	def __makeNewTrialScript(self):
		'''
		Function to make job script for tasks that set up files required to start a
		clean refine/reconstruction trial. The job script starts and ends at remoterundir
		'''
		pretasks = {}
		pretasks = self.addToTasks(pretasks,'# setup directory')
		pretasks = self.addToTasks(pretasks,'# recon dir may already exist with mpi commands during preparation')
		pretasks = self.addToTasks(pretasks,'#   of the job script. O.K. if mkdir fails')
		pretasks = self.addToTasks(pretasks,'mkdir -p %s' % self.params['recondir'])
		pretasks = self.addToTasks(pretasks,'cd %s' % self.params['recondir'])
		pretasks = self.addToTasks(pretasks,'')
		pretasks = self.addToTasks(pretasks,'/bin/rm -fv resolution.txt')
		pretasks = self.addToTasks(pretasks,'touch resolution.txt')
		pretasks = self.addToTasks(pretasks,'cd %s' % self.params['remoterundir'])
		self.addJobCommands(pretasks)
		self.addSimpleCommand('')

	def makePostIterationScript(self):
		'''
		Function to make job script for tasks to do after performing iterated tasks
		'''
		pass

	def __addCopyByFileListFromRemoteHostTasks(self,tasks):
		'''
		Performs rsync to copy the files listed in files_from_remote_host back to localhost.
		'''
		tasks = self.addToTasks(tasks,'# copy files back to localhost rundir')
		f = open(os.path.join(self.params['remoterundir'],'files_from_remote_host'),'r')
		lines = f.readlines()
		f.close()
		lines.append('files_from_remote_host\n')
		for line in lines:
			filename = os.path.basename(line.replace('\n',''))
			tasks = self.addToTasks(tasks,"rsync -e 'ssh -o StrictHostKeyChecking=no' -rotouv --partial %s %s:%s/%s" % (filename,self.params['localhost'],self.params['rundir'],filename))
		return tasks

	def __addCleanUpReconDirTasks(self,tasks):
		'''
		Clean up recondir before packing.  This makes sure that these files in
		remoterundirs will not be over-written by those in the recondir since
		the latters are normally just a soft link.
		'''
		f = open(os.path.join(self.params['remoterundir'],'files_to_remote_host'),'r')
		lines = f.readlines()
		f.close()
		tasks = self.addToTasks(tasks,'# pack up recondir')
		tasks = self.addToTasks(tasks,'cd %s' % self.params['recondir'])
		# clean up files that are already in localhost rundir
		for line in lines:
			filename = os.path.basename(line.replace('\n',''))
			#tasks = self.addToTasks(tasks,'/bin/rm -fv  %s' % filename)
		return tasks

	def __saveFileListFromRemoteHost(self):
		'''
		Record the filenames in files_from_remote_host attribute in a file
		'''
		f = open(os.path.join(self.params['remoterundir'],'files_from_remote_host'),'w')
		f.writelines(map((lambda x: x+'\n'),self.files_from_remote_host))
		f.close()

	def __makePackResultsScript(self):
		'''
		Add tasks that packs up the recondir results to job commands
		'''
		self.addToLog('....Compressing refinement results for uploading....')
		tasks = {}
		###  Removing this for now as it removes a needed file and may not be necessary 
		#tasks = self.__addCleanUpReconDirTasks(tasks)
		
		# cd to the directory that holds the recon dir. For unpacking in to recon dir, we need to tar
		# the entire recon directory.
		tasks = self.addToTasks(tasks,'cd %s' % self.params['remoterundir'])
		#tasks = self.addToTasks(tasks,'cd %s' % self.params['recondir'])
		
		# Garibaldi does not work with the absolute path in the tar command
		#result_tar = os.path.join(self.params['remoterundir'],'recon_results.tar.gz')
		result_tar = 'recon_results.tar.gz'

		self.files_from_remote_host.append(result_tar)
		if not glob.glob('*.pickle'):
			tasks = self.addToTasks(tasks,'tar cvzf %s recon/' % (result_tar))
		else:
			# include pickle file only if created in previous steps
			tasks = self.addToTasks(tasks,'tar cvzf %s %s recon/' % (result_tar, "*.pickle"))
		self.files_from_remote_host.append(self.commandfile)
		self.__saveFileListFromRemoteHost()
		if self.params['remoterundir'] != self.params['rundir']:
			tasks = self.__addCopyByFileListFromRemoteHostTasks(tasks)
		self.addJobCommands(tasks)

	def logTaskStatus(self,existing_tasks,tasktype,tasklogfile, iter=None):
		'''
		Use taskStatusLogger.py to examine log or result file generated from a task
		'''
		if self.params['appionwrapper'] != '':
			wrapper_webcaller = self.params['appionwrapper']+' webcaller.py'
		else:
			wrapper_webcaller = 'webcaller.py'
		cmd = '--jobtype=%s --tasktype=%s --tasklogfile=%s' % (self.jobtype,tasktype,tasklogfile)
		if iter:
			cmd += ' --iter=%d' % (iter)
		# Use webcaller in append mode to send the sys.stdout to the log file
		cmd = "%s '%s %s' %s a" % (wrapper_webcaller,'taskStatusLogger.py',cmd,self.logfile)
		return self.addToTasks(existing_tasks,cmd)

	def makeRefineTasks(self,iter):
		'''
		Function to add a series of tasks to be performed at each iteration of refinement
		'''
		tasks = {}
		'''
		Need to add what is needed in the subclass with addToTasks function
		'''
		tasks = self.addToTasks(tasks,'')
		return tasks

	def setAttributes(self):
		self.tasks = {}
		self.files_from_remote_host = []
		self.command_list = []
		self.min_mem_list = []
		self.nproc_list = []
		self.ppn = self.params['ppn']
		self.nodes = self.params['nodes']
		self.walltime = self.params['walltime']
		self.mem = self.params['mem']
		self.nproc = self.params['nproc']
		self.setuponly = self.params['setuponly']
		self.jobtype = self.params['jobtype']
		self.jobid = self.params['jobid']
		self.remoterundir = self.params['remoterundir']
		self.setName(self.params['runname'])
		self.logfile = os.path.join(self.params['remoterundir'],self.getName()+'.log')
		self.commandfile = os.path.join(self.params['remoterundir'],self.getName()+'.commands')
		self.cputime = self.params['cput']
		self.expid = self.params['expid']
		self.rundir = self.params['rundir']
		self.queue = self.params['queue']
		# TO Do: need to get appion bin dir from appionwrapper environment variable Appion_Bin_Dir
		self.appion_bin_dir = ''
		
	def convertAngstromToPixel(self, angstromLength):
		''' 
		returns the equivalent length converted to pixels as an integer value. 
		If the passed in value is not set, just forward it along. 
		'''
		if angstromLength:
			floatValue = float(angstromLength) / self.params['apix']
			intValue = int(round(floatValue))
		else:
			intValue = angstromLength	
			
		return intValue
	       

	def __initializeLog(self):
		'''
		Initialize logfile for writing.  Will overwrite exisiting ones
		'''
		f = open(self.logfile,'w')
		f.write('Log for %s with runname %s (jobid= %d)\n' % (self.jobtype.upper(),self.params['runname'],self.jobid))
		f.close()
		
	def __writeCommandListToFile(self):
		'''
		Write the command list to a file for later use during upload.  Will overwrite exisiting ones.
		'''
		f = open(self.commandfile,'w')
		f.write('#Command List for %s with runname %s (jobid= %d)\n' % (self.jobtype.upper(),self.params['runname'],self.jobid))
		
		for command in self.command_list:
			f.write(command)
			f.write('\n')	
		
		f.close()

	def addToTasks(self,tasks,script,mem=2,nproc=1):
		'''
		Function to add one line of job command into existing tasks performed by the job.
		tasks = dictionary containing lists of scripts, mem, and nproc. can be initialized by an empty dictionary
		mem = task memory requirement required by the task for determining the memory the job need to reserve.
		nproc = the number of processors required by the task for determining the number of processors the job need to reserve.
		'''
		'''
		This is in the form of list of list for future development
		'''
		if len(tasks) == 0:
			for key in ('scripts','mem','nproc','file'):
				tasks[key] = []
		tasks['scripts'].append([script])
		tasks['mem'].append([mem])
		tasks['nproc'].append([nproc])
		return tasks

	def addJobCommands(self,tasks):
		'''
		Function to add a series of tasks to the job
		'''
		self.command_list.extend(map((lambda x:x[0]),tasks['scripts']))
		self.min_mem_list.extend(tasks['mem'])
		self.nproc_list.extend(tasks['nproc'])

	def addSimpleCommand(self,cmd):
		'''
		Add the command directly to the global list.
		It assumes default mem usage and single processor job
		'''
		self.addJobCommands(self.addToTasks({},cmd))

	def addToLog(self,text):
		'''
		Function to add text to logfile.
		'''
		bits = text.split('\n')
		if len(bits) > 0 and bits[-1] == '':
			# remove last white space if the user put linebreak at the end of the text
			bits = bits[:-1]
		for bit in bits:
			cmd = 'echo %s >> %s' % (bit,self.logfile)
			self.addJobCommands(self.addToTasks({},cmd))

	def isNewTrial(self):
		'''
		Check if clean up before start is needed.
		'''
		return self.params['startiter'] == 1
	
	def	createIterationCommandAndLog(self,iter):
		refinetasks = self.makeRefineTasks(iter)
		if 'scripts' in refinetasks.keys() and len(refinetasks['scripts']) >=1 and refinetasks['scripts'][0][0] !='':
			self.addToLog('....Starting iteration %d at %s...' % (iter, "`date`"))
			self.addJobCommands(refinetasks)
			self.addToLog('Done with iteration %d at %s' % (iter, "`date`"))
			self.addSimpleCommand('')

	def needIter0Recon(self):
		'''
		Returns True if the initial model should be remade using initial euler angles such as
		in the case of Frealign
		'''
		return False

	def createIter0CommandAndLog(self):
		self.createIterationCommandAndLog(0)

	def start(self):
		if self.isNewTrial():
			self.addSimpleCommand('')
			self.addToLog('....Setting up new refinement job trial....')
			# __removeReconDir is not in NewTrialScript because it is needed 
			# in setting up scripts even if the job script is not run.
			self.__removeReconDir()
			# __createReconDir physically creates recondir before or without
			# jobscript running so prepartion per iteration can be done.
			self.__createReconDir()
			self.__makeNewTrialScript()
			self.addSimpleCommand('# go to recondir after global new trial commands')
			self.addSimpleCommand('cd %s' % self.params['recondir'])
			self.makeNewTrialScript()
			self.addSimpleCommand('# return to rundir after package new trial commands')
			self.addSimpleCommand('cd %s' % self.params['remoterundir'])
		self.addSimpleCommand('')
		self.__makePreIterationScript()
		self.makePreIterationScript()
		if self.isNewTrial() and self.needIter0Recon():
			self.createIter0CommandAndLog()
		self.addSimpleCommand('')
		self.addSimpleCommand('')
		for iter in range(self.params['startiter'],self.params['enditer']+1):
			self.createIterationCommandAndLog(iter)
		self.addSimpleCommand('cd %s' % self.params['remoterundir'])
		self.addToLog('....Performing tasks after iterations....')
		self.makePostIterationScript()
		print self.params['remoterundir']
		self.__makePackResultsScript()
		self.__writeCommandListToFile()

	def onClose(self):
		self.addToLog('Done!')

	def getWalltime(self):
		return self.walltime
	def getName(self):
		return self.jobnamebase    
	def setName(self, newname):
		self.jobnamebase = newname + ".appionsub"               
	def getJobName(self):
		return self.jobnamebase + ".job"    
	def getNodes(self):
		return self.nodes
	def getPPN(self):
		return self.ppn
	def getCpuTime(self):
		return self.cputime
	def getMem(self):
		return  max([self.mem,max(max(self.min_mem_list))])
	def getPmem(self):
		return None
	def getQueue(self):
		return self.queue
	def getAccount(self):
		return None
	def getOutputDir(self):   	
		return self.remoterundir
	def getCommandList(self):
		return self.command_list
	def getJobId(self):
		return self.jobid    
	def setJobId(self, id):
		self.jobid = int(id)
	def getProjectId(self):
		return self.params['projectid']
	def getJobType(self):
		return self.jobtype    
	def getExpId(self):
		return self.expid    
	def getRundir(self):
		return self.rundir    
	def getLaunchAsShell(self):
		return self.launch_as_shell    
	def getSetupOnly(self):
		return self.setuponly  
	
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
