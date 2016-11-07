#!/usr/bin/env python

#pythonlib
import os
import sys
import math
import shutil
import subprocess
#pyami
from pyami import fileutil, mrc
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
		self.parser.add_option("--rawarea", dest="rawarea", default=False,
			action="store_true", help="use full area of the raw frame, not leginon image area")
		self.parser.add_option("--useGS", dest="useGS", default=False,
			action="store_true", help="Use Gram-Schmidt process to scale dark image")
		self.parser.add_option("--square", dest="square", default=False,
			action="store_true", help="Output square images")
		self.parser.add_option("--no-cyclechannels", dest="cyclechannels", default=True,
			action="store_false", help="Use only one reference channel for gain/dark correction")
		self.parser.add_option("--refimgid", dest="refimgid", type="int",
			help="Specify a corrected image to do gain/dark correction with", metavar="INT")
		self.parser.add_option("--trim", dest="trim", type="int", default=0,
			help="Trim edge off after frame stack gain/dark correction", metavar="INT")
		self.parser.add_option("--total_dose", dest="total_dose", type=float,
			help="Total dose for all frames, if value not saved in database (optional)", metavar="")
		self.parser.add_option("--expweight", dest="expweight", default=False, action="store_true",
			help="turns on exposure weighting, dont specify option to turn off exposure weighting", metavar="")
		self.parser.add_option("--expperframe", dest="expperframe", type=float,
			help="Exposure per frame in electrons per Angstrom squared", metavar="")

	#=======================
	def checkConflicts(self):
		exename = 'unblur_openmp.exe'
		exe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(exe):
			apDisplay.printError('Correction program "%s" not available' % exename)
		# Local directory creating and permission checking
		if self.params['tempdir']:
			try:
				fileutil.mkdirs(self.params['tempdir'])
				os.access(self.params['tempdir'],os.W_OK|os.X_OK)
			except:
				raise
				apDisplay.printError('Local temp directory not writable')


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
		self.dd.setDoseFDriftCorrOptions(self.params)
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
		self.dd.setAlignedCameraEMData()
		framelist = self.dd.getFrameList(self.params)
		self.dd.setAlignedSumFrameList(framelist)

		### first remove any existing stack file
		apFile.removeFile(self.dd.framestackpath)
		apFile.removeFile(self.dd.tempframestackpath)
		
		### only work on frame stacks in which all the frames have been properly saved
		total_frames = self.dd.getNumberOfFrameSaved()
		framepath = self.dd.getRawFrameDirFromImage(imgdata)
		total_frames_actual = mrc.read_file_header(framepath)['mz']
		if total_frames != total_frames_actual:
			apDisplay.printWarning("number of frames saved in database is NOT equal to the number of frames actually written to raw frame .mrc file")
			return

		if self.dd.hasBadPixels():
			self.dd.setUseFrameAlignerFlat(False)
			### make stack
			self.dd.makeCorrectedFrameStack(self.params['rawarea'])
		else:
			self.dd.setUseFrameAlignerFlat(True)
			self.dd.makeRawFrameStackForOneStepCorrectAlign(self.params['rawarea'])
		# Align
		# make a fake log so that catchUpDDAlign will know that frame stack is done
		fakelog = self.dd.framestackpath[:-4]+'_Log.txt'
		f = open(fakelog,'w')
		f.write('Fake log to mark the unaligned frame stack as done\n')
		f.close()
		# Doing the alignment
		if self.dd.getUseFrameAlignerFlat():
			self.dd.gainCorrectAndAlignFrameStack()
		else:
			self.dd.unblurFiltCorrectedFrameStack(self.params, imgdata)
		if os.path.isfile(self.dd.aligned_sumpath):
			self.aligned_imagedata = self.dd.makeAlignedImageData(alignlabel=self.params['alignlabel'])
			apFile.removeFile(self.dd.aligned_sumpath)
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
		qparams = appiondata.ApDDStackParamsData(preset=self.params['preset'],align=True,bin=self.params['bin'],stack=stackdata)
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



