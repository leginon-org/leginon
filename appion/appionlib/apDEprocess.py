#!/usr/bin/env python

import numpy
from pyami import mrc,imagefun
from appionlib import apDDprocess,apDisplay

try:
	#The tifffile module only works with python 2.6 and above
	from pyami import tifffile
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

if __name__ == '__main__':
	dd = DEProcessing()
	dd.setImageId(1640790)
	start_frame = 0
	nframe = 5
	framelist = range(start_frame,start_frame+nframe)
	corrected = dd.correctFrameImage(framelist)
	mrc.write(corrected,'corrected_frame%d_%d.mrc' % (start_frame,nframe))
