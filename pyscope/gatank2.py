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

class GatanK2(ccdcamera.CCDCamera):
	name = 'GatanK2'
	def __init__(self):
		self.ed_mode = 'super resolution'
		ccdcamera.CCDCamera.__init__(self)
		self.cameraid = 0
		self.camera = gatansocket.GatanSocket()

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

	def getCameraSize(self):
		size = ccdcamera.CCDCamera.getCameraSize(self)
		if self.getEDMode() == 'super resolution':
			size = {'x': 2*size['x'], 'y': 2*size['y']}
		return size

	def getEDModes(self):
		return ('linear', 'counting', 'super resolution')

	def getEDMode(self):
		return self.ed_mode

	def setEDMode(self, mode):
		assert mode in self.getEDModes()
		self.ed_mode = mode

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

	def getEnergyFiltered(self):
		method_names = [
			'getEnergyFilter',
			'setEnergyFilter',
			'getEnergyFilterWidth',
			'setEnergyFilterWidth',
			'alignEnergyFilterZeroLossPeak',
		]

		for method_name in method_names:
			if not hasattr(self, method_name):
				return False
		return True

	def getEnergyFilter(self):
		script = 'if(%s()) Exit(1.0) else Exit(-1.0)' % (self.filter_functions['getEnergyFilter'],)
		result = self.camera.ExecuteScript(script)
		return result > 0.0

	def setEnergyFilter(self, value):
		if value:
			i = 1
		else:
			i = 0
		script = '%s(%d)' % (self.filter_functions['setEnergyFilter'], i)
		self.camera.ExecuteScript(script)

	def getEnergyFilterWidth(self):
		script = 'Exit(%s())' % (self.filter_functions['getEnergyFilterWidth'],)
		result = self.camera.ExecuteScript(script)
		return result

	def setEnergyFilterWidth(self, value):
		script = 'if(%s(%f)) Exit(1.0) else Exit(-1.0)' % (self.filter_functions['setEnergyFilterWidth'], value)
		result = self.camera.ExecuteScript(script)
		if result < 0.0:
			raise RuntimeError('unable to set energy filter width')

	def alignEnergyFilterZeroLossPeak(self):
		script = 'if(%s()) Exit(1.0) else Exit(-1.0)' % (self.filter_functions['alignEnergyFilterZeroLossPeak'],)
		result = self.camera.ExecuteScript(script)
		if result < 0.0:
			raise RuntimeError('unable to align energy filter zero loss peak')

	'''
	def getNumberOfFrames(self):
		raise NotImplementedError()

	def getSaveRawFrames(self):
		raise NotImplementedError()

	def setSaveRawFrames(self, value):
		raise NotImplementedError()

	def getPreviousRawFramesName(self):
		raise NotImplementedError()
        
	def getNumberOfFramesSaved(self):
		raise NotImplementedError()

	def getUseFrames(self):
		raise NotImplementedError()

	def setUseFrames(self, frames):
		raise NotImplementedError()

	def getFrameRate(self):
		raise NotImplementedError()

	def setFrameRate(self, fps):
		raise NotImplementedError()

	def getReadoutDelay(self):
		raise NotImplementedError()

	def setReadoutDelay(self, milliseconds):
		raise NotImplementedError()

	def getTemperatureStatus(self):
		raise NotImplementedError()

	## method name altered to prevent Leginon from setting temperature
	def set_TemperatureStatus(self, state):
		raise NotImplementedError()

	def getTemperature(self):
		raise NotImplementedError()

	def set_Temperature(self, degrees):
		raise NotImplementedError()
	'''

class GatanK2Super(GatanK2):
	name = 'GatanK2Super'
	def calculateK2Params(self):
		params = {
			'readMode': 3,  # 0 linear, 2 counting, 3 superres
			'scaling': 1.0,   # ???
			'hardwareProc': 2, #0 none, 2 dark, 4 gain, 6 dark/gain
			'doseFrac': False,
			'frameTime': 0.04,
			'alignFrames': False,
			'saveFrames': False,
			'filtSize': 0,
			'filt': [],
		}
		return params
