# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyScope/ccdcamera.py,v $
# $Revision: 1.6 $
# $Name: not supported by cvs2svn $
# $Date: 2005-12-14 17:07:32 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

class GeometryError(Exception):
	pass

class CCDCamera(object):
	name = 'CCD Camera'

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

	def getImage(self):
		raise NotImplementedError

class FastCCDCamera(CCDCamera):
	name = 'Fast CCD Camera'
