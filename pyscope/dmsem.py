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

isDM230 = False
simulation = False
if simulation:
	print 'USING SIMULATION SETTINGS'

# only one connection will be shared among all classes
def connect():
	if not hasattr(gatansocket, 'myGS'):
		gatansocket.myGS = gatansocket.GatanSocket()
	return gatansocket.myGS

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
		if isDM230 and self.save_frames or self.align_frames:
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
		print acqparams
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

		# workaround dose fractionation image rotate-flip not applied problem
		if self.save_frames or self.align_frames:
			image_shape = image.shape
			# assume number of columns is less than rows
			image_dtype = image.dtype
			image = numpy.fliplr(numpy.rot90(image,1))
		# workaround to offset image problem
		startx = self.getOffset()['x']
		starty = self.getOffset()['y']
		if startx != 0 or starty != 0:
			endx = self.dimension['x'] + startx
			endy = self.dimension['y'] + starty
			image = image[starty:endy,startx:endx]
		print 'modified',image.shape

		if self.dm_processing == 'gain normalized' and self.ed_mode in ('counting','super resolution'):
			print 'ASARRAY'
			image = numpy.asarray(image, dtype=numpy.float32)
			print 'DIVIDE'
			image /= self.float_scale
		return image

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
	cameraid = 1
	binning_limits = [1,2,4]
	binmethod = 'exact'

class GatanUltraScan(DMSEM):
	name = 'GatanUltraScan'
	cameraid = 0
	binning_limits = [1,2,4,8]
	binmethod = 'exact'

class GatanK2Base(DMSEM):
	name = 'GatanK2Base'
	cameraid = 0
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
			print 'SETK2PARAMS', k2params
			self.camera.SetK2Parameters(**k2params)
			fileparams = self.calculateFileSavingParams()
			print 'SETUPFILESAVING', fileparams
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
		print 'frame params: ',params
		return params

	def calculateFileSavingParams(self):
		if self.isDoseFracOn():
			frames_name = time.strftime('%Y%m%d_%H%M%S', time.localtime())
			self.frames_name = frames_name + '%02d' % (self.idcounter.next(),)
		else:
			self.frames_name = 'dummy'
		if self.filePerImage:
			path = 'D:\\frames\\' + self.frames_name
			fileroot = 'frame'
		else:
			path = 'D:\\frames\\'
			fileroot = self.frames_name

		rotation = 270 # degrees
		flip = 0  # 0=none, 4=flip columns before rot, 8=flip after
		rot_flip = rotation / 90 + flip

		params = {
			'rotationFlip': rot_flip,
			'dirname': path,
			'rootname': fileroot,
			'filePerImage': self.filePerImage,
		}
		return params

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

class GatanK2Super(GatanK2Base):
	name = 'GatanK2Super'
	ed_mode = 'super resolution'
	binning_limits = [1]
	binmethod = 'floor'
	if simulation:
		hw_proc = 'none'
	else:
		hw_proc = 'dark+gain'
