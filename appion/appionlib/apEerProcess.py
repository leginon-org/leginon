#!/usr/bin/env python

import os
import numpy
from pyami import mrc
from appionlib import apDDprocess,apDisplay

from pyami import numpil

# testing options
save_jpg = False
debug = False
ddtype = 'falcon'

class EerProcessing(apDDprocess.DDFrameProcessing):
	def __init__(self,wait_for_new=False):
		super(EerProcessing,self).__init__(wait_for_new)
		self.setDefaultDimension(4096,4096)
		self.correct_dark_gain = True
		
	def hasNonZeroDark(self):
		return False

	def getNumberOfFrameSavedFromImageData(self,imagedata):
		# Falcon EER nframes is the number of rolling-shutter frames
		return imagedata['camera']['nframes']

	def getRefImageData(self,reftype):
		if reftype == 'dark':
			# eer format has zero dark
			return None
		imagedata = self.getCorrectedImageData()
		return imagedata[reftype]

	def getRawFrameDirFromImage(self,imagedata):
		'''
		Falcon4 raw frames are saved as image stack for feeding into gpu program.
		RawFrameDir here is actually the filename with eer extension.
		'''
		# strip off DOS path in rawframe directory name if included
		rawframename = imagedata['camera']['frames name'].split('\\')[-1]
		if not rawframename:
			apDisplay.printWarning('No Raw Frame Saved for %s' % imagedata['filename'])
		session_frame_path = self.getSessionFramePathFromImage(imagedata)
		# frame stackfile is image filename plus '.frames.eer'
		rawframedir = os.path.join(session_frame_path,'%s.frames.eer' % imagedata['filename'])
		if not self.waitForPathExist(rawframedir,30):
			apDisplay.printError('Raw Frame movie %s does not exist.' % rawframedir)
		apDisplay.printMsg('Raw Frame movie from image is %s' % (rawframedir,))
		return rawframedir

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
