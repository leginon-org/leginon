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

		# instead of single align bfactor, bft, this has two entries
		self.parser.add_option("--Bft_global",dest="Bft_global",metavar="#",type=float,default=500.0,
                        help=" Global B-Factor for alignment, default 500.0.")

		self.parser.add_option("--Bft_local",dest="Bft_local",metavar="#",type=float,default=150.0,
                        help=" Global B-Factor for alignment, default 150.0.")

		self.parser.add_option("--force_cpu_flat", dest="force_cpu_flat", default=False,
			action="store_true", help="Use cpu to make frame flat field corrrection")

		self.parser.add_option("--rendered_frame_size", dest="rendered_frame_size", type="int", default=1,
			help="Sum this number of saved frames as a rendered frame in alignment", metavar="INT")
		self.parser.add_option("--eer_sampling", dest="eer_sampling", type="int", default=1,
			help="Upsampling eer frames. Fourier binning will be added to returnthe results back", metavar="INT")

	def addBinOption(self):
		self.parser.add_option("--bin",dest="bin",metavar="#",type=float,default="1.0",
			help="Binning factor relative to the dd stack. MotionCor2 takes float value (optional)")

	#=======================
	def checkConflicts(self):
		super(MotionCor2UCSFAlignStackLoop,self).checkConflicts()
		# does NOT keep stack by default
		if self.params['keepstack'] is True:
			apDisplay.printWarning('Frame stack saving not available to MotionCor2 from UCSF')
			self.params['keepstack'] = False

	def getAlignBin(self):
		alignbin = self.params['bin']
		if alignbin > 1:
			bintext = '_%4.1fx' % (alignbin)
		else:
			bintext = ''
		return bintext

	def isUseFrameAlignerFlat(self):
		has_bad_pixels = False
		is_align = self.isAlign()
		has_non_zero_dark = False
		apDisplay.printMsg('frame flip debug: has_bad_pixel %s, is_align %s, has_non_zero_dark %s' % (has_bad_pixels, is_align, has_non_zero_dark))
		if has_bad_pixels or not is_align or has_non_zero_dark:
			self.dd.setUseFrameAlignerFlat(False)
			return False
		else:
			self.dd.setUseFrameAlignerFlat(True)
			return True

	def setFrameAligner(self):
		self.framealigner = apDDFrameAligner.MotionCor2_UCSF()
		# use the first gpuids as gpuid in log. See why this is set here in Issue #5576
		self.params['gpuid'] = int(self.params['gpuids'].split(',')[0].strip())

	def setOtherProcessImageResultParams(self):
		# The alignment is done in tempdir (a local directory to reduce network traffic)
		# include both hostname and gpu to identify the temp output
		#self.temp_aligned_sumpath = 'temp%s.gpuid_%d_sum.mrc' % (self.hostname, self.gpuid)
		super(MotionCor2UCSFAlignStackLoop,self).setOtherProcessImageResultParams()
		self.temp_aligned_dw_sumpath = 'temp%s.gpuid_%d_sum_DW.mrc' % (self.hostname, self.gpuid)
		#self.temp_aligned_stackpath = 'temp%s.gpuid_%d_aligned_st.mrc' % (self.hostname, self.gpuid)
		# NOTE: self.params in self.framealigner alignparam mapping are directly transferred.
		self.framealigner.setKV(self.dd.getKVFromImage(self.dd.image))
		self.framealigner.setTotalRawFrames(self.dd.getNumberOfFrameSaved())
		is_eer = self.dd.image['camera']['eer frames']
		self.framealigner.setIsEer(is_eer)
		if self.params['totaldose'] is not None:
			totaldose = self.params['totaldose']
		else:
			totaldose = apDatabase.getDoseFromImageData(self.dd.image)
		self.framealigner.setTotalDose(totaldose)
		self.has_dose = True
		if not is_eer:
			if totaldose is None and self.params['doseweight']:
				self.has_dose = False
				apDisplay.printWarning('No total dose estimated. Dose weighted alignment will be skipped')
		else:
			if totaldose is None:
				apDisplay.printWarning('Per frame dose of 0.03 e/p is assumed on eer raw frames since no value is entered.')

#		self.temp_aligned_dw_sumpath = 'temp%s.gpuid_%d_sum_DW.mrc' % (self.hostname, self.params['gpuid'])
		if self.isUseFrameAlignerFlat() and not self.params['force_cpu_flat']:
			frame_flip, frame_rotate=self.dd.getImageFrameOrientation()
			self.dd.setUseFrameAlignerYFlip(frame_flip)
			self.dd.setUseFrameAlignerRotate(frame_rotate)
			self.framealigner.setGainYFlip(frame_flip)
			self.framealigner.setGainRotate(frame_rotate)
			if self.dd.hasBadPixels():
				# defect handling
				# defect map here needs to be of the orientation of the frames
				self.dd.makeModifiedDefectMrc()
				modified_defect_map_path = self.dd.getModifiedDefectMrcPath()
				self.framealigner.setDefectMapCmd(modified_defect_map_path)
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
		need_flip = False
		if 'eer' in self.dd.__class__.__name__.lower():
			# output from -InEer is y-flipped even though gain in mrc
			# format is not relative to the eer file
			need_flip = True
		if gain_flip:
			need_flip = not need_flip
		if need_flip:
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
