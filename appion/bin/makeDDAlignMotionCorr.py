#!/usr/bin/env python
from appionlib import apDDAlignStackMaker
from appionlib import apDDFrameAligner

class MotionCorrAlignStackLoop(apDDAlignStackMaker.AlignStackLoop):
	#=======================
	def setupParserOptions(self):
		super(MotionCorrAlignStackLoop,self).setupParserOptions()
		self.parser.add_option("--gpuid", dest="gpuid", type="int", default=0,
			help="GPU device id used in gpu processing", metavar="INT")
		self.parser.add_option("--nrw", dest="nrw", type="int", default=1,
			help="Number (1, 3, 5, ...) of frames in running average window. 0 = disabled", metavar="INT")
		

	#=======================
	def checkConflicts(self):
		super(MotionCorrAlignStackLoop,self).checkConflicts()
		if self.params['align'] and not self.params['defergpu']:
			# We don't have gpu locking
			if self.params['parallel']:
					apDisplay.printWarning('Make sure that you use different gpuid for each parallel process')

	def setFrameAligner(self):
		self.framealigner = apDDFrameAligner.MotionCorr2_UCSF()

	#=======================
	def preLoopFunctions(self):
		self.setFrameAligner()
		self.framealigner.setFrameAlignOptions(self.params)
		super(MotionCorrAlignStackLoop,self).preLoopFunctions()
		self.dd.setGPUid(self.params['gpuid'])

if __name__ == '__main__':
	makeStack = MotionCorrAlignStackLoop()
	makeStack.run()
