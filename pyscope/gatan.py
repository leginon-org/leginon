#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#

import ccdcamera
import sys
import numpy
import time

try:
	import pythoncom
	import pywintypes
	import win32com.client
	import comarray
except ImportError:
	pass

## create a single connection to tecnaiccd COM object.
## Muliple calls to get_tecnaiccd will return the same connection.
## Store the handle in win32com.client module, which is safer than in
## this module due to multiple imports.
win32com.client.tecnaiccd = None
def get_tecnaiccd():
	if win32com.client.tecnaiccd is None:
			 win32com.client.tecnaiccd = win32com.client.dynamic.Dispatch('TecnaiCCD.GatanCamera.2')
	return win32com.client.tecnaiccd


class Gatan(ccdcamera.CCDCamera):
	name = 'Gatan'
	cameraid = 0
	def __init__(self):
		self.unsupported = []
		ccdcamera.CCDCamera.__init__(self)

		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
		try:
			self._camera = get_tecnaiccd()
		except pywintypes.com_error, e:
			raise RuntimeError('unable to initialize Gatan interface')

		self.calculated_camerasize = self._calculateCameraSize()

		self.binning = {'x': self.camera.Binning, 'y': self.camera.Binning}
		self.offset = {'x': self.camera.CameraLeft, 'y': self.camera.CameraTop}
		self.dimension = {'x': self.camera.CameraRight - self.camera.CameraLeft,
						'y': self.camera.CameraBottom - self.camera.CameraTop}
		self.exposuretype = 'normal'

		if not self.getRetractable():
			self.unsupported.append('getInserted')
			self.unsupported.append('setInserted')

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

		self.filter_functions = {}
		for name, method_name in self.script_functions:
			if self.hasScriptFunction(name):
				self.filter_functions[method_name] = name
			else:
				self.unsupported.append(method_name)

	def __getattr__(self, name):
		# When asked for self.camera, instead return self._camera, but only
		# after setting the current camera id
		if name == 'camera':
			self._camera.CurrentCamera = self.cameraid
			return self._camera
		else:
			return ccdcamera.CCDCamera.__getattr__(self, name)

	def __getattribute__(self, attr_name):
		#if hasattr(self, 'unsupported') and attr_name in object.__getattribute__(self, 'unsupported'):
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
		return self.camera.ExposureTime*1000.0

	def setExposureTime(self, value):
		self.camera.ExposureTime = value/1000.0

	def getExposureTypes(self):
		return ['normal', 'dark']

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		if value not in ['normal', 'dark']:
			raise ValueError('invalid exposure type')
		self.exposuretype = value

	def acquireRaw(self):
		t0 = time.time()
		image = comarray.call(self.camera, 'AcquireRawImage')
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0
		return image

	def _getImage(self):
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

					image = self.acquireRaw()

					self.setInserted(True)
					return image
			else:
				exposuretime = self.getExposureTime()
				self.setExposureTime(0)
				image = self.acquireRaw()
				self.setExposureTime(exposuretime)
				return image
		try:
			image = self.acquireRaw()
			return image.astype(numpy.uint16)
		except pywintypes.com_error, e:
			raise ValueError('invalid image dimensions')

	def _getCameraSize(self):
		return self.calculated_camerasize

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
		inserted = self.getInserted()
		if not inserted and value:
			self.camera.Insert()
		elif inserted and not value:
			self.camera.Retract()
		else:
			return
		time.sleep(5)

	def getInserted(self):
		if self.camera.IsInserted:
			return True
		else:
			return False

	def _calculateCameraSize(self):
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

	def hasScriptFunction(self, name):
		script = 'if(DoesFunctionExist("%s")) Exit(1.0) else Exit(-1.0)'
		script %= name
		result = self.camera.ExecuteScript(script)
		return result > 0.0

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

class Gatan0(Gatan):
	name = 'Gatan0'
	cameraid = 0

class Gatan1(Gatan):
	name = 'Gatan1'
	cameraid = 1

class Gatan2(Gatan):
	name = 'Gatan2'
	cameraid = 2

class Gatan3(Gatan):
	name = 'Gatan3'
	cameraid = 3

