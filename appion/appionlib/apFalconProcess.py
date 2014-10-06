#!/usr/bin/env python

import os
import numpy
from pyami import mrc
from appionlib import apDDprocess,apDisplay

from pyami import numraw
from pyami import numpil

# testing options
save_jpg = False
debug = False
ddtype = 'falcon'

class FalconProcessing(apDDprocess.DDFrameProcessing):
	def __init__(self,wait_for_new=False):
		super(FalconProcessing,self).__init__(wait_for_new)
		self.setDefaultDimension(4096,4096)
		self.correct_dark_gain = False
		
	def getNumberOfFrameSavedFromImageData(self,imagedata):
		# Falcon nframes is the number of frame bins
		return imagedata['camera']['nframes']

	def getRefImageData(self,reftype):
		return None

	def getFrameNamePattern(self,framedir):
		filenames = os.listdir(framedir)
		head = 'Intermediate'
		while len(filenames) < 3 and filenames[0].startswith(head):
			time.sleep(5)
			filenames = os.listdir(framedir)
		print filenames
		for i,t0 in enumerate(filenames[0]):
			if t0 != filenames[1][i]:
				break
		self.framename_pattern = filenames[0][:i]

	def getFrameNameFromNumber(self,frame_number):
		return '%s%d.raw' % (self.framename_pattern,frame_number)

	def readFrameImage(self,frameimage_path,offset,crop_end,bin):
		a = numraw.read(frameimage_path)
		a = a.astype(numpy.int16)
		a = self.modifyFrameImage(a,offset,crop_end,bin)
		return a

	def handleOldFrameOrientation(self):
		return False, 3

	def makeCorrectedFrameStack(self, use_full_raw_area=False):
		'''
		only works with cpu
		'''
		return self.makeCorrectedFrameStack_cpu(use_full_raw_area)

	def correctFrameImage(self,framelist,use_full_raw_area=False):
		return self.__correctFrameImage(framelist,use_full_raw_area)	

	def __correctFrameImage(self,framelist,use_full_raw_area=False):
		# load raw frames
		corrected_array = self.sumupFrames(self.rawframe_dir,framelist)
		if corrected_array is False:
			return False
		if save_jpg:
			numpil.write(corrected,'%s_gain_corrected.jpg' % ddtype,'jpeg')
		return corrected_array

if __name__ == '__main__':
	dd = FalconProcessing()
	dd.setImageId(1640790)
	start_frame = 0
	nframe = 5
	framelist = range(start_frame,start_frame+nframe)
	corrected = dd.correctFrameImage(framelist)
	mrc.write(corrected,'corrected_frame%d_%d.mrc' % (start_frame,nframe))
