#!/usr/bin/env python
from appionlib import apDDMotionCorrMaker
from appionlib import apDDFrameAligner

class MotionCorrPurdueLoop(apDDMotionCorrMaker.MotionCorrAlignStackLoop):
	'''
	Runing Purdue version of MotionCorr
	'''
	#=======================
	def setupParserOptions(self):
		super(MotionCorrPurdueLoop,self).setupParserOptions()
		self.parser.add_option("--nrw", dest="nrw", type="int", default=1,
			help="Number (1, 3, 5, ...) of frames in running average window. 0 = disabled", metavar="INT")
		self.parser.add_option("--flp", dest="flp", type="int", default=0,
			help="Flip frames along Y axis. (0 = no flip, 1 = flip", metavar="INT")

	def setFrameAligner(self):
		self.framealigner = apDDFrameAligner.MotionCorr_Purdue()

if __name__ == '__main__':
	makeStack = MotionCorrPurdueLoop()
	makeStack.run()
