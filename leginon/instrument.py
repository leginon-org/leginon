# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/instrument.py,v $
# $Revision: 1.8 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-23 22:24:07 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import data
import remotecall

class Proxy(object):
	def __init__(self, objectservice):
		self.tems = {}
		self.ccdcameras = {}
		self.tem = None
		self.ccdcamera = None
		self.objectservice = objectservice
		self.objectservice._addDescriptionHandler(add=self.onAddDescription,
																							remove=self.onRemoveDescription)

	def onAddDescription(self, nodename, name, description, types):
		pass

	def onRemoveDescription(self, nodename, name):
		pass

	def getTEMNames(self):
		objects = self.objectservice.getObjectsByType('TEM')
		self.tems = {}
		for nodename, name in objects:
			string = '%s (%s)' % (name, nodename)
			proxy = self.objectservice.getObjectProxy(nodename, name)
			self.tems[string] = proxy
		return self.tems.keys()

	def getCCDCameraNames(self):
		objects = self.objectservice.getObjectsByType('CCDCamera')
		self.ccdcameras = {}
		for nodename, name in objects:
			string = '%s (%s)' % (name, nodename)
			proxy = self.objectservice.getObjectProxy(nodename, name)
			self.ccdcameras[string] = proxy
		return self.ccdcameras.keys()

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

	def getData(self, dataclass):
		if issubclass(dataclass, data.ScopeEMData):
			proxy = self.tem
		elif issubclass(dataclass, data.CameraEMData):
			proxy = self.ccdcamera
		elif issubclass(dataclass, data.CameraImageData):
			instance = dataclass()
			instance['scope'] = self.getData(data.ScopeEMData)
			instance['camera'] = self.getData(data.CameraEMData)
			return instance
		if proxy is None:
			raise ValueError('no proxy selected for this data class')
		instance = dataclass()
		keys = []
		attributes = []
		types = []
		for key, attribute in parametermapping:
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
	('magnification', 'Magnifiction'),
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

