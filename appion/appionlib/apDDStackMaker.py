#!/usr/bin/env python

#pythonlib
import os
import sys
import math
import shutil
import subprocess
#pyami
from pyami import fileutil
#leginon
from leginon import ddinfo
#appion
from appionlib import apDDLoop
from appionlib import apDisplay
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apFile
from appionlib import apStack
from appionlib import appiondata

class FrameStackLoop(apDDLoop.DDStackLoop):
	#=======================
	def setupParserOptions(self):
		super(FrameStackLoop,self).setupParserOptions()
		# Boolean
		self.parser.add_option("--rawarea", dest="rawarea", default=False,
			action="store_true", help="use full area of the raw frame, not leginon image area")
		self.parser.add_option("--useGS", dest="useGS", default=False,
			action="store_true", help="Use Gram-Schmidt process to scale dark image")
		self.parser.add_option("--square", dest="square", default=False,
			action="store_true", help="Output square images")
		self.parser.add_option("--no-cyclechannels", dest="cyclechannels", default=True,
			action="store_false", help="Use only one reference channel for gain/dark correction")
		# String
		# Integer
		self.parser.add_option("--refimgid", dest="refimgid", type="int",
			help="Specify a corrected image to do gain/dark correction with", metavar="INT")

		self.parser.add_option("--trim", dest="trim", type="int", default=0,
			help="Trim edge off after frame stack gain/dark correction", metavar="INT")

	#=======================
	def checkConflicts(self):
			# Stack cleaning should not be done in some cases
			if not self.params['keepstack']:
					apDisplay.printError('Why making only gain/dark-corrected ddstacks but not keeping them')

	def getFrameType(self):
		# set how frames are saved depending on what is found in the basepath
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		if sessiondata['frame path']:
			# 3.0+
			return ddinfo.getRawFrameType(sessiondata['frame path'])
		else:
			# pre-3.0
			return ddinfo.getRawFrameType(sessiondata['image path'])

	#=======================
	def preLoopFunctions(self):
		self.dd = apDDprocess.initializeDDFrameprocess(self.params['sessionname'],self.params['wait'])
		self.dd.setUseGS(self.params['useGS'])
		self.dd.setRunDir(self.params['rundir'])
		self.dd.setTempDir(self.params['tempdir'])
		self.dd.setRawFrameType(self.getFrameType())
		self.dd.setUseFrameAlignerFlat(True)
		self.dd.setSquareOutputShape(self.params['square'])
		self.dd.setTrimingEdge(self.params['trim'])
		# keepstack is resolved for various cases in conflict check.  There should be no ambiguity by now
		self.dd.setKeepStack(self.params['keepstack'])
		self.dd.setCycleReferenceChannels(self.params['cyclechannels'])

	
		if self.params['refimgid']:
			self.dd.setDefaultImageForReference(self.params['refimgid'])
		self.imageids = []
		if self.params['stackid']:
			# create a list of unaligned imageids from the particle stack
			imageids_from_stack = apStack.getImageIdsFromStack(self.params['stackid'])
			self.imageids = self.getUnAlignedImageIds(imageids_from_stack)
		# Optimize AppionLoop wait time for this since the processing now takes longer than
		# image acquisition
		self.setWaitSleepMin(0.4)
		self.setProcessBatchCount(1)

	#=======================
	def processImage(self, imgdata):
		super(FrameStackLoop,self).processImage(imgdata)
		# need to avoid non-frame saved image for proper caching
		if imgdata is None or imgdata['camera']['save frames'] != True:
			apDisplay.printWarning('%s skipped for no-frame-saved\n ' % imgdata['filename'])
			return
		if self.params['stackid'] and imgdata.dbid not in self.imageids:
			return

		### set processing image
		try:
			self.dd.setImageData(imgdata)
		except Exception, e:
			apDisplay.printWarning(e.args[0])
			return

		if self.params['parallel'] and (os.path.isfile(self.dd.getFrameStackPath(temp=True)) or os.path.isfile(self.dd.getFrameStackPath())):
			# This is a secondary image lock check, checking the first output of the process.
			# It alone is not good enough
			apDisplay.printWarning('Some other parallel process is working on the same image. Skipping')
			return

		# set other parameters
		self.dd.setNewBinning(self.params['bin'])

		# place holder for alignment result path setting
		self.setOtherProcessImageResultPaths()

		### first remove any existing stack file
		apFile.removeFile(self.dd.framestackpath)
		apFile.removeFile(self.dd.tempframestackpath)

		if not self.isUseFrameAlignerFlat():
			### make stack
			self.dd.makeCorrectedFrameStack(self.params['rawarea'])
		else:
			self.dd.makeRawFrameStackForOneStepCorrectAlign(self.params['rawarea'])

		self.otherProcessImage(imgdata)

		# Clean up
		if not self.params['keepstack']:
			apFile.removeFile(self.dd.framestackpath)
		self.otherCleanUp(imgdata)

	def isAlign(self):
		return False

	def isUseFrameAlignerFlat(self):
		self.dd.setUseFrameAlignerFlat(False)
		return False

	def setOtherProcessImageResultPaths(self):
		pass

	def otherProcessImage(self,imgdata):
		'''
		Place holder for more processing before clean up
		'''
		pass

	def otherCleanUp(self,imgdata):
		'''
		Place holder for more clean up
		'''
		pass

	def insertFunctionRun(self):
		if self.params['stackid']:
			stackdata = apStack.getOnlyStackData(self.params['stackid'])
		else:
			stackdata = None
		qparams = appiondata.ApDDStackParamsData(preset=self.params['preset'],align=self.isAlign(),bin=self.params['bin'],stack=stackdata)
		qpath = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		sessiondata = self.getSessionData()
		q = appiondata.ApDDStackRunData(runname=self.params['runname'],params=qparams,session=sessiondata,path=qpath)
		results = q.query()
		if results:
			return results[0]
		else:
			if self.params['commit'] is True:
				q.insert()
				return q

if __name__ == '__main__':
	makeStack = FrameStackLoop()
	makeStack.run()



