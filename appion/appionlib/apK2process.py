#!/usr/bin/env python

import numpy
from pyami import mrc,imagefun
from leginon import leginondata
from appionlib import apDDprocess,apDisplay

# testing options
save_jpg = False
debug = False
ddtype = 'thin'

class GatanK2Processing(apDDprocess.DDFrameProcessing):
	def __init__(self,wait_for_new=False):
		super(GatanK2Processing,self).__init__(wait_for_new)
		self.setDefaultDimension(3840,3712)
		self.correct_dark_gain = True
		
	def getNumberOfFrameSavedFromImageData(self,imagedata):
		return int(imagedata['camera']['frame rate']*imagedata['camera']['exposure time']/1000)

	def getFrameNameFromNumber(self,frame_number):
		return 'frame_%03d.mrc' % (frame_number+1)

	def getUsedFramesFromImageData(self,imagedata):
		return range(self.getNumberOfFrameSavedFromImageData(imagedata))

	def readFrameImage(self,frameimage_path,offset,crop_end,bin):
		a = mrc.read(frameimage_path)
		a = numpy.asarray(a,dtype=numpy.float32)

		# work around wrong dimension problem from applying rotation to the frame images
		# This commented out because the alignment program can not take non-square image anyway.
		#tempdict = {'y':crop_end['x'],'x':crop_end['y']}
		#crop_end = tempdict

		# modify the size if needed
		a = self.modifyFrameImage(a,offset,crop_end,bin)
		return a

	def getDefaultCorrectedImageData(self):
		if self.image['camera']['ccdcamera']['name'] == 'GatanK2Super':
			return leginondata.AcquisitionImageData().direct_query(1989908)
		elif self.image['camera']['ccdcamera']['name'] == 'GatanK2Counting':
			return leginondata.AcquisitionImageData().direct_query(1989725)
		else:
			return self.image
		
	def getRefImageData(self,reftype):
		if not self.use_full_raw_area:
			refdata = self.image[reftype]
			if refdata is None:
				default_image = self.getDefaultCorrectedImage()
				refdata = default_image[reftype]
		else:
			# use most recent CorrectorImageData
			# TO DO: this should research only ones before the image is taken.
			scopedata = self.image['scope']
			channel = self.image['channel']
			refdata = self.c_client.researchCorrectorImageData(reftype, scopedata, self.camerainfo, channel)
		return refdata

if __name__ == '__main__':
	dd = GatanK2Processing()
	dd.setImageId(1640790)
	start_frame = 0
	nframe = 5
	corrected = dd.correctFrameImage(start_frame,nframe)
	mrc.write(corrected,'corrected_frame%d_%d.mrc' % (start_frame,nframe))
