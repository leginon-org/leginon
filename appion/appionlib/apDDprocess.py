#!/usr/bin/env python

import os
import sys
import numpy
import time
import scipy.stats
import scipy.ndimage as ndimage
import numextension
from pyami import mrc,imagefun,arraystats,numpil
try:
	#The faster tifffile module only works with python 2.6 and above
	from pyami import tifffile
	use_tifffile = True
except:
	use_tifffile = False
	import Image
from leginon import correctorclient
from appionlib import apDisplay, apDatabase

# testing options
save_jpg = False
debug = False
ddtype = 'thin'

class DirectDetectorProcessing(object):
	def __init__(self,wait_for_new=False):
		self.image = None
		self.stripenorm_imageid = None
		self.waittime = 0 # in minutes
		if wait_for_new:
			self.waittime = 30 # in minutes
		self.camerainfo = {}
		self.c_client = correctorclient.CorrectorClient()
		# change this to True for loading bias image for correction
		self.use_bias = False
		self.use_GS = False
		if debug:
			self.log = open('newref.log','w')
			self.scalefile = open('darkscale.log','w')

	def setImageId(self,imageid):
		from leginon import leginondata
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

	def setUseGS(self,status):
		self.use_GS = status

	def getNumberOfFrameSaved(self):
		return self.image['camera']['nframes']

	def getScaledBrightArray(self,nframe):
		return self.scaleRefImage('bright',nframe)

	def getSingleFrameDarkArray(self):
		darkdata = self.__getRefImageData('dark')
		nframes = darkdata['camera']['nframes']
		return darkdata['image'] / nframes

	def OldgetSingleFrameDarkArray(self):
		# work around for the bug in DE server between 11sep07 and 11nov22
		return self.__getRefImageData('dark')['image']

	def getRawFramesName(self):
		return self.framesname

	def setRawFrameDir(self,path):
		self.rawframe_dir = path

	def getRawFrameDir(self):
		return self.rawframe_dir

	def getRawFrameDirFromImage(self,imagedata):
		# strip off DOS path in rawframe directory name 
		rawframename = imagedata['camera']['frames name'].split('\\')[-1]
		if not rawframename:
			apDisplay.printWarning('No Raw Frame Saved for %s' % imagedata['filename'])
		# raw frames are saved in a subdirctory of image path
		imagepath = imagedata['session']['image path']

		rawframedir = os.path.join(imagepath,'%s.frames' % imagedata['filename'])
		waitmin = 0
		while not os.path.exists(rawframedir):
			if self.waittime < 0.1:
				apDisplay.printError('Raw Frame Directory %s does not exist.' % rawframedir)
			apDisplay.printWarning('Raw Frame Directory %s does not exist. Wait for 3 min.' % rawframedir)
			time.sleep(180)
			waitmin += 3
			apDisplay.printMsg('Waited for %d min so far' % waitmin)
		return rawframedir

	def OldgetRawFrameDirFromImage(self,imagedata):
		# works between 11sep07 and 11nov22
		# strip off DOS path in rawframe directory name 
		rawframename = imagedata['camera']['frames name'].split('\\')[-1]
		if not rawframename:
			apDisplay.printWarning('No Raw Frame Saved for %s' % imagedata['filename'])
		# raw frames are saved in a subdirctory of image path
		imagepath = imagedata['session']['image path']
		rawframedir = os.path.join(imagepath,'rawframes',rawframename)
		if not os.path.exists(rawframedir):
			apDisplay.printError('Raw Frame Directory %s does not exist' % rawframedir)
		return rawframedir


	def __getRefImageData(self,reftype):
		if not self.use_full_raw_area:
			refdata = self.image[reftype]
			#refdata = self.c_client.getAlternativeChannelReference(reftype,refdata)
			#if self.image.dbid <= 1815252 and self.image.dbid >= 1815060:
				# special case to back correct images with bad references
				#refdata = apDatabase.getRefImageDataFromSpecificImageId(reftype,1815281)
		else:
			# use most recent CorrectorImageData
			# TO DO: this should research only ones before the image is taken.
			scopedata = self.image['scope']
			channel = self.image['channel']
			refdata = self.c_client.researchCorrectorImageData(reftype, scopedata, self.camerainfo, channel)
		return refdata

	def scaleRefImage(self,reftype,nframe,bias=False):
		refdata = self.__getRefImageData(reftype)
		ref_nframe = len(refdata['camera']['use frames'])
		refscale = float(nframe) / ref_nframe
		scaled_refarray = refdata['image'] * refscale
		return scaled_refarray

	def __setRawFrameInfoFromImage(self):
		'''
		set rawframe_dir, nframe, and totalframe of the current image
		'''
		imagedata = self.image
		if not imagedata:
			apDisplay.printError('No image set.')
		# set rawframe path
		self.setRawFrameDir(self.getRawFrameDirFromImage(imagedata))
		# initialize self.nframe
		self.nframe = self.getNumberOfFrameSaved()
		# total number of frames saved
		self.totalframe = self.getNumberOfFrameSaved()

	def setCameraInfo(self,nframe,use_full_raw_area):
		'''
		set cemrainfo attributes with current values of the image
		'''
		self.camerainfo = self.__getCameraInfoFromImage(nframe,use_full_raw_area)

	def __getCameraInfoFromImage(self,nframe,use_full_raw_area):
		'''
		returns dictionary of camerainfo obtained from the current image
		and current instance values such as nframe and use_full_raw_area flag
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
		camerainfo['norm'] = self.image['norm']
		print self.image['norm']['filename']
		# Really should check frame rate but it is not saved now, so use exposure time
		camerainfo['exposure time'] = self.image['camera']['exposure time']
		return camerainfo
			
	def __conditionChanged(self,new_nframe,new_use_full_raw_area):
		'''
		Checking changed camerainfo since last used so that cached 
		references can be used if not changed.
		'''
		# return True all the time to use Gram-Schmidt process to calculate darkarray scale
		if self.use_GS:
			return True
		if len(self.camerainfo.keys()) == 0:
			if debug:
				self.log.write( 'first frame image to be processed\n ')
			return True
		if self.camerainfo['norm'].dbid != self.image['norm'].dbid:
			if debug:
				self.log.write( 'fail norm %d vs %d test\n ' % (self.camerainfo['norm'].dbid,self.image['norm'].dbid))
			return True
		if self.use_full_raw_area != new_use_full_raw_area:
			if debug:
				self.log.write('fail full raw_area %s test\n ' % (new_use_full_raw_area))
			return True
		else:
			newcamerainfo = self.__getCameraInfoFromImage(new_nframe,new_use_full_raw_area)
			for key in self.camerainfo.keys():
				if key != 'ccdcamera' and self.camerainfo[key] != newcamerainfo[key] and debug:
						self.log.write('fail %s test\n ' % (key))
						return True
		return False
			
	def __loadOneRawFrame(self,rawframe_dir,frame_number):
		'''
		Load from rawframe_dir the chosen frame of the current image.
		'''
		try:
			bin = self.camerainfo['binning']
			offset = self.camerainfo['offset']
			dimension = self.camerainfo['dimension']
		except:
			# default
			bin = {'x':1,'y':1}
			offset = {'x':0,'y':0}
			dimension = {'x':4096,'y':3072}
		crop_end = {'x': offset['x']+dimension['x']*bin['x'], 'y':offset['y']+dimension['y']*bin['y']}

		rawframe_path = os.path.join(rawframe_dir,'RawImage_%d.tif'%frame_number)
		apDisplay.printMsg('Raw frame path: %s' %  rawframe_path)
		waitmin = 0
		while not os.path.exists(rawframe_path):
			if self.waittime < 0.1:
				apDisplay.printWarning('Raw Frame File %s does not exist.' % rawframe_path)
				return False
			apDisplay.printWarning('Raw Frame File %s does not exist. Wait for 3 min.' % rawframe_path)
			time.sleep(180)
			waitmin += 3
			apDisplay.printMsg('Waited for %d min so far' % waitmin)
			if waitmin > self.waittime:
				return False
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
			a = numpy.swapaxes(a,1,0)
		if bin['x'] > 1:
			if bin['x'] == bin['y']:
				a = imagefun.bin(a,bin['x'])
			else:
				apDisplay.printError("Binnings in x,y are different")
		# numarray gotten from tiffile is different from PIL
		if use_tifffile:
			return a[:,::-1]
		else:
			return a

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
				if rawarray is False:
					return False
			else:
				oneframe = self.__loadOneRawFrame(rawframe_dir,frame_number)
				if oneframe is False:
					return False
				rawarray += oneframe
		return rawarray

	def correctFrameImage(self,start_frame,nframe,use_full_raw_area=False):
		corrected = self.__correctFrameImage(start_frame,nframe,use_full_raw_area)
		if corrected is False:
			apDisplay.printError('Failed to correct Image')
		else:
			return corrected

	def test__correctFrameImage(self,start_frame,nframe,use_full_raw_area=False):
		# check parameter
		if not self.image:
			apDisplay.printError("You must set an image for the operation")
		if start_frame not in range(self.totalframe):
			apDisplay.printError("Starting Frame not in saved raw frame range, can not be processed")
		if (start_frame + nframe) > self.totalframe:
			newnframe = self.totalframe - start_frame
			apDisplay.printWarning( "%d instead of %d frames will be used since not enough frames are saved." % (newnframe,nframe))
			nframe = newnframe
		self.use_full_raw_area = use_full_raw_area
		get_new_refs = self.__conditionChanged(nframe,use_full_raw_area)
		if get_new_refs:
			self.setCameraInfo(nframe,use_full_raw_area)
		if debug:
			self.log.write('%s %s\n' % (self.image['filename'],get_new_refs))
		return False

	def darkCorrection(self,rawarray,darkarray,nframe):
		apDisplay.printMsg('Doing dark correction')
		onedshape = rawarray.shape[0] * rawarray.shape[1]
		b = darkarray.reshape(onedshape)
		if self.use_GS:
			apDisplay.printWarning('..Use Gram-Schmidt process to determine scale')
			dark_scale = self.c_client.calculateDarkScale(rawarray,darkarray)
		else:
			dark_scale = nframe
		corrected = (rawarray - dark_scale * darkarray)
		return corrected,dark_scale

	def makeNorm(self,brightarray,darkarray,dark_scale):
		apDisplay.printMsg('..Making new norm array from dark scale of %.2f' % dark_scale)
		#calculate normarray
		normarray = self.c_client.calculateNorm(brightarray,darkarray,dark_scale)
		# clip norm to a smaller range to filter out very big values
		clipmin = min(1/3.0,max(normarray.min(),1/normarray.max()))
		clipmax = max(3.0,min(normarray.max(),1/normarray.min()))
		normarray = numpy.clip(normarray, clipmin, clipmax)
		return normarray

	def __correctFrameImage(self,start_frame,nframe,use_full_raw_area=False,stripe_correction=False):
		'''
		This returns corrected numpy array of given start and total number
		of raw frames of the current image set for the class instance.  
		Full raw frame area can be returned as an option.
		'''
		# check parameter
		if not self.image:
			apDisplay.printError("You must set an image for the operation")
		if start_frame not in range(self.totalframe):
			apDisplay.printError("Starting Frame not in saved raw frame range, can not be processed")
		if (start_frame + nframe) > self.totalframe:
			newnframe = self.totalframe - start_frame
			apDisplay.printWarning( "%d instead of %d frames will be used since not enough frames are saved." % (newnframe,nframe))
			nframe = newnframe

		get_new_refs = self.__conditionChanged(nframe,use_full_raw_area)
		if debug:
			self.log.write('%s %s\n' % (self.image['filename'],get_new_refs))
		if not get_new_refs and start_frame ==0:
			apDisplay.printWarning("Imaging condition unchanged. Reference in memory will be used.")

		# o.k. to set attribute now that condition change is checked
		self.use_full_raw_area = use_full_raw_area

		# DARK CORRECTION
		if get_new_refs:
			# load dark 
			self.setCameraInfo(nframe,use_full_raw_area)
			unscaled_darkarray = self.getSingleFrameDarkArray()
			self.unscaled_darkarray = unscaled_darkarray
		else:
			unscaled_darkarray = self.unscaled_darkarray

		# load raw frames
		rawarray = self.sumupFrames(self.rawframe_dir,start_frame,nframe)
		if rawarray is False:
			return False
		if save_jpg:
			numpil.write(unscaled_darkarray,'%s_dark.jpg' % ddtype,'jpeg')
			numpil.write(rawarray,'%s_raw.jpg' % ddtype,'jpeg')
		corrected, dark_scale = self.darkCorrection(rawarray,unscaled_darkarray,nframe)
		if save_jpg:
			numpil.write(corrected,'%s_dark_corrected.jpg' % ddtype,'jpeg')
		if debug:
			self.scalefile.write('%s\t%.4f\n' % (start_frame,dark_scale))
		apDisplay.printMsg('..Dark Scale= %.4f' % dark_scale)
		# GAIN CORRECTION
		apDisplay.printMsg('Doing gain correction')
		if get_new_refs:
			scaled_brightarray = self.getScaledBrightArray(nframe)
			if not self.use_GS and self.image['norm']:
				normarray = self.image['norm']['image']
			else:
				normarray = self.makeNorm(scaled_brightarray,unscaled_darkarray, dark_scale)
			self.normarray = normarray
		else:
			normarray = self.normarray
		if save_jpg:
			numpil.write(normarray,'%s_norm.jpg' % ddtype,'jpeg')
			numpil.write(scaled_brightarray,'%s_bright.jpg' % ddtype,'jpeg')
		corrected = corrected * normarray

		# BAD PIXEL FIXING
		plan = self.getCorrectorPlan(self.camerainfo)
		apDisplay.printMsg('Fixing bad pixel, columns, and rows')
		self.c_client.fixBadPixels(corrected,plan)
		apDisplay.printMsg('Cliping corrected image')
		corrected = numpy.clip(corrected,0,10000)
		#if save_jpg:
			#numpil.write(corrected,'%s_gain_corrected.jpg' % ddtype,'jpeg')
		print 'corrected',arraystats.mean(corrected),corrected.min(),corrected.max()

		if stripe_correction:
			stripenorm = self.getStripeNormArray(512,use_full_raw_area)
			mrc.write(stripenorm,'stripenorm.mrc')
			corrected = corrected * stripenorm
		return corrected

	def getCorrectorPlan(self,camerainfo):
		plandata =  self.image['corrector plan']
		if plandata:
			plan = self.c_client.formatCorrectorPlan(plandata)
		else:
			plan, plandata = self.c_client.retrieveCorrectorPlan(self.camerainfo)
		return plan

	def getStripeNormArray(self,length=256,use_full_raw_area=False):
		'''
		Experimental correction to remove horizontal stripe that is not removed from
		the dark and gain corrections.  The convolution this function perform will
		produce blurring if there is true signal in the image that is used as reference.
		This is a flaw in the current code since it uses the data image to calculate
		the stripenormarray.
		'''
		if self.stripenorm_imageid == self.image.dbid:
			apDisplay.printWarning('Same Image, use existing stripe norm array to save time')
			return self.stripenormarray
		image_nframes = self.getNumberOfFrameSaved()
		array = self.__correctFrameImage(0,image_nframes,use_full_raw_area,False)
		shape = array.shape
		if shape < length:
			length = shape
		length = int(length)
		stripearray = numpy.ones(shape)
		for weightshape in ((1,length),(length,1)):
			weightarray = numpy.ones((1,length))
			stripearray = stripearray * ndimage.filters.convolve(array,weightarray,mode='reflect')
		self.stripenorm_imageid = self.image.dbid
		self.stripenormarray = (stripearray.mean() / stripearray)**2
		return self.stripenormarray

	def makeCorrectedRawFrameStack(self,rundir, use_full_raw_area=False):
		sys.stdout.write('\a')
		sys.stdout.flush()
		framestackpath = os.path.join(rundir,self.image['filename']+'_st.mrc')
		total_frames = self.getNumberOfFrameSaved()
		half_way_frame = int(total_frames // 2)
		first = 0 
		for start_frame in range(first,first+total_frames):
			array = self.__correctFrameImage(start_frame,1,use_full_raw_area,False)
			# if non-fatal error occurs, end here
			if array is False:
				break
			array.max()
			if start_frame == first:
				# overwrite old stack mre file
				mrc.write(array,framestackpath)
			elif start_frame == half_way_frame:
				mrc.append(array,framestackpath,True)
			else:
				# Only calculate stats if the last frame
				mrc.append(array,framestackpath,False)
		return framestackpath

if __name__ == '__main__':
	dd = DirectDetectorProcessing()
	dd.setImageId(1640790)
	start_frame = 0
	nframe = 5
	corrected = dd.correctFrameImage(start_frame,nframe)
	mrc.write(corrected,'corrected_frame%d_%d.mrc' % (start_frame,nframe))
