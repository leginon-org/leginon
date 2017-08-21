#!/usr/bin/env python

#pythonlib
import os
import sys
import math
import shutil
import subprocess
import multiprocessing as mp
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
		self.parser.add_option("--compress", dest="compress", default=False,
			action="store_true", help="Compress raw frames after stack making")
		self.parser.add_option("--override_db", dest="override_db", default=False,
			action="store_true", help="Override database for bad rows, columns, and image flips")
		# String
		self.parser.add_option("--framepath", dest="framepath",
			help="Force Session Frame Path to this", metavar="PATH")
		# Integer
		self.parser.add_option("--refimgid", dest="refimgid", type="int",
			help="Specify a corrected image to do gain/dark correction with", metavar="INT")

		self.parser.add_option("--trim", dest="trim", type="int", default=0,
			help="Trim edge off after frame stack gain/dark correction", metavar="INT")
		
	### add options here
		self.parser.add_option('--clip', dest='clip', default=None, type='int', help= "Clip 'clip' pixels from the raw frames and pad back out with the mean.")
		self.parser.add_option('--bad_cols', dest='bad_cols', default='', help= "Bad columns in raw frames")
		self.parser.add_option('--bad_rows', dest='bad_rows', default='', help= "Bad rows in raw frames")
		self.parser.add_option("--flipgain", dest="flipgain", default=False,
			action="store_true", help="Flip dark and bright top to bottom before correcting frames")


	#=======================
	def checkConflicts(self):
			# Stack cleaning should not be done in some cases
			if not self.params['keepstack']:
					apDisplay.printError('Why making only gain/dark-corrected ddstacks but not keeping them')

	def getFrameType(self):
		# set how frames are saved depending on what is found in the basepath
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		return ddinfo.getRawFrameTypeFromSession(sessiondata)

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
		self.dd.clip=self.params['clip']
		self.first_image = True
		if self.params['override_db'] is True:
			self.dd.override_db = True
			self.dd.badcols = [int(n) for n in self.params['bad_cols'].split(',')]
			self.dd.badrows = [int(n) for n in self.params['bad_rows'].split(',')]
			self.dd.flipgain = self.params['flipgain']
			
		# specification that is not default
		if self.params['framepath']:
			self.dd.setForcedFrameSessionPath(self.params['framepath'])
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
		self.nframes = self.dd.getNumberOfFrameSavedFromImageData(imgdata)

		# place holder for alignment result path setting
		self.setOtherProcessImageResultParams()

		### first remove any existing stack file
		apFile.removeFile(self.dd.framestackpath)
		apFile.removeFile(self.dd.tempframestackpath)

		if not self.isUseFrameAlignerFlat():
			### make stack named as self.dd.tempframestackpath
			self.dd.makeCorrectedFrameStack(self.params['rawarea'])
		else:
			self.dd.makeRawFrameStackForOneStepCorrectAlign(self.params['rawarea'])

		# place holder for alignment
		self.otherProcessImage(imgdata)

		# Clean up
		if not self.params['keepstack']:
			apFile.removeFile(self.dd.framestackpath)
		self.otherCleanUp(imgdata)

		# Compress the raw frames
		if self.params['commit']:
			self.postProcessOriginalFrames(imgdata)
			self.postProcessReferences(imgdata)

	def	getUseBufferFromImage(self, imgdata):
		db_use_buffer = ddinfo.getUseBufferFromImage(imgdata)
		if db_use_buffer is True or self.dd.getAllAlignImagePairData(None,imgdata):
			return False
		else:
			return db_use_buffer

	def postProcessReferences(self, imgdata):
		if self.getUseBufferFromImage(imgdata):
			head_dir = self.dd.getSessionFramePathFromImage(imgdata)
			ref_dir = os.path.join(head_dir, 'references')
			to_dir = imgdata['session']['frame path']
			# Do not remove sent file since there will be updates nor delay running.
			j = mp.Process(target=apFile.rsync, args=[ref_dir, to_dir, False, 0])
			j.start()
		return

	def postProcessOriginalFrames(self, imgdata):
		if self.first_image:
			delay = 30
			self.first_image = False
		else:
			delay = 5
		raw_frame_path = self.dd.getRawFrameDir()
		head_dir = os.path.split(raw_frame_path)[0]
		to_dir = imgdata['session']['frame path']
		if not self.params['compress']:
			# just rsync from buffer
			if self.getUseBufferFromImage(imgdata):
				j = mp.Process(target=apFile.rsync, args=[raw_frame_path, to_dir, False, delay])
				j.start()
			return

		# compress before rsync
		if self.getUseBufferFromImage(imgdata):
			# make permanent frame path
			try:
				fileutil.mkdirs(to_dir)
			except:
				apDisplay.printWarning('Error making destination %s' % to_dir)
				to_dir = None

		if 'Falcon' in self.dd.__class__.__name__:
			if self.getUseBufferFromImage(imgdata):
				apDisplay.printMsg('Falcon does not compress well. skip compression')
				j = mp.Process(target=apFile.rsync, args=[raw_frame_path, to_dir, False, delay])
		else:
			j = mp.Process(target=apFile.compress_and_rsync, args=[raw_frame_path, to_dir, False, delay])
		j.start()
		apDisplay.printColor('Sent multiprocess job','green')

	def isAlign(self):
		return False

	def isUseFrameAlignerFlat(self):
		self.dd.setUseFrameAlignerFlat(False)
		return False

	def setOtherProcessImageResultParams(self):
		# place holder for alignment result path setting
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



