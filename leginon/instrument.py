# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/instrument.py,v $
# $Revision: 1.21 $
# $Name: not supported by cvs2svn $
# $Date: 2005-03-01 01:33:28 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import data
import remotecall
import gui.wx.Events

class Proxy(object):
	def __init__(self, objectservice, session=None, wxeventhandler=None):
		self.tems = {}
		self.ccdcameras = {}
		self.imagecorrections = {}
		self.tem = None
		self.ccdcamera = None
		self.camerasize = None
		self.magnifications = {}
		self.camerasizes = {}
		self.imagecorrection = None
		self.session = session
		self.wxeventhandler = wxeventhandler
		self.objectservice = objectservice
		self.objectservice._addDescriptionHandler(add=self.onAddDescription,
																							remove=self.onRemoveDescription)

	def onAddDescription(self, nodename, name, description, types):
		if 'TEM' in types:
			proxy = self.objectservice.getObjectProxy(nodename, name)
			self.tems[name] = proxy
			self.magnifications[name] = proxy.Magnifications
			if self.wxeventhandler is not None:
				names = self.getTEMNames()
				evt = gui.wx.Events.SetTEMsEvent(self.wxeventhandler, names)
				self.wxeventhandler.GetEventHandler().AddPendingEvent(evt)
			if self.tem is None:
				self.setTEM(name)

		if 'CCDCamera' in types:
			proxy = self.objectservice.getObjectProxy(nodename, name)
			self.ccdcameras[name] = proxy
			self.camerasizes[name] = proxy.CameraSize
			if self.wxeventhandler is not None:
				names = self.getCCDCameraNames()
				evt = gui.wx.Events.SetCCDCamerasEvent(self.wxeventhandler, names)
				self.wxeventhandler.GetEventHandler().AddPendingEvent(evt)
			if self.ccdcamera is None:
				self.setCCDCamera(name)

		if 'ImageCorrection' in types:
			proxy = self.objectservice.getObjectProxy(nodename, name)
			self.imagecorrections[name] = proxy
			if self.imagecorrection is None:
				self.setImageCorrection(name)

	def onRemoveDescription(self, nodename, name):
		if name in self.tems and self.tem is self.tems[name]:
			self.setTEM(None)
			del self.tems[name]
		try:
			del self.magnifications[name]
		except KeyError:
			pass

		if name in self.ccdcameras and self.ccdcamera is self.ccdcameras[name]:
			self.setCCDCamera(None)
			del self.ccdcameras[name]
		try:
			del self.camerasizes[name]
		except KeyError:
			pass

		if name in self.imagecorrections:
			if self.imagecorrection is self.imagecorrections[name]:
				self.setImageCorrection(None)

	def getTEMName(self):
		if self.tem is None:
			return None
		return self.tem._name

	def getTEMNames(self):
		tems = self.tems.keys()
		tems.sort()
		return tems

	def getCCDCameraName(self):
		if self.ccdcamera is None:
			return None
		return self.ccdcamera._name

	def getCCDCameraNames(self):
		ccdcameras = self.ccdcameras.keys()
		ccdcameras.sort()
		return ccdcameras

	def getImageCorrectionName(self):
		if self.imagecorrection is None:
			return None
		return self.imagecorrection._name

	def getImageCorrectionNames(self):
		ics = self.imagecorrections.keys()
		ics.sort()
		return ics

	def setTEM(self, name):
		if name is None:
			self.tem = None
		else:
			try:
				self.tem = self.tems[name]
			except KeyError:
				raise ValueError('TEM \'%s\' not available' % name)
		if self.wxeventhandler is not None:
			evt = gui.wx.Events.SetTEMEvent(self.wxeventhandler, name)
			self.wxeventhandler.GetEventHandler().AddPendingEvent(evt)

	def setCCDCamera(self, name):
		if name is None:
			self.ccdcamera = None
			self.camerasize = None
		else:
			try:
				self.ccdcamera = self.ccdcameras[name]
				self.camerasize = self.camerasizes[name]
			except KeyError:
				raise ValueError('CCD camera \'%s\' not available' % name)
		if self.wxeventhandler is not None:
			evt = gui.wx.Events.SetCCDCameraEvent(self.wxeventhandler, name)
			self.wxeventhandler.GetEventHandler().AddPendingEvent(evt)

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
			return self.imagecorrection.getImageData(self.getCCDCameraName())
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
		if 'session' in instance:
			instance['session'] = self.session
		if 'tem' in instance:
			instance['tem'] = self.getTEMName()
		if 'ccdcamera' in instance:
			instance['ccdcamera'] = self.getCCDCameraName()
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
	('pixel size', 'PixelSize'),
)

