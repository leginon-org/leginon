#!/usr/bin/env python

#pythonlib
import os
import sys
import math
import shutil
import subprocess
#appion
from appionlib import appionLoop2
from appionlib import apDisplay
from appionlib import apDDprocess
from appionlib import apFile
from appionlib import apStack
from appionlib import appiondata

class MakeRawFrameStackLoop(appionLoop2.AppionLoop):
	#=======================
	def setupParserOptions(self):
		self.parser.add_option("--rawarea", dest="rawarea", default=False,
			action="store_true", help="use full area of the raw frame, not leginon image area")
		self.parser.add_option("--useGS", dest="useGS", default=False,
			action="store_true", help="Use Gram-Schmidt process to scale dark image")
		self.parser.add_option("--align", dest="align", default=False,
			action="store_true", help="Make Aligned frame stack")
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="INT")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Binning factor to make the stack (optional)", metavar="INT")
		self.parser.remove_option("--uncorrected")
		self.parser.remove_option("--reprocess")

	#=======================
	def checkConflicts(self):
		if self.params['align']:
			exename = 'dosefgpu_driftcorr'
			driftcorrexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
			if not os.path.isfile(driftcorrexe):
				apDisplay.printError('Drift correction program not available')

	#=======================
	def preLoopFunctions(self):
		self.dd = apDDprocess.initializeDDprocess(self.params['sessionname'],self.params['wait'])
		self.dd.setUseGS(self.params['useGS'])
		self.imageids = []
		if self.params['stackid']:
			self.imageids = apStack.getImageIdsFromStack(self.params['stackid'])

	#=======================
	def processImage(self, imgdata):
		# need to avoid non-frame saved image for proper caching
		if imgdata is None or imgdata['camera']['save frames'] != True:
			apDisplay.printWarning('%s skipped for no-frame-saved\n ' % imgdata['filename'])
			return
		if self.params['stackid'] and imgdata.dbid not in self.imageids:
			return
		imgname = imgdata['filename']
		stackname = imgname+'_st.mrc'

		### first remove any existing stack file
		rundir = self.params['rundir']
		stackfilepath = os.path.join(rundir, stackname)
		apFile.removeFile(stackfilepath)

		### set processing image
		try:
			self.dd.setImageData(imgdata)
		except Exception, e:
			apDisplay.printWarning(e.message)
			return

		self.dd.setNewBinning(self.params['bin'])
		if self.params['align']:
			self.dd.setAlignedCameraEMData()
		### make stack
		self.dd.makeCorrectedRawFrameStack(rundir, self.params['rawarea'])
		if self.params['align']:
			self.dd.alignCorrectedFrameStack(rundir)
			if os.path.isfile(self.dd.aligned_stackpath):
				self.aligned_imagedata = self.dd.makeAlignedImageData()
				apDisplay.printMsg(' Replacing unaligned stack with the aligned one....')
				apFile.removeFile(self.dd.framestackpath)
				shutil.move(self.dd.aligned_stackpath,self.dd.framestackpath)

	def commitToDatabase(self, imgdata):
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
			self.rundata = results[0]
		else:
			if self.params['commit'] is True:
				q.insert()
				self.rundata = q
			else:
				self.rundata = {}

if __name__ == '__main__':
	makeStack = MakeRawFrameStackLoop()
	makeStack.run()



