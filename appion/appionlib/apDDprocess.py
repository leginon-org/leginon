#!/usr/bin/env python

import os
import sys
import numpy
import time
import scipy.stats
import scipy.ndimage as ndimage
import numextension
from pyami import mrc,imagefun,arraystats,numpil
from leginon import correctorclient,leginondata
from appionlib import apDisplay, apDatabase,apDBImage, appiondata
import subprocess

# testing options
save_jpg = False
debug = False
ddtype = 'thin'

#=======================
def initializeDDFrameprocess(sessionname,wait_flag=False):
	'''
	initialize the DDprocess according to the camera
	'''
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
	dcamdata = apDatabase.getFrameImageCamera(sessiondata)
	if not dcamdata:
		apDisplay.printError('Can not determine DD camera type')
	if 'GatanK2' in dcamdata['name']:
		from appionlib import apK2process
		return apK2process.GatanK2Processing(wait_flag)
	elif 'DE' in dcamdata['name']:
		from appionlib import apDEprocess
		return apDEprocess.DEProcessing(wait_flag)
	else:
		apDisplay.printError('Unknown frame camera name %s' % dcamdata['name'])

class DirectDetectorProcessing(object):
	def __init__(self):
		'''
		Base class for DD processing
		'''
		self.image = None
		self.setRunDir(os.getcwd())

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
		'''
		Set the image is to be considered for processs.
		self.rundir must be set first before calling this.
		'''
		self.image = imagedata

	def getImageData(self):
		return self.image

	def setFrameStackPath(self):
		imagename = self.image['filename']
		
		if self.image['preset'] is not None and '-a' in self.image['preset']['name']:
			# aligned image have -a in its preset name
			aligned_presetname = self.image['preset']['name']
			bits = imagename.split(aligned_presetname)
			org_presetname = aligned_presetname.join(aligned_presetname.split('-a')[:-1])
			# remove trailing empty string and version
			while len(bits) > 1 and (len(bits[-1]) == 0 or (len(bits[-1]) >= 4 and '_v' in bits[-1])):
				bits.pop(-1)
			imagename = aligned_presetname.join(bits) +org_presetname 
		self.framestackpath = os.path.join(self.rundir,imagename+'_st.mrc')
		
			
	def setRunDir(self,rundir):
		'''
		This is the rundir for ddstack
		'''
		self.rundir = rundir

	def getRunDir(self):
		return self.rundir

	def getNumberOfFrameSaved(self):
		return self.getNumberOfFrameSavedFromImageData(self.image)

	def getNumberOfFrameSavedFromImageData(self,imagedata):
		return imagedata['camera']['nframes']

	def getUsedFramesFromImageData(self,imagedata):
		return imagedata['camera']['use frames']

	def getAlignImagePairData(self,ddstackrundata,query_source=True):
		'''
		This returns DD AlignImagePairData if exists, returns False if not.
		Image set in the class instance can either be the source or result of the alignment
		'''
		if query_source:
			q = appiondata.ApDDAlignImagePairData(source=self.image,ddstackrun=ddstackrundata)
		else:
			q = appiondata.ApDDAlignImagePairData(result=self.image,ddstackrun=ddstackrundata)
		r = q.query(results=1)
		if r:
			return r[0]
		else:
			return False

class DDFrameProcessing(DirectDetectorProcessing):
	'''
	Class to process raw frames from DD
	'''
	def __init__(self,wait_for_new=False):
		super(DDFrameProcessing,self).__init__()
		self.waittime = 0 # in minutes
		if wait_for_new:
			self.waittime = 30 # in minutes
		self.camerainfo = {}
		self.setDefaultDimension(4096,3072)
		self.c_client = correctorclient.CorrectorClient()
		self.stack_binning = 1
		self.correct_dark_gain = True
		self.correct_frame_mask = False
		self.aligned_camdata = None
		# change this to True for loading bias image for correction
		self.use_bias = False
		self.use_GS = False
		self.setUseAlternativeChannelReference(False)
		self.setDefaultImageForReference(0)
		if debug:
			self.log = open('newref.log','w')
			self.scalefile = open('darkscale.log','w')

	def setImageData(self,imagedata):
		super(DDFrameProcessing,self).setImageData(imagedata)
		# dark/gain corrected stack is saved here
		self.setFrameStackPath()
		self.__setRawFrameInfoFromImage()
		# These two are only used if alignment of the frames are made
		self.aligned_sumpath = os.path.join(self.rundir,self.image['filename']+'_c.mrc')
		self.aligned_stackpath = os.path.join(self.rundir,self.framestackpath[:-4]+'_c'+self.framestackpath[-4:])

	def getDefaultDimension(self):
		return self.dimension

	def setDefaultDimension(self,xdim,ydim):
		self.dimension = {'x':xdim,'y':ydim}

	def setUseGS(self,status):
		self.use_GS = status

	def getScaledBrightArray(self,nframe):
		return self.scaleRefImage('bright',nframe)

	def getSingleFrameDarkArray(self):
		darkdata = self.getRefImageData('dark')
		nframes = self.getNumberOfFrameSavedFromImageData(darkdata)
		return darkdata['image'] / nframes

	def getFrameNameFromNumber(self,frame_number):
		raise NotImplementedError()

	def OldgetSingleFrameDarkArray(self):
		# work around for the bug in DE server between 11sep07 and 11nov22
		return self.getRefImageData('dark')['image']

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
		if not self.waitForPathExist(rawframedir):
			apDisplay.printError('Raw Frame Dir %s does not exist.' % rawframedir)
		return rawframedir

	def setUseAlternativeChannelReference(self,use_alt_channel=False):
		self.use_alt_channel_ref = use_alt_channel

	def getUseAlternativeChannelReference(self):
		return self.use_alt_channel_ref

	def setDefaultImageForReference(self,imageid):
		self.default_ref_image = imageid

	def getDefaultImageForReference(self):
		return self.default_ref_image

	def waitForPathExist(self,newpath,sleep_time=180):
		waitmin = 0
		while not os.path.exists(newpath):
			if self.waittime < 0.1:
				return False
			apDisplay.printWarning('%s does not exist. Wait for %.1f min.' % (newpath,sleep_time/60.0))
			time.sleep(sleep_time)
			waitmin += sleep_time / 60.0
			apDisplay.printMsg('Waited for %.1f min so far' % waitmin)
		return True

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

	def getDefaultCorrectedImageData(self):
		imageid = self.getDefaultImageForReference()
		imagedata = leginondata.AcquisitionImageData().direct_query(imageid)
		if self.image['camera']['ccdcamera']['name'] != imagedata['camera']['ccdcamera']['name']:
			apDisplay.printError('Default reference image not from the same camera as the data')
		apDisplay.printMsg('Reference image comes from %s' % imagedata['filename'])
		return imagedata

	def getRefImageData(self,reftype):
		refdata = self._getRefImageData(reftype)
		if self.getUseAlternativeChannelReference():
			oldrefname = refdata['filename']
			refdata = self.c_client.getAlternativeChannelReference(reftype,refdata)
			#apDisplay.printWarning('Use Alternative Channel Reference %s instead of %s' % (refdata['filename'],oldrefname))
		return refdata

	def _getRefImageData(self,reftype):
		if self.getDefaultImageForReference():
			imagedata = self.getDefaultCorrectedImageData()
			return imagedata[reftype]
		if not self.use_full_raw_area:
			refdata = self.image[reftype]
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
		refdata = self.getRefImageData(reftype)
		ref_nframe = len(self.getUsedFramesFromImageData(refdata))
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
		imagecam = self.getImageCameraEMData()
		binning = imagecam['binning']
		offset = imagecam['offset']
		dimension = imagecam['dimension']
		if use_full_raw_area:
			for axis in ('x','y'):
				dimension[axis] = binning[axis] * dimension[axis] + 2 * offset[axis]
				offset[axis] = 0
				binning[axis] = 1
		camerainfo = {}
		camerainfo['ccdcamera'] = imagecam['ccdcamera']
		camerainfo['binning'] = binning
		camerainfo['offset'] = offset
		camerainfo['dimension'] = dimension
		camerainfo['nframe'] = nframe
		camerainfo['norm'] = self.getRefImageData('norm')
		if camerainfo['norm']:
			print camerainfo['norm']['filename']
		else:
			self.correct_dark_gain = False
		# Really should check frame rate but it is not saved now, so use exposure time
		camerainfo['exposure time'] = imagecam['exposure time']
		return camerainfo
			
	def __conditionChanged(self,new_nframe,new_use_full_raw_area):
		'''
		Checking changed camerainfo since last used so that cached 
		references can be used if not changed.
		'''
		if len(self.camerainfo.keys()) == 0:
			if debug:
				self.log.write( 'first frame image to be processed\n ')
			return True
		# no need to change condition if no dark/gain correction will be made
		if not self.correct_dark_gain:
			return False
		# return True all the time to use Gram-Schmidt process to calculate darkarray scale
		if self.use_GS:
			return True
		# self.camerainfo is not set for the new image yet so it may be different
		current_norm = self.getRefImageData('norm')
		if current_norm and self.camerainfo['norm'].dbid != current_norm.dbid:
			if debug:
				self.log.write( 'fail norm %d vs %d test\n ' % (self.camerainfo['norm'].dbid,current_norm.dbid))
			return True
		if self.use_full_raw_area != new_use_full_raw_area:
			if debug:
				self.log.write('fail full raw_area %s test\n ' % (new_use_full_raw_area))
			return True
		else:
			newcamerainfo = self.__getCameraInfoFromImage(new_nframe,new_use_full_raw_area)
			for key in self.camerainfo.keys():
				# data instance would be different
				# norm is checked already above
				datakeys = ('ccdcamera','norm')
				if key not in datakeys:
					if self.camerainfo[key] != newcamerainfo[key] and debug:
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
			dimension = self.getDefaultDimension()
		crop_end = {'x': offset['x']+dimension['x']*bin['x'], 'y':offset['y']+dimension['y']*bin['y']}
		framename = self.getFrameNameFromNumber(frame_number)
		rawframe_path = os.path.join(rawframe_dir,framename)
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
		return self.readFrameImage(rawframe_path,offset,crop_end,bin)

	def readFrameImage(self,frameimage_path,offset,crop_end,bin):
		'''
		Read full size frame image as numpy array at the camera configuration
		'''
		# simulated image here. Need to define specifically in the subclass
		dim = self.getDefaultDimension()
		a = numpy.ones((dim['y'],dim['x']))
		# modify the read array with cropping and binning
		a = self.modifyFrameImage(a,offset,crop_end,bin)
		return a

	def modifyFrameImage(self,a,offset,crop_end,bin):
		a = numpy.asarray(a,dtype=numpy.float32)
		a = a[offset['y']:crop_end['y'],offset['x']:crop_end['x']]
		if bin['x'] > 1:
			if bin['x'] == bin['y']:
				a = imagefun.bin(a,bin['x'])
			else:
				apDisplay.printError("Binnings in x,y are different")
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

	def __correctFrameImage(self,start_frame,nframe,use_full_raw_area=False):
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
		if not get_new_refs and start_frame != 0:
			apDisplay.printWarning("Imaging condition unchanged. Reference in memory will be used.")

		# o.k. to set attribute now that condition change is checked
		self.use_full_raw_area = use_full_raw_area
		if get_new_refs:
			# set camera info for loading frames
			self.setCameraInfo(nframe,use_full_raw_area)

		# load raw frames
		rawarray = self.sumupFrames(self.rawframe_dir,start_frame,nframe)
		if rawarray is False:
			return False
		if save_jpg:
			numpil.write(rawarray,'%s_raw.jpg' % ddtype,'jpeg')

		if not self.correct_dark_gain:
			apDisplay.printMsg('Use summed frame image without further correction')
			return rawarray

		# DARK CORRECTION
		if get_new_refs:
			# load dark 
			unscaled_darkarray = self.getSingleFrameDarkArray()
			self.unscaled_darkarray = unscaled_darkarray
		else:
			unscaled_darkarray = self.unscaled_darkarray
		if save_jpg:
			numpil.write(unscaled_darkarray,'%s_dark.jpg' % ddtype,'jpeg')

		corrected, dark_scale = self.darkCorrection(rawarray,unscaled_darkarray,nframe)
		if save_jpg:
			numpil.write(corrected,'%s_dark_corrected.jpg' % ddtype,'jpeg')
		if debug:
			self.scalefile.write('%s\t%.4f\n' % (start_frame,dark_scale))
		apDisplay.printMsg('..Dark Scale= %.4f' % dark_scale)

		# MASK CORRECTION
		if self.correct_frame_mask:
			if get_new_refs:
				apDisplay.printMsg('Making debris mask')
				mask = self.makeMaskArray(start_frame)
				self.mask = mask
				if save_jpg and mask.max() > mask.min():
					numpil.write(mask.astype(numpy.int)*255,'%s_mask.jpg' % ddtype,'jpeg')
			else:
				mask = self.mask


		# GAIN CORRECTION
		apDisplay.printMsg('Doing gain correction')
		if get_new_refs:
			scaled_brightarray = self.getScaledBrightArray(nframe)
			normdata = self.getRefImageData('norm')
			apDisplay.printWarning('Use Norm Reference %s' % (normdata['filename'],))
			if not self.use_GS and normdata:
				normarray = normdata['image']
			else:
				normarray = self.makeNorm(scaled_brightarray,self.unscaled_darkarray, dark_scale)
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
		if self.correct_frame_mask:
			if numpy.any(mask):
				apDisplay.printMsg('Doing mask correction')
				corrected = self.correctMaskRegion(corrected,mask,True)
		if save_jpg:
			numpil.write(corrected,'%s_gain_corrected.jpg' % ddtype,'jpeg')
		print 'corrected',arraystats.mean(corrected),corrected.min(),corrected.max()

		return corrected

	def getCorrectorPlan(self,camerainfo):
		plandata =  self.image['corrector plan']
		if plandata:
			plan = self.c_client.formatCorrectorPlan(plandata)
		else:
			plan, plandata = self.c_client.retrieveCorrectorPlan(self.camerainfo)
		return plan

	def makeMaskArray(self,start_frame_index):
		'''
		This function creates debris mask from a frame of the current image.
		Debris settle on dd may be processed in the integrated image used in
		gain correction but not on raw frames.  In such a case, a mask needs
		to be created to replace the values in the region with random values
		so that it does not create problem in alignment and ctf estimation.
		This function creates it dynamically.
		'''
		# These paramters probably only works in counted or super-resolution
		# mode where the debris is shown as continuous object but not random
		# noise
		nframe = 1
		sigma = 2
		thresh = 1 * nframe
		apDisplay.printMsg('  using %s' % self.image['filename'])
		apDisplay.printMsg('  frame index %d' % start_frame_index)
		# load raw frames
		oneframe = self.sumupFrames(self.rawframe_dir,start_frame_index,nframe)
		oneframe, dark_scale = self.darkCorrection(oneframe,self.unscaled_darkarray,nframe)
		# Filter and then threshold the result to show only debris
		mask=ndimage.gaussian_filter(oneframe,sigma)
		#mrc.write(mask,'filtered.mrc')
		mask = numpy.where(mask<=thresh,True,False)
		#mrc.write(mask.astype(numpy.int),'maska.mrc')
		last_clabels = 100
		clabels = 99 # fake label count to start
		apDisplay.printMsg('..Dilating segamented mask until stable')
		itr = 0
		while clabels < last_clabels:
			last_clabels = clabels
			mask = ndimage.morphology.binary_dilation(mask,ndimage.morphology.generate_binary_structure(2,1),2)
			regions,clabels = ndimage.label(mask)
			itr += 2
		apDisplay.printMsg('    Completed in %d iterations' % itr)
		if clabels == 1 and numpy.all(mask):
			mask = numpy.logical_not(mask)
			apDisplay.printWarning('No debris found to be masked')
		else:
			apDisplay.printMsg('    %d mask segment(s) found' % clabels)
		#mrc.write(mask.astype(numpy.int),'maskb.mrc')
		return mask

	def correctMaskRegion(self,image,mask,use_random=True):
		'''
		Fill in mask region with either random number of normal distribution
		or the mean of the image.
		'''
		stats = arraystats.mean(image),arraystats.std(image)
		if use_random:
			fill_values = stats[1] * numpy.random.randn(image.shape[0],image.shape[1])+stats[0]
		else:
			fill_values = stats[1] * numpy.ones(image.shape)
		masked = numpy.where(mask,fill_values,image)
		return masked
		
	def modifyImageArray(self,array):
		cdata = self.getAlignedCameraEMData()
		if not cdata:
			# Only bin the image if not for alignment with dosefgpu_driftcorr program
			additional_binning = self.getNewBinning()
			return imagefun.bin(array,additional_binning)
		else:
			# Have cdata only if alignment will be done
			additional_binning = cdata['binning']['x'] / self.getImageCameraEMData()['binning']['x']
			# Need squared image for alignment
			array = imagefun.bin(array,additional_binning)
			array = array[cdata['offset']['y']:cdata['offset']['y']+cdata['dimension']['y'],cdata['offset']['x']:cdata['offset']['x']+cdata['dimension']['x']]
		apDisplay.printMsg('frame image shape is now x=%d,y=%d' % (array.shape[1],array.shape[0]))
		return array
		
	def makeCorrectedFrameStack(self, use_full_raw_area=False):
		'''
		Creates a file of gain/dark corrected stack of frames
		'''
		sys.stdout.write('\a')
		sys.stdout.flush()
		total_frames = self.getNumberOfFrameSaved()
		half_way_frame = int(total_frames // 2)
		first = 0
		for start_frame in range(first,first+total_frames):
			array = self.__correctFrameImage(start_frame,1,use_full_raw_area)
			# if non-fatal error occurs, end here
			if array is False:
				break
			array = self.modifyImageArray(array)
			apDisplay.printMsg('final frame shape to put in stack x=%d,y=%d' % (array.shape[1],array.shape[0]))
			if start_frame == first:
				# overwrite old stack mrc file
				mrc.write(array,self.framestackpath)
			elif start_frame == half_way_frame:
				# Only calculate stats if half way in the stack making to save time
				mrc.append(array,self.framestackpath,True)
			else:
				mrc.append(array,self.framestackpath,False)
		return self.framestackpath

	def setNewBinning(self,bin):
		'''
		Camera binning of the stack.
		'''
		self.stack_binning = bin

	def getNewBinning(self):
		return self.stack_binning

	def getImageCameraEMData(self):
		return leginondata.CameraEMData(initializer=self.image['camera'])

	def setAlignedCameraEMData(self):
		'''
		DD aligned image will be uploaded into database with a square
		camera dimension at the center and the specificed binning
		'''
		camdata = self.getImageCameraEMData()
		mindim = min(camdata['dimension']['x'],camdata['dimension']['y'])
		camerasize = {}
		newbin = self.getNewBinning()
		for axis in ('x','y'):
			if camdata['binning'][axis] != 1 or camdata['offset'][axis] != 0:
				apDisplay.displayError('Starting image must be unbinned and at full dimension for now')
			if newbin < camdata['binning'][axis]:
				apDisplay.displayError('can not change to smaller binning')
			camerasize[axis] = (camdata['offset'][axis]*2+camdata['dimension'][axis])*camdata['binning'][axis]
			camdata['dimension'][axis] = mindim * camdata['binning'][axis] / newbin
			camdata['binning'][axis] = newbin
			camdata['offset'][axis] = (camerasize[axis]/newbin -camdata['dimension'][axis])/2
		self.aligned_camdata = camdata

	def getAlignedCameraEMData(self):
		return self.aligned_camdata
		
	def updateFrameStackHeaderImageStats(self,stackpath):
		'''
		This function update the header of dosefgpu_driftcorr corrected stack file without array stats.
		'''
		if not os.path.isfile(stackpath):
			return
		header = mrc.readHeaderFromFile(stackpath)
		if header['amax'] == header['amin']:
			return
		apDisplay.printMsg('Update the stack header with middle slice')
		total_frames = header['nz']
		half_way_frame = int(total_frames // 2)
		array = mrc.read(stackpath,half_way_frame)
		stats = arraystats.all(array)
		header['amin'] = stats['min']+0
		header['amax'] = stats['max']+0
		header['amean'] = stats['mean']+0
		header['rms'] = stats['std']+0
		mrc.update_file_header(stackpath, header)
		
	def alignCorrectedFrameStack(self):
		'''
		Xueming Li's gpu program for aligning frames using all defaults
		Valid square gain/dark corrected ddstack is the input.
		'''
		rundir = self.getRunDir()
		cmd = 'dosefgpu_driftcorr %s -fcs %s -ssc 1 -fct %s' % (self.framestackpath,self.aligned_sumpath,self.aligned_stackpath)
		apDisplay.printMsg('Running: %s'% cmd)
		self.proc = subprocess.Popen(cmd, shell=True)
		self.proc.wait()
		if os.path.isfile(self.aligned_stackpath):
			self.updateFrameStackHeaderImageStats(self.aligned_stackpath)
		else:
			apDisplay.printError('dosefgpu_driftcorr FAILED: \n%s not created.' % os.path.basename(self.aligned_stackpath))

	def makeAlignedImageData(self):
		'''
		Prepare ImageData to be uploaded after alignment
		'''
		camdata = self.getAlignedCameraEMData()
		align_presetdata = leginondata.PresetData(initializer=self.image['preset'])
		if align_presetdata is None:
			old_name = 'ma'
			align_presetdata = leginondata.PresetData(
					name='ma-a',
					magnification=self.image['scope']['magnification'],
					defocus=self.image['scope']['defocus'],
					tem = self.image['scope']['tem'],
					ccdcamera = camdata['ccdcamera'],
			)
		else:
			old_name = align_presetdata['name']
			align_presetdata['name'] = old_name+'-a'
		align_presetdata['dimension'] = camdata['dimension'],
		align_presetdata['binning'] = camdata['binning'],
		align_presetdata['offset'] = camdata['offset'],
		align_presetdata['exposure time'] = camdata['exposure time']
		# make new imagedata with the align_preset amd aligned CameraEMData
		imagedata = leginondata.AcquisitionImageData(initializer=self.image)
		imagedata['preset'] = align_presetdata
		imagefilename = imagedata['filename']
		bits = imagefilename.split(old_name)
		before_string = old_name.join(bits[:-1])
		newfilename = align_presetdata['name'].join((before_string,bits[-1]))
		imagedata['camera'] = camdata
		imagedata['camera']['align frames'] = True
		imagedata['image'] = mrc.read(self.aligned_sumpath)
		imagedata['filename'] = apDBImage.makeUniqueImageFilename(imagedata,old_name,align_presetdata['name'])
		return imagedata


	def isReadyForAlignment(self):
		'''
		Check to see if frame stack creation is completed.
		'''
		rundir = self.getRunDir()
		if not self.waitForPathExist(self.framestackpath,60):
			apDisplay.printWarning('Stack making not started, Skipping')
			return False
		# Unless the _Log.txt is made, even if faked, the frame stack is not completed
		logpath = self.framestackpath[:-4]+'_Log.txt'
		if not self.waitForPathExist(logpath,60):
			apDisplay.printWarning('Stack making not finished, Skipping')
			return False
		return True	


class DDStackProcessing(DirectDetectorProcessing):
	'''
	Class to use gain/dark corrected DDStack. Need to setImage and then setFrameStackPath so
	that the ddstackrun can be determined from image if not specified.
	'''
	def getIsAligned(self):
		return self.image['preset'] is not None and '-a' in self.image['preset']['name']

	def setDDStackRun(self,ddstackrunid=None):
		if ddstackrunid:
			# This works with image set
			ddstackrun = appiondata.ApDDStackRunData.direct_query(ddstackrunid)
		else:
			if self.getIsAligned():
				# This works if self.image is set
				ddstackrun = self.getAlignImagePairData(None,query_source=False)['ddstackrun']
			else:
				apDisplay.printError('Image not from aligned ddstack run.  Can not determine stack location without ddstack id')
		self.ddstackrun = ddstackrun

	def getDDStackRun(self):
		apDisplay.printMsg('Stack is from %s (id = %d)' % (self.ddstackrun['runname'],self.ddstackrun.dbid))
		return self.ddstackrun

	def setImageData(self,imagedata):
		super(DDStackProcessing,self).setImageData(imagedata)

	def setFrameStackPath(self,ddstackrunid=None):
		self.setDDStackRun(ddstackrunid)
		self.setRunDir(self.getDDStackRun()['path']['path'])
		super(DDStackProcessing,self).setFrameStackPath()

	def getDDStackFrameSumImage(self,start_frame,nframe,roi=None):
		'''
		DDStack are gain/dark corrected and may or may not be aligned
		'''
		if not os.path.isfile(self.framestackpath):
			apDisplay.printError('No DD Stack to make image from')
		apDisplay.printMsg('Getting summed image from %s' % self.framestackpath)
		apDisplay.printMsg(' summing total of %d images start at frame %d' % (nframe,start_frame))
		stack = mrc.mmap(self.framestackpath)
		if not roi:
			sum = numpy.sum(stack[start_frame:start_frame+nframe,:,:],axis=0)
		else:
			apDisplay.printMsg(' crop range of (%d,%d) to (%d,%d)' % (rot['x'][0],roi['x'][1]-1,roi['y'][0],roi['y'][1]-1))
			sum = numpy.sum(stack[start_frame:start_frame+nframe,roi['y'][0]:roi['y'][1],roi['x'][0]:roi['x'][1]],axis=0)
		return sum

if __name__ == '__main__':
	dd = DirectDetectorProcessing()
	dd.setRunDir('./')
	dd.setImageId(1991218)
	dd.setAlignedCameraEMData()
	start_frame = 0
	mrc.write(corrected,'corrected_frame%d_%d.mrc' % (start_frame,nframe))
