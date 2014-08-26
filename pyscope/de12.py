import sys
import DECameraClientLib
import struct
import types
import numpy
import time
import pyami.imagefun

import ccdcamera
class DE12(ccdcamera.CCDCamera):
	name = 'DE12OLD'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		self.camera_name = 'DE12'
		self.server = DECameraClientLib.DECameraClientLib()
		self.connect()		
		self.offset = {'x': 0, 'y': 0}
		self.dimension = {'x': 4096, 'y': 3072}
		self.binning = {'x': 1, 'y': 1}
		#update a few essential camera properties to default values
		self.setProperty('Correction Mode', 'Uncorrected Raw')
		self.setProperty('Ignore Number of Frames', 0)
		self.setProperty('Preexposure Time (seconds)', 0.043)		

	def __del__(self):
		self.disconnect()

	def connect(self):
		self.server.connect()
		self.server.setActiveCamera(self.camera_name)

	def disconnect(self):
		if(self.server.connected) :
			self.server.disconnect()

	def _getCameraSize(self):
		return self.getDictProp('Image Size')

	def getCameras(self):		
		return self.server.getAvailableCameras()		

	def print_props(self):		
		camera_properties = self.server.getActiveCameraProperties()
		for one_property in camera_properties:
			print one_property, self.server.getProperty(one_property)		

	def getProperty(self, name):		
		value = self.server.getProperty(name)
		return value

	def setProperty(self, name, value):		
		value = self.server.setProperty(name, value)
		return value

	def getExposureTime(self):
		seconds = self.getProperty('Exposure Time (seconds)')
		ms = int(seconds * 1000.0)
		return ms

	def setExposureTime(self, ms):
		seconds = ms / 1000.0
		print 'SETTING EXPTIME', time.time(), seconds
		self.setProperty('Exposure Time (seconds)', seconds)

	def getDictProp(self, name):		
		x = int(self.server.getProperty(name + ' X'))
		y = int(self.server.getProperty(name + ' Y'))
		return {'x': x, 'y': y}

	def setDictProp(self, name, xydict):		
		self.server.setProperty(name + ' X', int(xydict['x']))
		self.server.setProperty(name + ' Y', int(xydict['y']))		

	def getDimension(self):
		return self.dimension

	def setDimension(self, dimdict):
		self.dimension = dimdict
	
	def getBinning(self):
		return self.binning

	def setBinning(self, bindict):
		self.binning = bindict

	def getOffset(self):
		return self.offset

	def setOffset(self, offdict):
		self.offset = offdict

	def _getImage(self):
		t0 = time.time()
		image = self.server.GetImage()
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0
		if not isinstance(image, numpy.ndarray):
			raise ValueError('DE12 GetImage did not return array')
		image = self.finalizeGeometry(image)
		print 'Pausing, otherwise, no frames name when this returns.'
		time.sleep(0.5)
		return image

	def finalizeGeometry(self, image):
		row_start = self.offset['y'] * self.binning['y']
		col_start = self.offset['x'] * self.binning['x']
		nobin_rows = self.dimension['y'] * self.binning['y']
		nobin_cols = self.dimension['x'] * self.binning['x']
		row_end = row_start + nobin_rows
		col_end = col_start + nobin_cols
		nobin_image = image[row_start:row_end, col_start:col_end]
		assert self.binning['x'] == self.binning['y']
		binning = self.binning['x']
		bin_image = pyami.imagefun.bin(nobin_image, binning)
		bin_image = numpy.fliplr(bin_image)
		return bin_image

	def getPixelSize(self):
		psize = 6e-6
		return {'x': psize, 'y': psize}

	def getRetractable(self):
		return True
		
	def setInserted(self, value):
		if value:
			de12value = 'Extended'
			sleeptime = 20
		else:
			de12value = 'Retracted'
			sleeptime = 8
		self.setProperty("Camera Position", de12value)
		time.sleep(sleeptime)
		
	def getInserted(self):
		de12value = self.getProperty('Camera Position Status')
		return de12value == 'Extended'

	def getExposureTypes(self):
		return ['normal','dark']

	def getExposureType(self):
		exposure_type = self.getProperty('Exposure Mode')		
		return exposure_type.lower()
		
	def setExposureType(self, value):		
		self.setProperty('Exposure Mode', value.capitalize()) 

	def getNumberOfFrames(self):
		return self.getProperty('Total Number of Frames')

	def getSaveRawFrames(self):
		'''Save or Discard'''
		value = self.getProperty('Autosave Raw Frames')
		if value == 'Save':
			return True
		elif value == 'Discard':
			return False
		else:
			raise ValueError('unexpected value from Autosave Raw Frames: %s' % (value,))

	def setSaveRawFrames(self, value):
		'''True: save frames,  False: discard frames'''
		if value:
			value_string = 'Save'
		else:
			value_string = 'Discard'
		self.setProperty('Autosave Raw Frames', value_string)

	def getPreviousRawFramesName(self):
		frames_name = self.getProperty('Autosave Frames - Previous Dataset Name')
		return frames_name
        
	def getNumberOfFramesSaved(self):
		nframes = self.getProperty('Autosave Raw Frames - Frames Written in Last Exposure')
		return int(nframes)

	def getUseFrames(self):
		nsum = self.getProperty('Autosave Sum Frames - Sum Count')
		first = self.getProperty('Autosave Sum Frames - Ignored Frames')
		print 'NSUM', nsum
		print 'FIRST', first
		last = first + nsum
		ntotal = self.getNumberOfFrames()
		if last > ntotal:
			last = ntotal
		sumframes = range(first,last)
		return tuple(sumframes)

	def setUseFrames(self, frames):
		total_frames = self.getNumberOfFrames()
		if frames:
			nskip = frames[0]
			last = frames[-1]
		else:
			nskip = 0
			last = total_frames - 1
		nsum = last - nskip + 1
		if nsum > total_frames:
			nsum = total_frames
		nsum = int(nsum)
		print 'NSUM', nsum
		print 'NSKIP', nskip
		self.setProperty('Autosave Sum Frames - Sum Count', nsum)
		self.setProperty('Autosave Sum Frames - Ignored Frames', nskip)

	def getFrameRate(self):
		return self.getProperty('Frames Per Second')

	def getReadoutDelay(self):
		return self.getProperty('Sensor Readout Delay (milliseconds)')

	def setReadoutDelay(self, milliseconds):
		self.setProperty('Sensor Readout Delay (milliseconds)', milliseconds)
