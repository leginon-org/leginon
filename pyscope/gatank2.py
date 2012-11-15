#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#

import ccdcamera
import sys
import time
import gatansocket

class GatanK2Base(ccdcamera.CCDCamera):

	# so subclasses can all share the same socket connection
	camera = None
	@classmethod
	def connect_socket(cls):
		cls.camera = gatansocket.GatanSocket()

	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		self.cameraid = 0

		self.binning = {'x': 1, 'y': 1}
		self.offset = {'x': 0, 'y': 0}
		size = self.getCameraSize()
		self.dimension = {'x': size['x'], 'y': size['y']}
		self.exposuretype = 'normal'
		self.exposure_ms = 200
		self.float_scale = 1000.0
		# what to do in digital micrograph before handing back the image
		# unprocessed, dark subtracted, gain normalized
		self.dm_processing = 'gain normalized'

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
		self.offset = dict(value)

	def getDimension(self):
		return dict(self.dimension)

	def setDimension(self, value):
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
		acqparams = {
			'processing': processing,
			'binning': self.binning['x'],
			'top': self.offset['y'],
			'left': self.offset['x'],
			'bottom': self.offset['y']+self.dimension['y'],
			'right': self.offset['x']+self.dimension['x'],
			'exposure': self.exposure_ms / 1000.0,
		}
		return acqparams

	# our name mapped to SerialEM plugin value
	readmodes = {'linear': 0, 'counting': 1, 'super resolution': 2}

	def calculateK2Params(self):
		params = {
			'readMode': self.readmodes[self.ed_mode],
			'scaling': self.float_scale,
			'hardwareProc': 6, #0 none, 2 dark, 4 gain, 6 dark/gain
			'doseFrac': False,
			'frameTime': 0.04,
			'alignFrames': False,
			'saveFrames': False,
			'filtSize': 0,
			'filt': [],
		}
		return params

	def _getImage(self):
		k2params = self.calculateK2Params()
		print 'SETK2', k2params
		self.camera.SetK2Parameters(**k2params)
		acqparams = self.calculateAcquireParams()
		t0 = time.time()
		print 'GETIMAGE', acqparams
		image = self.camera.GetImage(**acqparams)
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0
		if self.dm_processing == 'gain normalized':
			image = numpy.asarray(image, dtype=numpy.float32)
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


class GatanK2Linear(GatanK2Base):
	name = 'GatanK2Linear'
	ed_mode = 'linear'

class GatanK2Counting(GatanK2Base):
	name = 'GatanK2Counting'
	ed_mode = 'counting'

class GatanK2Super(GatanK2Base):
	name = 'GatanK2Super'
	ed_mode = 'super resolution'
