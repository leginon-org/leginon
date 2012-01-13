#!/usr/bin/env python

#pythonlib
import os
import sys
import math
#appion
from appionlib import appionLoop2
from appionlib import apDDprocess
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apStack

class MakeRawFrameStackLoop(appionLoop2.AppionLoop):
	#=======================
	def setupParserOptions(self):
		self.parser.add_option("--rawarea", dest="rawarea", default=False,
			action="store_true", help="use full area of the raw frame, not leginon image area")
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="INT")
		self.parser.remove_option("--uncorrected")
		self.parser.remove_option("--reprocess")

	#=======================
	def checkConflicts(self):
		pass

	#=======================
	def preLoopFunctions(self):
		self.dd = apDDprocess.DirectDetectorProcessing()
		self.imageids = []
		if self.params['stackid']:
			self.imageids = apStack.getImageIdsFromStack(self.params['stackid'])

	#=======================
	def processImage(self, imgdata):
		# need to avoid non-frame saved image for proper caching
		if imgdata is None or imgdata['camera']['save frames'] != True:
			self.dd.log.write('%s skipped for no-frame-saved\n ' % imgdata['filename'])
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

		### run batchboxer
		self.dd.makeCorrectedRawFrameStack(rundir, self.params['rawarea'])

	def commitToDatabase(self, imgdata):
		pass

if __name__ == '__main__':
	makeStack = MakeRawFrameStackLoop()
	makeStack.run()



