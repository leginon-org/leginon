# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/instrument.py,v $
# $Revision: 1.15 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-24 20:15:21 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import data
import remotecall

class Proxy(object):
	def __init__(self, objectservice, session=None):
		self.tems = {}
		self.ccdcameras = {}
		self.imagecorrections = {}
		self.tem = None
		self.ccdcamera = None
		self.imagecorrection = None
		self.session = session
		self.objectservice = objectservice
		self.objectservice._addDescriptionHandler(add=self.onAddDescription,
																							remove=self.onRemoveDescription)

	def onAddDescription(self, nodename, name, description, types):
		if 'TEM' in types:
			proxy = self.objectservice.getObjectProxy(nodename, name)
			self.tems[name] = proxy
			if self.tem is None:
				self.setTEM(name)

		if 'CCDCamera' in types:
			proxy = self.objectservice.getObjectProxy(nodename, name)
			self.ccdcameras[name] = proxy
			if self.ccdcamera is None:
				self.setCCDCamera(name)

		if 'ImageCorrection' in types:
			proxy = self.objectservice.getObjectProxy(nodename, name)
			self.imagecorrections[name] = proxy
			if self.imagecorrection is None:
				self.setImageCorrection(name)

	def onRemoveDescription(self, nodename, name):
		if name in self.tems and self.tem is self.tems[name]:
			self.tem = None

		if name in self.ccdcameras and self.ccdcamera is self.ccdcameras[name]:
			self.ccdcamera = None

		if name in self.imagecorrections:
			if self.imagecorrection is self.imagecorrections[name]:
				self.imagecorrection = None

	def getTEMNames(self):
		return self.tems.keys()

	def getCCDCameraNames(self):
		return self.ccdcameras.keys()

	def getImageCorrectionNames(self):
		return self.imagecorrections.keys()

	def setTEM(self, name):
		if name is None:
			self.tem = None
		else:
			self.tem = self.tems[name]

	def setCCDCamera(self, name):
		if name is None:
			self.ccdcamera = None
		else:
			self.ccdcamera = self.ccdcameras[name]

	def setImageCorrection(self, name):
		if name is None:
			self.imagecorrection = None
		else:
			self.imagecorrection = self.imagecorrections[name]

	def getData(self, dataclass, image=True):
		if issubclass(dataclass, data.ScopeEMData):
			proxy = self.tem
		elif issubclass(dataclass, data.CameraEMData):
			proxy = self.ccdcamera
		elif issubclass(dataclass, data.CameraImageData):
			instance = dataclass()
			instance['scope'] = self.getData(data.ScopeEMData)
			instance['camera'] = self.getData(data.CameraEMData, image=image)
			if image:
				instance['image'] = instance['camera']['image data']
				instance['camera']['image data'] = None
			instance['session'] = self.session
			return instance
		elif issubclass(dataclass, data.CorrectedCameraImageData):
			if self.imagecorrection is None:
				raise RuntimeError('no image correction set')
			return self.imagecorrection.ImageData
		if proxy is None:
			raise ValueError('no proxy selected for this data class')
		instance = dataclass()
		keys = []
		attributes = []
		types = []
		for key, attribute in parametermapping:
			if not image and attribute == 'Image':
				continue
			if key not in instance:
				continue
			attributetypes = proxy.getAttributeTypes(attribute)
			if not attributetypes:
				continue
			if 'r' in attributetypes:
				keys.append(key)
				attributes.append(attribute)
				types.append('r')
		result = proxy.multiCall(attributes, types)
		for i, key in enumerate(keys):
			instance[key] = result[i]
		instance['session'] = self.session
		return instance

	def setData(self, instance):
		if isinstance(instance, data.ScopeEMData):
			proxy = self.tem
		elif isinstance(instance, data.CameraEMData):
			proxy = self.ccdcamera
		elif isinstance(instance, data.CameraImageData):
			instance = dataclass()
			self.setData(instance['scope'])
			self.setData(instance['camera'])
			return
		if proxy is None:
			raise ValueError('no proxy selected for this data instance')
		keys = []
		attributes = []
		types = []
		args = []
		for key, attribute in parametermapping:
			if key not in instance or instance[key] is None:
				continue
			attributetypes = proxy.getAttributeTypes(attribute)
			if not attributetypes:
				continue
			if 'w' in attributetypes:
				types.append('w')
			elif 'method' in attributetypes:
				types.append('method')
			else:
				continue
			keys.append(key)
			attributes.append(attribute)
			args.append((instance[key],))
		proxy.multiCall(attributes, types, args)

class TEM(remotecall.Locker):
	pass

class CCDCamera(remotecall.Locker):
	pass

class FastCCDCamera(CCDCamera):
	pass

parametermapping = (
	# ScopeEM
	('magnification', 'Magnification'),
	('spot size', 'SpotSize'),
	('image shift', 'ImageShift'),
	('beam shift', 'BeamShift'),
	('focus', 'Focus'),
	('defocus', 'Defocus'),
	('reset defocus', 'resetDefocus'),
	('intensity', 'Intensity'),
	('magnifications', 'Magnifications'),
	('screen current', 'ScreenCurrent'),
	('stigmator', 'Stigmator'),
	('beam tilt', 'BeamTilt'),
	('corrected stage position', 'CorrectedStagePosition'),
	('stage position', 'StagePosition'),
	('column pressure', 'ColumnPressure'),
	('high tension', 'HighTension'),
	('main screen position', 'MainScreenPosition'),
	('small screen position', 'SmallScreenPosition'),
	('film stock', 'FilmStock'),
	('film exposure number', 'FilmExposureNumber'),
	('pre film exposure', 'preFilmExposure'),
	('post film exposure', 'postFilmExposure'),
	('film exposure type', 'FilmExposureType'),
	('film exposure time', 'FilmExposureTime'),
	('film manual exposure time', 'FilmManualExposureTime'),
	('film automatic exposure time', 'FilmAutomaticExposureTime'),
	('film text', 'FilmText'),
	('film user code', 'FilmUserCode'),
	('film date type', 'FilmDateType'),
	# not used
	#('beam blank', 'BeamBlank'),
	#('film exposure', 'filmExposure'),
	#('low dose', 'LowDose'),
	#('low dose mode', 'LowDoseMode'),
	#('turbo pump', 'TurboPump'),
	#('holder type', 'HolderType'),
	#('holder status', 'HolderStatus'),
	#('stage status', 'StageStatus'),
	#('vacuum status', 'VacuumStatus'),
	#('column valves', 'ColumnValves'),

	# CameraEM
	('dimension', 'Dimension'),
	('binning', 'Binning'),
	('offset', 'Offset'),
	('exposure time', 'ExposureTime'),
	('exposure type', 'ExposureType'),
	('image data', 'Image'),
	('inserted', 'Inserted'),
)

