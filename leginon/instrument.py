# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/instrument.py,v $
# $Revision: 1.1 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-18 18:50:17 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import remotecall

class Proxy(object):
	def __init__(self, objectservice):
		self.objectservice = objectservice
		self.tems = {}
		self.ccdcameras = {}
		self.tem = None
		self.ccdcamera = None

	def getTEMNames(self):
		objects = self.objectservice.getObjectsByType(remotecall.TEM)
		for nodename, name in objects:
			string = '%s (%s)' % (name, nodename)
			proxy = self.objectservice.getObjectProxy(nodename, name)
			self.tems[string] = proxy
		return self.tems.keys()

	def getCCDCameraNames(self):
		objects = self.objectservice.getObjectsByType(remotecall.CCDCamera)
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

