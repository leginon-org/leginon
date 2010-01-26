#!/usr/bin/env python

#pythonlib
import os
import sys
import re
import math
import cPickle
import time
#appion
from appionlib import appionLoop2
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apCtf
from appionlib import apMatlab
from appionlib import apParam

"""
try:
	import pymat
except:
	apDisplay.environmentError()
	raise
"""

import mlabraw as pymat

class aceLoop(appionLoop2.AppionLoop):
	def setProcessingDirName(self):
		self.processdirname = "ace"

	def preLoopFunctions(self):
		self.params['matdir']         = os.path.join(self.params['rundir'],"matfiles")
		self.params['opimagedir']     = os.path.join(self.params['rundir'],"opimages")
		self.params['tempdir']    = os.path.join(self.params['rundir'],"temp")
		apParam.createDirectory(os.path.join(self.params['matdir']), warning=False)
		apParam.createDirectory(os.path.join(self.params['opimagedir']), warning=False)
		apParam.createDirectory(os.path.join(self.params['tempdir']), warning=False)

		if self.params['sessionname'] is not None:
			self.params['outtextfile']=os.path.join(self.params['rundir'], self.params['sessionname']+".txt")
	
		apParam.resetVirtualFrameBuffer()
		apMatlab.checkMatlabPath(self.params)
		acepath = os.path.join(os.getcwd(), self.functionname+".py")
		#if not os.path.isfile(acepath):
		#	apDisplay.printWarning("'"+self.functionname+".py' usually needs to be run in the "+\
		#		"same directory as all of its matlab files")
		print "Connecting to matlab ... "
		if self.params['xvfb'] is True:
			apParam.resetVirtualFrameBuffer()
		try:
			self.matlab = pymat.open()
			#self.matlab = pymat.open('matlab -nodisplay')
		except:
			apDisplay.environmentError()
			raise
		apMatlab.setAceConfig(self.matlab, self.params)

	def postLoopFunctions(self):
		pymat.close(self.matlab)
		apCtf.printCtfSummary(self.params)

	def reprocessImage(self, imgdata):
		"""
		Returns 
		True, if an image should be reprocessed
		False, if an image was processed and should NOT be reprocessed
		None, if image has not yet been processed 
		e.g. a confidence less than 80%
		"""
		if self.params['reprocess'] is None:
			return None
		ctfvalue, conf = apCtf.getBestCtfValueForImage(imgdata)
		if ctfvalue is None:
			return None

		if conf > self.params['reprocess']:
			return False
		else:
			return True

	def processImage(self, imgdata):
		# RESTART MATLAB EVERY 500 IMAGES OR IT RUNS OUT OF MEMORY
		if self.stats['count'] % 500 == 0:
			apDisplay.printWarning("processed 500 images. restarting matlab...")
			pymat.close(self.matlab)
			time.sleep(5)
			self.matlab = pymat.open()

		scopeparams = {
			'kv':      imgdata['scope']['high tension']/1000,
			'apix':    apDatabase.getPixelSize(imgdata),
			'cs':      self.params['cs'],
			'tempdir': self.params['tempdir'],
		}
		### Scott's hack for FSU CM
		### For CM high tension is given in kv instead of v
		if imgdata['scope']['tem']['name'] == "CM":
			scopeparams['kv'] = imgdata['scope']['high tension']

		apMatlab.setScopeParams(self.matlab, scopeparams)
		### RUN ACE
		self.ctfvalue = apMatlab.runAce(self.matlab, imgdata, self.params)


	def commitToDatabase(self, imgdata):
		apCtf.insertAceParams(imgdata, self.params)
		apCtf.commitCtfValueToDatabase(imgdata, self.matlab, self.ctfvalue, self.params)

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
		self.parser.add_option("--resamplefr", dest="resamplefr", type="float", default=1.5,
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
		self.parser.add_option("--newnominal", dest="newnominal", default=False,
			action="store_true", help="newnominal")
		self.parser.add_option("--xvfb", dest="xvfb", default=False,
			action="store_true", help="xvfb")

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

