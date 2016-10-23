#!/usr/bin/env python
from appionlib import apDDAlignStackMaker
from appionlib import apDDFrameAligner
from appionlib import apDisplay

class MotionCorrAlignStackLoop(apDDAlignStackMaker.AlignStackLoop):
	'''
	Base class for MotionCorr implementation that uses gpu
	'''
	#=======================
	def setupParserOptions(self):
		super(MotionCorrAlignStackLoop,self).setupParserOptions()
		self.parser.add_option("--gpuid", dest="gpuid", type="int", default=0,
			help="GPU device id used in gpu processing", metavar="INT")

	#=======================
	def checkConflicts(self):
		super(MotionCorrAlignStackLoop,self).checkConflicts()
		if self.params['align'] and not self.params['defergpu']:
			# We don't have gpu locking
			if self.params['parallel']:
					apDisplay.printWarning('Make sure that you use different gpuid for each parallel process')

	def setFrameAligner(self):
		self.framealigner = apDDFrameAligner.MotionCorr1()

	#=======================
	def preLoopFunctions(self):
		self.setFrameAligner()
		self.framealigner.setFrameAlignOptions(self.params)
		super(MotionCorrAlignStackLoop,self).preLoopFunctions()
		self.dd.setGPUid(self.params['gpuid'])
		self.gpuid = self.params['gpuid']

	def setTempPaths(self):
		# The alignment is done in tempdir (a local directory to reduce network traffic)
		# logpth carries the name of the tempframestack
		bintext = self.getAlignBin()
		self.temp_logpath = self.dd.tempframestackpath[:-4]+bintext+'_Log.txt'
		self.temp_aligned_sumpath = 'temp%s.gpuid_%d_sum.mrc' % (self.hostname, self.dd.gpuid)
		self.temp_aligned_stackpath = 'temp%s.gpuid_%d_aligned_st.mrc' % (self.hostname, self.dd.gpuid)

if __name__ == '__main__':
	makeStack = MotionCorrAlignStackLoop()
	makeStack.run()
