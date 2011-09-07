#!/usr/bin/env python

import os
import numpy
from pyami import mrc,imagefun
try:
	#The faster tifffile module only works with python 2.6 and above
	from pyami import tifffile
	use_tifffile = True
except:
	use_tifffile = False
	import Image
from leginon import leginondata
from leginon import correctorclient
from appionlib import apDisplay

class DirectDetectorProcessing(object):
	def __init__(self):
		self.image = None
		self.camerainfo = {}
		self.c_client = correctorclient.CorrectorClient()

	def setImageId(self,imageid):
		q = leginondata.AcquisitionImageData()
		result = q.direct_query(imageid)
		if result:
			self.setImageData(result)
		else:
			apDisplay.printError("Image with ID of %d not found" % imageid)

	def getImageId(self):
		return self.image.dbid

	def setImageData(self,imagedata):
		self.image = imagedata
		self.__setRawFrameInfoFromImage()

	def getImageData(self):
		return self.image

	def __getNumberOfFrameSaved(self,rawframedir):
		return self.camerainfo['nframe']

	def getRawFrameDirFromImage(self,imagedata):
		# strip off DOS path in rawframe directory name 
		rawframename = imagedata['camera']['frames name'].split('\\')[-1]
		# raw frames are saved in a subdirctory of image path
		imagepath = imagedata['session']['image path']
		rawframedir = os.path.join(imagepath,'rawframes',rawframename)
		if not os.path.exists(rawframedir):
			apDisplay.printError('Raw Frame Directory %s does not exist' % rawframedir)
		return rawframedir

	def __setRawFrameInfoFromImage(self):
		'''
		set rawframe_dir, rawframe_seq, and nframe of the current image
		'''
		imagedata = self.image
		if not imagedata:
			apDisplay.printError('No image set.')
		rawframeseq = imagedata['camera']['use frames']
		rawframedir = self.getRawFrameDirFromImage(imagedata)
		# set attribute values
		self.rawframe_dir = rawframedir
		self.rawframe_seq = rawframeseq
		self.nframe = len(self.rawframe_seq)

	def __setCameraInfo(self,nframe,use_full_raw_area):
		'''
		set cemrainfo attributes with current values of the image
		'''
		self.camerainfo = self.__getCameraInfoFromImage(nframe,use_full_raw_area)

	def __getCameraInfoFromImage(self,nframe,use_full_raw_area):
		'''
		returns dictionary of camerainfo obtained from the current image
		'''
		binning = self.image['camera']['binning']
		offset = self.image['camera']['offset']
		dimension = self.image['camera']['dimension']
		if use_full_raw_area:
			for axis in ('x','y'):
				dimension[axis] = binning[axis] * dimension[axis] + 2 * offset[axis]
				offset[axis] = 0
				binning[axis] = 1
		camerainfo = {}
		camerainfo['ccdcamera'] = self.image['camera']['ccdcamera']
		camerainfo['binning'] = binning
		camerainfo['offset'] = offset
		camerainfo['dimension'] = dimension
		camerainfo['nframe'] = nframe
		return camerainfo
			
	def __conditionChanged(self,new_nframe,new_use_full_raw_area):
		'''
		Checking changed camerainfo since last used so that cached 
		references can be used if not changed.
		'''
		if len(self.camerainfo.keys()) == 0:
			return True
		if self.camerainfo['ccdcamera'].dbid != self.image['camera']['ccdcamera'].dbid:
			return True
		if new_use_full_raw_area and self.use_full_raw_area == new_use_full_raw_area:
			if self.camerainfo['nframe'] == new_nframe:
				return True
		else:
			newcamerainfo = self.__getCameraInfoFromImage(new_nframe,new_use_full_raw_area)
			for key in self.camerainfo.keys():
				if key != 'ccdcamera' and self.camerainfo[key] != newcamerainfo[key]:
						return True
		return False
			
	def __loadOneRawFrame(self,rawframe_dir,frame_number):
		'''
		Load from rawframe_dir the chosen frame of the current image.
		'''
		bin = self.camerainfo['binning']
		offset = self.camerainfo['offset']
		dimension = self.camerainfo['dimension']
		crop_end = {'x': offset['x']+dimension['x']*bin['x'], 'y':offset['y']+dimension['y']*bin['y']}

		rawframe_path = os.path.join(rawframe_dir,'Image%d.tif'%frame_number)
		if use_tifffile:
			# Use Faster tiff conversion to numpy module.
			tif = tifffile.TIFFfile(rawframe_path)
			a = tif.asarray()
			a = numpy.asarray(a,dtype=numpy.float32)
			a = a[offset['y']:crop_end['y'],offset['x']:crop_end['x']]
		else:
			# Use PIL
			pil_img = Image.open(rawframe_path)
			pil_cropped_img = pil_img.crop((offset['x'],offset['y'],crop_end['x'],crop_end['y']))
			a = numpy.array(pil_cropped_img.getdata()).reshape((pil_cropped_img.size))
		if bin['x'] > 1:
			if bin['x'] == bin['y']:
				a = imagefun.bin(a,bin['x'])
			else:
				apDisplay.printError("Binnings in x,y are different")
		#a = a[:,::-1]
		return numpy.fliplr(a)

	def sumupFrames(self,rawframe_dir,start_frame,nframe):
		'''
		Load a number of consecutive raw frames from known directory,
		sum them up, and return as numpy array.
		nframe = total number of frames to sum up.
		
		'''
		apDisplay.printMsg( 'Summing up %d Frames starting from %d ....' % (nframe,start_frame))
		for frame_number in range(start_frame,start_frame+nframe):
			if frame_number == start_frame:
				rawarray = self.__loadOneRawFrame(rawframe_dir,frame_number)
			else:
				rawarray += self.__loadOneRawFrame(rawframe_dir,frame_number)
		return rawarray

	def scaleRefImage(self,reftype,nframe):
		if not self.use_full_raw_area:
			refdata = self.image[reftype]
		else:
			# use most recent CorrectorImageData
			# TO DO: this should research only ones before the image is taken.
			scopedata = self.image['scope']
			channel = self.image['channel']
			refdata = self.c_client.researchCorrectorImageData(reftype, scopedata, self.camerainfo, channel)
		ref_nframe = len(refdata['camera']['use frames'])
		refscale = float(nframe) / ref_nframe
		scaled_refarray = refdata['image'] * refscale
		return scaled_refarray

	def correctFrameImage(self,start_frame,nframe,use_full_raw_area=False):
		'''
		This returns corrected numpy array of given start and total number
		of raw frames of the current image set for the class instance.  
		Full raw frame area can be returned as an option.
		'''
		# check parameter
		if not self.image:
			apDisplay.printError("You must set an image for the operation")
		if start_frame not in range(self.nframe):
			apDisplay.printError("Starting Frame not in raw frame sequence, can not be processed")
		if (start_frame + nframe) > self.nframe:
			newnframe = self.nframe - start_frame
			apDisplay.printWarning( "%d instead of %d frames will be used since not enough frames are saved." % (newnframe,nframe))
			nframe = newnframe

		get_new_refs = self.__conditionChanged(nframe,use_full_raw_area)
		# o.k. to set attribute now that condition change is checked
		self.use_full_raw_area = use_full_raw_area
		if get_new_refs:
			# load dark and bright
			self.__setCameraInfo(nframe,use_full_raw_area)
			scaled_darkarray = self.scaleRefImage('dark',nframe)
			scaled_brightarray = self.scaleRefImage('bright',nframe)
			normarray = self.c_client.calculateNorm(scaled_brightarray,scaled_darkarray)
			self.normarray = normarray
			self.scaled_darkarray = scaled_darkarray
		else:
			normarray = self.normarray
			scaled_darkarray = self.scaled_darkarray

		# load raw frames
		rawarray = self.sumupFrames(self.rawframe_dir,start_frame,nframe)
		# gain correction
		corrected = (rawarray - scaled_darkarray) * normarray
		# fix bad pixels
		plan = self.c_client.retrieveCorrectorPlan(self.camerainfo)
		self.c_client.fixBadPixels(corrected,plan)
		corrected = numpy.clip(corrected,0,10000)
		return corrected

	def makeCorrectedRawFrameStack(self,rundir, use_full_raw_area=False):
		rawframedir = self.getRawFrameDirFromImage(self.image)
		framestackpath = os.path.join(rundir,self.image['filename']+'_st.mrc')
		total_frames = self.__getNumberOfFrameSaved()
		for start_frame in range(total_frames):
			array = self.correctFrameImage(start_frame,1,use_full_raw_area)
			if start_frame == 0:
				# overwrite old stack mre file
				mrc.write(array,framestackpath)
			elif start_frame == total_frames-1:
				mrc.append(array,framestackpath,True)
			else:
				# Only calculate stats if the last frame
				mrc.append(array,framestackpath,False)

if __name__ == '__main__':
	dd = DirectDetectorProcessing()
	dd.setImageId(1640790)
	start_frame = 0
	nframe = 5
	corrected = dd.correctFrameImage(start_frame,nframe)
	mrc.write(corrected,'corrected_frame%d_%d.mrc' % (start_frame,nframe))
