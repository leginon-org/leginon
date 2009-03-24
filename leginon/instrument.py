# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/instrument.py,v $
# $Revision: 1.38 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-22 22:48:19 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import leginondata
import remotecall
import gui.wx.Events

class InstrumentError(Exception):
	pass

class NotAvailableError(InstrumentError):
	pass

class Proxy(object):
	def __init__(self, objectservice, session=None, wxeventhandler=None):
		self.tems = {}
		self.ccdcameras = {}
		self.imagecorrections = {}
		self.tem = None
		self.ccdcamera = None
		self.camerasize = None
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
			if self.wxeventhandler is not None:
				names = self.getTEMNames()
				evt = gui.wx.Events.SetTEMsEvent(self.wxeventhandler, names=names)
				self.wxeventhandler.GetEventHandler().AddPendingEvent(evt)
			if self.tem is None:
				self.setTEM(name)

		if 'CCDCamera' in types:
			proxy = self.objectservice.getObjectProxy(nodename, name)
			self.ccdcameras[name] = proxy
			self.camerasizes[name] = proxy.CameraSize
			if self.wxeventhandler is not None:
				names = self.getCCDCameraNames()
				evt = gui.wx.Events.SetCCDCamerasEvent(self.wxeventhandler, names=names)
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

	def getTEM(self, temname):
		try:
			return self.tems[temname]
		except KeyError:
			raise NotAvailableError('TEM \'%s\' not available' % temname)

	def getTEMName(self):
		if self.tem is None:
			return None
		return self.tem._name

	def getTEMNames(self):
		tems = self.tems.keys()
		tems.sort()
		return tems

	def getTEMData(self, name=None):
		if name is None:
			if self.tem is None:
				return None
			else:
				name = self.tem._name
				#dbtype = self.tem.DatabaseType
		else:
			if name not in self.tems:
				raise RuntimeError('no TEM \'%s\' available' % name)
		instrumentdata = leginondata.InstrumentData()
		instrumentdata['name'] = name
		#instrumentdata['type'] = dbtype
		#print dbtype
		try:
			instrumentdata['hostname'] = self.tems[name].Hostname
		except:
			raise RuntimeError('unable to get TEM hostname')
		return instrumentdata

	def getMagnifications(self, name=None):
		if name is None:
			if self.tem is None:
				return []
			else:
				name = self.tem._name
		else:
			if name not in self.tems:
				raise RuntimeError('no TEM \'%s\' available' % name)
		mags = self.tems[name].Magnifications
		return mags

	def getCCDCamera(self, ccdcameraname):
		try:
			return self.ccdcameras[ccdcameraname]
		except KeyError:
			raise NotAvailableError('CCD Camera \'%s\' not available' % ccdcameraname)

	def getCCDCameraName(self):
		if self.ccdcamera is None:
			return None
		return self.ccdcamera._name

	def getCCDCameraNames(self):
		ccdcameras = self.ccdcameras.keys()
		ccdcameras.sort()
		return ccdcameras

	def getCCDCameraData(self, name=None):
		if name is None:
			if self.ccdcamera is None:
				return None
			else:
				name = self.ccdcamera._name
				#dbtype = self.ccdcamera.DatabaseType
		else:
			if name not in self.ccdcameras:
				raise RuntimeError('no CCD camera \'%s\' available' % name)
		instrumentdata = leginondata.InstrumentData()
		instrumentdata['name'] = name
		#instrumentdata['type'] = dbtype
		#print dbtype
		try:
			instrumentdata['hostname'] = self.ccdcameras[name].Hostname
		except:
			raise RuntimeError('unable to get TEM hostname')
		return instrumentdata

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
				raise NotAvailableError('TEM \'%s\' not available' % name)
		if self.wxeventhandler is not None:
			evt = gui.wx.Events.SetTEMEvent(self.wxeventhandler, name=name)
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
				raise NotAvailableError('CCD camera \'%s\' not available' % name)
		if self.wxeventhandler is not None:
			evt = gui.wx.Events.SetCCDCameraEvent(self.wxeventhandler, name=name)
			self.wxeventhandler.GetEventHandler().AddPendingEvent(evt)

	def setImageCorrection(self, name):
		if name is None:
			self.imagecorrection = None
		else:
			self.imagecorrection = self.imagecorrections[name]

	def getTEMParameter(self, temname, name):
		for parameter, attr_name in parametermapping:
			if parameter == name:
				return getattr(self.tems[temname], attr_name)
		raise ValueError

	def getCCDCameraParameter(self, ccdcameraname, name):
		for parameter, attr_name in parametermapping:
			if parameter == name:
				return getattr(self.ccdcameras[ccdcameraname], attr_name)
		raise ValueError

	def getData(self, dataclass, image=True, temname=None, ccdcameraname=None):
		if issubclass(dataclass, leginondata.ScopeEMData):
			if temname is None:
				proxy = self.tem
			else:
				try:
					proxy = self.tems[temname]
				except KeyError:
					raise NotAvailableError('TEM \'%s\' not available' % temname)
		elif issubclass(dataclass, leginondata.CameraEMData):
			if ccdcameraname is None:
				proxy = self.ccdcamera
			else:
				try:
					proxy = self.ccdcameras[ccdcameraname]
				except KeyError:
					raise NotAvailableError('CCD Camera \'%s\' not available' % ccdcameraname)
		elif issubclass(dataclass, leginondata.CorrectedCameraImageData):
			if self.imagecorrection is None:
				raise RuntimeError('no image correction set')
			return self.imagecorrection.getImageData(self.getCCDCameraName())
		elif issubclass(dataclass, leginondata.CameraImageData):
			instance = dataclass()
			instance['scope'] = self.getData(leginondata.ScopeEMData, temname=temname)
			instance['camera'] = self.getData(leginondata.CameraEMData, image=image,
																					ccdcameraname=ccdcameraname)
			if image:
				instance['image'] = instance['camera']['image data']
				instance['camera']['image data'] = None
			instance['session'] = self.session
			return instance
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
		results = proxy.multiCall(attributes, types)
		for i, key in enumerate(keys):
			try:
				if isinstance(results[i], Exception):
					raise results[i]
			except AttributeError:
				continue
			instance[key] = results[i]
		if 'session' in instance:
			instance['session'] = self.session
		if 'tem' in instance:
			instance['tem'] = self.getTEMData(name=temname)
		if 'ccdcamera' in instance:
			instance['ccdcamera'] = self.getCCDCameraData(name=ccdcameraname)
		return instance

	def setData(self, instance, temname=None, ccdcameraname=None):
		if isinstance(instance, leginondata.ScopeEMData):
			if temname is None:
				proxy = self.tem
			else:
				try:
					proxy = self.tems[temname]
				except KeyError:
					raise NotAvailableError('TEM \'%s\' not available' % temname)
		elif isinstance(instance, leginondata.CameraEMData):
			if ccdcameraname is None:
				proxy = self.ccdcamera
			else:
				try:
					proxy = self.ccdcameras[ccdcameraname]
				except KeyError:
					raise NotAvailableError('CCD Camera \'%s\' not available' % ccdcameraname)
		elif isinstance(instance, leginondata.CameraImageData):
			instance = dataclass()
			self.setData(instance['scope'], temname=temname)
			self.setData(instance['camera'], ccdcameraname=ccdcameraname)
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
		results = proxy.multiCall(attributes, types, args)
		for result in results:
			try:
				if isinstance(result, Exception):
					raise result
			except AttributeError:
				pass

	def setCorrectionChannel(self, channel, imagecorrection=None):
		if imagecorrection is None:
			proxy = self.imagecorrection
		else:
			try:
				proxy = self.imagecorrections[imagecorrection]
			except KeyError:
				raise NotAvailableError('Image correction \'%s\' not available' % (imagecorrection,))
		proxy.setChannel(channel)	

class TEM(remotecall.Locker):
	def getDatabaseType(self):
		return 'TEM'

class CCDCamera(remotecall.Locker):
	def getDatabaseType(self):
		return 'CCDCamera'

class FastCCDCamera(CCDCamera):
	pass

parametermapping = (
	# ScopeEM
	('system time', 'SystemTime'),
	('magnification', 'Magnification'),
	('spot size', 'SpotSize'),
	('image shift', 'ImageShift'),
	('beam shift', 'BeamShift'),
	('focus', 'Focus'),
	('defocus', 'Defocus'),
	('reset defocus', 'resetDefocus'),
	('intensity', 'Intensity'),
	('screen current', 'ScreenCurrent'),
	('stigmator', 'Stigmator'),
	('beam tilt', 'BeamTilt'),
	('corrected stage position', 'CorrectedStagePosition'),
	('stage position', 'StagePosition'),
	('column pressure', 'ColumnPressure'),
	('high tension', 'HighTension'),
	('main screen position', 'MainScreenPosition'),
	('main screen magnification', 'MainScreenMagnification'),
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
	('objective current', 'ObjectiveCurrent'),
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
	#('column valves', 'ColumnValvePosition'),

	# CameraEM
	('dimension', 'Dimension'),
	('binning', 'Binning'),
	('offset', 'Offset'),
	('exposure time', 'ExposureTime'),
	('exposure type', 'ExposureType'),
	('image data', 'Image'),
	('inserted', 'Inserted'),
	('pixel size', 'PixelSize'),
	('energy filtered', 'EnergyFiltered'),
	('energy filter', 'EnergyFilter'),
	('energy filter width', 'EnergyFilterWidth'),
	#('readout callback', 'ReadoutCallback'),
)

