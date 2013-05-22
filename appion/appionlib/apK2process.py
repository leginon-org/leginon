#!/usr/bin/env python

import os
import numpy
import datetime
from pyami import mrc,imagefun
from leginon import leginondata,ddinfo
from appionlib import apDDprocess,apDisplay

# testing options
save_jpg = False
debug = False
ddtype = 'thin'

class GatanK2Processing(apDDprocess.DDFrameProcessing):
	def __init__(self,wait_for_new=False):
		super(GatanK2Processing,self).__init__(wait_for_new)
		self.setDefaultDimension(3838,3710)
		self.correct_dark_gain = True
		self.correct_frame_mask = False
		
	def getNumberOfFrameSavedFromImageData(self,imagedata):
		return int(imagedata['camera']['exposure time'] / imagedata['camera']['frame time'])

	def getFrameNameFromNumber(self,frame_number):
		return 'frame_%03d.mrc' % (frame_number+1)

	def getUsedFramesFromImageData(self,imagedata):
		return range(self.getNumberOfFrameSavedFromImageData(imagedata))

	def getRawFrameDirFromImage(self,imagedata):
		print 'RawFrameType',self.getRawFrameType()
		if self.getRawFrameType() == 'singles':
			return super(GatanK2Processing,self).getRawFrameDirFromImage(imagedata)
		'''
		K2 raw frames are now saved as image stack for feeding into gpu program.
		RawFrameDir here is now actually the filename with mrc extension.
		'''
		# strip off DOS path in rawframe directory name 
		rawframename = imagedata['camera']['frames name'].split('\\')[-1]
		if not rawframename:
			apDisplay.printWarning('No Raw Frame Saved for %s' % imagedata['filename'])
		# raw frames are saved in a subdirctory of image path
		imagepath = imagedata['session']['image path']
		rawframe_basepath = ddinfo.getRawFrameSessionPathFromImagePath(imagepath)
		# frame stackfile is image filename plus '.frames.mrc'
		rawframedir = os.path.join(rawframe_basepath,'%s.frames.mrc' % imagedata['filename'])
		if not self.waitForPathExist(rawframedir,30):
			apDisplay.printError('Raw Frame Dir %s does not exist.' % rawframedir)
		return rawframedir

	def loadOneRawFrame(self,rawframe_path,frame_number):
		'''
		Load one raw frame depending on the rawframetype
		'''
		print 'RawFrameType',self.getRawFrameType()
		if self.getRawFrameType() == 'singles':
			return super(GatanK2Processing,self).loadOneRawFrame(rawframe_path,frame_number)
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

	def readFrameImage(self,frameimage_path,offset,crop_end,bin):
		'''
		Read a frame file from the frame directory
		'''
		a = mrc.read(frameimage_path)
		a = numpy.asarray(a,dtype=numpy.float32)

		# modify the size if needed
		a = self.modifyFrameImage(a,offset,crop_end,bin)
		return a

	def isOldNRAMMData(self):
		'''
		Work around old NRAMM data that has a bad reference, but not in any
		one outside.  This works because we don't think anyone outside uses
		this module before that.
		'''
		return self.image.timestamp.date() < datetime.date(2012,12,31)

	def getDefaultCorrectedImageData(self):
		if not self.isOldNRAMMData():
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
		if self.isOldNRAMMData and self.image.dbid < 1989842:
			# image dimension is not consistent with the frames
			# Use the default camera dimension, binning, and offset of the frames
			# (rotated and flipped full size)
			defaultcamdata = self.getDefaultCorrectedImageData()['camera']
			for key in ('dimension','binning','offset'):
				camdata[key] = defaultcamdata[key]
		return camdata

	def _getRefImageData(self,reftype):
		if self.getDefaultImageForReference():
			imagedata = super(GatanK2Processing,self).getDefaultCorrectedImageData()
			return imagedata[reftype]
		if not self.use_full_raw_area:
			refdata = self.image[reftype]
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
