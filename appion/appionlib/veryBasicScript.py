#!/usr/bin/env python

#builtin
import os
import sys
import time
from optparse import OptionParser
#leginon
from pyami import mem
#appion
from appionlib import apParam
from appionlib import apDisplay

####
# This is a low-level file with NO database connections
# Please keep it this way
####

#=====================
#=====================
class VeryBasicScript(object):
	#=====================
	def __init__(self,optargs=sys.argv[1:],quiet=False):
		"""
		Starts a new function and gets all the parameters
		"""
		### setup some expected values
		self.startmem = mem.active()
		self.t0 = time.time()
		self.createDefaultStats()
		self.quiet = quiet
#		self.timestamp = apParam.makeTimestamp()
#		if not self.quiet:
#			apDisplay.printMsg("Time stamp: "+self.timestamp)
		self.functionname = apParam.getFunctionName(sys.argv[0])
		if not self.quiet:
			apDisplay.printMsg("Function name: "+self.functionname)

		apParam.setUmask()
		self.parsePythonPath()
# 		loadavg = os.getloadavg()[0]
# 		if loadavg > 2.0:
# 			apDisplay.printMsg("Load average is %.2f, wait for %.1f second " % (round(loadavg,2),loadavg**2))
# 			time.sleep(loadavg**2)
# 			apDisplay.printMsg("Load average is high "+str(round(loadavg,2)))

		### setup default parser: run directory, etc.
		self.setParams(optargs)
		self.checkConflicts()

		### write function log
		self.logfile = apParam.writeFunctionLog(sys.argv, msg=(not self.quiet))

		### any custom init functions go here
		self.onInit()

	def setParams(self,optargs=sys.argv[1:]):
		self.parser = OptionParser()
		self.setupParserOptions()
		self.params = apParam.convertParserToParams(self.parser)
		self.checkForDuplicateCommandLineInputs(optargs)


	#=====================
	def checkForDuplicateCommandLineInputs(self,optargs=sys.argv[1:]):
		args = optargs
		argmdict = {}
		for arg in args:
			elements=arg.split('=')
			opt = elements[0].lower()
			if opt[0] == "-":
				## if action='append', then opt is allowed multiple times
				option = self.parser.get_option(opt)
				if option is not None and option.action == 'append':
					multiple_ok = True
				else:
					multiple_ok = False
				if opt in argmdict and not multiple_ok:
					apDisplay.printError("Multiple arguments were supplied for argument: "+str(opt))
				argmdict[opt] = True

	#=====================
	def createDefaultStats(self):
		self.stats = {}
		self.stats['starttime'] = time.time()
		self.stats['count'] = 1
		self.stats['lastcount'] = 0
		self.stats['startmem'] = mem.active()
		self.stats['memleak'] = 0
		self.stats['peaksum'] = 0
		self.stats['lastpeaks'] = None
		self.stats['imagesleft'] = 1
		self.stats['peaksumsq'] = 0
		self.stats['timesum'] = 0
		self.stats['timesumsq'] = 0
		self.stats['skipcount'] = 0
		self.stats['waittime'] = 0
		self.stats['lastimageskipped'] = False
		self.stats['notpair'] = 0
		self.stats['memlist'] = [mem.active()]

	#=====================
	def close(self):
		self.onClose()
# 		loadavg = os.getloadavg()[0]
# 		if loadavg > 2.0:
# 			apDisplay.printMsg("Load average is high "+str(round(loadavg,2)))
# 			time.sleep(loadavg**2)
		apParam.closeFunctionLog(functionname=self.functionname, 
			logfile=self.logfile, msg=(not self.quiet))
		if self.quiet is False:
			apDisplay.printMsg("Ended at "+time.strftime("%a, %d %b %Y %H:%M:%S"))
			if apDisplay.isDebugOn():
				apDisplay.printDebug("Memory increase during run: %.3f MB"%((mem.active()-self.startmem)/1024.0))
			apDisplay.printColor("Total run time:\t"+apDisplay.timeString(time.time()-self.t0),"green")

	#=====================
	def parsePythonPath(self):
		pythonpath = os.environ.get("PYTHONPATH")
		if pythonpath is None:
			return
		paths = pythonpath.split(":")
		leginons = {}
		appions = {}
		for p in paths:
			if "appion" in p:
				appions[p] = None
			if "leginon" in p:
				leginons[p] = None
		leginons = leginons.keys()
		appions = appions.keys()
#		if len(appions) > 1:
#			apDisplay.printWarning("There is more than one appion directory in your PYTHONPATH")
#			print appions
#		if len(leginons) > 1:
#			apDisplay.printWarning("There is more than one leginon directory in your PYTHONPATH")
#			print leginons

	#######################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################

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
		return

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

####
# This is a low-level file with NO database connections
# Please keep it this way
####

class BasicScriptInstanceRun(object):
	'''
	Create an instance of a subclass of BasicScript
	according to the jobtype and then run it
	'''
	def __init__(self):
		command = sys.argv[1:]
		self.jobtype = self.getJobType(command)
		self.app = self.createInst(self.jobtype,command)
		if self.app is None:
			apDisplay.printError('No BasicScript subclass instance created')
		else:
			self.app.start()
			self.run()
			self.app.close()

	def getJobType(self, command):
		jobtype = None
		#Search for the command option that specified the job type
		for option in command:
			if option.startswith(r'--jobtype='):
				#We only need the part after the '='
				jobtype = option.split('=')[1]
				#Don't process anymore of the list then needed
				break
		return jobtype

	def createInst(self, jobtype, command):
		'''
		Create Instance of BasicScript or its subclasses according to the jobtype.
		'''
		jobInstance = VeryBasicScript()
		return jobInstance

	def run(self):
		'''
		Do something
		'''
		pass

####
# Usage example
####

class TestScript(VeryBasicScript):
	#------------
	def setupParserOptions(self):
		apDisplay.printMsg("Parser options")
	#------------
	def checkConflicts(self):
		apDisplay.printMsg("Conflicts")
	#------------
	def start(self):
		apDisplay.printMsg("Hey this works")

if __name__ == '__main__':
	testscript = TestScript()
	testscript.start()
	testscript.close()




