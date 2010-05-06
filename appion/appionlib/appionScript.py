#!/usr/bin/env python

import pyami.quietscipy

#builtin
import os
import re
import sys
import time
import subprocess
from optparse import OptionParser
#appion
from appionlib import basicScript
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apProject
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apWebScript
#leginon
import sinedon
from pyami import mem
from pyami import version

#=====================
#=====================
class AppionScript(basicScript.BasicScript):
	#=====================
	def __init__(self, useglobalparams=True):
		"""
		Starts a new function and gets all the parameters
		"""
		### setup some expected values
		sys.stdout.write("\n\n")
		self.quiet = False
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
		loadavg = os.getloadavg()[0]
		if loadavg > 2.0:
			time.sleep(loadavg**2)
			apDisplay.printMsg("Load average is high "+str(round(loadavg,2)))

		### setup default parser: run directory, etc.
		self.parser = OptionParser()
		if useglobalparams is True:
			self.setupGlobalParserOptions()
		self.setupParserOptions()
		self.params = apParam.convertParserToParams(self.parser)
		self.checkForDuplicateCommandLineInputs()
		#if 'outdir' in self.params and self.params['outdir'] is not None:
		#	self.params['rundir'] = self.params['outdir']

		### setup correct database after we have read the project id
		if 'projectid' in self.params and self.params['projectid'] is not None:
			apDisplay.printWarning("Using split database")
			# use a project database
			newdbname = apProject.getAppionDBFromProjectId(self.params['projectid'])
			sinedon.setConfig('appiondata', db=newdbname)
			apDisplay.printColor("Connected to database: '"+newdbname+"'", "green")

		### check if user wants to print help message
		if 'commit' in self.params and self.params['commit'] is True:
			apDisplay.printMsg("Committing data to database")
		else:
			apDisplay.printWarning("Not committing data to database")

		self.checkConflicts()
		if useglobalparams is True:
			self.checkGlobalConflicts()

		### setup run directory
		self.setProcessingDirName()
		self.setupRunDirectory()

		### write function log
		self.logfile = apParam.writeFunctionLog(sys.argv, msg=(not self.quiet))

		### upload command line parameters to database
		self.uploadScriptData()

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
			opttype = self.optdict[dest].type
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

	#=====================
	def getSessionData(self):
		sessiondata = None
		if 'sessionname' in self.params:
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		elif not sessiondata and 'session' in self.params and isinstance(self.params['session'],str):
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		elif not sessiondata and 'stackid' in self.params:
			from appionlib import apStack
			sessiondata = apStack.getSessionDataFromStackId(self.params['stackid'])
		else:
			s = re.search('/([0-9][0-9][a-z][a-z][a-z][0-9][0-9][^/]*)/', self.params['rundir'])
			if s:
				self.params['sessionname'] = s.groups()[0]
				sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		return sessiondata

	#=====================
	def getClusterJobData(self):
		partq = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		clustq = appiondata.ApClusterJobData()
		clustq['path'] = partq
		clustdatas = clustq.query()
		if not clustdatas:
			### insert a cluster job
			clustq['name'] = self.params['runname']+".appionsub.job"
			clustq['clusterpath'] = partq
			clustq['user'] = apParam.getUsername()
			clustq['cluster'] = apParam.getHostname()
			clustq['status'] = "R"
			clustq['session'] = self.getSessionData()
			### need a proper way to create a jobtype
			clustq['jobtype'] = self.functionname.lower()
			return clustq
		elif len(clustdatas) == 1:
			### we have an entry
			### we need to say that we are running
			apWebScript.setJobToRun(clustdatas[0].dbid)
			return clustdatas[0]
		else:
			### special case: more than one job with given path
			apDisplay.printWarning("More than one cluster job has this path")
			return clustdatas[0]

	#=====================
	def uploadScriptData(self):
		"""
		Using tables to track program run parameters in a generic fashion
		inspired by Roberto Marabini and Carlos Oscar Sanchez Sorzano from the Xmipp team/Carazo lab
		"""
		prognameq = appiondata.ScriptProgramName()
		prognameq['name'] = self.functionname

		userq = appiondata.ScriptUserName()
		userq['name'] = apParam.getUsername()

		hostq = appiondata.ScriptHostName()
		hostq['name'] = apParam.getHostname()
		hostq['ip'] = apParam.getHostIP()
		hostq['system'] = apParam.getSystemName()
		hostq['distro'] = apParam.getLinuxDistro()
		hostq['nproc'] = apParam.getNumProcessors()
		hostq['memory'] = apParam.getTotalMemory()
		hostq['cpu_vendor'] = apParam.getCPUVendor()
		hostq['gpu_vendor'] = apParam.getGPUVendor()
		hostq['arch'] = apParam.getMachineArch()

		progrunq = appiondata.ScriptProgramRun()
		progrunq['runname'] = self.params['runname']
		progrunq['progname'] = prognameq
		progrunq['username'] = userq
		progrunq['hostname'] = hostq
		progrunq['rundir'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		progrunq['job'] = self.getClusterJobData()
		progrunq['revision'] = version.getSubverionRevision()
		appiondir = apParam.getAppionDirectory()
		progrunq['appion_path'] = appiondata.ApPathData(path=os.path.abspath(appiondir))

		for paramname in self.params.keys():
			paramnameq = appiondata.ScriptParamName()
			paramnameq['name'] = paramname
			paramnameq['progname'] = prognameq

			paramvalueq = appiondata.ScriptParamValue()
			paramvalueq['value'] = str(self.params[paramname])
			usage = self.usageFromParamDest(paramname, self.params[paramname])
			#print "usage: ", usage
			paramvalueq['usage'] = usage
			paramvalueq['paramname'] = paramnameq
			paramvalueq['progrun'] = progrunq
			if usage is not None and self.params['commit'] is True:
				paramvalueq.insert()

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

		#if apDatabase.queryDirectory(self.params['rundir']):
		#	self.preExistingDirectoryError()

		#create the run directory, if needed
		apParam.createDirectory(self.params['rundir'], warning=(not self.quiet))
		os.chdir(self.params['rundir'])

	#=====================
	def close(self):
		### run custom closing functions
		self.onClose()
		### run basic script closing functions
		basicScript.BasicScript.close(self)
		apDisplay.printMsg("Run directory:\n "+self.params['rundir'])
		### additionally set to done is database
		if self.params['commit'] is True:
			clustdata = self.getClusterJobData()
			apWebScript.setJobToDone(clustdata.dbid)


	#=====================
	def setupGlobalParserOptions(self):
		"""
		set the input parameters
		"""
		self.parser.add_option("-n", "--runname", dest="runname", default=self.timestamp,
			help="Name for processing run, e.g. --runname=run1", metavar="NAME")
		self.parser.add_option("-d", "--description", dest="description",
			help="Description of the processing run (must be in quotes)", metavar="TEXT")
		self.parser.add_option("-p", "--projectid", dest="projectid", type="int",
			help="Project id associated with processing run, e.g. --projectid=159", metavar="#")
		self.parser.add_option("-R", "--rundir", "--outdir", dest="rundir",
			help="Run path for storing output, e.g. --rundir=/data/appion/runs/run1",
			metavar="PATH")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit processing run to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit processing run to database")

	#=====================
	def checkGlobalConflicts(self):
		"""
		make sure the necessary parameters are set correctly
		"""
		if self.params['runname'] is None:
			apDisplay.printError("enter a runname, e.g. --runname=run1")
		if self.params['projectid'] is None:
			apDisplay.printError("enter a project id, e.g. --projectid=159")

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
		self.parser.set_usage("Usage: %prog --commit --description='<text>' [options]")
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="INT")

	#=====================
	def checkConflicts(self):
		"""
		make sure the necessary parameters are set correctly
		"""
		apDisplay.printError("you did not create a 'checkConflicts' function in your script")
		if self.params['runname'] is None:
			apDisplay.printError("enter a run name ID, e.g. --runname=run1")
		if self.params['description'] is None:
			apDisplay.printError("enter a description, e.g. --description='awesome data'")

	#=====================
	def setProcessingDirName(self):
		self.processdirname = self.functionname

	#=====================
	def setRunDir(self):
		"""
		this function only runs if no rundir is defined at the command line
		"""
		from appionlib import apStack
		if ( self.params['rundir'] is None
		and 'session' in self.params
		and self.params['session'] is not None ):
			#auto set the run directory
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
			path = os.path.abspath(sessiondata['image path'])
			path = re.sub("leginon","appion",path)
			path = re.sub("/rawdata","",path)
			path = os.path.join(path, self.processdirname, self.params['runname'])
			self.params['rundir'] = path
		if ( self.params['rundir'] is None
		and 'reconid' in self.params
		and self.params['reconid'] is not None ):
			self.params['stackid'] = apStack.getStackIdFromRecon(self.params['reconid'], msg=False)
		if ( self.params['rundir'] is None
		and 'stackid' in self.params
		and self.params['stackid'] is not None ):
			#auto set the run directory
			stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
			path = os.path.abspath(stackdata['path']['path'])
			path = os.path.dirname(path)
			path = os.path.dirname(path)
			self.params['rundir'] = os.path.join(path, self.processdirname, self.params['runname'])
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

class TestScript(AppionScript):
	def setupParserOptions(self):
		apDisplay.printMsg("Parser options")
	def checkConflicts(self):
		apDisplay.printMsg("Conflicts")
	def setRunDir(self):
		self.params['rundir'] = os.getcwd()
	def start(self):
		apDisplay.printMsg("Hey this works")

if __name__ == '__main__':
	print "__init__"
	testscript = TestScript()
	print "start"
	testscript.start()
	print "close"
	testscript.close()




