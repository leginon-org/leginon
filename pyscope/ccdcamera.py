# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import time
import threading
from . import baseinstrument

class GeometryError(Exception):
	pass

class CCDCamera(baseinstrument.BaseInstrument):
	name = 'CCD Camera'
	binning_limits = [1,2,4,8]
	binmethod = 'exact'

	capabilities = baseinstrument.BaseInstrument.capabilities + (
		{'name': 'PixelSize', 'type': 'property'},
		{'name': 'Retractable', 'type': 'property'},
		{'name': 'ExposureTypes', 'type': 'property'},
		{'name': 'CameraSize', 'type': 'property'},
		{'name': 'Binning', 'type': 'property'},
		{'name': 'Dimension', 'type': 'property'},
		{'name': 'ExposureTime', 'type': 'property'},
		{'name': 'ExposureType', 'type': 'property'},
		{'name': 'Offset', 'type': 'property'},
		{'name': 'ExposureTimestamp', 'type': 'property'},
		{'name': 'IntensityAveraged', 'type': 'property'},
		{'name': 'SeriesLength', 'type': 'property'},
		## methods:
		{'name': 'startMovie', 'type': 'method'},
		{'name': 'stopMovie', 'type': 'method'},
		{'name': 'waitForCameraReady', 'type': 'method'},
		## optional:
		{'name': 'EnergyFilter', 'type': 'property'},
		{'name': 'EnergyFilterWidth', 'type': 'property'},
		{'name': 'EnergyFilterOffset', 'type': 'property'},
		{'name': 'FrameFlip', 'type': 'property'},
		{'name': 'FrameRotate', 'type': 'property'},
		{'name': 'UseCds', 'type': 'property'},
		{'name': 'FastSave', 'type': 'property'},
	)

	def __init__(self):
		baseinstrument.BaseInstrument.__init__(self)
		self.initConfig()
		self.zplane = self.conf['zplane']
		if 'height' in self.conf and 'width' in self.conf:
			self.configured_size = {'x': self.conf['width'], 'y': self.conf['height']}
		else:
			self.configured_size = None
		self.buffer = {}
		self.buffer_ready = {}
		self.bufferlock = threading.Lock()
		self.readoutcallback = None
		self.callbacks = {}
		self.exposure_timestamp = None
		self.use_cds = False
		self.series_length = 0

	def getZplane(self):
		return self.zplane

	def getCameraModelName(self):
		return self.name

	def getIntensityAveraged(self):
		# Returns True if camera array value is normalized internally
		# and thus does not increase value for longer exposure time.
		return False

	def calculateCenteredGeometry(self, dimension, binning):
		camerasize = self.getCameraSize()
		offsetx = (camerasize['x']//binning - dimension)//2
		offsety = (camerasize['y']//binning - dimension)//2
		geometry = {'dimension': {'x': dimension, 'y': dimension},
								'offset': {'x': offsetx, 'y': offsety},
								'binning': {'x': binning, 'y': binning}}
		return geometry

	def validateGeometry(self, geometry=None):
		if geometry is None:
			geometry = self.getGeometry()
		camerasize = self.getCameraSize()
		for a in ['x', 'y']:
			if geometry['dimension'][a] < 0 or geometry['offset'][a] < 0:
				return False
			size = geometry['dimension'][a] + geometry['offset'][a]
			size *= geometry['binning'][a]
			if size > camerasize[a]:
				return False
		return True

	def getGeometry(self):
		geometry = {}
		geometry['dimension'] = self.getDimension()
		geometry['offset'] = self.getOffset()
		geometry['binning'] = self.getBinning()
		return geometry

	def setGeometry(self, geometry):
		if not self.validateGeometry(geometry):
			raise GeometryError
		self.setDimension(geometry['dimension'])
		self.setOffset(geometry['offset'])
		self.setBinning(geometry['binning'])

	def getSettings(self):
		settings = self.getGeometry()
		settings['exposure time'] = self.getExposureTime()
		try:
			settings['save frames'] = self.getSaveRawFrames()
		except:
			settings['save frames'] = False
		try:
			settings['frame time'] = self.getFrameTime()
		except:
			settings['frame time'] = None
		try:
			settings['request nframes'] = self.getRequestNFrames()
		except:
			settings['request nframes'] = self.getNumberOfFrames()
		try:
			settings['use frames'] = self.getUseFrames()
		except:
			settings['use frames'] = ()
		try:
			settings['readout delay'] = self.getReadoutDelay()
		except:
			settings['readout delay'] = 0
		try:
			settings['align frames'] = self.getAlignFrames()
		except:
			settings['save frames'] = False
		try:
			settings['align frame filter'] = self.getAlignFilter()
		except:
			settings['align frame filter'] = 'None'
		return settings

	def setSettings(self, settings):
		self.setGeometry(settings)
		self.setExposureTime(settings['exposure time'])
		try:
			self.setSaveRawFrames(settings['save frames'])
		except:
			pass
		try:
			self.setUseFrames(settings['use frames'])
		except:
			pass
		try:
			self.setFrameTime(settings['frame time'])
		except:
			pass
		try:
			self.setRequestNFrames(settings['request nframes'])
		except:
			pass
		try:
			self.setReadoutDelay(settings['readout delay'])
		except:
			pass
		try:
			self.setAlignFrames(settings['align frames'])
		except:
			pass
		try:
			self.setAlignFilter(settings['align filter'])
		except:
			pass

	def getBinnedMultiplier(self):
		'''
Standard hardware binning causes a binned pixel to have
following:
	binned value = binning^2 * unbinned value
	OR
	unbinned value = binned value / binning^2
Sometime binning is done in software or modified in software, so there
could be a non-standard factor:
	binned value = binning^2 * unbinnned value / M
	OR
	unbinned value = M * binned value / binning^2
This method returns that multiplier, M.  In the standard case, returns 1.0.
		'''
		return 1.0

	def getBinning(self):
		raise NotImplementedError

	def setBinning(self, value):
		raise NotImplementedError

	def getOffset(self):
		raise NotImplementedError

	def setOffset(self, value):
		raise NotImplementedError

	def getDimension(self):
		raise NotImplementedError

	def setDimension(self, value):
		raise NotImplementedError

	def getExposureTime(self):
		# float milliseconds
		raise NotImplementedError

	def setExposureTime(self, value):
		# float milliseconds
		raise NotImplementedError

	def getExposureTypes(self):
		raise NotImplementedError

	def getExposureType(self):
		raise NotImplementedError

	def setExposureType(self, value):
		raise NotImplementedError

	def getPixelSize(self):
		raise NotImplementedError

	def getCameraBinnings(self):
		return self.binning_limits

	def getCameraBinMethod(self):
		return self.binmethod

	def getCameraSize(self):
		if self.configured_size is not None:
			return dict(self.configured_size)
		else:
			try:
				return self._getCameraSize()
			except:
				raise RuntimeError('You need to configure "width" and "height" in instruments.cfg, or implement _getCameraSize() in your camera class')

	def getExposureTimestamp(self):
		return self.exposure_timestamp

	def registerCallback(self, name, callback):
		print('REGISTER', name, callback, time.time())
		self.callbacks[name] = callback

	def waitForCameraReady(self):
		'''
		Wait for acquisition set blocking asynchronous process to finish
		'''
		pass

	def getImage(self):
		if self.readoutcallback:
			name = str(time.time())
			self.registerCallback(name, self.readoutcallback)
			self.backgroundReadout(name)
		else:
			return self._getImage()

	def setReadoutCallback(self, callback):
		self.readoutcallback = callback

	def getReadoutCallback(self):
		return None

	def backgroundReadout(self, name):
		#self.buffer_ready[name] = threading.Event()
		threading.Thread(target=self.getImageToCallback, args=(name,)).start()
		t = 0.2 + self.getExposureTime() / 1000.0
		time.sleep(t)
		## wait for t or getImage to be done, which ever is first
		#self.buffer_ready[name].wait(t)
		print('EXPOSURE DONE (READOUT NOT DONE)', time.time())

	def getImageToCallback(self, name):
		print('GETIMAGETOCALLBACK', name, time.time())
		image = self._getImage()
		try:
			print('CALLBACK', self.callbacks[name], time.time())
			self.callbacks[name](image)
			print('CALLBACKDONE', time.time())
		finally:
			del self.callbacks[name]

	def getImageToBuffer(self, name):
		image = self._getImage()
		self.bufferlock.acquire()
		self.buffer[name] = image
		self.bufferlock.release()
		self.buffer_ready[name].set()

	def getBuffer(self, name, block=True):
		if block:
			self.buffer_ready[name].wait()
		self.bufferlock.acquire()
		if name in self.buffer:
			image = self.buffer[name]
			del self.buffer[name]
			del self.buffer_ready[name]
		else:	
			image = None
		self.bufferlock.release()
		return image

	def _getImage(self):
		raise NotImplementedError

	def getRetractable(self):
		return False

	def getEnergyFiltered(self):
		return False

	def getSaveRawFrames(self):
		return False

	def getNumberOfFrames(self):
		return 1
	#def setSaveRawFrames(self, value):
	#	raise NotImplementedError

	def getAlignFrames(self):
		return False

	#def setAlignFrames(self, value):
	#	raise NotImplementedError

	def getAlignFilter(self):
		return 'None'

	#def setAlignFilter(self, value):
	#	raise NotImplementedError

	def getSystemGainDarkCorrected(self):
		# deprecated in v3.6
		return False

	def getSystemDarkSubtracted(self):
		return False

	def getFrameGainCorrected(self):
		return False

	def getSumGainCorrected(self):
		return False

	def getCalculateNormOnDark(self):
		return True

	def requireRecentDarkOnBright(self):
		return False

	def getFrameFlip(self):
		# flip before? rotation
		return False

	def getFrameRotate(self):
		# rotation in multiple of 90 degrees
		return 0

	def getSaveLzwTiffFrames(self):
		# Lzw Tiff file saving for frames
		return False

	def getSaveEer(self):
		# EERfile saving for frames
		return False

	def requireRecentDarkCurrentReferenceOnBright(self):
		return False
	
	def getRetractable(self):
		raise NotImplementedError

	def setInserted(self, value):
		raise NotImplementedError

	def getInserted(self):
		raise NotImplementedError

	def startMovie(self,filename, exposure_time_ms):
		pass

	def stopMovie(self,filename, exposure_time_ms):
		# set series_length
		self.series_length = 1
		pass

	def getSeriesLength(self):
		return self.series_length

	def _midNightDelay(self, delay_start, delay_length, force_insert=0):
		'''
		Sleep for delay_length of minutes starting at delay_start in minutes
		before midnight.  To prevent camera automatically retract and thus
		release its shutter control, a retractable camera will be inserted
		at force_insert interval.
		'''
		if delay_start is None or delay_length is None or delay_length < 1:
			# timing not defined or length is zero
			return
		ctime = time.strftime("%H:%M:%S")
		h,m,s = list(map((lambda x: int(x)),ctime.split(':')))
		if h < 12:
			h += 12
		else:
			h -= 12
		second_since_noon = (h*60+m)*60+s
		delay_start_time = (12*60-delay_start)*60
		delay_end_time = (12*60-delay_start+delay_length)*60
		if second_since_noon > delay_end_time or second_since_noon < delay_start_time:
			return
		sleep_time = delay_end_time - second_since_noon
		print('Sleeping started at %s for %d seconds' % (ctime, int(sleep_time)))
		sleep_start = time.time()
		remain_time = sleep_time - (time.time() - sleep_start)
		if force_insert > 0 and self.getRetractable():
			while remain_time > force_insert*60:
				time.sleep(force_insert*60)
				self.setInserted(True)
				remain_time = sleep_time - (time.time() - sleep_start)
				print('force inserted', remain_time)
				continue
			# finish with the remain_time
			time.sleep(remain_time)
			return
		# just sleep if not retractable
		time.sleep(sleep_time)

	def getFastSave(self):
		# Fastsave saves a small image arrary for frame camera to reduce handling time.
		return False

	def setFastSave(self, state):
		# Fastsave saves a small image arrary for frame camera to reduce handling time.
		pass
 
	def getEnergyFilterWidthRange(self):
		return 0.0,1000.0

	def getEnergyShiftRange(self):
		return 0.0,1.0
