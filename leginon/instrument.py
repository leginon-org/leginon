# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/instrument.py,v $
# $Revision: 1.5 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-23 19:44:25 $
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
		if proxy is None:
			raise ValueError('No proxy selected for this data class')
		instance = dataclass()
		parameters = []
		for key, attribute in parametermapping:
			if key in instance and proxy.hasattr(attribute):
				parameters.append((key, attribute))
		names = [p[1] for p in parameters]
		types = ['get']*len(names)
		result = proxy.multiCall(names, types)
		for i, key in enumerate(parameters):
			instance[key] = result[i]
		return instance

class TEM(remotecall.Locker):
	pass

class CCDCamera(remotecall.Locker):
	pass

parametermapping = (
  ('magnification', 'Magnifiction'),
  ('magnifications', 'Magnifications'),
  ('spot size', 'SpotSize'),
  ('intensity', 'Intensity'),
  ('image shift', 'ImageShift'),
  ('beam shift', 'BeamShift'),
  ('defocus', 'Defocus'),
  ('focus', 'Focus'),
  #('reset defocus', 'resetDefocus'),
  ('screen current', 'ScreenCurrent'),
  ('beam blank', 'BeamBlank'),
  ('stigmator', 'Stigmator'),
  ('beam tilt', 'BeamTilt'),
  ('corrected stage position', 'CorrectedStagePosition'),
  ('stage position', 'StagePosition'),
  ('holder type', 'HolderType'),
  ('holder status', 'HolderStatus'),
  ('stage status', 'StageStatus'),
  ('vacuum status', 'VacuumStatus'),
  ('column valves', 'ColumnValves'),
  ('column pressure', 'ColumnPressure'),
  ('turbo pump', 'TurboPump'),
  ('high tension', 'HighTension'),
  ('main screen position', 'MainScreenPosition'),
  ('small screen position', 'SmallScreenPosition'),
  ('low dose', 'LowDose'),
  ('low dose mode', 'LowDoseMode'),
  ('film stock', 'FilmStock'),
  ('film exposure number', 'FilmExposureNumber'),
  #('pre film exposure', 'preFilmExposure'),
  #('post film exposure', 'postFilmExposure'),
  #('film exposure', 'filmExposure'),
  ('film exposure type', 'FilmExposureType'),
  ('film exposure time', 'FilmExposureTime'),
  ('film manual exposure time', 'FilmManualExposureTime'),
  ('film automatic exposure time', 'FilmAutomaticExposureTime'),
  ('film text', 'FilmText'),
  ('film user code', 'FilmUserCode'),
  ('film date type', 'FilmDateType'),
)

