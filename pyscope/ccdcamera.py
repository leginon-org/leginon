# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyScope/ccdcamera.py,v $
# $Revision: 1.9 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-22 23:04:58 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import time
import threading

class GeometryError(Exception):
	pass

class CCDCamera(object):
	name = 'CCD Camera'

	def __init__(self):
		self.buffer = {}
		self.buffer_ready = {}
		self.bufferlock = threading.Lock()

	def calculateCenteredGeometry(self, dimension, binning):
		camerasize = self.getCameraSize()
		offset = (camerasize['x']/binning - dimension)/2
		geometry = {'dimension': {'x': dimension, 'y': dimension},
								'offset': {'x': offset, 'y': offset},
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
		return settings

	def setSettings(self, settings):
		self.setGeometry(settings)
		self.setExposureTime(settings['exposure time'])

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
		raise NotImplementedError

	def setExposureTime(self, value):
		raise NotImplementedError

	def getExposureTypes(self):
		raise NotImplementedError

	def getExposureType(self):
		raise NotImplementedError

	def setExposureType(self, value):
		raise NotImplementedError

	def getPixelSize(self):
		raise NotImplementedError

	def getCameraSize(self):
		raise NotImplementedError

	def getImage(self, bgreadout=False):
		if bgreadout:
			return self.backgroundReadout()
		else:
			return self._getImage()

	def backgroundReadout(self):
		name = str(time.time())
		self.buffer_ready[name] = threading.Event()
		threading.Thread(target=self.getImageToBuffer, args=(name,)).run()
		t = 1.0 + self.getExposureTime() / 1000.0
		## wait for t or getImage to be done, which ever is first
		self.buffer_ready[name].wait(t)
		return name

	def getImageToBuffer(self, name):
		image = self._getImage()
		self.bufferlock.acquire()
		self.buffer[name] = image
		self.bufferlock.release()
		self.buffer_ready[name].set()

	def getBuffer(self, name, block=False):
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

class FastCCDCamera(CCDCamera):
	name = 'Fast CCD Camera'
