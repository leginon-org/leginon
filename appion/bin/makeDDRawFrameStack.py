#!/usr/bin/env python

#pythonlib
import os
import sys
import math
import shutil
import subprocess
#leginon
from leginon import ddinfo
#appion
from appionlib import appionLoop2
from appionlib import apDisplay
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apFile
from appionlib import apStack
from appionlib import appiondata

class MakeFrameStackLoop(appionLoop2.AppionLoop):
	#=======================
	def setupParserOptions(self):
		self.parser.add_option("--rawarea", dest="rawarea", default=False,
			action="store_true", help="use full area of the raw frame, not leginon image area")
		self.parser.add_option("--useGS", dest="useGS", default=False,
			action="store_true", help="Use Gram-Schmidt process to scale dark image")
		self.parser.add_option("--align", dest="align", default=False,
			action="store_true", help="Make Aligned frame stack")
		self.parser.add_option("--defergpu", dest="defergpu", default=False,
			action="store_true", help="Make unaligned frame stack first on computer without gpu alignment program")
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="INT")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Binning factor to make the stack (optional)", metavar="INT")
		self.parser.add_option("--refimgid", dest="refimgid", type="int",
			help="Specify a corrected image to do gain/dark correction with", metavar="INT")
		self.parser.remove_option("--uncorrected")
		self.parser.remove_option("--reprocess")

	#=======================
	def checkConflicts(self):
		if self.params['align'] and not self.params['defergpu']:
			exename = 'dosefgpu_driftcorr'
			driftcorrexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
			if not os.path.isfile(driftcorrexe):
				apDisplay.printError('Drift correction program not available')
			if self.params['parallel']:
				apDisplay.printError('parallel processing only works without gpu processing i.e., align must be deferred')

	def getFrameType(self):
		# set how frames are saved depending on what is found in the basepath
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		return ddinfo.getRawFrameType(sessiondata['image path'])

	#=======================
	def preLoopFunctions(self):
		self.dd = apDDprocess.initializeDDFrameprocess(self.params['sessionname'],self.params['wait'])
		self.dd.setUseGS(self.params['useGS'])
		self.dd.setRunDir(self.params['rundir'])
		self.dd.setRawFrameType(self.getFrameType())
		
		if self.params['refimgid']:
			self.dd.setDefaultImageForReference(self.params['refimgid'])
		self.imageids = []
		if self.params['stackid']:
			self.imageids = apStack.getImageIdsFromStack(self.params['stackid'])
		# Optimize AppionLoop wait time for this since the processing now takes longer than
		# image acquisition
		self.setWaitSleepMin(0.4)
		self.setProcessBatchCount(1)

	#=======================
	def processImage(self, imgdata):
		# initialize aligned_imagedata as if not aligned
		self.aligned_imagedata = None
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
			apDisplay.printWarning(e.message)
			return

		if self.params['parallel'] and os.path.isfile(self.dd.getFrameStackPath()):
			# This is a secondary image lock check, checking the first output of the process.
			# It alone is not good enough
			apDisplay.printWarning('Some other parallel process is working on the same image. Skipping')
			return

		# set other parameters
		self.dd.setNewBinning(self.params['bin'])
		if self.params['align']:
			self.dd.setAlignedCameraEMData()

		### first remove any existing stack file
		apFile.removeFile(self.dd.framestackpath)
		### make stack
		self.dd.makeCorrectedFrameStack(self.params['rawarea'])

		# Align
		if self.params['align']:
			# make a fake log so that catchUpDDAlign will know that frame stack is done
			fakelog = self.dd.framestackpath[:-4]+'_Log.txt'
			f = open(fakelog,'w')
			f.write('Fake log to mark the unaligned frame stack as done\n')
			f.close()
			if self.params['defergpu']:
				return
			# Doing the alignment
			self.dd.alignCorrectedFrameStack()
			if os.path.isfile(self.dd.aligned_stackpath):
				self.aligned_imagedata = self.dd.makeAlignedImageData()
				apDisplay.printMsg(' Replacing unaligned stack with the aligned one....')
				apFile.removeFile(self.dd.framestackpath)
				shutil.move(self.dd.aligned_stackpath,self.dd.framestackpath)

	def commitToDatabase(self, imgdata):
		if self.aligned_imagedata != None:
			apDisplay.printMsg('Uploading aligned image as %s' % imgdata['filename'])
			q = appiondata.ApDDAlignImagePairData(source=imgdata,result=self.aligned_imagedata,ddstackrun=self.rundata)
			q.insert()

	def insertFunctionRun(self):
		qparams = appiondata.ApDDStackParamsData(preset=self.params['preset'],align=self.params['align'],bin=self.params['bin'],)
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
	makeStack = MakeFrameStackLoop()
	makeStack.run()



