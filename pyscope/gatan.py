#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import ccdcamera
import numarray
import sys

try:
	import pythoncom
	import pywintypes
	import win32com.client
except ImportError:
	pass
else:
	try:
		import TecnaiCCDWrapper
	except ImportError:
		from pyScope import TecnaiCCDWrapper

class Gatan(ccdcamera.CCDCamera):
	name = 'Gatan'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		self.unsupported = []

		self.cameraid = 0

		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
		try:
			self.camera = win32com.client.dynamic.Dispatch('TecnaiCCD.GatanCamera.2')
		except pywintypes.com_error, e:
			raise RuntimeError('unable to initialize Gatan interface')

		self.camerasize = self._getCameraSize()

		self.binning = {'x': self.camera.Binning, 'y': self.camera.Binning}
		self.offset = {'x': self.camera.CameraLeft, 'y': self.camera.CameraTop}
		self.dimension = {'x': self.camera.CameraRight - self.camera.CameraLeft,
											'y': self.camera.CameraBottom - self.camera.CameraTop}
		self.exposuretype = 'normal'

		self.methodmapping = {
			'binning': {'get':'getBinning', 'set': 'setBinning'},
			'dimension': {'get':'getDimension', 'set': 'setDimension'},
			'offset': {'get':'getOffset', 'set': 'setOffset'},
			'camera size': {'get': 'getCameraSize'},
			'pixel size': {'get': 'getPixelSize'},
			'exposure time': {'get':'getExposureTime', 'set': 'setExposureTime'},
			'exposure type': {'get':'getExposureType', 'set': 'setExposureType'},
			'speed': {'get': 'getSpeed', 'set': 'setSpeed'},
			'inserted': {'get': 'getInserted', 'set': 'setInserted'},
			'retractable': {'get': 'getRetractable'},
			'acquiring': {'get': 'getAcquiring'},
			'image data': {'get':'getImage'}
		}

		self.typemapping = {
			'binning': {'type': dict, 'values':
																		{'x': {'type': int}, 'y': {'type': int}}},
			'dimension': {'type': dict, 'values':
																		{'x': {'type': int}, 'y': {'type': int}}},
			'offset': {'type': dict, 'values':
																		{'x': {'type': int}, 'y': {'type': int}}},
			'exposure time': {'type': int},
			'exposure type': {'type': str, 'values': ['normal', 'dark']},
			'speed': {'type': int},
			'inserted': {'type': bool},
			'retractable': {'type': bool},
			'acquiring': {'type': bool},
			'image data': {'type': numarray.ArrayType},
		}

		if not self.getRetractable():
			self.unsupported.append('getInserted')
			self.unsupported.append('setInserted')
			del self.methodmapping['inserted']
			del self.typemapping['inserted']

	def __getattribute__(self, attr_name):
		if attr_name in object.__getattribute__(self, 'unsupported'):
			raise AttributeError('attribute not supported')
		return object.__getattribute__(self, attr_name)

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
		return int(self.camera.ExposureTime*1000)

	def setExposureTime(self, value):
		self.camera.ExposureTime = float(value)/1000.0

	def getExposureTypes(self):
		return ['normal', 'dark']

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		if value not in ['normal', 'dark']:
			raise ValueError('invalid exposure type')
		self.exposuretype = value

	def getImage(self):
		try:
			self.camera.Binning = self.binning['x']
			self.camera.CameraLeft = self.offset['x']
			self.camera.CameraTop = self.offset['y']
			self.camera.CameraRight = self.dimension['x'] + self.camera.CameraLeft
			self.camera.CameraBottom = self.dimension['y'] + self.camera.CameraTop
		except pywintypes.com_error, e:
			raise ValueError('invalid image dimensions')
		if self.getExposureType() == 'dark':
			if False:
			#if self.getRetractable():
				if self.getInserted():
					self.setInserted(False)
					image = TecnaiCCDWrapper.acquire(self.camera._oleobj_)
					self.setInserted(True)
					return image
			else:
				exposuretime = self.getExposureTime()
				self.setExposureTime(0)
				image = TecnaiCCDWrapper.acquire(self.camera._oleobj_)
				self.setExposureTime(exposuretime)
				return image
		try:
			return TecnaiCCDWrapper.acquire(self.camera._oleobj_)
		except pywintypes.com_error, e:
			raise ValueError('invalid image dimensions')

	def getCameraSize(self):
		return self.camerasize

	def getPixelSize(self):
		x, y = self.camera.GetCCDPixelSize(self.cameraid)
		return {'x': x, 'y': y}

	def getAcquiring(self):
		if self.camera.IsAcquiring:
			return True
		else:
			return False

	def getSpeed(self):
		return self.camera.Speed

	def setSpeed(self, value):
		try:
			self.camera.Speed = value
		except pywintypes.com_error, e:
			raise ValueError('invalid speed')

	def getRetractable(self):
		if self.camera.IsRetractable:
			return True
		else:
			return False

	def setInserted(self, value):
		if value:
			self.camera.Insert()
		else:
			self.camera.Retract()

	def getInserted(self):
		if self.camera.IsInserted:
			return True
		else:
			return False

	def _getCameraSize(self):
		binning = self.camera.Binning
		left = self.camera.CameraLeft
		right = self.camera.CameraRight
		top = self.camera.CameraTop
		bottom = self.camera.CameraBottom

		self.camera.CameraLeft = 0
		self.camera.CameraTop = 0

		size = {}
		for i in ['CameraRight', 'CameraBottom']:
			for j in [4096, 2048, 1024]:
				try:
					setattr(self.camera, i, j)
				except:
					continue
				try:
					setattr(self.camera, i, j + 1)
				except:
					size[i] = j
					break
			if i not in size:
				j = 0
				while True:
					try:
						setattr(self.camera, i, j)
						j += 1
					except:
						break
				size[i] = j - 1
		self.camera.Binning = binning
		self.camera.CameraLeft = left
		self.camera.CameraRight = right
		self.camera.CameraTop = top
		self.camera.CameraBottom = bottom
		return {'x': size['CameraRight'], 'y': size['CameraBottom']}

