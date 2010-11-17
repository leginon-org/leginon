import copy
import ccdcamera
import numpy
import random
random.seed()
import time
import remote
import os

class SimCCDCamera(ccdcamera.CCDCamera):
	name = 'SimCCDCamera'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		self.camera_size = {'x': 4096, 'y': 4096}
		#self.camera_size = {'x': 4096, 'y': 3072}
		self.binning_values = {'x': [1, 2, 4, 8], 'y': [1, 2, 4, 8]}
		self.pixel_size = {'x': 2.5e-5, 'y': 2.5e-5}
		self.exposure_types = ['normal', 'dark', 'bias']

		self.binning = {'x': 1, 'y': 1}
		self.offset = {'x': 0, 'y': 0}
		self.dimension = copy.copy(self.camera_size)
		self.exposure_time = 0.01
		self.exposure_type = 'normal'

		self.energy_filter = False
		self.energy_filter_width = 0.0

		self.views = ('square', 'empty')
		self.view = 'square'
		#self.view = 'empty'
		self.frames_on = True
		self.frame_rate = 0.05
		self.inserted = True
		self.saverawframes = False
		self.rawframesname = 'frames'

	def getRetractable(self):
		return True

	def getInserted(self):
		return self.inserted

	def setInserted(self, value):
		self.inserted = value

	def setView(self, view):
		self.view = view

	def getView(self):
		return self.view

	def getViews(self):
		return self.views

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
				if value[axis] < 0 or value[axis] >= self.camera_size[axis]:
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
				if value[axis] < 1 or value[axis] > self.camera_size[axis]:
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

	def getCameraSize(self):
		return copy.copy(self.camera_size)

	def _simBias(self, shape):
		bias = numpy.arange(100,115)
		bias = numpy.resize(bias, shape)
		noise = numpy.random.normal(0.0, 2.0, shape)
		bias = bias + noise
		bias = numpy.asarray(bias, numpy.uint16)
		#print 'BIAS', bias
		return bias

	def _simDark(self, shape, exptime):
		# return image:  dark + bias
		## counts per second
		darkrate = numpy.array((0.1, 0.1, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2), numpy.float32)
		dark = exptime * darkrate
		dark = numpy.resize(dark, shape)
		dark = dark + self._simBias(shape)
		dark = numpy.asarray(dark, numpy.uint16)
		#print 'DARK', dark
		return dark

	def _simExposure(self, shape, exptime):
		# return image:  dark + bias + exposure
		# light sensitivity in counts per second
		sensitivity = self.binning['x'] * self.binning['y'] * numpy.arange(2000, 2065)
		sensitivity = numpy.resize(sensitivity, shape)
		exposure = exptime * sensitivity
		noise = numpy.random.normal(0.0, 50.0, shape)
		exposure = exposure + noise
		final = self._simDark(shape, exptime) + exposure
		final = numpy.asarray(final, numpy.uint16)
		#print 'EXP', final
		return final

	def _simNormal(self, shape, exptime):
		# return image:  transparency * (dark + bias + exposure)
		final = self._simExposure(shape, exptime) * self._simSample(shape)
		final = numpy.asarray(final, numpy.uint16)
		#print 'NORMAL', final
		return final

	def _simSample(self, shape):
		if self.view == 'empty':
			transparency = numpy.ones(shape, dtype=numpy.float32)
		elif self.view == 'square':
			transparency = 0.9 * numpy.ones(shape, dtype=numpy.float32)
			row_offset = random.randint(-shape[0]/8, shape[0]/8) + shape[0]/4
			column_offset = random.randint(-shape[1]/8, shape[1]/8) + shape[0]/4
			transparency[row_offset:row_offset+shape[0]/2,
					column_offset:column_offset+shape[1]/2] = 0.7
		#print 'VIEW', transparency
		return transparency

	def _getImage(self):
		if not self.validateGeometry():
			raise ValueError('invalid image geometry')

		for axis in ['x', 'y']:
			if self.dimension[axis] % self.binning[axis] != 0:
				raise ValueError('invalid dimension/binning combination')

		columns = self.dimension['x']
		rows = self.dimension['y']

		shape = (rows, columns)

		t0 = time.time()
		## exposure time
		time.sleep(self.exposure_time)
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0

		if self.frames_on:
			nframes = self.getNumberOfFrames()
			exptime = self.frame_rate
		else:
			nframes = 1
			exptime = self.exposure_time

		sum = numpy.zeros(shape, numpy.uint16)
		for i in range(nframes):
			if self.exposure_type == 'bias':
				frame = self._simBias(shape)
			elif self.exposure_type == 'dark':
				frame = self._simDark(shape, exptime)
			elif self.exposure_type == 'normal':
				frame = self._simNormal(shape, exptime)
			else:
				raise RuntimeError('unknown exposure type: %s' % (self.exposure_type,))
			sum += frame

		print 'SAVERAWFRAMES', self.saverawframes
		if self.saverawframes:
			try:
				os.mkdir(self.rawframesname)
			except:
				pass

		return sum

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

	def getNumberOfFrames(self):
		if self.frames_on:
			nframes = int(round(self.exposure_time / self.frame_rate))
			return nframes
		else:
			return None

	def getSaveRawFrames(self):
		'''Save or Discard'''
		return self.saverawframes

	def setSaveRawFrames(self, value):
		'''True: save frames,  False: discard frames'''
		self.saverawframes = bool(value)

	def setNextRawFramesName(self, value):
		self.rawframesname = value

	def getNextRawFramesName(self):
		return self.rawframesname

	def getPreviousRawFramesName(self):
		return self.rawframesname

class SimOtherCCDCamera(SimCCDCamera):
	name = 'SimOtherCCDCamera'
	def _getImage(self):
		im = SimCCDCamera._getImage(self)
		im = 10 * im
		return im
