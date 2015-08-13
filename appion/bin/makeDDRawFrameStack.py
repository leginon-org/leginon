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

class MakeFrameStackLoop(apDDLoop.DDStackLoop):
	#=======================
	def setupParserOptions(self):
		super(MakeFrameStackLoop,self).setupParserOptions()
		# Boolean
		self.parser.add_option("--rawarea", dest="rawarea", default=False,
			action="store_true", help="use full area of the raw frame, not leginon image area")
		self.parser.add_option("--useGS", dest="useGS", default=False,
			action="store_true", help="Use Gram-Schmidt process to scale dark image")
		self.parser.add_option("--align", dest="align", default=False,
			action="store_true", help="Make Aligned frame stack")
		self.parser.add_option("--square", dest="square", default=False,
			action="store_true", help="Output square images")
		self.parser.add_option("--defergpu", dest="defergpu", default=False,
			action="store_true", help="Make unaligned frame stack first on computer without gpu alignment program")
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
		if self.params['align'] and not self.params['defergpu']:
			exename = 'dosefgpu_driftcorr'
			gpuexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
			if not os.path.isfile(gpuexe):
				apDisplay.printError('Correction program "%s" not available' % exename)
			# We don't have gpu locking
			if self.params['parallel']:
					apDisplay.printWarning('Make sure that you use different gpuid for each parallel process')
			# Local directory creating and permission checking
			if self.params['tempdir']:
				try:
					fileutil.mkdirs(self.params['tempdir'])
					os.access(self.params['tempdir'],os.W_OK|os.X_OK)
				except:
					raise
					apDisplay.printError('Local temp directory not writable')
		else:
			# makes no sense to save gain corrected ddstack in tempdir if no alignment
			# will be done on the same machine
			if self.params['tempdir']:
				apDisplay.printWarning('tempdir is not neccessary without aligning on the same host. Reset to None')
				self.params['tempdir'] = None
			# Stack cleaning should not be done in some cases
			if not self.params['keepstack']:
				if self.params['defergpu']:
					apDisplay.printWarning('The gain/dark-corrected stack must be saved if alignment is deferred')
					self.params['keepstack'] = True
				else:
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
		self.dd.setUseGPUFlat(True)
		self.dd.setSquareOutputShape(self.params['square'])
		self.dd.setTrimingEdge(self.params['trim'])
		self.dd.setDoseFDriftCorrOptions(self.params)
		self.dd.setGPUid(self.params['gpuid'])
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
		super(MakeFrameStackLoop,self).processImage(imgdata)
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
		if self.params['align']:
			self.dd.setAlignedCameraEMData()
			framelist = self.dd.getFrameList(self.params)
			self.dd.setAlignedSumFrameList(framelist)

		### first remove any existing stack file
		apFile.removeFile(self.dd.framestackpath)
		apFile.removeFile(self.dd.tempframestackpath)
		if self.dd.hasBadPixels() or not self.params['align']:
			self.dd.setUseGPUFlat(False)
			### make stack
			self.dd.makeCorrectedFrameStack(self.params['rawarea'])
		else:
			self.dd.setUseGPUFlat(True)
			self.dd.makeRawFrameStackForOneStepCorrectAlign(self.params['rawarea'])
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
			if self.dd.getUseGPUFlat():
				self.dd.gainCorrectAndAlignFrameStack()
			else:
				self.dd.alignCorrectedFrameStack()
			if os.path.isfile(self.dd.aligned_sumpath):
				self.aligned_imagedata = self.dd.makeAlignedImageData(alignlabel=self.params['alignlabel'])
				if os.path.isfile(self.dd.aligned_stackpath):
					# aligned_stackpath exists either because keepstack is true
					apDisplay.printMsg(' Replacing unaligned stack with the aligned one....')
					apFile.removeFile(self.dd.framestackpath)
					apDisplay.printMsg('Moving %s to %s' % (self.dd.aligned_stackpath,self.dd.framestackpath))
					shutil.move(self.dd.aligned_stackpath,self.dd.framestackpath)
			# Clean up tempdir in case of failed alignment
			if self.dd.framestackpath != self.dd.tempframestackpath:
				apFile.removeFile(self.dd.tempframestackpath)
		if not self.params['keepstack']:
			apFile.removeFile(self.dd.framestackpath)

	def insertFunctionRun(self):
		if self.params['stackid']:
			stackdata = apStack.getOnlyStackData(self.params['stackid'])
		else:
			stackdata = None
		qparams = appiondata.ApDDStackParamsData(preset=self.params['preset'],align=self.params['align'],bin=self.params['bin'],stack=stackdata)
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



