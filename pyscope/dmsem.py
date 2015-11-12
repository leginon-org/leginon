#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#

# target intensity:  140410.1

import ccdcamera
import sys
import time
import gatansocket
import numpy
import itertools
import os
from pyscope import moduleconfig

simulation = False
if simulation:
	print 'USING SIMULATION SETTINGS'

# only one connection will be shared among all classes
def connect():
	if not hasattr(gatansocket, 'myGS'):
		gatansocket.myGS = gatansocket.GatanSocket()
	return gatansocket.myGS

configs = moduleconfig.getConfigured('dmsem.cfg')

class DMSEM(ccdcamera.CCDCamera):
	ed_mode = None
	filter_method_names = [
			'getEnergyFilter',
			'setEnergyFilter',
			'getEnergyFilterWidth',
			'setEnergyFilterWidth',
			'alignEnergyFilterZeroLossPeak',
		]

	def __init__(self):
		self.unsupported = []
		self.camera = connect()

		self.idcounter = itertools.cycle(range(100))

		ccdcamera.CCDCamera.__init__(self)

		if not self.getEnergyFiltered():
			self.unsupported.extend(self.filter_method_names)
		self.bblankerid = 0
		self.binning = {'x': 1, 'y': 1}
		self.offset = {'x': 0, 'y': 0}
		self.tempoffset = dict(self.offset)
		self.camsize = self.getCameraSize()
		self.dimension = {'x': self.camsize['x'], 'y': self.camsize['y']}
		self.exposuretype = 'normal'
		self.user_exposure_ms = 100
		self.float_scale = 1000.0
		# what to do in digital micrograph before handing back the image
		# unprocessed, dark subtracted, gain normalized
		#self.dm_processing = 'gain normalized'
		self.dm_processing = 'unprocessed'
		self.save_frames = False
		self.frames_name = None
		#self.frame_rate = 4.0
		self.dosefrac_frame_time = 0.200
		self.record_precision = 0.100
		self.readout_delay_ms = 0
		self.align_frames = False
		self.align_filter = 'None'

	def __getattribute__(self, attr_name):
		if attr_name in object.__getattribute__(self, 'unsupported'):
			raise AttributeError('attribute not supported')
		return object.__getattribute__(self, attr_name)

	def getDmsemConfig(self,optionname,itemname=None):
		if itemname is None:
			return configs[optionname]
		else:
			return configs[optionname][itemname]

	def getOffset(self):
		return dict(self.offset)

	def setOffset(self, value):
		# Work around
		self.offset = dict(value)
		self.tempoffset = {'x':0,'y':0}

	def getDimension(self):
		return dict(self.dimension)

	def setDimension(self, value):
		# Work around
		self.dimension = dict(value)

	def getBinning(self):
		return dict(self.binning)

	def setBinning(self, value):
		if value['x'] != value['y']:
			raise ValueError('multiple binning dimesions not supported')
		self.binning = dict(value)

	def getRealExposureTime(self):
		return self.getExposureTime() / 1000.0

	def getExposureTime(self):
		return self.user_exposure_ms

	def setExposureTime(self, value):
		self.user_exposure_ms = value

	def getExposureTypes(self):
		return ['normal', 'dark']

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		if value not in ['normal', 'dark']:
			raise ValueError('invalid exposure type')
		self.exposuretype = value

	def isDM230orUp(self):
		version_id,version_string = self.getDMVersion()
		if version_id and version_id >= 40300:
			return True
		return False

	def isDM231orUp(self):
		version_id,version_string = self.getDMVersion()
		if version_id and version_id >= 40301:
			return True
		return False

	def needConfigDimensionFlip(self,height,width):
		# DM 2.3.0 and up needs camera dimension input in its original
		# orientation regardless of rotation when dose fractionation is used.
		if self.isDM230orUp() and (self.save_frames or self.align_frames):
			if height > width:
				return True

		return False

	def calculateAcquireParams(self):
		exptype = self.getExposureType()
		if exptype == 'dark':
			processing = 'dark'
		else:
			processing = self.dm_processing

		# I think it's negative...
		shutter_delay = -self.readout_delay_ms / 1000.0

		physical_binning = self.binning['x']
		if self.ed_mode != 'super resolution':
			binscale = 1
		else:
			binscale = 2
			if self.binning['x'] > 1:
				# physical binning is half super resolution binning except when the latter is 1
				physical_binning /= binscale

		height = self.offset['y']+self.dimension['y']
		width = self.offset['x']+self.dimension['x']
		if self.needConfigDimensionFlip(height,width):
			tmpheight = height
			height = width
			width = tmpheight
		acqparams = {
			'processing': processing,
			'height': height,
			'width': width,
			'binning': physical_binning,
			'top': self.tempoffset['y'] / binscale,
			'left': self.tempoffset['x'] / binscale,
			'bottom': height / binscale,
			'right': width / binscale,
			'exposure': self.getRealExposureTime(),
			'shutterDelay': shutter_delay,
		}
		print 'DM acqire shape (%d, %d)' % (height,width)
		return acqparams

	def custom_setup(self):
		# required for non-K2 cameras
		self.camera.SetReadMode(-1)

	def _getImage(self):
		self.camera.SelectCamera(self.cameraid)
		self.custom_setup()
		acqparams = self.calculateAcquireParams()

		t0 = time.time()
		image = self.camera.GetImage(**acqparams)
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0

		if self.getExposureType() == 'dark':
			self.modifyDarkImage(image)
		# workaround dose fractionation image rotate-flip not applied problem
		print 'received shape',image.shape
		if self.save_frames or self.align_frames:
			if not self.isDM231orUp():
				k2_rotate = self.getDmsemConfig('k2','rotate')
				k2_flip = self.getDmsemConfig('k2','flip')
				if k2_rotate:
					image = numpy.rot90(image,4-k2_rotate)
				if k2_flip:
					image = numpy.fliplr(image)
		# workaround to offset image problem
		startx = self.getOffset()['x']
		starty = self.getOffset()['y']
		if startx != 0 or starty != 0:
			endx = self.dimension['x'] + startx
			endy = self.dimension['y'] + starty
			image = image[starty:endy,startx:endx]
		print 'modified shape',image.shape

		if self.dm_processing == 'gain normalized' and self.ed_mode in ('counting','super resolution'):
			image = numpy.asarray(image, dtype=numpy.float32)
			image /= self.float_scale
		return image

	def modifyDarkImage(self,image):
		'''
		in-place modification of image array
		'''
		return

	def getPixelSize(self):
		## TODO: move to config file:
		# pixel size on Gatan K2
		return {'x': 5e-6, 'y': 5e-6}

	def getRetractable(self):
		return True

	def setInserted(self, value):
		inserted = self.getInserted()
		if not inserted and value:
			self.camera.InsertCamera(self.cameraid, value)
		elif inserted and not value:
			self.camera.InsertCamera(self.cameraid, value)
		else:
			return
		## TODO:  determine necessary settling time:
		time.sleep(5)

	def getInserted(self):
		return self.camera.IsCameraInserted(self.cameraid)

	def setReadoutDelay(self, ms):
		if not ms:
			ms = 0
		self.readout_delay_ms = ms

	def getReadoutDelay(self):
		return self.readout_delay_ms

	def getDMVersion(self):
		'''
		version: version_long, major.minor.sub
		'''
		dm_version = self.getDmsemConfig('dm','dm_version')
		if dm_version:
			bits = map((lambda x:int(x)),dm_version.split('.'))
			version_long = (bits[0]+2)*10000 + (bits[1] //10)*100 + bits[1] % 10
		else:
			version_long = self.camera.GetDMVersion()
		if version_long < 40000:
			major = 1
			minor = None
			sub = None
			if version_long >=31100:
				# 2.3.0 gives an odd number of 31100
				major = 2
				minor = 3
				sub = 0
				version_long = 40300
		elif version_long == 40000:
			# minor version can be 0 or 1 in this case
			# but likely 1 since we have not used this module until k2 is around
			major = 2
			minor = 1
			sub = 0
		else:
			major = version_long // 10000 - 2
			remainder = version_long - (major+2) * 10000
			minor = remainder // 100
			sub = remainder % 100
		return (version_long,'%d.%d.%d' % (major,minor,sub))

	def hasScriptFunction(self, name):
		return self.camera.hasScriptFunction(name)

	def getEnergyFiltered(self):
		'''
		Return True if energy filter is available through this DM
		'''
		for method_name in self.filter_method_names:
			method_name = method_name[0].upper() + method_name[1:]
			if method_name not in self.camera.filter_functions.keys():
				return False
		return True

	def getEnergyFilter(self):
		'''
		Return True if post column energy filter is enabled
		with slit in
		'''
		return self.camera.GetEnergyFilter() > 0.0

	def setEnergyFilter(self, value):
		'''
		Enable/Disable post column energy filter
		by retracting the slit
		'''
		if value:
			i = 1
		else:
			i = 0
		result = self.camera.SetEnergyFilter(i)
		if result < 0.0:
			raise RuntimeError('unable to set energy filter slit position')

	def getEnergyFilterWidth(self):
		return self.camera.GetEnergyFilterWidth()

	def setEnergyFilterWidth(self, value):
		result = self.camera.SetEnergyFilterWidth(value)
		if result < 0.0:
			raise RuntimeError('unable to set energy filter width')

	def alignEnergyFilterZeroLossPeak(self):
		result = self.camera.AlignEnergyFilterZeroLossPeak()
		if result < 0.0:
			raise RuntimeError('unable to align energy filter zero loss peak')

class GatanOrius(DMSEM):
	name = 'GatanOrius'
	try:
		cameraid = configs['orius']['camera_id']
	except:
		pass
	binning_limits = [1,2,4]
	binmethod = 'exact'

class GatanUltraScan(DMSEM):
	name = 'GatanUltraScan'
	try:
		cameraid = configs['ultrascan']['camera_id']
	except:
		pass
	binning_limits = [1,2,4,8]
	binmethod = 'exact'

class GatanK2Base(DMSEM):
	name = 'GatanK2Base'
	try:
		cameraid = configs['k2']['camera_id']
	except:
		pass
	# our name mapped to SerialEM plugin value
	readmodes = {'linear': 0, 'counting': 1, 'super resolution': 2}
	ed_mode = 'base'
	hw_proc = 'none'
	binning_limits = [1,2,4,8]
	binmethod = 'floor'
	filePerImage = False
	def custom_setup(self):
		#self.camera.SetShutterNormallyClosed(self.cameraid,self.bblankerid)
		if self.ed_mode != 'base':
			k2params = self.calculateK2Params()
			self.camera.SetK2Parameters(**k2params)
			fileparams = self.calculateFileSavingParams()
			if fileparams['rootname'] != 'dummy':
				print 'FILESAVING', fileparams['dirname'],fileparams['rootname']
			self.camera.SetupFileSaving(**fileparams)

	def getFrameTime(self):
		ms = self.dosefrac_frame_time * 1000.0
		return ms

	def setFrameTime(self,ms):
		seconds = ms / 1000.0
		self.dosefrac_frame_time = seconds

	def getExposurePrecision(self):
		if self.isDoseFracOn():
			frame_time = self.dosefrac_frame_time
		else:
			frame_time = self.record_precision
		return frame_time

	def getRealExposureTime(self):
		'''
		The real exposure time is rounded to the nearest
		"exposure precision unit" in seconds, but not less than one "unit"
		'''
		precision = self.getExposurePrecision()
		user_time = self.user_exposure_ms / 1000.0
		if user_time < precision:
			real_time = precision
		else:
			real_time = round(user_time / precision) * precision
		return real_time

	def getExposureTime(self):
		real_time = self.getRealExposureTime()
		real_time_ms = int(round(real_time * 1000))
		return real_time_ms

	# our name mapped to SerialEM plugin value
	hardwareProc = {'none': 0, 'dark': 2, 'gain': 4, 'dark+gain': 6}

	def isDoseFracOn(self):
		return self.save_frames or self.align_frames

	def calculateK2Params(self):
		frame_time = self.dosefrac_frame_time
		params = {
			'readMode': self.readmodes[self.ed_mode],
			#'scaling': self.float_scale,
			'scaling': 1.0,
			'hardwareProc': self.hardwareProc[self.hw_proc],
			'doseFrac': self.isDoseFracOn(),
			'frameTime': frame_time,
			'alignFrames': self.align_frames,
			'saveFrames': self.save_frames,
			'filt': self.align_filter,
		}
		return params

	def calculateFileSavingParams(self):
		'''
		Creates raw frame file saving parameters independent of
		the integrated image returned to Leginon
		'''
		if self.isDoseFracOn():
			frames_name = time.strftime('%Y%m%d_%H%M%S', time.localtime())
			self.frames_name = frames_name + '%02d' % (self.idcounter.next(),)
		else:
			self.frames_name = 'dummy'
		raw_frame_dir = self.getDmsemConfig('k2','raw_frame_dir')
		if self.filePerImage:
			path = raw_frame_dir + self.frames_name
			fileroot = 'frame'
		else:
			path = raw_frame_dir 
			fileroot = self.frames_name

		# 0 means takes what DM gives
		rot_flip = 0
		if not self.isDM231orUp():
			# Backward compatibility
			flip = int(not self.getDmsemConfig('k2','flip'))  # 0=none, 4=flip columns before rot, 8=flip after
			rot_flip = self.getDmsemConfig('k2','rotate') + flip

		params = {
			'rotationFlip': rot_flip,
			'dirname': path,
			'rootname': fileroot,
			'filePerImage': self.filePerImage,
			'earlyReturnFrameCount': self.getEarlyReturnFrameCount(),
		}
		return params

	def getEarlyReturnFrameCount(self):
		return self.getDmsemConfig('k2','early_return_frame_count')

	def setAlignFrames(self, value):
		self.align_frames = bool(value)

	def getAlignFrames(self):
		return self.align_frames

	def setAlignFilter(self, value):
		self.align_filter = str(value)

	def getAlignFilter(self):
		return self.align_filter

	def getSaveRawFrames(self):
		return self.save_frames

	def setSaveRawFrames(self, value):
		self.save_frames = bool(value)

	def getPreviousRawFramesName(self):
		return self.frames_name

	def getNumberOfFrames(self):
		frame_time = self.dosefrac_frame_time
		real_time = self.getRealExposureTime()
		nframes = int(round(real_time / frame_time))
		return nframes

	def getNumberOfFramesSaved(self):
		if self.save_frames:
			return self.getNumberOfFrames()
		else:
			return 0

	def setUseFrames(self, frames):
		pass

	def getUseFrames(self):
		nframes = self.getNumberOfFrames()
		return tuple(range(nframes))

	def getFrameFlip(self):
		'''
		Frame Flip is defined as up-down flip
		'''
		return self.isDM231orUp()

	def getFrameRotate(self):
		'''
		Frame Rotate direction is defined as x to -y rotation applied after up-down flip
		'''
		return 0

class GatanK2Linear(GatanK2Base):
	name = 'GatanK2Linear'
	ed_mode = 'linear'
	hw_proc = 'none'

class GatanK2Counting(GatanK2Base):
	logged_methods_on = True
	name = 'GatanK2Counting'
	ed_mode = 'counting'
	if simulation:
		hw_proc = 'none'
	else:
		hw_proc = 'dark+gain'

	def modifyDarkImage(self,image):
		if self.isDM231orUp():
			image[:,:] = 0

class GatanK2Super(GatanK2Base):
	name = 'GatanK2Super'
	ed_mode = 'super resolution'
	binning_limits = [1]
	binmethod = 'floor'
	if simulation:
		hw_proc = 'none'
	else:
		hw_proc = 'dark+gain'

	def modifyDarkImage(self,image):
		if self.isDM231orUp():
			image[:,:] = 0

	def getPixelSize(self):
		## TODO: move to config file:
		# pixel size on Gatan K2
		return {'x': 2.5e-6, 'y': 2.5e-6}

