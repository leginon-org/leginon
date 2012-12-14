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

		self.binning = {'x': 1, 'y': 1}
		self.offset = {'x': 0, 'y': 0}
		self.tempoffset = dict(self.offset)
		self.camsize = self.getCameraSize()
		self.dimension = {'x': self.camsize['x'], 'y': self.camsize['y']}
		self.exposuretype = 'normal'
		self.exposure_ms = 125
		self.float_scale = 1000.0
		# what to do in digital micrograph before handing back the image
		# unprocessed, dark subtracted, gain normalized
		#self.dm_processing = 'gain normalized'
		self.dm_processing = 'unprocessed'
		self.save_frames = False
		self.frames_name = None
		self.frame_rate = 4.0
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

	def getExposureTime(self):
		return self.exposure_ms

	def setExposureTime(self, value):
		self.exposure_ms = value

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

		acqparams = {
			'processing': processing,
			'binning': self.binning['x'],
			'top': self.tempoffset['y'],
			'left': self.tempoffset['x'],
			'bottom': self.offset['y']+self.dimension['y'],
			'right': self.offset['x']+self.dimension['x'],
			'exposure': self.exposure_ms / 1000.0,
			'shutterDelay': shutter_delay,
		}
		print acqparams
		return acqparams

	# our name mapped to SerialEM plugin value
	readmodes = {'linear': 0, 'counting': 1, 'super resolution': 2}
	hardwareProc = {'none': 0, 'dark': 2, 'gain': 4, 'dark+gain': 6}

	def calculateK2Params(self):
		frame_time = 1.0 / self.frame_rate
		params = {
			'readMode': self.readmodes[self.ed_mode],
			#'scaling': self.float_scale,
			'scaling': 1.0,
			'hardwareProc': self.hardwareProc[self.hw_proc],
			'doseFrac': self.save_frames or self.align_frames,
			'frameTime': frame_time,
			'alignFrames': self.align_frames,
			'saveFrames': self.save_frames,
			'filt': self.align_filter,
		}
		print 'frame params: ',params
		return params

	def calculateFileSavingParams(self):
		drive = 'D:'
		dirname = 'frames'
		frames_name = time.strftime('%Y%m%d_%H%M%S', time.localtime())
		frames_name = frames_name + '%02d' % (self.idcounter.next(),)
		path = os.path.join(drive, dirname, frames_name)
		self.frames_name = frames_name

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
        
	def getNumberOfFramesSaved(self):
		nframes = self.getProperty('Autosave Raw Frames - Frames Written in Last Exposure')
		return int(nframes)

	def getFrameRate(self):
		return self.frame_rate

	def setFrameRate(self, fps):
		if fps:
			self.frame_rate = fps

	def setReadoutDelay(self, ms):
		if not ms:
			ms = 0
		self.readout_delay_ms = ms

	def getReadoutDelay(self):
		return self.readout_delay_ms

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
