#!/usr/bin/env python

import numpy
from pyami import mrc,imagefun
from leginon import leginondata
from appionlib import apDDprocess,apDisplay

# testing options
save_jpg = False
debug = False
ddtype = 'thin'
at_nramm = True

class GatanK2Processing(apDDprocess.DDFrameProcessing):
	def __init__(self,wait_for_new=False):
		super(GatanK2Processing,self).__init__(wait_for_new)
		self.setDefaultDimension(3840,3712)
		self.correct_dark_gain = True
		self.correct_frame_mask = True
		
	def getNumberOfFrameSavedFromImageData(self,imagedata):
		return int(imagedata['camera']['frame rate']*imagedata['camera']['exposure time']/1000)

	def getFrameNameFromNumber(self,frame_number):
		return 'frame_%03d.mrc' % (frame_number+1)

	def getUsedFramesFromImageData(self,imagedata):
		return range(self.getNumberOfFrameSavedFromImageData(imagedata))

	def readFrameImage(self,frameimage_path,offset,crop_end,bin):
		a = mrc.read(frameimage_path)
		a = numpy.asarray(a,dtype=numpy.float32)

		# modify the size if needed
		a = self.modifyFrameImage(a,offset,crop_end,bin)
		return a

	def getDefaultCorrectedImageData(self):
		if not at_nramm:
			return self.image
		# local change
		if self.image['camera']['ccdcamera']['name'] == 'GatanK2Super':
			return leginondata.AcquisitionImageData().direct_query(1989908)
		elif self.image['camera']['ccdcamera']['name'] == 'GatanK2Counting':
			return leginondata.AcquisitionImageData().direct_query(1989725)
		else:
			return self.image

	def getImageCameraEMData(self):
		camdata = leginondata.CameraEMData(initializer=self.image['camera'])
		# local change. Need to remove before release
		if at_nramm and self.image.dbid < 1989842:
			# image dimension is not consistent with the frames
			# Use the default camera dimension, binning, and offset of the frames
			# (rotated and flipped full size)
			defaultcamdata = self.getDefaultCorrectedImageData()['camera']
			for key in ('dimension','binning','offset'):
				camdata[key] = defaultcamdata[key]
		return camdata

	def _getRefImageData(self,reftype):
		if not self.use_full_raw_area:
			refdata = self.image[reftype]
			refdata = None
			if refdata is None:
				# Use chosen default image
				apDisplay.printWarning('No %s reference for the image, use default' % reftype) 
				default_image = self.getDefaultCorrectedImageData()
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
