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

simulation = False
if simulation:
	print 'USING SIMULATION SETTINGS'


# only one connection will be shared among all classes
def connect():
	if not hasattr(gatansocket, 'myGS'):
		gatansocket.myGS = gatansocket.GatanSocket()
	return gatansocket.myGS

class GatanK2Base(ccdcamera.CCDCamera):
	name = 'GatanK2Base'
	ed_mode = 'base'
	hw_proc = 'none'
	def __init__(self):
		self.camera = connect()
		self.cameraid = 0

		self.idcounter = itertools.cycle(range(100))

		ccdcamera.CCDCamera.__init__(self)

		self.binning_limits = [1,2,3,4,5,6,7,8]
		self.binmethod = 'floor'
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
		self.record_frame_time = 0.100
		self.readout_delay_ms = 0
		self.align_frames = False
		self.align_filter = 'None'

		self.script_functions = [
			('AFGetSlitState', 'getEnergyFilter'),
			('AFSetSlitState', 'setEnergyFilter'),
			('AFGetSlitWidth', 'getEnergyFilterWidth'),
			('AFSetSlitWidth', 'setEnergyFilterWidth'),
			('AFDoAlignZeroLoss', 'alignEnergyFilterZeroLossPeak'),
			('IFCGetSlitState', 'getEnergyFilter'),
			('IFCSetSlitState', 'setEnergyFilter'),
			('IFCGetSlitWidth', 'getEnergyFilterWidth'),
			('IFCSetSlitWidth', 'setEnergyFilterWidth'),
			('IFCDoAlignZeroLoss', 'alignEnergyFilterZeroLossPeak'),
		]

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

	def getFrameTime(self):
		if self.isDoseFracOn():
			frame_time = self.dosefrac_frame_time
		else:
			frame_time = self.record_frame_time
		return frame_time

	def getRealExposureTime(self):
		'''
		The real exposure time is rounded to the nearest
		frame time, but not less than one frame.
		'''
		frame_time = self.getFrameTime()
		user_time = self.user_exposure_ms / 1000.0
		if user_time < frame_time:
			real_time = frame_time
		else:
			real_time = round(user_time / frame_time) * frame_time
		return real_time

	def getExposureTime(self):
		real_time = self.getRealExposureTime()
		real_time_ms = int(round(real_time * 1000))
		return real_time_ms

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

	# our name mapped to SerialEM plugin value
	readmodes = {'linear': 0, 'counting': 1, 'super resolution': 2}
	hardwareProc = {'none': 0, 'dark': 2, 'gain': 4, 'dark+gain': 6}

	def isDoseFracOn(self):
		return self.save_frames or self.align_frames

	def calculateK2Params(self):
		frame_time = self.getFrameTime()
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
		frames_name = time.strftime('%Y%m%d_%H%M%S', time.localtime())
		self.frames_name = frames_name + '%02d' % (self.idcounter.next(),)
		path = 'D:\\frames\\' + self.frames_name

		rotation = 270 # degrees
		flip = 0  # 0=none, 4=flip columns before rot, 8=flip after
		rot_flip = rotation / 90 + flip

		params = {
			'rotationFlip': rot_flip,
			'dirname': path,
			'rootname': 'frame',
		}
		return params

	def _getImage(self):
		if self.ed_mode != 'base':
			k2params = self.calculateK2Params()
			self.camera.SetK2Parameters(**k2params)
			fileparams = self.calculateFileSavingParams()
			self.camera.SetupFileSaving(**fileparams)
		acqparams = self.calculateAcquireParams()

		t0 = time.time()
		image = self.camera.GetImage(**acqparams)
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0

		print 'got',image.shape
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
		frame_time = self.getFrameTime()
		real_time = self.getRealExposureTime()
		nframes = int(round(real_time / frame_time))
		return nframes

	def getNumberOfFramesSaved(self):
		if self.save_frames:
			return self.getNumberOfFrames()
		else:
			return 0

	def getFrameRate(self):
		frame_rate = 1.0 / self.getFrameTime()
		return frame_rate

	def setFrameRate(self, fps):
		if fps:
			self.dosefrac_frame_time = 1.0 / fps

	def setReadoutDelay(self, ms):
		if not ms:
			ms = 0
		self.readout_delay_ms = ms

	def getReadoutDelay(self):
		return self.readout_delay_ms

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
	if simulation:
		hw_proc = 'none'
	else:
		hw_proc = 'dark+gain'

	def __init__(self):
		super(GatanK2Super,self).__init__()
		self.binning_limits = [1]
		self.binmethod = 'floor'
