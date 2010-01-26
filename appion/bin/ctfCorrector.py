#!/usr/bin/env python

#pythonlib
import os
import sys
import re
import cPickle
import time
#appion
from appionlib import appionLoop2
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apMatlab
from appionlib import apCtf
from appionlib import apParam
try:
	import mlabraw as pymat
except:
	apDisplay.environmentError()
	raise

class aceLoop(appionLoop2.AppionLoop):

	#======================
	def setProcessingDirName(self):
		self.processdirname = "ctfCorrect"

	#======================
	def preLoopFunctions(self):
		self.params['matdir']     = os.path.join(self.params['rundir'],"matfiles")
		self.params['opimagedir'] = os.path.join(self.params['rundir'],"opimages")
		self.params['tempdir']    = os.path.join(self.params['rundir'],"temp")
		apParam.createDirectory(os.path.join(self.params['matdir']), warning=False)
		apParam.createDirectory(os.path.join(self.params['opimagedir']), warning=False)
		apParam.createDirectory(os.path.join(self.params['tempdir']), warning=False)
		if self.params['sessionname'] is not None:
			self.params['outtextfile']=os.path.join(self.params['rundir'], self.params['sessionname']+".txt")
		apMatlab.checkMatlabPath(self.params)
		acepath = os.path.join(os.getcwd(), self.functionname+".py")
		if not os.path.isfile(acepath):
			apDisplay.printWarning("'"+self.functionname+".py' usually needs to be run in the "+\
				"same directory as all of its matlab files")
		print "Connecting to matlab ... "
		try:
			self.matlab = pymat.open()
		except:
			apDisplay.environmentError()
			raise
		apCtf.mkTempDir(self.params['tempdir'])
		apMatlab.setAceConfig(self.matlab, self.params)

	#======================
	def postLoopFunctions(self):
		pymat.close(self.matlab)

	#======================
	def processImage(self, imgdata):
		apCtf.runAceCorrect(matlab,img,params)

	#======================
	def setupParserOptions(self):
		self.parser.add_option("--edgethcarbon", dest="edgethcarbon", type="float", default=0.8,
			help="edge carbon, default=0.8", metavar="#")
		self.parser.add_option("--edgethice", dest="edgethice", type="float", default=0.6,
			help="edge ice, default=0.6", metavar="#")
		self.parser.add_option("--pfcarbon", dest="pfcarbon", type="float", default=0.9,
			help="pfcarbon, default=0.9", metavar="#")
		self.parser.add_option("--pfice", dest="pfice", type="float", default=0.3,
			help="pfice, default=0.3", metavar="#")
		self.parser.add_option("--overlap", dest="overlap", type="int", default=2,
			help="overlap, default=2", metavar="#")	
		self.parser.add_option("--fieldsize", dest="fieldsize", type="int", default=512,
			help="fieldsize, default=512", metavar="#")
		self.parser.add_option("--resamplefr", dest="resamplefr", type="int", default=1,
			help="resamplefr, default=1", metavar="#")
		self.parser.add_option("--drange", dest="drange", type="int", default=0,
			help="drange, default=0", metavar="#")
		self.parser.add_option("--medium", dest="medium", default="carbon",
			help="sample medium, default=carbon", metavar="MEDIUM")
		self.parser.add_option("--cs", dest="cs", type="float", default=2.0,
			help="cs, default=2.0", metavar="#")
		self.parser.add_option("--display", dest="display", type="int", default=1,
			help="display, default=1", metavar="#")
		self.parser.add_option("--stig", dest="stig", type="int", default=0,
			help="stig, default=0", metavar="#")
		self.parser.add_option("--nominal", dest="nominal", 
			help="nominal")
		self.parser.add_option("--useestnominal", dest="useestnominal", default=False,
			action="store_true", help="useestnominal")

	#======================
	def checkConflicts(self):
		if self.params['nominal'] is not None and (self.params['nominal'] > 0 or self.params['nominal'] < -15e-6):
			apDisplay.printError("Nominal should be of the form nominal=-1.2e-6 for -1.2 microns")
		if not (self.params['drange'] == 1 or self.params['drange']== 0):
			apDisplay.printError("drange should only be 0 or 1")
		if not (self.params['medium'] == 'carbon' or self.params['medium'] == 'ice'):
			apDisplay.printError("medium can only be 'carbon' or 'ice'")
		if not (self.params['display'] == 0 or self.params['display'] == 1):
			apDisplay.printError("display must be 0 or 1")
		if not (self.params['stig'] == 0 or self.params['stig'] == 1):
			apDisplay.printError("stig must be 0 or 1")		
		return


if __name__ == '__main__':
	imgLoop = aceLoop()
	imgLoop.run()

