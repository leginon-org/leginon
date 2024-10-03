#!/usr/bin/env python

import numpy
from pyami import mrc,imagefun
from appionlib import apDDprocess,apDisplay
import os
try:
	import tifffile
except:
	apDisplay.printError('Need tifffile to use apDEprocess module')

# testing options
save_jpg = False
debug = False
ddtype = 'thin'

class DEProcessing(apDDprocess.DDFrameProcessing):
	def __init__(self,wait_for_new=False):
		super(DEProcessing,self).__init__(wait_for_new)
		self.setDefaultDimension(4096,3072)
		self.correct_dark_gain = True
		
	def hasNonZeroDark(self):
		return True

	def getNumberOfFrameSavedFromImageData(self,imagedata):
		# DE nframes is the true base frame numbers saved
		return imagedata['camera']['nframes']

	def getFrameNameFromNumber(self,frame_number):
		return 'RawImage_%d.tif' % frame_number

	def handleOldFrameOrientation(self):
		return True, 2

	def readFrameImage(self,frameimage_path,offset,crop_end,bin):
		tif = tifffile.TIFFfile(frameimage_path)
		a = tif.asarray()
		a = self.modifyFrameImage(a,offset,crop_end,bin)
		return a

	def getRawFrameDirFromImage(self,imagedata):
		'''
		K2 raw frames are saved as image stack for feeding into gpu program.
		RawFrameDir here is actually the filename with mrc extension.
		'''
		# strip off DOS path in rawframe directory name if included
		rawframename = imagedata['camera']['frames name'].split('\\')[-1]
		if not rawframename:
			apDisplay.printWarning('No Raw Frame Saved for %s' % imagedata['filename'])
		session_frame_path = self.getSessionFramePathFromImage(imagedata)
		# frame stackfile is image filename plus '.frames.mrc'
		rawframedir = os.path.join(session_frame_path,'%s.frames.mrc' % imagedata['filename'])
		if not self.waitForPathExist(rawframedir,30):
			apDisplay.printError('Raw Frame Dir %s does not exist.' % rawframedir)
		return rawframedir

	def loadOneRawFrame(self,rawframe_path,frame_number):
		'''
		Load one raw frame depending on the rawframetype
		'''
		if self.getRawFrameType() == 'singles':
			return super(DEProcessing,self).loadOneRawFrame(rawframe_path,frame_number)
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


if __name__ == '__main__':
	dd = DEProcessing()
	dd.setImageId(1640790)
	start_frame = 0
	nframe = 5
	framelist = list(range(start_frame,start_frame+nframe))
	corrected = dd.correctFrameImage(framelist)
	mrc.write(corrected,'corrected_frame%d_%d.mrc' % (start_frame,nframe))
