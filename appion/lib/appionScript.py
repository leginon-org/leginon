#!/usr/bin/python -O

import warnings
warnings.filterwarnings('ignore', module='scipy')

#builtin
import sys
import os
import re
import time
import math
import random
import cPickle
from string import lowercase
from optparse import OptionParser
#appion
import apDisplay
import apDatabase
import apParam
import apDB
#leginon
from pyami import mem


class AppionScript(object):
	appiondb  = apDB.apdb
	leginondb = apDB.db

	#=====================
	def __init__(self):
		self.quiet = False
		### clean up any preliminary warnings
		sys.stderr.write("\n\n")
		#set the name of the function; needed for param setup
		self.t0 = time.time()
		self.timestamp = time.strftime("%y%b%d").lower()+lowercase[time.localtime()[4]%26]
		self.functionname = apParam.getFunctionName(sys.argv[0])
		self.appiondir = apParam.getAppionDirectory()
		apParam.setUmask()

		### setup default parser: output directory, etc.
		self.parser = OptionParser()
		self.setupParserOptions()
		self.params = apParam.convertParserToParams(self.parser)

		### check if user wants to print help message
		if 'commit' in self.params:
			if self.params['commit'] is False:
				apDisplay.printWarning("Not committing data to database")
			else:
				apDisplay.printMsg("Committing data to database")
		self.checkConflicts()

		### setup output directory
		self.setProcessingDirName()
		self.setupOutputDirectory()
		self.params['rundir'] = self.params['outdir']
		if apDatabase.queryDirectory(self.params['outdir']):
			self.preExistingDirectoryError()

		### write function log
		self.logfile = apParam.writeFunctionLog(sys.argv, msg=(not self.quiet))

		### any custom init functions go here
		self.onInit()

	#=====================
	def setupOutputDirectory(self):
		#IF NO OUTDIR IS SET
		if self.params['outdir'] is None:
			self.setOutDir()
		#create the output directory, if needed
		if self.quiet is False:
			apDisplay.printMsg("Output directory: "+self.params['outdir'])
		apParam.createDirectory(self.params['outdir'], warning=(not self.quiet))
		os.chdir(self.params['outdir'])

	#=====================
	def close(self):
		self.onClose()
		apParam.closeFunctionLog(params=self.params, logfile=self.logfile, msg=(not self.quiet))
		if self.quiet is False:
			apDisplay.printMsg("outdir:\n "+self.params['outdir'])
			apDisplay.printColor("COMPLETE SCRIPT:\t"+apDisplay.timeString(time.time()-self.t0),"green")

	#######################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################

	#=====================
	def preExistingDirectoryError(self):
		apDisplay.printWarning("Output directory already exists in the database")

	#=====================
	def setupParserOptions(self):
		"""
		set the input parameters
		"""
		self.parser.set_usage("Usage: %prog --session=<session> --commit --description='<text>' [options]")
		self.parser.add_option("-d", "--description", dest="description",
			help="Description of the template (must be in quotes)", metavar="TEXT")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location to copy the templates to", metavar="PATH")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit template to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit template to database")
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="INT")
		self.parser.add_option("--runid", "-r", dest="runid", default=self.timestamp,
			help="Run ID name, e.g. --runid=run1", metavar="NAME")

	#=====================
	def checkConflicts(self):
		"""
		make sure the necessary parameters are set correctly
		"""
		if self.params['session'] is None:
			apDisplay.printError("enter a session ID, e.g. --session=07jun06a")
		if self.params['description'] is None:
			apDisplay.printError("enter a description, e.g. --description='awesome data'")

	#=====================
	def setProcessingDirName(self):
		self.processdirname = self.functionname

	#=====================
	def setOutDir(self):
		import apStack
		if ( self.params['outdir'] is None 
		and 'session' in self.params 
		and self.params['session'] is not None ):
			#auto set the output directory
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
			path = os.path.abspath(sessiondata['image path'])
			path = re.sub("leginon","appion",path)
			path = re.sub("/rawdata","",path)
			path = os.path.join(path, self.processdirname)
			self.params['outdir'] = path
		if ( self.params['outdir'] is None 
		and 'reconid' in self.params 
		and self.params['reconid'] is not None ):
			self.params['stackid'] = apStack.getStackIdFromRecon(self.params['reconid'], msg=False)
		if ( self.params['outdir'] is None 
		and 'stackid' in self.params
		and self.params['stackid'] is not None ):
			#auto set the output directory
			stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
			path = os.path.abspath(stackdata['path']['path'])
			path = os.path.dirname(path)
			path = os.path.dirname(path)
			self.params['outdir'] = os.path.join(path, self.processdirname)

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
	def start(self):
		apDisplay.printMsg("Hey this works")

if __name__ == '__main__':
	print "__init__"
	testscript = TestScript()
	print "start"
	testscript.start()
	print "close"
	testscript.close()
	


