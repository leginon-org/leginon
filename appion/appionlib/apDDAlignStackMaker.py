#!/usr/bin/env python
import subprocess
import os
import socket
import shutil

#pyami
from pyami import fileutil
#appion
from appionlib import apDisplay
from appionlib import apDDStackMaker
from appionlib import apDDFrameAligner
from appionlib import apFile

class AlignStackLoop(apDDStackMaker.FrameStackLoop):
	def setupParserOptions(self):
		super(AlignStackLoop,self).setupParserOptions()
		self.parser.add_option("--align", dest="align", default=False,
			action="store_true", help="Make Aligned frame stack")
		self.parser.add_option("--defergpu", dest="defergpu", default=False,
			action="store_true", help="Make unaligned frame stack first on computer without gpu alignment program")

	#=======================
	def checkConflicts(self):
		if self.params['align'] and not self.params['defergpu']:
			self.checkFrameAlignerExecutable()

			# Local directory creating and permission checking
			if self.params['tempdir']:
				try:
					fileutil.mkdirs(self.params['tempdir'])
					os.access(self.params['tempdir'],os.W_OK|os.X_OK)
				except:
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

	def setFrameAligner(self):
		self.framealigner = apDDFrameAligner.DDFrameAligner()

	def checkFrameAlignerExecutable(self):
		self.framealigner = apDDFrameAligner.DDFrameAligner()
		exename = self.framealigner.getExecutableName()
		gpuexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	#		gpuexe = "/emg/sw/script/motioncorr-master/bin/"+exename
		print 'gpuexe path is '+gpuexe
		if not os.path.isfile(gpuexe):
			apDisplay.printError('Correction program "%s" not available' % exename)

	#=======================
	def preLoopFunctions(self):
		self.setFrameAligner()
		self.framealigner.setFrameAlignOptions(self.params)
		super(AlignStackLoop,self).preLoopFunctions()

	def setOtherProcessImageResultParams(self):
		'''
		result path needed for alignment. This is run before alignment
		'''
		self.hostname = socket.gethostname()
		# The alignment is done in tempdir (a local directory to reduce network traffic)
		# include both hostname and gpu to identify the temp output
		self.temp_aligned_sumpath = 'temp%s_sum.mrc' % (self.hostname)
		self.temp_aligned_dw_sumpath = 'temp%s_sum_DW.mrc' % (self.hostname)
		self.temp_aligned_stackpath = 'temp%s_aligned_st.mrc' % (self.hostname)
		self.temp_logpath = self.dd.tempframestackpath[:-4]+'_Log.txt'

		self.log = self.dd.framestackpath[:-4]+'_Log.txt'
		self.framealigner.setInputFrameStackPath(self.dd.tempframestackpath)
		self.framealigner.setAlignedSumPath(self.temp_aligned_sumpath)
		self.framealigner.setAlignedStackPath(self.temp_aligned_stackpath)
		self.framealigner.setLogPath(self.temp_logpath)

		if self.isAlign():
			# set framelist
			# ??? Why do this first (for DE camera ?
			self.dd.setAlignedCameraEMData()
			framelist = self.dd.getFrameListFromParams(self.params)
			self.dd.setAlignedSumFrameList(framelist)
			self.framealigner.setAlignedSumFrameList(framelist)
			# whether the sum can be don in framealigner depends on the framelist
			self.framealigner.setIsUseFrameAlignerSum(self.isUseFrameAlignerSum())
			self.framealigner.setSaveAlignedStack = self.dd.getKeepAlignedStack()
			if self.isUseFrameAlignerFlat():
				self.dd.makeDarkNormMrcs()
				gain_ref = self.dd.getNormRefMrcPath()
				per_frame_dark_ref = self.dd.getDarkRefMrcPath()
				self.framealigner.setGainDarkCmd(gain_ref, per_frame_dark_ref)

	def isAlign(self):
		return self.params['align']

	def isUseFrameAlignerFlat(self):
		if self.dd.hasBadPixels() or not self.isAlign():
			self.dd.setUseFrameAlignerFlat(False)
			return False
		else:
			self.dd.setUseFrameAlignerFlat(True)
			return True

	def isUseFrameAlignerSum(self):
		return self.dd.isSumSubStackWithFrameAligner()

	#=======================
	def otherProcessImage(self, imgdata):
		# Align
		if self.params['align']:
			# make a fake log so that catchUpDDAlign will know that frame stack is done
			fakelog = self.log
			f = open(fakelog,'w')
			f.write('Fake log to mark the unaligned frame stack as done\n')
			f.close()
			if self.params['defergpu']:
				return
			
			os.chdir(self.dd.tempdir)
			self.alignFrameStack()
			self.is_ok = self.organizeAlignedSum()
			if not self.is_ok:
				os.chdir(self.dd.rundir)
				return
			self.organizeAlignedStack()
			os.chdir(self.dd.rundir)
	
	def organizeAlignedSum(self):
		'''
		Move local temp results to rundir in the official names
		'''
		temp_aligned_sumpath = self.temp_aligned_sumpath
		temp_aligned_dw_sumpath = self.temp_aligned_dw_sumpath
		temp_aligned_stackpath = self.temp_aligned_stackpath
		
		if not os.path.isfile(temp_aligned_sumpath):
			apDisplay.printWarning('Frame alignment FAILED: \n%s not created.' % os.path.basename(temp_aligned_sumpath))
			return False
		else:
			# successful alignment
			self.convertLogFile()
			if self.dd.getKeepAlignedStack():
				# bug in MotionCorr requires this
				self.updateFrameStackHeaderImageStats(temp_aligned_stackpath)
			if not self.isUseFrameAlignerSum():
				# replace the sum with one corresponds with framelist
				self.sumSubStackWithNumpy(temp_aligned_stackpath,temp_aligned_sumpath)

			# temp_aligned_sumpath should have the right number of frames at this point
			shutil.move(temp_aligned_sumpath,self.dd.aligned_sumpath)
			if self.params['doseweight'] is True:
				shutil.move(temp_aligned_dw_sumpath,self.dd.aligned_dw_sumpath)
			return self.dd.aligned_sumpath

	def organizeAlignedStack(self):
		'''
		Things to do after alignment.
			1. Save the sum as imagedata
			2. Replace unaligned ddstack
		'''
		if os.path.isfile(self.dd.aligned_sumpath):
			# Save the alignment result
			self.aligned_imagedata = self.dd.makeAlignedImageData(alignlabel=self.params['alignlabel'])
			if self.params['doseweight'] is True:
				self.params['align_dw_label'] = self.params['alignlabel']+"-DW"
				self.aligned_dw_imagedata = self.dd.makeAlignedDWImageData(alignlabel=self.params['align_dw_label'])
			if self.params['keepstack']:
				shutil.move(self.temp_aligned_stackpath,self.dd.aligned_stackpath)
			else:
				apFile.removeFile(self.temp_aligned_stackpath)

			# replace the unaligned stack with aligned_stack
			if os.path.isfile(self.dd.aligned_stackpath):
				# aligned_stackpath exists either because keepstack is true
				apDisplay.printMsg(' Replacing unaligned stack with the aligned one....')
				apFile.removeFile(self.dd.framestackpath)
				apDisplay.printMsg('Moving %s to %s' % (self.dd.aligned_stackpath,self.dd.framestackpath))
				shutil.move(self.dd.aligned_stackpath,self.dd.framestackpath)

	def otherCleanUp(self, imgdata):
		if not self.is_ok:
			apDisplay.printWarning('Nothing to clean up')
			return
		# Clean up tempdir in case of failed alignment
		if self.dd.framestackpath != self.dd.tempframestackpath:
			apFile.removeFile(self.dd.tempframestackpath)

	def convertLogFile(self):
		'''
		Standard LogFile is in XX form.
		'''
		if self.dd.tempdir != self.dd.rundir:
			# Move the Log to permanent location for display and inspection
			if os.path.isfile(self.temp_logpath):
				shutil.move(self.temp_logpath,self.log)
				apDisplay.printMsg('Moving result for %s from %s to %s' % (self.dd.image['filename'],self.dd.tempdir,self.dd.rundir))

	def alignFrameStack(self):
		# Align
		if self.params['align']:
			# Doing the alignment
			self.framealigner.alignFrameStack()

