#!/usr/bin/env python

import pyami.quietscipy

#builtin
import os
import re
import sys
import time
import subprocess
import glob
from optparse import OptionParser
#appion
from appionlib import basicScript
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apThread
#leginon
import leginon.leginonconfig
import sinedon
from pyami import mem
from pyami import version
from pyami import fileutil

#=====================
#=====================
class FileScript(basicScript.BasicScript):
	#=====================
	def __init__(self,optargs=sys.argv[1:],quiet=False,useglobalparams=True,maxnproc=None):
		"""
		Starts a new function and gets all the parameters
		"""
		### setup some expected values
		self.successful_run = False
		self.params = {}
		sys.stdout.write("\n\n")
		self.quiet = quiet
		self.maxnproc = maxnproc
		self.startmem = mem.active()
		self.t0 = time.time()
		self.createDefaultStats()
		self.timestamp = apParam.makeTimestamp()
		self.argdict = {}
		self.optdict = {}
		apDisplay.printMsg("Time stamp: "+self.timestamp)
		self.functionname = apParam.getFunctionName(sys.argv[0])
		apDisplay.printMsg("Function name: "+self.functionname)
		self.appiondir = apParam.getAppionDirectory()
		apDisplay.printMsg("Appion directory: "+self.appiondir)
		self.parsePythonPath()
# 		loadavg = os.getloadavg()[0]
# 		if loadavg > 2.0:
# 			apDisplay.printMsg("Load average is high "+str(round(loadavg,2)))
# 			loadsquared = loadavg*loadavg
# 			time.sleep(loadavg)
# 			apDisplay.printMsg("New load average "+str(round(os.getloadavg()[0],2)))
		self.setLockname('lock')

		### setup default parser: run directory, etc.
		self.setParams(optargs,useglobalparams)
		#if 'outdir' in self.params and self.params['outdir'] is not None:
		#	self.params['rundir'] = self.params['outdir']

		self.checkConflicts()
		if useglobalparams is True:
			self.checkGlobalConflicts()

		### setup run directory
		self.setProcessingDirName()
		self.setupRunDirectory()

		### Start pool of threads to run subprocesses.
		### Later you will use self.process_launcher.launch(...) to
		### put commands into the queue.
		### There is currently a timeout built into it that will cause
		### the threads to die if they have no tasks after 10 seconds.
		self.process_launcher = apThread.ProcessLauncher(2, self.params['rundir'])

		### write function log
		self.logfile = apParam.writeFunctionLog(sys.argv, msg=(not self.quiet))


		### any custom init functions go here
		self.onInit()

	#=====================
	def argumentFromParamDest(self, dest):
		"""
		For a given optparse destination (dest, e.g., 'runname')
			this will determine the command line
			argument (e.g., -n)
		"""
		if len(self.argdict) == 0:
			for opt in self.parser.option_list:
				arg = str(opt.get_opt_string.im_self)
				if '/' in arg:
					args = arg.split('/')
					arg = args[-1:][0]
				self.argdict[opt.dest] = arg
				self.optdict[opt.dest] = opt
		if dest in self.argdict:
			return self.argdict[dest]
		return "????"

	#=====================
	def usageFromParamDest(self, dest, value):
		"""
		For a given optparse destination (dest, e.g., 'commit')
			and value (e.g., 'False') this will generate the command line
			usage (e.g., '--no-commit')
		"""
		usage = None
		if value is None:
			return None
		argument = self.argumentFromParamDest(dest)
		if not dest in self.optdict:
			return None
		optaction = self.optdict[dest].action
		if optaction == 'store':
			#opttype = self.optdict[dest].type
			value = str(value)
			if not ' ' in value:
				usage = argument+"="+value
			else:
				usage = argument+"='"+value+"'"
		elif optaction == 'store_true' or optaction == 'store_false':
			storage = 'store_'+str(value).lower()
			for opt in self.parser.option_list:
				if opt.dest == dest and opt.action == storage:
					arg = str(opt.get_opt_string.im_self)
					if '/' in arg:
						args = arg.split('/')
						arg = args[-1:][0]
					usage = arg
		return usage

	def getSessionDictFromSessionName(self,name):
		'''
		Replace apDatabase.getSessionDataFromSessionName call with this for FileScript.
		'''
		sessiondata = {}
		sessiondata['name'] = name
		return sessiondata

	#=====================
	def getSessionData(self):
		sessiondata = None
		if 'sessionname' in self.params and self.params['sessionname'] is not None:
			sessiondata = self.getSessionDictFromSessionName(self.params['sessionname'])
		return sessiondata

	#=====================
	def setupRunDirectory(self):
		"""
		Set the run directory
		"""
		if self.params['rundir'] is None:
			apDisplay.printWarning("run directory not defined, automatically setting it")
			self.setProcessingDirName()
			self.setRunDir()
			if self.params['rundir'] is None:
				apDisplay.printError("No run directory was set")

		if self.quiet is False:
			apDisplay.printMsg("Run directory: "+self.params['rundir'])

		if not os.path.isdir(self.params['rundir']):
				apDisplay.printError("run directory must exist for FileScript run")

		os.chdir(self.params['rundir'])

	#=====================
	def __del__(self):
		"""
		This functions runs whenever the program stops, even if it crashes
		"""
		pass

	#=====================
	def close(self):
		### run basic script closing functions
		basicScript.BasicScript.close(self)
		apDisplay.printMsg("Run directory:\n "+self.params['rundir'])
		### additionally set to done is database
		self.successful_run = True


	def setParams(self,optargs,useglobalparams=True):
		self.parser = OptionParser()
		if useglobalparams is True:
			self.setupGlobalParserOptions()
		self.setupParserOptions()
		self.params = apParam.convertParserToParams(self.parser)
		self.checkForDuplicateCommandLineInputs(optargs)

	#=====================
	def setupGlobalParserOptions(self):
		"""
		set the input parameters
		"""
		self.parser.add_option("-n", "--runname", dest="runname", default=self.timestamp,
			help="Name for processing run, e.g. --runname=run1", metavar="NAME")
		self.parser.add_option("-R", "--rundir", "--outdir", dest="rundir",
			help="Run path for storing output, e.g. --rundir=/data/appion/runs/run1",
			metavar="PATH")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit processing run to database")

		self.parser.add_option("--expid", "--expId", dest="expid", type="int",
			help="Session id associated with processing run, e.g. --expId=7159", metavar="#")
		self.parser.add_option("--nproc", dest="nproc", type="int",
			help="Number of processor to use", metavar="#")

		# jobtype is a dummy option for now so that it is possible to use the same command line that
		# is fed to runJob.py to direct command line running.  Do not use the resulting param.
		self.parser.add_option("--jobtype", dest="jobtype",
			help="Job Type of processing run, e.g., partalign", metavar="X")



	#=====================
	def checkGlobalConflicts(self):
		"""
		make sure the necessary parameters are set correctly
		"""
		if self.params['runname'] is None:
			apDisplay.printError("enter a runname, e.g. --runname=run1")
		if self.maxnproc is not None and self.params['nproc'] is not None:
			if self.params['nproc'] > self.maxnproc:
				apDisplay.printWarning('You have specify --nproc=%d.\n  However,we know from experience larger than %d processors in this script can cause problem.\n  We have therefore changed --nproc to %d for you.' % (self.params['nproc'],self.maxnproc,self.maxnproc))
				self.params['nproc'] = self.maxnproc

	#######################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################

	#=====================
	def preExistingDirectoryError(self):
		apDisplay.printWarning("Run directory already exists in the database")

	#=====================
	def setupParserOptions(self):
		"""
		set the input parameters
		this function should be rewritten in each program
		"""
		apDisplay.printError("you did not create a 'setupParserOptions' function in your script")
		self.parser.set_usage("Usage: %prog --commit' [options]")
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="INT")

	#=====================
	def checkConflicts(self):
		"""
		make sure the necessary parameters are set correctly
		"""
		apDisplay.printError("you did not create a 'checkConflicts' function in your script")
		if self.params['runname'] is None:
			apDisplay.printError("enter an unique run name, e.g. --runname=run1")

	#=====================
	def setProcessingDirName(self):
		self.processdirname = self.functionname

	def getDefaultBaseAppionDir(self,sessiondata,subdirs=[]):
		'''
		This function sets default base appiondir using leginon.cfg image path settings when rundir
		is not specified in the script. Such case will only occur if user construct the
		script his/herself, not from web.
		'''
		path = leginon.leginonconfig.IMAGE_PATH
		if path:
			path = os.path.join(path,sessiondata['name'])
		else:
			path = os.path.abspath(sessiondata['image path'])
			path = re.sub("/rawdata","",path)
		pieces = path.split('leginon')
		path = 'leginon'.join(pieces[:-1]) + 'appion' + pieces[-1]
		for subdir in subdirs:
			path = os.path.join(path, subdir)
		return path

	#=====================
	def setRunDir(self):
		"""
		this function only runs if no rundir is defined at the command line
		"""
		if self.params['rundir'] is None:
			apDisplay.printError('FileScript must have rundir defined')
		self.params['outdir'] = self.params['rundir']

	#=====================
	def start(self):
		"""
		this is the main component of the script
		where all the processing is done
		"""
		raise NotImplementedError()

	#=====================
	def onInit(self):
		return

	#=====================
	def onClose(self):
		return

	def runFileScriptInIndependentThread(self,cmd):
		self.process_launcher.launch(cmd, shell=True)

	def runFileScriptInSubprocess(self,cmd,logfilepath):
		# Running another FileScript as a subprocess
		apDisplay.printMsg('running FileScript:')
		apDisplay.printMsg('------------------------------------------------')
		apDisplay.printMsg(cmd)
		# stderr=subprocess.PIPE only works with shell=True with python 2.4.
		# works on python 2.6.  Use shell=True now but shell=True does not
		# work with path changed by appionwrapper.  It behaves as if the wrapper
		# is not used
		proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		stdout_value = proc.communicate()[0]
		while proc.returncode is None:
			time.wait(60)
			stdout_value = proc.communicate()[0]
		try:
			logdir = os.path.dirname(logfilepath)
			apParam.createDirectory(logdir)
			file = open(logfilepath,'w')
		except:
			apDisplay.printError('Log file can not be created, process did not run.')
		file.write(stdout_value)
		file.close()
		if proc.returncode > 0:
			pieces = cmd.split(' ')
			apDisplay.printWarning('FileScript %s had an error. Please check its log file: \n%s' % (pieces[0].upper(),logfilepath))
		else:
			apDisplay.printMsg('FileScript ran successfully')
		apDisplay.printMsg('------------------------------------------------')
		return proc.returncode

	#=====================
	def setLockname(self,name):
		self.lockname = '_'+name

	def cleanParallelLock(self):
		for file in glob.glob('%s*' % self.lockname):
			os.remove(file)

	def lockParallel(self,dbid):
		'''
		Check and create lock for dbid when running multiple instances on different
		hosts. This is as safe as we can do.  If in doubt, add a secondary check
		for the first output in the function
		'''
		try:
			fileutil.open_if_not_exists('%s%d' % (self.lockname,dbid)).close()
		except OSError:
			return True # exists before locking
		
	def unlockParallel(self,dbid):
		try:
			os.remove('%s%d' % (self.lockname,dbid))
		except:
			apDisplay.printError('Parallel unlock failed')
		
	#=====================
	
class TestScript(FileScript):
	def setupParserOptions(self):
		apDisplay.printMsg("Parser options")
	def checkConflicts(self):
		apDisplay.printMsg("Conflicts")
	def setRunDir(self):
		self.params['rundir'] = os.getcwd()
	def start(self):
		apDisplay.printMsg("Hey this works")
		raise NotImplementedError

if __name__ == '__main__':
	print "__init__"
	testscript = TestScript()
	print "start"
	testscript.start()
	print "close"
	testscript.close()




