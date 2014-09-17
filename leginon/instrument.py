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

from leginon import leginondata
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
		self.tem = None
		self.ccdcamera = None
		self.camerasize = None
		self.camerasizes = {}
		self.camerabinnings = [1]
		self.allcamerabinnings = {}
		self.camerabinmethod = None
		self.camerabinmethods = {}
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
			self.allcamerabinnings[name] = proxy.CameraBinnings
			self.camerabinmethods[name] = proxy.CameraBinMethod
			if self.wxeventhandler is not None:
				names = self.getCCDCameraNames()
				evt = gui.wx.Events.SetCCDCamerasEvent(self.wxeventhandler, names=names)
				self.wxeventhandler.GetEventHandler().AddPendingEvent(evt)
			if self.ccdcamera is None:
				self.setCCDCamera(name)

	def onRemoveDescription(self, nodename, name):
		if name in self.tems and self.tem is self.tems[name]:
			self.setTEM(None)
			del self.tems[name]

		if name in self.ccdcameras and self.ccdcamera is self.ccdcameras[name]:
			self.setCCDCamera(None)
			del self.ccdcameras[name]
		try:
			del self.camerasizes[name]
			del self.allcamerabinnings[name]
			del self.camerabinmethods[name]
		except KeyError:
			pass

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
				cs = self.tem.Cs
				#dbtype = self.tem.DatabaseType
		else:
			if name not in self.tems:
				raise RuntimeError('no TEM \'%s\' available' % name)
			else:
				cs = None
		instrumentdata = leginondata.InstrumentData()
		instrumentdata['name'] = name
		#instrumentdata['type'] = dbtype
		#print dbtype
		try:
			instrumentdata['hostname'] = self.tems[name].Hostname
		except:
			raise RuntimeError('unable to get TEM hostname')
		results = instrumentdata.query(results=1)
		## save in DB if not already there
		if results:
			dbinstrumentdata = results[0]
			if dbinstrumentdata['cs'] is None:
				raise RuntimeError('You must run db schema update script on existing TEMs before using this version of Leginon')
			elif cs is not None and dbinstrumentdata['cs'] != cs:
				raise RuntimeError('TEM Cs in instruments.cfg does not match database value. Correct either one to use it in Leginon')
		else:
			if cs is None:
				cs = 2.0e-3
			instrumentdata['cs'] = cs
			dbinstrumentdata = instrumentdata
			dbinstrumentdata.insert()
		return dbinstrumentdata

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
			raise RuntimeError('unable to get Camera hostname')
		results = instrumentdata.query(results=1)
		## save in DB if not already there
		if results:
			dbinstrumentdata = results[0]
		else:
			dbinstrumentdata = instrumentdata
			dbinstrumentdata.insert()
		return dbinstrumentdata

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
			self.camerabinnings = [1]
			self.camerabinmethod = 'exact'
		else:
			try:
				self.ccdcamera = self.ccdcameras[name]
				self.camerasize = self.camerasizes[name]
				self.camerabinnings = self.allcamerabinnings[name]
				self.camerabinmethod = self.camerabinmethods[name]
			except KeyError:
				raise NotAvailableError('CCD camera \'%s\' not available' % name)
		if self.wxeventhandler is not None:
			evt = gui.wx.Events.SetCCDCameraEvent(self.wxeventhandler, name=name)
			self.wxeventhandler.GetEventHandler().AddPendingEvent(evt)

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

	def getData(self, dataclass, temname=None, ccdcameraname=None):
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
		results = proxy.multiCall(attributes, types)
		for i, key in enumerate(keys):
			try:
				if isinstance(results[i], Exception):
					# avoid exception for now on TSRI Krios
					if temname == 'Krios':
						continue
					continue
					#raise results[i]
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

class TEM(remotecall.Locker):
	def getDatabaseType(self):
		return 'TEM'

class CCDCamera(remotecall.Locker):
	def getDatabaseType(self):
		return 'CCDCamera'

parametermapping = (
	# ScopeEM
	# The order should base on dependency
	('system time', 'SystemTime'),
	('probe mode','ProbeMode'),
	('magnification', 'Magnification'),
	('spot size', 'SpotSize'),
	('intensity', 'Intensity'),
	('beam shift', 'BeamShift'),
	('image shift', 'ImageShift'),
	('focus', 'Focus'),
	('defocus', 'Defocus'),
	('reset defocus', 'resetDefocus'),
	('screen current', 'ScreenCurrent'),
	('stigmator', 'Stigmator'),
	('beam tilt', 'BeamTilt'),
	('stage speed', 'StageSpeed'),
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
	('exp wait time', 'ExpWaitTime'),
	('tem energy filtered', 'EnergyFiltered'),
	('tem energy filter', 'EnergyFilter'),
	('tem energy filter width', 'EnergyFilterWidth'),
	('aperture size', 'ApertureSize'),
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
	('exposure timestamp', 'ExposureTimestamp'),
	('inserted', 'Inserted'),
	('pixel size', 'PixelSize'),
	('energy filtered', 'EnergyFiltered'),
	('energy filter', 'EnergyFilter'),
	('energy filter width', 'EnergyFilterWidth'),
	('nframes', 'NumberOfFrames'),
	('align frames', 'AlignFrames'),
	('align filter', 'AlignFilter'),
	('save frames', 'SaveRawFrames'),
	('frames name', 'PreviousRawFramesName'),
	('use frames', 'UseFrames'),
	('frame time', 'FrameTime'),
	('frame flip', 'FrameFlip'),
	('frame rotate', 'FrameRotate'),
	('readout delay', 'ReadoutDelay'),
	('temperature', 'Temperature'),
	('temperature status', 'TemperatureStatus'),
	('binned multiplier', 'BinnedMultiplier'),
	('gain index', 'GainIndex'),
	('system corrected', 'SystemGainDarkCorrected'),
)

