#!/usr/bin/env python

import os
import sys
import numpy
import time
import math
import scipy.stats
import scipy.ndimage as ndimage
ma = numpy.ma
import shutil
from pyami import mrc,imagefun,arraystats,numpil
from leginon import correctorclient,leginondata,ddinfo
from appionlib import apDisplay, apDatabase,apDBImage, appiondata,apFile
import subprocess
import socket
import itertools

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
		apDisplay.printError('Can not determine DD camera type. Did you save frames?')
	if 'GatanK2' in dcamdata['name']:
		from appionlib import apK2process
		return apK2process.GatanK2Processing(wait_flag)
	elif 'DE' in dcamdata['name']:
		from appionlib import apDEprocess
		return apDEprocess.DEProcessing(wait_flag)
	elif 'TIA' in dcamdata['name'] or 'Falcon' in dcamdata['name']:
		from appionlib import apFalconProcess
		return apFalconProcess.FalconProcessing(wait_flag)
	elif 'Appion' in dcamdata['name']:
		from appionlib import apAppionCamProcess
		return apAppionCamProcess.AppionCamFrameProcessing(wait_flag)
	elif 'Sim' in dcamdata['name']:
		from appionlib import apSimFrameProcess
		return apSimFrameProcess.SimFrameProcessing(wait_flag)
	else:
		apDisplay.printError('Unknown frame camera name %s' % dcamdata['name'])

class DirectDetectorProcessing(object):
	def __init__(self):
		'''
		Base class for DD processing
		'''
		self.image = None
		self.setRunDir(os.getcwd())
		self.setTempDir()
		self.sumframelist = None
		self.altchannel_cycler = itertools.cycle([False,True])
		self.frame_modified = False

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
		# dark/gain corrected stack is saved here
		self.setFrameStackPath()

	def getImageData(self):
		return self.image

	def setFrameStackPath(self):
		'''
		Frame stack path set by this function is gain/dark corrected. It can either
		be aligned or not.
		'''
		imagename = self.image['filename']

		if self.image['camera']['align frames']:
			# Use pair data to find the align source image
			result = self.getAlignImagePairData(None,query_source=False)
			if result is False:
				# This means that frames were aligned by camera algorithm and frame stack was not saved
				return False
			source_imagedata = result['source']
			imagename = source_imagedata['filename']
		self.tempframestackpath = os.path.join(self.tempdir,imagename+'_st.mrc')
		self.framestackpath = os.path.join(self.rundir,imagename+'_st.mrc')
		
	def getFrameStackPath(self,temp=False):
		if not temp:
			return self.tempframestackpath
		else:
			return self.framestackpath	
		
	def setTempDir(self,tempdir=None):
		'''
		This is the rundir for ddstack
		'''
		if tempdir:
			self.tempdir = tempdir
		else:
			self.tempdir = self.rundir

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
		nframe = imagedata['camera']['nframes']
		if nframe is None:
			# older data or k2
			nframe =  int(imagedata['camera']['exposure time'] / imagedata['camera']['frame time'])
		# avoid 0 for dark image scaling and frame list creation
		if nframe == 0:
			nframe = 1
		return nframe

	def setSquareOutputShape(self,value=False):
		self.square_output = value

	def getUsedFramesFromImageData(self,imagedata):
		return imagedata['camera']['use frames']

	def checkFrameListRange(self,framelist):
		# check parameter
		if not self.image:
			apDisplay.printError("You must set an image for the operation")
		if min(framelist) not in range(self.totalframe):
			apDisplay.printError("Starting Frame not in saved raw frame range, can not be processed")
		framelength_original = len(framelist)
		framelist_original = list(framelist)
		while max(framelist) >= self.totalframe:
			del framelist[framelist.index(max(framelist))]
		if len(framelist) < framelength_original:
			apDisplay.printWarning( "%s instead of %s frames will be used since not enough frames are saved." % (framelist,framelist_original))
		return framelist

	def getAllAlignImagePairData(self,ddstackrundata,query_source=True):
		'''
		This returns DD all AlignImagePairData. source query may have more
		than one result.  This function gets all not just the most recent one.
		'''
		if query_source:
			q = appiondata.ApDDAlignImagePairData(source=self.image,ddstackrun=ddstackrundata)
		else:
			q = appiondata.ApDDAlignImagePairData(result=self.image,ddstackrun=ddstackrundata)
		r = q.query()
		return r

	def getAlignImagePairData(self,ddstackrundata,query_source=True):
		'''
		This returns DD AlignImagePairData if exists, returns False if not.
		Image set in the class instance can either be the source or result of the alignment
		'''
		results = self.getAllAlignImagePairData(ddstackrundata,query_source)
		if results:
			return results[0]
		else:
			return False

	def getStillFrames(self,threshold):
		'''
		Returns frames that shift less than threshold (in pixels) relative to either the frame before
		or the frame after.
		'''
		stills = []
		logfile = self.framestackpath[:-4]+'_Log.txt'
		if not os.path.isfile(logfile):
			apDisplay.printWarning('No alignment log file %s found for thresholding drift' % logfile)
			return False
		positions = ddinfo.readPositionsFromAlignLog(logfile)
		# place holder for first frame shift duplication
		shifts = [None,]
		for p in range(len(positions)-1):
			shift = math.hypot(positions[p][0]-positions[p+1][0],positions[p][1]-positions[p+1][1])
			shifts.append(shift)
		# duplicate first and last shift for the end points
		shifts.append(shifts[-1])
		shifts[0] = shifts[1]
		# pick out passed frames
		for i in range(len(shifts[:-1])):
			# keep the frame if at least one shift around the frame is small enough
			if min(shifts[i],shifts[i+1]) < threshold:
				# index is off by 1 because of the duplication
				stills.append(i)
		return stills

	def getFrameList(self,params):
		'''
		Get list of frames
		'''
		# frame list according to start frame and number of frames
		if 'nframe' not in params.keys() or not params['nframe']:
			if 'startframe' not in params.keys() or params['startframe'] is None:
				framelist = range(self.getNumberOfFrameSavedFromImageData(self.image))
			else:
				framelist = range(params['startframe'],self.getNumberOfFrameSavedFromImageData(self.image))
		else:
			framelist = range(params['startframe'],params['startframe']+params['nframe'])
		if 'driftlimit' not in params.keys() or not params['driftlimit']:
			return framelist
		else:
			# drift limit considered
			stillframes = self.getStillFrames(params['driftlimit'] / params['apix'])
			if stillframes is False:
				return framelist
			framelist = list(set(framelist).intersection(set(stillframes)))
			framelist.sort()
			apDisplay.printMsg('Limit frames used to %s' % (framelist,))
			return framelist

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
		self.rawframetype = None
		self.rawtransfer_wait = 20.0
		self.framestackpath = None
		self.stack_binning = 1
		self.correct_dark_gain = True
		self.correct_frame_mask = False
		self.aligned_camdata = None
		self.square_output = False
		# change this to True for loading bias image for correction
		self.use_full_raw_area = False
		self.use_bias = False
		self.use_GS = False
		self.use_gpu_flat = False
		self.gpuid = 0
		self.keep_stack = True
		self.save_aligned_stack = True
		self.setTrimingEdge(0)
		self.alignparams = {}
		self.hostname = socket.gethostname().split('.')[0]
		self.setUseAlternativeChannelReference(False)
		self.setCycleReferenceChannels(False)
		self.setDefaultImageForReference(0)
		if debug:
			self.log = open('newref.log','w')
			self.scalefile = open('darkscale.log','w')

	def setImageData(self,imagedata,ignore_raw=False):
		super(DDFrameProcessing,self).setImageData(imagedata)
		if not ignore_raw:
			self.__setRawFrameInfoFromImage()
		else:
			self.__setRawFrameInfoFromDDStack()
		if debug:
			apDisplay.printMsg('%s' % (self.image['filename']))
			apDisplay.printMsg('%s' % ( self.framestackpath))
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

	def setUseGPUFlat(self,use_gpu_flat):
		self.use_gpu_flat = use_gpu_flat

	def getUseGPUFlat(self):
		return self.use_gpu_flat

	def setGPUid(self,gpuid):
		self.gpuid = gpuid

	def getSingleFrameDarkArray(self):
		try:
			darkdata = self.getRefImageData('dark')
			nframes = self.getNumberOfFrameSavedFromImageData(darkdata)
			return darkdata['image'] / nframes
		except:
			dimension = self.getDefaultDimension()
			return numpy.zeros((dimension['y'],dimension['x']))

	def getFrameNameFromNumber(self,frame_number):
		raise NotImplementedError()

	def OldgetSingleFrameDarkArray(self):
		# work around for the bug in DE server between 11sep07 and 11nov22
		return self.getRefImageData('dark')['image']

	def getRawFramesName(self):
		return self.framesname

	def setRawFrameDir(self,path):
		if debug:
			apDisplay.printMsg('setting rawframedir %s' % (path,))
		self.rawframe_dir = path

	def getRawFrameDir(self):
		return self.rawframe_dir

	def getRawFrameStackPath(self):
		if self.getRawFrameType() == 'stack':
			return self.getRawFrameDir()
		else:
			return self.makeRawFrameStack()

	def setRawFrameType(self,frametype='singles'):
		if frametype in ('singles','stack'):
			self.rawframetype = frametype

	def getRawFrameType(self):
		if not self.rawframetype:
			if self.image:
				# Do this only on the first image
				self.setRawFrameType(ddinfo.getRawFrameType(self.image['session']['frame path']))
			else:
				apDisplay.printError('RawFrameType not set')
		return self.rawframetype

	def getFrameNamePattern(self,framedir):
		pass

	def getRawFrameDirFromImage(self,imagedata):
		# strip off DOS path in rawframe directory name 
		rawframename = imagedata['camera']['frames name'].split('\\')[-1]
		if not rawframename:
			apDisplay.printWarning('No Raw Frame Saved for %s' % imagedata['filename'])
		if imagedata['session']['frame path']:
			 rawframe_basepath = imagedata['session']['frame path']
		else:
			# raw frames are saved in a subdirctory of image path pre-3.0
			imagepath = imagedata['session']['image path']
			rawframe_basepath = ddinfo.getRawFrameSessionPathFromSessionPath(imagepath)
		rawframedir = os.path.join(rawframe_basepath,'%s.frames' % imagedata['filename'])
		if not self.waitForPathExist(rawframedir,self.rawtransfer_wait):
			apDisplay.printError('Raw Frame Dir %s does not exist.' % rawframedir)
		self.getFrameNamePattern(rawframedir)
		return rawframedir

	def setCycleReferenceChannels(self, value=False):
		self.cycle_ref_channels = value

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

	def getCorrectedImageData(self):
		'''
		Returns image for getting reference.  If this is not set externally,
		the image being processed is returned
		'''
		imageid = self.getDefaultImageForReference()
		if imageid:
			imagedata = leginondata.AcquisitionImageData().direct_query(imageid)
			if self.image['camera']['ccdcamera']['name'] != imagedata['camera']['ccdcamera']['name']:
				apDisplay.printError('Default reference image id=%d not from the same camera as the data' % (imageid))
				apDisplay.printMsg('Reference comes from %s' % imagedata['filename'])
			return imagedata
		else:
			apDisplay.printMsg('Reference comes from current image')
			return self.image

	def getRefImageData(self,reftype):
		refdata = self._getRefImageData(reftype)
		if self.getUseAlternativeChannelReference():
			oldrefname = refdata['filename']
			refdata = self.c_client.getAlternativeChannelReference(reftype,refdata)
			#apDisplay.printWarning('Use Alternative Channel Reference %s instead of %s' % (refdata['filename'],oldrefname))
		return refdata

	def _getRefImageData(self,reftype):
		imagedata = self.getCorrectedImageData()
		if not self.use_full_raw_area:
			refdata = imagedata[reftype]
			#if self.image.dbid <= 1815252 and self.image.dbid >= 1815060:
				# special case to back correct images with bad references
				#refdata = apDatabase.getRefImageDataFromSpecificImageId(reftype,1815281)
		else:
			# use most recent CorrectorImageData
			# TO DO: this should research only ones before the image is taken.
			scopedata = imagedata['scope']
			channel = imagedata['channel']
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
		# total number of frames saved
		self.totalframe = self.getNumberOfFrameSaved()

	def __setRawFrameInfoFromDDStack(self):
		'''
		set totalframe only if ddstack is made
		'''
		#self.nframe = self.getNumberOfFrameSaved()
		self.totalframe = self.getNumberOfFrameSaved()

	def setCameraInfo(self,nframe,use_full_raw_area):
		'''
		set cemrainfo attributes with current values of the image
		'''
		apDisplay.printMsg('Setting new camera info....')
		self.camerainfo = self.__getCameraInfoFromImage(nframe,use_full_raw_area)

	def getTrimingEdge(self):
		return self.trim

	def setTrimingEdge(self,value):
		self.trim = int(value)

	def trimArray(self,array):
		t = self.getTrimingEdge()
		return array[t:array.shape[0]-t,t:array.shape[1]-t]

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
		if not camerainfo['norm']:
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
			
	def loadOneRawFrame(self,rawframe_dir,frame_number):
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
			apDisplay.printWarning('Frame File %s does not exist. Wait for 1 min.' % rawframe_path)
			time.sleep(60)
			waitmin += 1
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

	def handleOldFrameOrientation(self):
		# No flip rotation as default
		return False, 0

	def getImageFrameOrientation(self):
		frame_flip = self.image['camera']['frame flip']
		frame_rotate = self.image['camera']['frame rotate']
		apDisplay.printDebug('frame flip %s, frame_rotate %s' % (frame_flip,frame_rotate))
		if frame_rotate is None:
			# old data have no orientation record
			frame_flip,frame_rotate = self.handleOldFrameOrientation()
		apDisplay.printDebug('frame flip %s, frame_rotate %s' % (frame_flip,frame_rotate))
		return frame_flip, frame_rotate

	def modifyFrameImage(self,a,offset,crop_end,bin):
		a = numpy.asarray(a,dtype=numpy.float32)
		frame_flip, frame_rotate = self.getImageFrameOrientation()
		if frame_flip:
			if frame_rotate and frame_rotate == 2:
				# Faster to just flip left-right than up-down flip + rotate
				apDisplay.printColor("flipping the frame left-right",'blue')
				a = numpy.fliplr(a)
				frame_rotate = 0
			else:
				apDisplay.printColor("flipping the frame up-down",'blue')
				a = numpy.flipud(a)
			self.frame_modified = True
		if frame_rotate:
			apDisplay.printColor("rotating the frame by %d degrees" % (frame_rotate*90,),'blue')
			a = numpy.rot90(a,frame_rotate)
			self.frame_modified = True
		a = a[offset['y']:crop_end['y'],offset['x']:crop_end['x']]
		if bin['x'] > 1:
			if bin['x'] == bin['y']:
				a = imagefun.bin(a,bin['x'])
			else:
				apDisplay.printError("Binnings in x,y are different")
		return a

	def sumupFrames(self,rawframe_dir,framelist):
		'''
		Load a number of consecutive raw frames from known directory,
		sum them up, and return as numpy array.
		nframe = total number of frames to sum up.
		
		'''
		start_frame = framelist[0]
		apDisplay.printMsg( 'Summing up %d Frames %s ....' % (len(framelist),framelist))
		for frame_number in framelist:
			if frame_number == start_frame:
				rawarray = self.loadOneRawFrame(rawframe_dir,frame_number)
				if rawarray is False:
					return False
			else:
				oneframe = self.loadOneRawFrame(rawframe_dir,frame_number)
				if oneframe is False:
					return False
				rawarray += oneframe
		return rawarray

	def correctFrameImage(self,framelist,use_full_raw_area=False):
		corrected = self.__correctFrameImage(framelist,use_full_raw_area)
		if corrected is False:
			apDisplay.printError('Failed to correct Image')
		else:
			return corrected

	def test__correctFrameImage(self,framelist,use_full_raw_area=False):
		framelist = self.checkFrameListRange(framelist)
		self.use_full_raw_area = use_full_raw_area
		nframe = len(framelist)
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

	def __correctFrameImage(self,framelist,use_full_raw_area=False):
		'''
		This returns corrected numpy array of given start and total number
		of raw frames of the current image set for the class instance.  
		Full raw frame area can be returned as an option.
		'''
		framelist = self.checkFrameListRange(framelist)
		nframe = len(framelist)
		start_frame = framelist[0]
		get_new_refs = self.__conditionChanged(nframe,use_full_raw_area)

		# local restriction
		if not hasattr(self,'unscaled_darkarray') or not hasattr(self,'normarray'):
			get_new_refs = True
		if self.cycle_ref_channels:
			# alternate channels
			get_new_refs = True
			self.setUseAlternativeChannelReference(self.altchannel_cycler.next())
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
		rawarray = self.sumupFrames(self.rawframe_dir,framelist)
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
				if not os.path.isfile("variance.mrc"):
					apDisplay.printMsg('Making debris mask')
					mask = self.makeMaskArray(start_frame)
					mrc.write(mask, "variance.mrc")
				else:
					mask = mrc.read("variance.mrc")
				# experimental.  Need to create variance.map to run
#				apDisplay.printMsg('Making variance threshold mask')
#				mask = self.makeVarianceMaskArray()
				self.mask = mask
				if save_jpg and mask.max() > mask.min():
					numpil.write(mask.astype(numpy.int)*255,'%s_mask.jpg' % ddtype,'jpeg')
			else:
				mask = self.mask


		# GAIN CORRECTION
		apDisplay.printMsg('Doing gain correction')
		if get_new_refs:
			normdata = self.getRefImageData('norm')
			if not self.use_GS and normdata:
				apDisplay.printWarning('Ref Session Path:%s' % normdata['session']['image path'])
				apDisplay.printWarning('Use Norm Reference %s' % (normdata['filename'],))
				normarray = normdata['image']
			else:
				scaled_brightarray = self.getScaledBrightArray(nframe)
				apDisplay.printWarning('Corresponding Bright Reference %s' % (normdata['bright']['filename'],))
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
		#Clipping is turned off to avoid artifacts in analog DD
		#apDisplay.printMsg('Cliping corrected image')
		#corrected = numpy.clip(corrected,0,10000)
		if self.correct_frame_mask:
			if numpy.any(mask):
				apDisplay.printMsg('Doing mask correction')
				corrected = self.correctMaskRegion(corrected,mask,True)
		if save_jpg:
			numpil.write(corrected,'%s_gain_corrected.jpg' % ddtype,'jpeg')

		return corrected

	def getCorrectorPlan(self,camerainfo):
		if not camerainfo:
			return None
		imagedata = self.getCorrectedImageData()
		plandata =  imagedata['corrector plan']
		if plandata:
			plan = self.c_client.formatCorrectorPlan(plandata)
		else:
			plan, plandata = self.c_client.retrieveCorrectorPlan(self.camerainfo)
		return plan

	def hasBadPixels(self):
		# set camerainfo so to find corretor plan
		self.setCameraInfo(1,self.use_full_raw_area)
		plan = self.getCorrectorPlan(self.camerainfo)
		if plan and (plan['columns'] or plan['rows'] or plan['pixels']):
			return True
		return False

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
		framelist = range(start_frame_index,start_frame_index+nframe)
		oneframe = self.sumupFrames(self.rawframe_dir,framelist)
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

	def makeLowVarianceMask(self,var_map,thresh=10):
		masked = ma.masked_less_equal(var_map,thresh)
		return masked.mask

	def makeHighVarianceMask(self,var_map,thresh=1000000):
		masked = ma.masked_greater_equal(var_map,thresh)
		return masked.mask

	def makeVarianceMaskArray(self,variancepath='variance.mrc'):
		v = mrc.read(variancepath)
		v1 = self.makeLowVarianceMask(v, 0.7)
		v2 = self.makeHighVarianceMask(v,10.0)
		return numpy.logical_or(v1,v2)

	def correctMaskRegion(self,image,mask,use_random=True):
		'''
		Fill in mask region with either random number of normal distribution
		or the mean of the image.
		'''
		stats = arraystats.mean(image),arraystats.std(image)
		if use_random:
			fill_values = stats[1] * numpy.random.randn(image.shape[0],image.shape[1])+stats[0]
		else:
			fill_values = stats[0] * numpy.ones(image.shape)
		masked = numpy.where(mask,fill_values,image)
		return masked
		
	def modifyImageArray(self,array):
		if self.getNewBinning() == 1 and not self.square_output:
			return array
		cdata = self.getAlignedCameraEMData()
		if not cdata:
			# Only bin the image if not for alignment with dosefgpu_driftcorr program
			additional_binning = self.getNewBinning()
			return imagefun.bin(array,additional_binning)
		else:
			# Have cdata only if alignment will be done
			additional_binning = cdata['binning']['x'] / self.getImageCameraEMData()['binning']['x']
			# Need squared image for alignment
			if self.square_output:
				if array.shape[0] == array.shape[1]:
					return array
				array = imagefun.bin(array,additional_binning)
				array = array[cdata['offset']['y']:cdata['offset']['y']+cdata['dimension']['y'],cdata['offset']['x']:cdata['offset']['x']+cdata['dimension']['x']]
		apDisplay.printMsg('frame image shape is now x=%d,y=%d' % (array.shape[1],array.shape[0]))
		return array

	def makeRawFrameStack(self):
		'''
		Creates a file of non-gain/dark corrected stack of frames
		'''
		sys.stdout.write('\a')
		sys.stdout.flush()
		rawframe_dir = self.getRawFrameDir()
		total_frames = self.getNumberOfFrameSaved()
		half_way_frame = int(total_frames // 2)
		first = 0
		frameprocess_dir = os.path.dirname(self.tempframestackpath)
		rawframestack_path = os.path.join(frameprocess_dir,self.image['filename']+'_raw_st.mrc')
		for start_frame in range(first,first+total_frames):
			array = self.loadOneRawFrame(rawframe_dir,start_frame)
			array = self.modifyImageArray(array)
			# if non-fatal error occurs, end here
			if array is False:
				break
			if start_frame == first:
				# overwrite old stack mrc file
				mrc.write(array,rawframestack_path)
			elif start_frame == half_way_frame:
				# Only calculate stats if half way in the stack making to save time
				mrc.append(array,rawframestack_path,True)
			else:
				mrc.append(array,rawframestack_path,False)
		return rawframestack_path

	def makeRawFrameStackForOneStepCorrectAlign(self, use_full_raw_area=False):
		'''
		Creates a file of non gain/dark corrected stack of frames
		'''
		self.setupDarkNormMrcs(use_full_raw_area)
		rawframestack_path = self.getRawFrameStackPath()
		if not os.path.isfile(self.tempframestackpath) and os.path.isfile(rawframestack_path):
			# frame flipping of the mrc ddstack
			frame_flip, frame_rotate = self.getImageFrameOrientation()
			if frame_flip or frame_rotate and not self.frame_modified:
				if frame_rotate:
					apDisplay.printError("stack rotation not implemented")
				if frame_flip:
					apDisplay.printColor("flipping frame stack",'blue')
					a = mrc.read(rawframestack_path)
					# 3D array left-right flip creates the effect of up-down flip on axis 1 and 2
					a = numpy.fliplr(a)
					if self.getTrimingEdge() > 0:
						a = self.trimArray(a)
					mrc.write(a,self.tempframestackpath)
			else:
				os.symlink(rawframestack_path,self.tempframestackpath)
			apDisplay.printMsg('link %s to %s.' % (rawframestack_path, self.tempframestackpath))
		return self.tempframestackpath

	def makeCorrectedFrameStack(self, use_full_raw_area=False):
		return self.makeCorrectedFrameStack_cpu(use_full_raw_area)

	def makeDosefgpuGainCorrectionParams(self):
		self.setupDarkNormMrcs(False)
		cmd = ''
		if self.dark_path:
			cmd += " -fdr %s" % self.dark_path
		if self.norm_path:
			cmd += " -fgr %s" % self.norm_path
		return cmd

	def setupDarkNormMrcs(self, use_full_raw_area=False):
		'''
		Creates local reference files for gain/dark-correcting the stack of frames
		'''
		if not self.correct_dark_gain:
			self.dark_path = None
			self.norm_path = None
			return
		sys.stdout.write('\a')
		sys.stdout.flush()
		if use_full_raw_area is True:
			apDisplay.displayError('use_full_raw_area when image is cropped is not implemented for gpu')
		frameprocess_dir = os.path.dirname(self.tempframestackpath)
		get_new_refs = self.__conditionChanged(1,use_full_raw_area)
		# o.k. to set attribute now that condition change is checked
		self.use_full_raw_area = use_full_raw_area
		# at least write dark and norm image once
		if get_new_refs or not hasattr(self,'dark_path'):
			# set camera info for loading frames
			self.setCameraInfo(1,use_full_raw_area)

			# output dark
			unscaled_darkarray = self.getSingleFrameDarkArray()
			self.dark_path = os.path.join(frameprocess_dir,'dark-%s-%d.mrc' % (self.hostname,self.gpuid))
			mrc.write(unscaled_darkarray,self.dark_path)

			# output norm
			normdata = self.getRefImageData('norm')
			if normdata['bright']:
				apDisplay.printWarning('From Bright Reference %s' % (normdata['bright']['filename'],))
			if self.use_gpu_flat:
				normarray = normdata['image']
				self.norm_path = os.path.join(frameprocess_dir,'norm-%s-%d.mrc' % (self.hostname,self.gpuid))
				apDisplay.printWarning('Save Norm Reference %s to %s' % (normdata['filename'],self.norm_path))
				mrc.write(normarray,self.norm_path)
	

	def makeCorrectedFrameStack_cpu(self, use_full_raw_area=False):
		'''
		Creates a file of gain/dark corrected stack of frames
		'''
		sys.stdout.write('\a')
		sys.stdout.flush()
		total_frames = self.getNumberOfFrameSaved()
		half_way_frame = int(total_frames // 2)
		first = 0
		for start_frame in range(first,first+total_frames):
			apDisplay.printMsg('Processing New Frame::::: ')
			array = self.__correctFrameImage([start_frame,],use_full_raw_area)
			# if non-fatal error occurs, end here
			if array is False:
				break
			array = self.modifyImageArray(array)
			if self.getTrimingEdge() > 0:
				array = self.trimArray(array)
			apDisplay.printMsg('final frame shape to put in stack x=%d,y=%d' % (array.shape[1],array.shape[0]))
			if start_frame == first:
				# overwrite old stack mrc file
				mrc.write(array,self.tempframestackpath)
			elif start_frame == half_way_frame:
				# Only calculate stats if half way in the stack making to save time
				mrc.append(array,self.tempframestackpath,True)
			else:
				mrc.append(array,self.tempframestackpath,False)
		return self.tempframestackpath

	def setNewBinning(self,bin):
		'''
		Camera binning of the stack.
		'''
		self.stack_binning = bin

	def getNewBinning(self):
		return self.stack_binning

	def setKeepStack(self,is_keepstack):
			self.keep_stack = is_keepstack
			if is_keepstack:
				self.save_aligned_stack = True

	def getImageCameraEMData(self):
		return leginondata.CameraEMData(initializer=self.image['camera'])

	def setAlignedCameraEMData(self):
		'''
		DD aligned image will be uploaded into database with the specified binning.
		If self.square_output is True, with a square
		camera dimension at the center and the specificed binning
		'''
		camdata = self.getImageCameraEMData()
		if self.square_output:
			mindim = min(camdata['dimension']['x'],camdata['dimension']['y'])
			dims = {'x':mindim,'y':mindim}
		else:
			dims = camdata['dimension']
		camerasize = {}
		newbin = self.getNewBinning()
		t = self.getTrimingEdge()
		for axis in ('x','y'):
			if camdata['binning'][axis] != 1 or camdata['offset'][axis] != 0:
				apDisplay.printError('Starting image must be unbinned and at full dimension for now')
			if newbin < camdata['binning'][axis]:
				apDisplay.displayError('can not change to smaller binning')
			camerasize[axis] = (camdata['offset'][axis]*2+camdata['dimension'][axis])*camdata['binning'][axis]
			camdata['dimension'][axis] = dims[axis] * camdata['binning'][axis] / newbin - 2*t / newbin
			camdata['binning'][axis] = newbin
			camdata['offset'][axis] = (camerasize[axis]/newbin -camdata['dimension'][axis])/2
		framelist = self.getAlignedSumFrameList()
		if framelist:
			camdata['use frames'] = framelist
		else:
			# DE camera might not use all frames in the original sum image
			camdata['use frames'] = range(self.totalframe)
		self.aligned_camdata = camdata

	def getAlignedCameraEMData(self):
		return self.aligned_camdata

	def setAlignedSumFrameList(self,framelist):
		self.sumframelist = framelist
		
	def getAlignedSumFrameList(self):
		return self.sumframelist
		
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

	def isSumSubStackWithDosefgpu(self):
		'''
		This funciton decides whether dosefgpu_driftcorr will be used for
		summing up ddstack.  Dosefgpu_driftcorr can only handle
		consecutive frame sum.
		'''
		framelist = self.getAlignedSumFrameList()
		# To save time, only proceed if necessary
		if framelist and framelist == range(min(framelist),min(framelist)+len(framelist)):
			self.save_aligned_stack = self.keep_stack
			return True
		# aligned_stack has to be saved to use Numpy to sum substack
		self.save_aligned_stack=True
		return False

	def setDoseFDriftCorrOptions(self,params):
		paramkeys = ['bft','fod','pbx']
		for goodkey in paramkeys:
			if goodkey in params.keys():
				self.alignparams[goodkey] = params[goodkey]

	def addDoseFDriftCorrOptions(self):
		cmd = ''
		for key in self.alignparams.keys():
			cmd += ' -%s %s' % (key,str(self.alignparams[key]))
		return cmd

	def gainCorrectAndAlignFrameStack(self):
		cmd = self.makeDosefgpuGainCorrectionParams()
		self.alignCorrectedFrameStack(gain_dark_cmd=cmd)

	def alignCorrectedFrameStack(self, gain_dark_cmd=''):
		'''
		Xueming Li's gpu program for aligning frames using all defaults
		Valid square gain/dark corrected ddstack is the input.
		'''
		# The alignment is done in tempdir (a local directory to reduce network traffic)
		os.chdir(self.tempdir)
		# include both hostname and gpu to identify the temp output
		temp_aligned_sumpath = 'temp%s.%d_sum.mrc' % (self.hostname,self.gpuid)
		temp_aligned_stackpath = 'temp%s.%d_aligned_st.mrc' % (self.hostname,self.gpuid)
		temp_log = self.tempframestackpath[:-4]+'_Log.txt'

		# Construct the command line with defaults
		cmd = 'dosefgpu_driftcorr %s -gpu %d -fcs %s -dsp 0' % (self.tempframestackpath,self.gpuid,temp_aligned_sumpath)
		# Options
		cmd += self.addDoseFDriftCorrOptions()
		# binning
		cmd += ' -bin %d' % (self.getNewBinning())
		# gain dark references
		cmd += gain_dark_cmd
		is_sum_with_dosefgpu =  self.isSumSubStackWithDosefgpu()
		if is_sum_with_dosefgpu:
			cmd += ' -nss %d -nes %d' % (min(self.sumframelist),max(self.sumframelist))
			cmd += ' -nss %d -nes %d' % (min(self.sumframelist),max(self.sumframelist))
		else:
			# minimal sum since it needs to be redone by numpy
			cmd += ' -nss %d -nes %d' % (0,1)
		if self.save_aligned_stack:
			cmd += ' -ssc 1 -fct %s' % (temp_aligned_stackpath)
		apDisplay.printMsg('Running: %s'% cmd)
		self.proc = subprocess.Popen(cmd, shell=True)
		self.proc.wait()

		if os.path.isfile(temp_aligned_sumpath):
			# successful alignment
			if self.save_aligned_stack:
				self.updateFrameStackHeaderImageStats(temp_aligned_stackpath)
			if self.tempdir != self.rundir:
				if os.path.isfile(temp_log):
					shutil.move(temp_log,self.framestackpath[:-4]+'_Log.txt')
					apDisplay.printMsg('Copying result for %s from %s to %s' % (self.image['filename'],self.tempdir,self.rundir))
			if not is_sum_with_dosefgpu:
				self.sumSubStackWithNumpy(temp_aligned_stackpath,temp_aligned_sumpath)
			shutil.move(temp_aligned_sumpath,self.aligned_sumpath)
			if self.keep_stack:
				shutil.move(temp_aligned_stackpath,self.aligned_stackpath)
			else:
				apFile.removeFile(temp_aligned_stackpath)
				apFile.removeFile(self.aligned_stackpath)
		else:
			if self.tempdir != self.rundir:
				# Move the Log to permanent location for future inspection
				if os.path.isfile(temp_log):
					shutil.move(self.tempframestackpath[:-4]+'_Log.txt',self.framestackpath[:-4]+'_Log.txt')
			apDisplay.printWarning('dosefgpu_driftcorr FAILED: \n%s not created.' % os.path.basename(temp_aligned_sumpath))
			#apDisplay.printError('If this happens consistently on an image, hide it in myamiweb viewer and continue with others' )
		os.chdir(self.rundir)

	def makeAlignedImageData(self,alignlabel='a'):
		'''
		Prepare ImageData to be uploaded after alignment
		'''
		camdata = self.getAlignedCameraEMData()
		new_array = mrc.read(self.aligned_sumpath)
		return apDBImage.makeAlignedImageData(self.image,camdata,new_array,alignlabel)

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

	def sumSubStackWithNumpy(self,stackpath,sumpath):
		stackproc = DDStackProcessing()
		framelist = self.getAlignedSumFrameList()
		# To save time, only proceed if necessary
		if framelist and framelist != range(self.totalframe):
			# set attribute without other complications
			stackproc.framestackpath = stackpath
			mrc.write(stackproc.getDDStackFrameSumImage(framelist),sumpath)

class DDStackProcessing(DirectDetectorProcessing):
	'''
	Class to use gain/dark corrected DDStack. Need to setImage and 
	then setFrameStackPath so that the ddstackrun can be determined
	from image if not specified.
	'''
	def __init__(self):
		super(DDStackProcessing,self).__init__()
		self.ddstackrun = None

	def getIsAligned(self):
		'''
		Leginon does not allow "-" in user-defined preset name. '-' is only added when aligned.
		'''
		return self.image['preset'] is not None and '-' in self.image['preset']['name']

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

	def getDDStackRun(self,show_msg=False):
		if self.ddstackrun and show_msg:
			apDisplay.printMsg('DDStack is from %s (id = %d)' % (self.ddstackrun['runname'],self.ddstackrun.dbid))
		return self.ddstackrun

	def setImageData(self,imagedata):
		super(DDStackProcessing,self).setImageData(imagedata)

	def setFrameStackPath(self,ddstackrunid=None):
		# This is sometimes called from setImageData which gives no ddstackrunid
		ddstackrundata = self.getDDStackRun()
		if ddstackrundata and ddstackrunid is None:
			# set ddstackrunid from ddstackrundata
			ddstackrunid = ddstackrundata.dbid
		self.setDDStackRun(ddstackrunid)
		self.setRunDir(self.getDDStackRun()['path']['path'])
		self.setTempDir(self.getRunDir())
		super(DDStackProcessing,self).setFrameStackPath()

	def getDDStackFrameSumImage(self,framelist,roi=None):
		'''
		DDStack are gain/dark corrected and may or may not be aligned
		'''
		if not os.path.isfile(self.framestackpath):
			apDisplay.printError('No DD Stack to make image from')
		apDisplay.printMsg('Getting summed image from %s' % self.framestackpath)
		stack = mrc.mmap(self.framestackpath)
		if max(framelist) >= stack.shape[0]:
			apDisplay.printError('Last frame in list index out of range')
		frametuple = tuple(framelist)
		apDisplay.printMsg(' summing frames %s' % (frametuple,))
		if not roi:
			sum = numpy.sum(stack[frametuple,:,:],axis=0)
		else:
			apDisplay.printMsg(' crop range of (%d,%d) to (%d,%d)' % (rot['x'][0],roi['x'][1]-1,roi['y'][0],roi['y'][1]-1))
			sum = numpy.sum(stack[frametuple,roi['y'][0]:roi['y'][1],roi['x'][0]:roi['x'][1]],axis=0)
		return sum

if __name__ == '__main__':
	dd = initializeDDFrameprocess('13jun18anchitestT1')
	dd.setRunDir('./')
	dd.setImageId(2380386)
	dd.setAlignedCameraEMData()
	dd.makeAlignedImageData()
	start_frame = 0
	#mrc.write(corrected,'corrected_frame%d_%d.mrc' % (start_frame,nframe))
