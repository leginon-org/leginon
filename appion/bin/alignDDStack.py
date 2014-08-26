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

class AlignFrameStackLoop(apDDLoop.DDStackLoop):
	#=======================
	def setupParserOptions(self):
		super(AlignFrameStackLoop,self).setupParserOptions()
		# Boolean
		# String
		# Integer
		self.parser.add_option("--ddstack", dest="ddstack", type="int",
			help="ID for ddstack run to make aligned ddstack(required)", metavar="INT")

	#=======================
	def checkConflicts(self):
		# Check that the program needed exists
		gpuexelist = ['dosefgpu_driftcorr']
		exename = 'dosefgpu_driftcorr'
		gpuexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(gpuexe):
			apDisplay.printError('Correction program "%s" not available' % exename)
		# We don't have gpu locking
		if self.params['parallel']:
				apDisplay.printWarning('Make sure that you use different gpuid for each parallel process')
		if self.params['stackid'] and not self.params['ddstack']:
			apDisplay.printError('Specify stack alone does not work.  Use makeDDRawFrameStack.py instead')

	#=======================
	def preLoopFunctions(self):
		self.dd = apDDprocess.initializeDDFrameprocess(self.params['sessionname'],self.params['wait'])
		self.dd.setRunDir(self.params['rundir'])
		self.dd.setDoseFDriftCorrOptions(self.params)
		self.dd.setGPUid(self.params['gpuid'])
		# keepstack is resolved for various cases in conflict check.  There should be no ambiguity by now
		self.dd.setKeepStack(self.params['keepstack'])
		
		self.gain_corrected_ddproc = None
		self.imageids = []
		if self.params['stackid']:
			# create a list of unaligned imageids from the particle stack
			imageids_from_stack = apStack.getImageIdsFromStack(self.params['stackid'])
			self.imageids = self.getUnAlignedImageIds(imageids_from_stack)
			if not self.params['ddstack']:
				print 'This does not work yet.  Need to create gain-corrected-ddstack first'
		if self.params['ddstack']:
			self.gain_corrected_ddproc = apDDprocess.DDStackProcessing()
			self.gain_corrected_ddproc.setDDStackRun(ddstackrunid=self.params['ddstack'])
		# Optimize AppionLoop wait time for this since the processing now takes longer than
		# image acquisition
		self.setWaitSleepMin(0.4)
		self.setProcessBatchCount(1)

	#=======================
	def processImage(self, imgdata):
		super(AlignFrameStackLoop,self).processImage(imgdata)
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
		self.dd.setAlignedCameraEMData()
		framelist = self.dd.getFrameList(self.params)
		self.dd.setAlignedSumFrameList(framelist)

		### first remove any existing stack file
		apFile.removeFile(self.dd.framestackpath)
		apFile.removeFile(self.dd.tempframestackpath)
		### symbolic link unaligned ddstack from its original dir to here
		self.gain_corrected_ddproc.setImageData(imgdata)
		self.gain_corrected_ddproc.setFrameStackPath()
		gain_corrected_framestackpath = self.gain_corrected_ddproc.getFrameStackPath()
		os.symlink(gain_corrected_framestackpath,self.dd.framestackpath)

		# Align
		# make a fake log so that catchUpDDAlign will know that frame stack is done
		fakelog = self.dd.framestackpath[:-4]+'_Log.txt'
		f = open(fakelog,'w')
		f.write('Fake log to mark the unaligned frame stack as done\n')
		f.close()
		# Doing the alignment
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
		self.gain_corrected_ddstackrundata = appiondata.ApDDStackRunData().direct_query(self.params['ddstack'])
		if self.params['stackid']:
			stackdata = apStack.getOnlyStackData(self.params['stackid'])
		else:
			stackdata = None
		qparams = appiondata.ApDDStackParamsData(preset=self.params['preset'],align=True,bin=self.params['bin'],unaligned_ddstackrun=self.gain_corrected_ddstackrundata,stack=stackdata)
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
	makeStack = AlignFrameStackLoop()
	makeStack.run()



