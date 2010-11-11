import sys
import DECameraClientLib
import struct
import types
import numpy
import time
import pyami.imagefun

import ccdcamera
class de12_software_sim(ccdcamera.CCDCamera):
	name = 'de12_software_sim'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		self.camera_name = 'Software Sim'
		self.server = DECameraClientLib.DECameraClientLib()
		self.connect()
		self.offset = {'x': 0, 'y': 0}
		self.dimension = {'x': 1024, 'y': 1024}
		self.binning = {'x': 1, 'y': 1}
		self.exposure_time = 1;

	def __del__(self):
		self.disconnect()

	def connect(self):
		self.server.connect()		
		self.server.setActiveCamera(self.camera_name)
		camera_properties = self.server.getActiveCameraProperties()

	def disconnect(self):
		if(self.server.connected) :
			self.server.disconnect()

	def getCameraSize(self):
		return self.getDictProp('Image Size')

	def getCameras(self):
		#self.connect()
		return self.server.getAvailableCameras()
		#self.disconnect()

	def print_props(self):
		#self.connect()
		camera_properties = self.server.getActiveCameraProperties()
		for one_property in camera_properties:
			print one_property, self.server.getProperty(one_property)
		#self.disconnect()

	def getProperty(self, name):
		#self.connect()
		value = self.server.getProperty(name)
		return value

	def setProperty(self, name, value):
		#self.connect()
		value = self.server.setProperty(name, value)
		return value

	def getExposureTime(self):
		#seconds = self.getProperty('Exposure Time')
		seconds = self.exposure_time
		ms = int(seconds * 1000.0)
		return ms

	def setExposureTime(self, ms):
		seconds = ms / 1000.0
		self.exposure_time = seconds
		#self.setProperty('Exposure Time', seconds)

	def getDictProp(self, name):
		#self.connect()
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
		image = self.server.GetImage()
		if not isinstance(image, numpy.ndarray):
			raise ValueError('DE12 GetImage did not return array')
		image = self.finalizeGeometry(image)
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
		return False

	def getExposureTypes(self):
		return ['normal','dark']

	def getExposureType(self):
		#exposure_type = self.getProperty('Exposure Mode')		
		return 'normal'
		
	def setExposureType(self, value):
		return
		#self.setProperty('Exposure Mode','Normal') 