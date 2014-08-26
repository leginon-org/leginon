import copy
import ccdcamera
import numpy
import random
random.seed()
import time

class SimCCDCamera(ccdcamera.CCDCamera):
	name = 'SimCCDCamera'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		self.binning_values = {'x': [1, 2, 4, 8], 'y': [1, 2, 4, 8]}
		self.pixel_size = {'x': 2.5e-5, 'y': 2.5e-5}
		self.exposure_types = ['normal', 'dark']

		self.binning = {'x': 1, 'y': 1}
		self.offset = {'x': 0, 'y': 0}
		self.dimension = copy.copy(self.getCameraSize())
		self.exposure_time = 0.01
		self.exposure_type = 'normal'

		self.energy_filter = False
		self.energy_filter_width = 0.0

	def getBinning(self):
		return copy.copy(self.binning)

	def setBinning(self, value):
		for axis in self.binning.keys():
			try:
				if value[axis] not in self.binning_values[axis]:
					raise ValueError('invalid binning')
			except KeyError:
				pass

		for axis in self.binning.keys():
			try:
				self.binning[axis] = value[axis]
			except KeyError:
				pass

	def getOffset(self):
		return copy.copy(self.offset)

	def setOffset(self, value):
		for axis in self.offset.keys():
			try:
				if value[axis] < 0 or value[axis] >= self.getCameraSize()[axis]:
					raise ValueError('invalid offset')
			except KeyError:
				pass

		for axis in self.offset.keys():
			try:
				self.offset[axis] = value[axis]
			except KeyError:
				pass

	def getDimension(self):
		return copy.copy(self.dimension)

	def setDimension(self, value):
		for axis in self.dimension.keys():
			try:
				if value[axis] < 1 or value[axis] > self.getCameraSize()[axis]:
					raise ValueError('invalid dimension')
			except KeyError:
				pass

		for axis in self.dimension.keys():
			try:
				self.dimension[axis] = value[axis]
			except KeyError:
				pass

	def getExposureTime(self):
		return self.exposure_time*1000.0

	def setExposureTime(self, value):
		if value < 0:
			raise ValueError('invalid exposure time')
		self.exposure_time = value/1000.0

	def getExposureTypes(self):
		return self.exposure_types

	def getExposureType(self):
		return self.exposure_type

	def setExposureType(self, value):
		if value not in self.exposure_types:
			raise ValueError('invalid exposure type')
		self.exposure_type = value

	def _getImage(self):
		if not self.validateGeometry():
			raise ValueError('invalid image geometry')

		for axis in ['x', 'y']:
			if self.dimension[axis] * self.binning[axis] > self.getCameraSize()[axis]:
				raise ValueError('invalid dimension/binning combination')

		columns = self.dimension['x']
		rows = self.dimension['y']

		shape = (rows, columns)

		t0 = time.time()
		## exposure time
		time.sleep(self.exposure_time)
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0

		if self.exposure_type == 'dark' or self.exposure_time == 0:
			return numpy.zeros(shape, numpy.uint16)
		else:
			return self.getSyntheticImage(shape)

	def getSyntheticImage(self,shape):
		mean = self.exposure_time * 1000.0
		sigma = 0.1 * mean
		image = numpy.random.normal(mean, sigma, shape)
		row_offset = random.randint(-shape[0]/8, shape[0]/8) + shape[0]/4
		column_offset = random.randint(-shape[1]/8, shape[1]/8) + shape[0]/4
		image[row_offset:row_offset+shape[0]/2,
		  column_offset:column_offset+shape[1]/2] *= 1.5
		image = numpy.asarray(image, dtype=numpy.uint16)
		return image

	def getEnergyFiltered(self):
		return True

	def getEnergyFilter(self):
		return self.energy_filter

	def setEnergyFilter(self, value):
		self.energy_filter = bool(value)

	def getEnergyFilterWidth(self):
		return self.energy_filter_width

	def setEnergyFilterWidth(self, value):
		self.energy_filter_width = float(value)

	def alignEnergyFilterZeroLossPeak(self):
		pass

	def getPixelSize(self):
		return dict(self.pixel_size)

class SimOtherCCDCamera(SimCCDCamera):
	name = 'SimOtherCCDCamera'
	def _getImage(self):
		im = SimCCDCamera._getImage(self)
		im = 10 * im
		return im

	def getRetractable(self):
		return True

	def setInserted(self, value):
		if value == self.getInserted():
			return
		self.inserted = value
		time.sleep(10)

	def getInserted(self):
		if not hasattr(self, 'inserted'):
			self.inserted = True
		return self.inserted

