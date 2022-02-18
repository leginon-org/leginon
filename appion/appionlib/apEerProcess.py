#!/usr/bin/env python

import os
import numpy
from pyami import mrc
from appionlib import apFalcon3Process,apDisplay

from pyami import numpil

# testing options
save_jpg = False
debug = False
ddtype = 'falcon'

class EerProcessing(apFalcon3Process.FalconProcessing):
	def __init__(self,wait_for_new=False):
		super(EerProcessing,self).__init__(wait_for_new)
		self.setDefaultDimension(4096,4096)
		self.correct_dark_gain = True
		
	def getNumberOfFrameSavedFromImageData(self,imagedata):
		# Falcon EER nframes is the number of rolling-shutter frames
		return imagedata['camera']['nframes']

	def getRefImageData(self,reftype):
		if reftype == 'dark':
			# eer format has zero dark
			return None
		imagedata = self.getCorrectedImageData()
		return imagedata[reftype]

	def loadOneRawFrame(self,rawframe_path,frame_number):
		'''
		Load from rawframe_path (a stack file) the chosen frame of the current image.
		'''
		raise NotImplemented('No eer support to read frame')

	def readImageFrame(self,framestack_path,frame_number,offset,crop_end,bin):
		'''
		Read a frame from the image stack
		'''
		raise NotImplemented('No eer support to read frame')

	def getFrameNamePattern(self,framedir):
		pass

	def getFrameNameFromNumber(self,frame_number):
		raise NotImplemented('No eer support to read frame')

	def getUsedFramesFromImageData(self,imagedata):
		# all saved frames
		return range(self.getNumberOfFrameSavedFromImageData(imagedata))

	def correctFrameImage(self,framelist,use_full_raw_area=False):
		return self.__correctFrameImage(framelist,use_full_raw_area)	

	def __correctFrameImage(self,framelist,use_full_raw_area=False):
		raise NotImplemented('No eer support to read frame')

if __name__ == '__main__':
	dd = EerProcessing()
	dd.setImageId(3859)
	print dd.getRawFrameDirFromImage(dd.image)
