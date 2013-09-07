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
		# Boolean
		self.parser.add_option("--rawarea", dest="rawarea", default=False,
			action="store_true", help="use full area of the raw frame, not leginon image area")
		self.parser.add_option("--useGS", dest="useGS", default=False,
			action="store_true", help="Use Gram-Schmidt process to scale dark image")
		self.parser.add_option("--align", dest="align", default=False,
			action="store_true", help="Make Aligned frame stack")
		self.parser.add_option("--gpuflat", dest="gpuflat", default=False,
			action="store_true", help="Use gpu for flat field (gain/dark/mask) correction")
		self.parser.add_option("--defergpu", dest="defergpu", default=False,
			action="store_true", help="Make unaligned frame stack first on computer without gpu alignment program")
		self.parser.add_option("--no-keepstack", dest="keepstack", default=True,
			action="store_false", help="Clean up frame stack after alignment and sum image upload")
		self.parser.add_option("--no-cyclechannels", dest="cyclechannels", default=True,
			action="store_false", help="Use only one reference channel for gain/dark correction")
		# String
		self.parser.add_option("--tempdir", dest="tempdir",
			help="Local path for storing temporary stack output, e.g. --tempdir=/tmp/appion/makeddstack",
			metavar="PATH")
		# Integer
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="INT")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Binning factor to make the stack (optional)", metavar="INT")
		self.parser.add_option("--refimgid", dest="refimgid", type="int",
			help="Specify a corrected image to do gain/dark correction with", metavar="INT")
		self.parser.add_option("--gpuid", dest="gpuid", type="int", default=0,
			help="GPU device id used in gpu processing", metavar="INT")
		self.parser.add_option("--ddstartframe", dest="startframe", type="int", default=0,
			help="starting frame for direct detector raw frame processing. The first frame is 0")
		self.parser.add_option("--ddnframe", dest="nframe", type="int",
			help="total frames to consider for direct detector raw frame processing")
		self.parser.remove_option("--uncorrected")
		self.parser.remove_option("--reprocess")

	#=======================
	def checkConflicts(self):
		if self.params['align'] and not self.params['defergpu']:
			gpuexelist = ['dosefgpu_driftcorr','dosefgpu_flat']
			exename = 'dosefgpu_driftcorr'
			gpuexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
			if not os.path.isfile(gpuexe):
				apDisplay.printError('Correction program "%s" not available' % exename)
			# We don't have gpu locking
			if self.params['parallel']:
					apDisplay.printWarning('Make sure that you use different gpuid for each parallel process')
			# As single processing sequential job, not sure if gpu is faster than cpu
			#self.params['gpuflat'] = True
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


		if self.params['gpuflat']:
			exename = 'dosefgpu_flat'
			gpuexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
			if not os.path.isfile(gpuexe):
				apDisplay.printWarning('Correction program "%s" not available. Use cpu for correction.' % exename)
				self.params['gpuflat'] = False

	def getFrameType(self):
		# set how frames are saved depending on what is found in the basepath
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		return ddinfo.getRawFrameType(sessiondata['image path'])

	#=======================
	def preLoopFunctions(self):
		self.dd = apDDprocess.initializeDDFrameprocess(self.params['sessionname'],self.params['wait'])
		self.dd.setUseGS(self.params['useGS'])
		self.dd.setRunDir(self.params['rundir'])
		self.dd.setTempDir(self.params['tempdir'])
		self.dd.setRawFrameType(self.getFrameType())
		self.dd.setUseGPUFlat(self.params['gpuflat'])
		self.dd.setGPUid(self.params['gpuid'])
		# keepstack is resolved for various cases in conflict check.  There should be no ambiguity by now
		self.dd.setKeepStack(self.params['keepstack'])
		self.dd.setCycleReferenceChannels(self.params['cyclechannels'])
		
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
			if os.path.isfile(self.dd.aligned_sumpath):
				self.aligned_imagedata = self.dd.makeAlignedImageData()
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



