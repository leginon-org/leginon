#!/usr/bin/env python

#pythonlib
import os
import shutil
import subprocess
import time
import socket
#leginon
from leginon import leginondata
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apDDprocess
from appionlib import apFile
from appionlib import appiondata
from appionlib import apDatabase
from appionlib import apScriptLog
from appionlib import apDDFrameAligner

class CatchUpFrameAlignmentLoop(appionScript.AppionScript):
	#=======================
	def setupParserOptions(self):
		self.parser.add_option("--ddstackid", dest="ddstackid", type="int",
			help="ID for dd frame stack run", metavar="INT")
		self.parser.add_option("--no-wait", dest="wait", default=True,
			action="store_false", help="Do not wait for frame stack to finish creation")
		self.parser.add_option("-m", "--mrclist", dest="mrcnames",
			help="List of mrc files to process, e.g. --mrclist=..003en,..002en,..006en", metavar="MRCNAME")
		self.parser.add_option("--gpuid", dest="gpuid", type="int", default=0,
			help="GPU device id used in gpu processing", metavar="INT")
		self.parser.add_option("--limit", dest="limit", type="int", default=0,
			help="Limit image processing to this number.  0 means no limit", metavar="INT")

	#=======================
	def checkConflicts(self):
		# make sure program exist
		exename = 'dosefgpu_driftcorr'
		driftcorrexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(driftcorrexe):
			apDisplay.printError('Drift correction program not available')
		if not self.params['ddstackid']:
			apDisplay.printMsg('Must have a ddstack run to catch up alignment')
		# make sure ddstack exists
		ddstackrun = appiondata.ApDDStackRunData().direct_query(self.params['ddstackid'])
		if ddstackrun:
			apDisplay.printMsg('Found dd frame stack run')
			# set self.rundata in this function because we may need it if rundir is not set in params
			self.rundata = ddstackrun
		else:
			apDisplay.printError('DD Frame Stack id %d does not exist' % self.params['ddstackid'])
		if not self.rundata['params']['align']:
			apDisplay.printError('DD Frame Stack id %d was not meant to be aligned' % self.params['ddstackid'])

	#=====================
	def setRunDir(self):
		self.params['rundir'] = self.rundata['path']['path']

	#=======================
	def onInit(self):
		if 'sessionname' not in self.params.keys():
			self.params['sessionname'] = leginondata.SessionData().direct_query(self.params['expid'])['name']
		self.dd = apDDprocess.initializeDDFrameprocess(self.params['sessionname'],self.params['wait'])
		# Set DDFrameAligner to Purdue version of MotionCorr
		self.framealigner = apDDFrameAligner.MotionCorr_Purdue()	

		self.dd.setRunDir(self.params['rundir'])
		#self.framealigner.setRunDir(self.params['rundir'])
		# The gain/dark corrected ddstack is unlikely to be on local disk
		if 'tempdir' not in self.params.keys():
			self.dd.setTempDir()
		else:
			self.dd.setTempDir(self.params['tempdir'])

		self.dd.setNewBinning(self.rundata['params']['bin'])

		# Get the unfinished ddstack run parameters to apply them here
		jobdata = apDatabase.getJobDataFromPathAndType(self.rundata['path']['path'], 'makeddrawframestack')
		self.ddstack_script_params = apScriptLog.getScriptParamValuesFromRunname(self.rundata['runname'],self.rundata['path'],jobdata)
		if 'no-keepstack' in self.ddstack_script_params.keys():
			self.dd.setKeepStack(False)
		self.framealigner.setFrameAlignOptions(self.ddstack_script_params)

		# Give an unique lockname
		self.setLockname('ddalign')
		self.success_count = 0

	def hasDDAlignedImagePair(self):
		alignpairdata = self.dd.getAlignImagePairData(self.rundata,query_source=True)
		return bool(alignpairdata)

	def hasAlignedSumImage(self):
		return os.path.isfile(self.dd.aligned_sumpath)

	def getAlignBin(self):
		alignbin = self.rundata['params']['bin']
		if alignbin > 1:
			bintext = '_%dx' % (alignbin)
		else:
			bintext = ''
		return bintext

	def setTempPaths(self):
		# The alignment is done in tempdir (a local directory to reduce network traffic)
		self.hostname = socket.gethostname()
		bintext = self.getAlignBin()
		self.temp_logpath = self.dd.tempframestackpath[:-4]+bintext+'_Log.txt'
		self.temp_aligned_sumpath = 'temp%s_%d_sum.mrc' % (self.hostname, self.params['gpuid'])
		self.temp_aligned_stackpath = 'temp%s_%d_aligned_st.mrc' % (self.hostname, self.params['gpuid'])

	def convertLogFile(self):
		'''
		Standard LogFile is in XX form.
		'''
		if self.temp_logpath != self.log:
			# Move the Log to permanent location for display and inspection
			if os.path.isfile(self.temp_logpath):
				shutil.move(self.temp_logpath,self.log)
				apDisplay.printMsg('Moving result for %s from %s to %s' % (self.dd.image['filename'],self.temp_logpath,self.log))

	#=======================
	def processImage(self, imgdata):
		# initialize aligned_imagedata as if not aligned
		self.aligned_imagedata = None
		# need to avoid non-frame saved image for proper caching
		if imgdata is None or imgdata['camera']['save frames'] != True:
			apDisplay.printWarning('%s skipped for no-frame-saved\n ' % imgdata['filename'])
			return
	
		### set processing image
		try:
			self.dd.setImageData(imgdata,ignore_raw=True)
		except Exception, e:
			apDisplay.printWarning(e.message)
			return
		# use non-temp framestack path as input
		self.framealigner.setInputFrameStackPath(self.dd.getFrameStackPath())
		self.log = self.dd.framestackpath[:-4]+'_Log.txt'
		# use temp paths as output to avoid conflict with parallel process
		self.setTempPaths()
		self.framealigner.setAlignedSumPath(self.temp_aligned_sumpath)
		self.framealigner.setAlignedStackPath(self.temp_aligned_stackpath)
		self.framealigner.setLogPath(self.temp_logpath)

		## various ways to skip the image
		if self.params['commit'] and self.hasDDAlignedImagePair():
			apDisplay.printWarning('aligned image %d from this run is already in the database. Skipped....' % imgdata.dbid)
			return
		if not self.params['commit'] and self.hasAlignedSumImage():
			# This checks for file, Therefore can not be rerun.
			apDisplay.printWarning('aligned image %d from this run is already in the directory. Skipped....' % imgdata.dbid)
			return
		if self.lockParallel(imgdata.dbid):
			apDisplay.printMsg('%s locked by another parallel run in the rundir' % (apDisplay.shortenImageName(imgdata['filename'])))
			return
		# This will wait for the stack to finish gain correction
		if not self.dd.isReadyForAlignment():
			apDisplay.printWarning('unaligned frame stack not created. Skipped....')
			self.unlockParallel(imgdata.dbid)
			return

		# set align parameters for the image
		framelist = self.dd.getFrameListFromParams(self.ddstack_script_params)
		self.dd.setAlignedSumFrameList(framelist)
		# AlignedCameraEMData needs framelist
		self.dd.setAlignedCameraEMData()
		self.nframes = self.dd.getNumberOfFrameSavedFromImageData(imgdata)
		self.framealigner.setInputNumberOfFrames(self.nframes)
		self.framealigner.setAlignedSumFrameList(framelist)

		self.framealigner.setGPUid(self.params['gpuid'])

		# original ddstack may not have done flat correction
		# if there is no bad pixel
		if self.dd.hasBadPixels():
			self.dd.setUseFrameAlignerFlat(False)
		else:
			self.dd.setUseFrameAlignerFlat(True)
			self.dd.makeDarkNormMrcs()
			gain_ref = self.dd.getNormRefMrcPath()
			per_frame_dark_ref = self.dd.getDarkRefMrcPath()
			self.framealigner.setGainDarkCmd(gain_ref, per_frame_dark_ref)


		# whether the sum can be done in framealigner depends on the framelist
		self.framealigner.setIsUseFrameAlignerSum(self.isUseFrameAlignerSum())
		self.framealigner.setSaveAlignedStack = self.dd.getKeepAlignedStack()

		# Doing the alignment
		self.framealigner.alignFrameStack()

		aligned_sum_path = self.organizeAlignedSum()
		if aligned_sum_path:
			self.organizeAlignedStack()
			self.success_count += 1
		self.unlockParallel(imgdata.dbid)

	def isUseFrameAlignerSum(self):
		return self.dd.isSumSubStackWithFrameAligner()

	def organizeAlignedSum(self):
		'''
		Move local temp results to rundir in the official names
		'''
		# THIS FUNCTION IS COPIED FROM ApDDAlignStacker
		temp_aligned_sumpath = self.temp_aligned_sumpath
		temp_aligned_stackpath = self.temp_aligned_stackpath
		
		apDisplay.printDebug( 'temp_aligned_sumpath= %s' % self.temp_aligned_sumpath)
		apDisplay.printDebug('temp_aligned_stackpath= %s' % self.temp_aligned_stackpath)
		apDisplay.printDebug('self.dd.aligned_sumpath= %s' % self.dd.aligned_sumpath)

		if not os.path.isfile(temp_aligned_sumpath):
			apDisplay.printWarning('Frame alignment FAILED: \n%s not created.' % os.path.basename(temp_aligned_sumpath))
			return False
		else:
			# successful alignment
			if 'alignlabel' not in self.ddstack_script_params.keys() or not self.ddstack_script_params['alignlabel']:
				# appion script params may not have included alignlabel
				self.ddstack_script_params['alignlabel'] = 'a'
			self.convertLogFile()
			if self.dd.getKeepAlignedStack():
				# bug in MotionCorr requires this
				self.dd.updateFrameStackHeaderImageStats(temp_aligned_stackpath)
			if not self.isUseFrameAlignerSum():
				# replace the sum with one corresponds with framelist
				self.sumSubStackWithNumpy(temp_aligned_stackpath,temp_aligned_sumpath)
			# temp_aligned_sumpath should have the right number of frames at this point
			shutil.move(temp_aligned_sumpath,self.dd.aligned_sumpath)
			return self.dd.aligned_sumpath

	def organizeAlignedStack(self):
		'''
		Things to do after alignment.
			1. Save the sum as imagedata
			2. Replace unaligned ddstack
		'''
		# THIS FUNCTION IS BASED ON THE ONE IN ApDDAlignStacker
		apDisplay.printDebug( 'temp_aligned_stackpath= %s' % self.temp_aligned_stackpath)
		apDisplay.printDebug('self.dd.aligned_stackpath= %s' % self.dd.aligned_stackpath)
		apDisplay.printDebug('self.dd.framestackpath= %s' % self.dd.framestackpath)
		self.final_framestackpath = self.dd.framestackpath

		if os.path.isfile(self.dd.aligned_sumpath):
			# Save the alignment result
			self.aligned_imagedata = self.dd.makeAlignedImageData(alignlabel=self.ddstack_script_params['alignlabel'])
			if 'no-keepstack' in self.ddstack_script_params.keys():
				apDisplay.printMsg('removing %s' % self.temp_aligned_stackpath)
				if os.path.isfile(self.temp_aligned_stackpath):
					apFile.removeFile(self.temp_aligned_stackpath)
			else:
				# keep it by replacing the original
				if not os.path.isfile(self.temp_aligned_stackpath):
					apDisplay.printWarning('No aligned stack generated as %s' % self.temp_aligned_stackpath)
				else:
					shutil.move(self.temp_aligned_stackpath,self.dd.aligned_stackpath)
					self.finalStackReplacement()		

	def finalStackReplacement(self):		
			# replace the unaligned stack with aligned_stack
			if os.path.isfile(self.dd.aligned_stackpath):
				# aligned_stackpath exists either because keepstack is true
				apDisplay.printMsg(' Replacing unaligned stack with the aligned one....')
				apFile.removeFile(self.final_framestackpath)
				apDisplay.printMsg('Moving %s to %s' % (self.dd.aligned_stackpath,self.final_framestackpath))
				shutil.move(self.dd.aligned_stackpath,self.final_framestackpath)

	def commitToDatabase(self, imgdata):
		if self.aligned_imagedata != None:
			apDisplay.printMsg('Uploading aligned image as %s' % self.aligned_imagedata['filename'])
			q = appiondata.ApDDAlignImagePairData(source=imgdata,result=self.aligned_imagedata,ddstackrun=self.rundata)
			q.insert()

	def getAllFiles(self):
		if not self.params['mrcnames']:
			# assume that we are in the ddstack rundir
			return os.listdir(os.getcwd())
		else:
			origfiles = self.params['mrcnames'].split(",")
			stackfiles = []
			for origfile in origfiles:
				if origfile[-4:] == '.mrc':
					origfile = origfile[:-4]
				stackfiles.append(origfile+'_st.mrc')
			return stackfiles

	def loopCheckAndProcess(self):
		allfiles = self.getAllFiles()
		images = []
		for filename in allfiles:
			if os.path.isfile(filename) and '_st.mrc' in filename and self.rundata['session']['name'] in filename:
				try:
					imagedata = leginondata.AcquisitionImageData(session=self.rundata['session'],filename=filename[:-7]).query()[0]
				except:
					continue
				images.append(imagedata)
		self.num_stacks = len(images)
		for imagedata in images:
			if self.params['limit'] > 0:
				if self.success_count >= self.params['limit']:
					return True
			# Avoid hidden and trash images
			if apDatabase.getImgCompleteStatus(imagedata) == False:
				apDisplay.printMsg('---------------------------------------------------------')
				apDisplay.printMsg(' Skipping hidden/trashed %s' % imagedata['filename'])
				apDisplay.printMsg('---------------------------------------------------------')
				continue
			apDisplay.printMsg('---------------------------------------------------------')
			apDisplay.printMsg('  Processing %s' % imagedata['filename'])
			apDisplay.printMsg('---------------------------------------------------------')
			self.processImage(imagedata)
			if self.params['commit']:
				self.commitToDatabase(imagedata)
			apDisplay.printMsg('\n')
		return False

	def start(self):
		apDisplay.printMsg('wait= %s' % (self.params['wait'],))
		max_loop_num_trials = 60 * 3
		wait_time = 20
		self.last_num_stacks = 0
		if self.params['wait']:
			num_trials = 0
			while True:
				limit_reached = self.loopCheckAndProcess()
				if limit_reached:
					apDisplay.printMsg('image limit reached. Stoping...')
					break
				if self.num_stacks <= self.last_num_stacks:
					if num_trials >= max_loop_num_trials:
						apDisplay.printColor('Checked for stack file %d times. Finishing....' % max_loop_num_trials,'magenta')
						apDisplay.printMsg('Rerun this script if you know more are coming')
						break
					else:
						num_trials += 1
				else:
					# reset trial number if new stack is found
					num_trials = 0
				apDisplay.printColor('Finished stack file checking in rundir. Will check again in %d seconds' % wait_time,'magenta')
				time.sleep(wait_time)
				self.last_num_stacks = self.num_stacks
		else:				
			self.loopCheckAndProcess()

	def onClose(self):
		self.cleanParallelLock()

if __name__ == '__main__':
	makeStack = CatchUpFrameAlignmentLoop()
	makeStack.start()



