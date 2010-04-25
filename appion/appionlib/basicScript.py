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
class BasicScript(object):
	#=====================
	def __init__(self):
		"""
		Starts a new function and gets all the parameters
		"""
		### setup some expected values
		self.startmem = mem.active()
		self.t0 = time.time()
		self.createDefaultStats()
		self.quiet = False
		self.timestamp = apParam.makeTimestamp()
		apDisplay.printMsg("Time stamp: "+self.timestamp)
		self.functionname = apParam.getFunctionName(sys.argv[0])
		apDisplay.printMsg("Function name: "+self.functionname)

		apParam.setUmask()
		self.parsePythonPath()
		loadavg = os.getloadavg()[0]
		if loadavg > 2.0:
			time.sleep(loadavg**2)
			apDisplay.printMsg("Load average is high "+str(round(loadavg,2)))

		### setup default parser: run directory, etc.
		self.parser = OptionParser()
		self.setupParserOptions()
		self.params = apParam.convertParserToParams(self.parser)
		self.checkForDuplicateCommandLineInputs()

		self.checkConflicts()

		### write function log
		self.logfile = apParam.writeFunctionLog(sys.argv, msg=(not self.quiet))

		### any custom init functions go here
		self.onInit()

	#=====================
	def checkForDuplicateCommandLineInputs(self):
		args = sys.argv[1:]
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
		loadavg = os.getloadavg()[0]
		if loadavg > 2.0:
			apDisplay.printMsg("Load average is high "+str(round(loadavg,2)))
			time.sleep(loadavg**2)
		apParam.closeFunctionLog(functionname=self.functionname, 
			logfile=self.logfile, msg=(not self.quiet))
		if self.quiet is False:
			apDisplay.printMsg("Ended at "+time.strftime("%a, %d %b %Y %H:%M:%S"))
			apDisplay.printMsg("Memory increase during run: %.3f MB"%((mem.active()-self.startmem)/1024.0))
			apDisplay.printMsg("Run directory:\n "+self.params['rundir'])
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
		if len(appions) > 1:
			apDisplay.printWarning("There is more than one appion directory in your PYTHONPATH")
			print appions
		if len(leginons) > 1:
			apDisplay.printWarning("There is more than one leginon directory in your PYTHONPATH")
			print leginons

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
		if self.params['runname'] is None:
			apDisplay.printError("enter a run name ID, e.g. --runname=run1")
		if self.params['description'] is None:
			apDisplay.printError("enter a description, e.g. --description='awesome data'")

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

####
# Usage example
####

class TestScript(BasicScript):
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




