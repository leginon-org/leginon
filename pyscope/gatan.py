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
import win32com.client
import gatancom

class Gatan(object):
	def __init__(self):
		self.exposuretype = 'normal'

		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
		try:
			self.camera = win32com.client.Dispatch('TecnaiCCD.GatanCamera')        
		except pywintypes.com_error, e:
			print 'Error dispatching TecnaiCCD.GatanCamera'
			print e
			return

		self.methodmapping = {
			'binning': {'get':'getBinning', 'set': 'setBinning'},
			'dimension': {'get':'getDimension', 'set': 'setDimension'},
			'offset': {'get':'getOffset', 'set': 'setOffset'},
			'exposure time': {'get':'getExposureTime', 'set': 'setExposureTime'},
			'exposure type': {'get':'getExposureType', 'set': 'setExposureType'},
			'inserted': {'get': 'getInserted', 'set': 'setInserted'},
			'image data': {'get':'getImage'}
		}

	def getOffset(self):
		return {'x': self.camera.CameraLeft, 'y': self.camera.CameraTop}

	def setOffset(self, value):
		dimension = self.getDimension()
		self.camera.CameraLeft = value['x']
		self.camera.CameraTop = value['y']
		self.camera.CameraRight = value['x'] + dimension['x']
		self.camera.CameraBottom = value['y'] + dimension['y']

	def getDimension(self):
		offset = self.getOffset()
		return {'x': self.camera.CameraRight - offset['x'],
						'y': self.camera.CameraBottom - offset['y']}

	def setDimension(self, value):
		offset = self.getOffset()
		self.camera.CameraRight = offset['x'] + value['x']
		self.camera.CameraBottom = offset['y'] + value['y']

	def getBinning(self):
		return {'x': self.camera.Binning, 'y': self.camera.Binning}

	def setBinning(self, value):
		if value['x'] != value['y']:
			raise ValueError('multiple binning dimesions not supported')
		self.camera.Binning = value['x']

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
		if self.getExposureType() == 'dark':
			if self.getInserted():
				self.setInserted(False)
				image = self.camera.AcquireRawImage()
				self.setInserted(True)
				return image
		return self.camera.AcquireRawImage()

	def setInserted(self, value):
		if value:
			self.camera.Insert()
		else:
			self.camera.Retract()

	def getInserted(self):
		if self.camera.IsInserted == 1:
			return True
		else:
			return False

