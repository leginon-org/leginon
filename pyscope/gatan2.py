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
import comtypes
import comtypes.client

class Gatan(ccdcamera.CCDCamera):
	name = 'Gatan'
	def __init__(self):
		self.unsupported = []
		ccdcamera.CCDCamera.__init__(self)

		self.cameraid = 0

		import comtypes
		self.camera = comtypes.client.CreateObject('TecnaiCCD.GatanCamera.2')
		import comtypes.gen.TECNAICCDLib
		self.gen_module = comtypes.gen.TECNAICCDLib

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

	def __getattribute__(self, attr_name):
		if attr_name in object.__getattribute__(self, 'unsupported'):
			raise AttributeError('attribute not supported')
		return object.__getattribute__(self, attr_name)

	def getOffset(self):
		return dict(self.offset)

	def dictToInt(self, d):
		new_d = {}
		for key, value in d.items():
			new_d[key] = int(value)
		return new_d

	def setOffset(self, value):
		self.offset = self.dictToInt(value)

	def getDimension(self):
		return dict(self.dimension)

	def setDimension(self, value):
		self.dimension = self.dictToInt(value)

	def getBinning(self):
		return dict(self.binning)

	def setBinning(self, value):
		if value['x'] != value['y']:
			raise ValueError('multiple binning dimesions not supported')
		self.binning = self.dictToInt(value)

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
		image = self.camera.AcquireRawImage()
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0
		image = image.astype(numpy.uint16)
		image.shape = self.dimension['y'], self.dimension['x']
		return image

	def _getImage(self):
		self.camera.Binning = self.binning['x']
		self.camera.CameraLeft = self.offset['x']
		self.camera.CameraTop = self.offset['y']
		self.camera.CameraRight = self.dimension['x'] + self.camera.CameraLeft
		self.camera.CameraBottom = self.dimension['y'] + self.camera.CameraTop
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
		image = self.acquireRaw()
		return image

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
		self.camera.Speed = value

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

