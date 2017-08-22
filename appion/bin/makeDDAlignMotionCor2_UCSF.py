#!/usr/bin/env python
import os
import shutil
from appionlib import apDDMotionCorrMaker
from appionlib import apDDFrameAligner
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apDisplay

class MotionCor2UCSFAlignStackLoop(apDDMotionCorrMaker.MotionCorrAlignStackLoop):
	#=======================
	def setupParserOptions(self):
		super(MotionCor2UCSFAlignStackLoop,self).setupParserOptions()

		#self.parser.remove_option('gpuid')
		self.parser.add_option("--gpuids", dest="gpuids", default='0')
		self.parser.add_option("--nrw", dest="nrw", type="int", default=1,
			help="Number (1, 3, 5, ...) of frames in running average window. 0 = disabled", metavar="INT")

		self.parser.add_option("--FmRef", dest="FmRef",type="int",default=0,
			help="Specify which frame to be the reference to which all other frames are aligned. Default 0 is aligned to the first frame, other values aligns to the central frame.", metavar="#")

		self.parser.add_option("--Iter", dest="Iter",type="int",default=7,
			help="Maximum iterations for iterative alignment, default is 7.")

                self.parser.add_option("--Tol", dest="Tol",type="float",default=0.5,
                        help="Tolerance for iterative alignment, in pixels", metavar="#")

		self.parser.add_option("--Patchrows",dest="Patchrows",metavar="#",type=int,default="0",
			help="Number of patches divides the y-axis to be used for patch based alignment. Default 0 corresponds to full frame alignment in the direction.")

		self.parser.add_option("--Patchcols",dest="Patchcols",metavar="#",type=int,default="0",
			help="Number of patches divides the x-axis to be used for patch based alignment. Default 0 corresponds to full frame alignment in the direction.")

		self.parser.add_option("--MaskCentrow",dest="MaskCentrow",metavar="#",type=int,default="0",
			help="Y Coordinates for center of subarea that will be used for alignment. Default 0 corresponds to center coordinate.")

		self.parser.add_option("--MaskCentcol",dest="MaskCentcol",metavar="#",type=int,default="0",
			help="X Coordinate for center of subarea that will be used for alignment. Default 0 corresponds to center coordinate.")

		self.parser.add_option("--MaskSizecols",dest="MaskSizecols",metavar="#",type=float,default="1.0",
			help="The X size of subarea that will be used for alignment, default 1.0 1.0 corresponding full size.")
		self.parser.add_option("--MaskSizerows",dest="MaskSizerows",metavar="#",type=float,default="1.0",
			help="The Y size of subarea that will be used for alignment, default 1.0 corresponding full size.")

		self.parser.add_option("--Bft",dest="Bft",metavar="#",type=float,default=100,
                        help=" B-Factor for alignment, default 100.")

		self.parser.add_option("--force_cpu_flat", dest="force_cpu_flat", default=False,
			action="store_true", help="Use cpu to make frame flat field corrrection")

	#=======================
	def checkConflicts(self):
		super(MotionCor2UCSFAlignStackLoop,self).checkConflicts()
		# does NOT keep stack by default
		if self.params['keepstack'] is True:
			apDisplay.printWarning('Frame stack saving not available to MotionCor2 from UCSF')
			self.params['keepstack'] = False
		# use the first gpuids as gpuid in log
		self.params['gpuid'] = int(self.params['gpuids'].split(',')[0].strip())

	def isUseFrameAlignerFlat(self):
		if self.dd.hasBadPixels() or not self.isAlign() or self.dd.hasNonZeroDark():
			self.dd.setUseFrameAlignerFlat(False)
			return False
		else:
			self.dd.setUseFrameAlignerFlat(True)
			return True

	def setFrameAligner(self):
		self.framealigner = apDDFrameAligner.MotionCor2_UCSF()

	def setOtherProcessImageResultParams(self):
		# The alignment is done in tempdir (a local directory to reduce network traffic)
		# include both hostname and gpu to identify the temp output
		#self.temp_aligned_sumpath = 'temp%s.gpuid_%d_sum.mrc' % (self.hostname, self.gpuid)
		super(MotionCor2UCSFAlignStackLoop,self).setOtherProcessImageResultParams()
		self.temp_aligned_dw_sumpath = 'temp%s.gpuid_%d_sum_DW.mrc' % (self.hostname, self.gpuid)
		#self.temp_aligned_stackpath = 'temp%s.gpuid_%d_aligned_st.mrc' % (self.hostname, self.gpuid)
		self.framealigner.setKV(self.dd.getKVFromImage(self.dd.image))
		self.framealigner.setTotalFrames(self.dd.getNumberOfFrameSaved())
		if self.params['totaldose'] is not None:
			totaldose = self.params['totaldose']
		else:
			totaldose = apDatabase.getDoseFromImageData(self.dd.image)
		self.framealigner.setTotalDose(totaldose)
		if totaldose is None and self.params['doseweight']:
			self.has_dose = False
			apDisplay.printWarning('No total dose estimated. Dose weighted alignment will be skipped')
		else:
			self.has_dose = True
#		self.temp_aligned_dw_sumpath = 'temp%s.gpuid_%d_sum_DW.mrc' % (self.hostname, self.params['gpuid'])
		if self.isUseFrameAlignerFlat() and not self.params['force_cpu_flat']:
			frame_flip, frame_rotate=self.dd.getImageFrameOrientation()
			self.dd.setUseFrameAlignerYFlip(frame_flip)
			self.dd.setUseFrameAlignerRotate(frame_rotate)
			self.framealigner.setGainYFlip(frame_flip)
			self.framealigner.setGainRotate(frame_rotate)
		else:
			self.dd.setUseFrameAlignerYFlip(False)
			self.dd.setUseFrameAlignerRotate(0)
			self.framealigner.setGainYFlip(False)
			self.framealigner.setGainRotate(0)

	def organizeAlignedSum(self):
		'''
		Move local temp results to rundir in the official names
		'''
		temp_aligned_sumpath = self.temp_aligned_sumpath
		temp_aligned_dw_sumpath = self.temp_aligned_dw_sumpath
		gain_flip, gain_rotate = self.framealigner.getGainModification()
		if gain_flip:
			apDisplay.printMsg('Flipping the aligned sum back')
			self.imageYFlip(temp_aligned_sumpath)
			self.imageYFlip(temp_aligned_dw_sumpath)
		if gain_rotate:
			apDisplay.printMsg('Rotating the aligned sum back')
			self.imageRotate(temp_aligned_sumpath, gain_rotate)
			self.imageRotate(temp_aligned_dw_sumpath, gain_rotate)
		# dose weighted result handled here
		if os.path.isfile(temp_aligned_sumpath):
			if self.params['doseweight'] is True and self.has_dose:
				shutil.move(temp_aligned_dw_sumpath,self.dd.aligned_dw_sumpath)
		return super(MotionCor2UCSFAlignStackLoop,self).organizeAlignedSum()

	def organizeAlignedStack(self):
		'''
		Things to do after alignment.
			1. Save the sum as imagedata
			2. Replace unaligned ddstack
		'''
		if os.path.isfile(self.dd.aligned_sumpath):
			if self.params['doseweight'] is True and self.has_dose:
				self.params['align_dw_label'] = self.params['alignlabel']+"-DW"
				self.aligned_dw_imagedata = self.dd.makeAlignedDWImageData(alignlabel=self.params['align_dw_label'])

		super(MotionCor2UCSFAlignStackLoop,self).organizeAlignedStack()

if __name__ == '__main__':
	makeStack = MotionCor2UCSFAlignStackLoop()
	makeStack.run()
