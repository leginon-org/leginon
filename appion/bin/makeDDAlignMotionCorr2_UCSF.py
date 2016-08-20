#!/usr/bin/env python
from appionlib import apDDAlignStackMaker
from appionlib import apDDFrameAligner
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apDisplay

class MotionCorrAlignStackLoop(apDDAlignStackMaker.AlignStackLoop):
	#=======================
	def setupParserOptions(self):
		super(MotionCorrAlignStackLoop,self).setupParserOptions()

		self.parser.add_option("--gpuid", dest="gpuid", type="int", default=0,
			help="GPU device id used in gpu processing", metavar="INT")

		self.parser.add_option("--nrw", dest="nrw", type="int", default=1,
			help="Number (1, 3, 5, ...) of frames in running average window. 0 = disabled", metavar="INT")

		self.parser.add_option("--FmRef", dest="FmRef",type="int",default=0,
			help="Specify which frame to be the reference to which all other frames are aligned. Default 0 is aligned to the first frame, other values aligns to the central frame.", metavar="#")

		self.parser.add_option("--Iter", dest="Iter",type="int",default=5,
			help="Maximum iterations for iterative alignment, default is 7.")

                self.parser.add_option("--Tol", dest="Tol",type="float",default=0.5,
                        help="Tolerance for iterative alignment, in pixels", metavar="#")

		self.parser.add_option("--Patch",dest="Patch",metavar="#,#",type=str,default=0,
			help="Number of patches to be used for patch based alignment. Default 0,0 corresponds to full frame alignment.")

		self.parser.add_option("--MaskCent",dest="MaskCent",metavar="#,#",type=str,default="0,0",
			help="Coordinates for center of subarea that will be used for alignment. Default 0,0 corresponds to center coordinate.")

		self.parser.add_option("--MaskSize",dest="MaskSize",metavar="#,#",type=str,default="0,0",
			help="The size of subarea that will be used for alignment, default 1.0 1.0 corresponding full size.")

		self.parser.add_option("--Throw",dest="Throw",metavar="#",type=int,default=0,
                        help="Throw initial number of frames")

		self.parser.add_option("--Trunc",dest="Trunc",metavar="#",type=int,default=0,
                        help="Truncate last number of frames")

		### making these into general options
#		self.parser.add_option("--doseweight",dest="doseweight",metavar="bool", default=False, 
#			action="store_true", help="dose weight the frame stack, according to Tim / Niko's curves")

#		self.parser.add_option("--FmDose",dest="FmDose",metavar="float",type=float,
#                        help="Frame dose in e/A^2. If not specified, will get value from database")


	#=======================
	def checkConflicts(self):
		super(MotionCorrAlignStackLoop,self).checkConflicts()
		if self.params['align'] and not self.params['defergpu']:
			# We don't have gpu locking
			if self.params['parallel']:
					apDisplay.printWarning('Make sure that you use different gpuid for each parallel process')
		
		# does NOT keep stack by default
		if self.params['keepstack'] is True:
			self.params['keepstack'] = False

	def setFrameAligner(self):
		self.framealigner = apDDFrameAligner.MotionCorr2_UCSF()

	#=======================
	def preLoopFunctions(self):

		ddprocessor = apDDprocess.DDFrameProcessing()

		# aligner functions
		self.setFrameAligner()
		self.framealigner.setFrameAlignOptions(self.params)
		super(MotionCorrAlignStackLoop,self).preLoopFunctions()
		ddprocessor.setGPUid(self.params['gpuid'])
		
	def setOtherProcessImageResultParams(self):
		super(MotionCorrAlignStackLoop,self).setOtherProcessImageResultParams()
		self.framealigner.setKV(self.dd.getKVFromImage(self.dd.image))
		self.framealigner.setTotalFrames(self.dd.getNumberOfFrameSaved())
		if self.params['totaldose'] is not None:
			self.framealigner.setTotalDose(self.params['totaldose'])
		else:
			self.framealigner.setTotalDose(apDatabase.getDoseFromImageData(self.dd.image))
#		self.temp_aligned_dw_sumpath = 'temp%s.gpuid_%d_sum_DW.mrc' % (self.hostname, self.params['gpuid'])
#		self.framealigner.setFmDose()


if __name__ == '__main__':
	makeStack = MotionCorrAlignStackLoop()
	makeStack.run()
