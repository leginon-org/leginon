#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import sys
sys.coinit_flags = 0
import pythoncom
import pywintypes
import win32com.client
try:
	import numarray as Numeric
except:
	import Numeric
try:
	import TecnaiCCDWrapper
	import gatancom
except ImportError:
	from pyScope import TecnaiCCDWrapper, gatancom

class Gatan(object):
	def __init__(self):
		self.unsupported = []

		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
		try:
			self.camera = win32com.client.Dispatch('TecnaiCCD.GatanCamera')        
		except pywintypes.com_error, e:
			raise RuntimeError('Unable to initialize Gatan interface')

		self.binning = {'x': self.camera.Binning, 'y': self.camera.Binning}
		self.offset = {'x': self.camera.CameraLeft, 'y': self.camera.CameraTop}
		self.dimension = {'x': self.camera.CameraRight - self.camera.CameraLeft,
											'y': self.camera.CameraBottom - self.camera.CameraTop}
		self.exposuretype = 'normal'

		self.methodmapping = {
			'binning': {'get':'getBinning', 'set': 'setBinning'},
			'dimension': {'get':'getDimension', 'set': 'setDimension'},
			'offset': {'get':'getOffset', 'set': 'setOffset'},
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
			'image data': {'type': Numeric.ArrayType},
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
		return self.offset

	def setOffset(self, value):
		self.offset = value

	def getDimension(self):
		return self.dimension

	def setDimension(self, value):
		self.dimension = value

	def getBinning(self):
		return self.binning

	def setBinning(self, value):
		if value['x'] != value['y']:
			raise ValueError('multiple binning dimesions not supported')
		self.binning = value

	def getExposureTime(self):
		return int(self.camera.ExposureTime*1000)

	def setExposureTime(self, value):
		self.camera.ExposureTime = float(value)/1000.0

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		if value not in ['normal', 'dark']:
			raise ValueError('Invalid exposure type')
		self.exposuretype = value

	def getImage(self):
		try:
			self.camera.Binning = self.binning['x']
			self.camera.CameraLeft = self.offset['x']
			self.camera.CameraTop = self.offset['y']
			self.camera.CameraRight = self.dimension['x'] + self.camera.CameraLeft
			self.camera.CameraBottom = self.dimension['y'] + self.camera.CameraTop
		except pywintypes.com_error, e:
			raise ValueError('Invalid image dimensions')
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
			raise ValueError('Invalid image dimensions')

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
			raise ValueError('Invalid speed')

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

