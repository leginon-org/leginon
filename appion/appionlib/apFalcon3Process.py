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

class FalconProcessing(apDDprocess.DDFrameProcessing):
	def __init__(self,wait_for_new=False):
		super(FalconProcessing,self).__init__(wait_for_new)
		self.setDefaultDimension(4096,4096)
		self.correct_dark_gain = False
		
	def hasNonZeroDark(self):
		return False

	def getNumberOfFrameSavedFromImageData(self,imagedata):
		# Falcon nframes is the number of frame bins
		return imagedata['camera']['nframes']

	def getRefImageData(self,reftype):
		return None

	def getRawFrameDirFromImage(self,imagedata):
		'''
		Falcon3 raw frames are saved as image stack for feeding into gpu program.
		RawFrameDir here is actually the filename with mrc extension.
		'''
		# strip off DOS path in rawframe directory name if included
		rawframename = imagedata['camera']['frames name'].split('\\')[-1]
		if not rawframename:
			apDisplay.printWarning('No Raw Frame Saved for %s' % imagedata['filename'])
		session_frame_path = self.getSessionFramePathFromImage(imagedata)
		# frame stackfile is image filename plus '.frames.mrc'
		apDisplay.printMsg('frame extension is %s' % self.extname)
		rawframedir = os.path.join(session_frame_path,'%s.frames.%s' % (imagedata['filename'],self.extname))
		if not self.waitForPathExist(rawframedir,30):
			apDisplay.printError('Raw Frame Dir %s does not exist.' % rawframedir)
		apDisplay.printMsg('Raw Frame Dir from image is %s' % (rawframedir,))
		return rawframedir

	def loadOneRawFrame(self,rawframe_path,frame_number):
		'''
		Load from rawframe_path (a stack file) the chosen frame of the current image.
		'''
		try:
			bin = self.camerainfo['binning']
			offset = self.camerainfo['offset']
			dimension = self.camerainfo['dimension']
		except:
			# default
			bin = {'x':1,'y':1}
			offset = {'x':0,'y':0}
			dimension = self.getDefaultDimension()
		crop_end = {'x': offset['x']+dimension['x']*bin['x'], 'y':offset['y']+dimension['y']*bin['y']}
		apDisplay.printMsg('Frame path: %s' %  rawframe_path)
		waitmin = 0
		while not os.path.exists(rawframe_path):
			if self.waittime < 0.1:
				apDisplay.printWarning('Frame File %s does not exist.' % rawframe_path)
				return False
			apDisplay.printWarning('Frame File %s does not exist. Wait for 3 min.' % rawframe_path)
			time.sleep(180)
			waitmin += 3
			apDisplay.printMsg('Waited for %d min so far' % waitmin)
			if waitmin > self.waittime:
				return False
		return self.readImageFrame(rawframe_path,frame_number,offset,crop_end,bin)

	def readImageFrame(self,framestack_path,frame_number,offset,crop_end,bin):
		'''
		Read a frame from the image stack
		'''
		a = mrc.read(framestack_path,frame_number)
		a = numpy.asarray(a,dtype=numpy.float32)

		# modify the size if needed
		a = self.modifyFrameImage(a,offset,crop_end,bin)
		return a

	def getFrameNamePattern(self,framedir):
		pass

	def getFrameNameFromNumber(self,frame_number):
		return '%s%d.raw' % (self.framename_pattern,frame_number)

	def getUsedFramesFromImageData(self,imagedata):
		return range(self.getNumberOfFrameSavedFromImageData(imagedata))

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
	dd.setImageId(5596287)
	start_frame = 0
	nframe = 5
	framelist = range(start_frame,start_frame+nframe)
	corrected = dd.correctFrameImage(framelist)
	mrc.write(corrected,'corrected_frame%d_%d.mrc' % (start_frame,nframe))
