# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/instrument.py,v $
# $Revision: 1.3 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-23 01:00:32 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

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
			self.ccdcamera = self.tems[name]

