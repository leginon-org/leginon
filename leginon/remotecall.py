# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/remotecall.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-17 00:39:56 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import inspect
import datatransport

class Request(object):
	def __init__(self, origin, node, name, attributename, type,
								args=(), kwargs={}):
		self.origin = origin
		self.node = node
		self.name = name
		self.attributename = attributename
		self.type = type
		self.args = args
		self.kwargs = kwargs

class Object(object):
	def __init__(self):
		self._register()

	def _query(self):
		members = inspect.getmembers(self, predicate=inspect.ismethod)
		interface = {}
		for name, method in members:
			if name[:1] == '_':
				pass
			elif name[:3] == 'get':
				key = name[3:]
				if not key:
					raise RuntimeError('Invalid attribute specification in interface')
				if key not in interface:
					interface[key] = {}
				interface[key]['r'] = method
			elif name[:3] == 'set':
				key = name[3:]
				if not key:
					raise RuntimeError('Invalid attribute specification in interface')
				if key not in interface:
					interface[key] = {}
				interface[key]['w'] = method
			else:
				if name not in interface:
					interface[name] = {}
				interface[name]['method'] = method
		return interface

	def _register(self):
		self._types = [c.__name__ for c in inspect.getmro(self.__class__)]
		self._interface = self._query()
		self._description = self._getDescription()

	def _execute(self, name, type, args=(), kwargs={}):
		try:
			result = self._interface[name][type](*args, **kwargs)
		except KeyError:
			result = TypeError('Invalid execution name')
		except Exception, result:
			pass
		return result

	def _getDescription(self):
		description = {}
		for name, methods in self._interface.items():
			description[name] = methods.keys()
		return description

class ObjectClientCall(object):
	def __init__(self, call, args):
		self.call = call
		self.args = args

	def __call__(self, *args, **kwargs):
		args = self.args + (args, kwargs)
		self.call(*args)

class ObjectClient(object):
	def __init__(self, objectservice, nodename, name):
		self.__objectservice = objectservice
		self.__nodename = nodename
		self.__name = name

	def __getattr__(self, name):
		d, t = self.__objectservice.descriptions[self.__nodename][self.__name]
		try:
			description = d[name]
		except KeyError:
			raise ValueError('No method %s in object description' % name)
		if 'method' in description:
			args = (self.__nodename, self.__name, name, 'method')
			return ObjectClientCall(self.__objectservice._call, args)
		elif 'r' in description:
			return self.__objectservice._call(self.__nodename, self.__name, name, 'r')
		else:
			raise TypeError('Attribute %s is not readable' % name)

class ObjectService(Object):
	def __init__(self, node):
		self.descriptions = {}
		self.clients = {}
		self.node = node
		Object.__init__(self)
		self._addObject('Object Service', self)

	def addDescription(self, nodename, name, description, types, location):
		if nodename not in self.clients:
			self.clients[nodename] = datatransport.Client(location,
																										self.node.clientlogger)
		if nodename not in self.descriptions:
			self.descriptions[nodename] = {}
		self.descriptions[nodename][name] = (description, types)

	def addDescriptions(self, descriptions):
		for description in descriptions:
			self.addDescription(*description)

	def _call(self, node, name, attributename, type, args=(), kwargs={}):
		request = Request(self.node.name, node, name, attributename, type,
											args, kwargs)
		try:
			return self.clients[node].send(request)
		except KeyError:
			raise ValueError('No client for node %s' % node)

	def _addObject(self, name, interface):
		self.node.databinder.addRemoteCallObject(self.node.name, name, interface)

	def _removeObject(self, name):
		self.node.databinder.addRemoteCallObject(self.node.name, name)

	def getObjectClient(self, nodename, name):
		return ObjectClient(self, nodename, name)

class NodeObjectService(ObjectService):
	def __init__(self, node):
		self.node = node
		ObjectService.__init__(self, node)

	def _addObject(self, name, interface):
		if 'Manager' not in self.clients:
			self.clients['Manager'] = self.node.managerclient
		ObjectService._addObject(self, name, interface)
		location = self.node.location()['data binder']
		args = (self.node.name, name, interface._description,
						interface._types, location)
		self._call('Manager', 'Object Service', 'addDescription', 'method', args)

class ManagerObjectService(ObjectService):
	def __init__(self, manager):
		ObjectService.__init__(self, manager)

	def addDescription(self, nodename, name, description, types, location):
		ObjectService.addDescription(self, nodename, name, description, types,
																	location)
		args = (nodename, name, description, types, location)
		descriptions = []
		for nn in self.descriptions:
			if nn == nodename:
				continue
			location = self.node.nodelocations[nodename]['location']
			#if location == self.node.nodelocations[nn]['location']
			#	location = 'local'
			for n in self.descriptions[nn]:
				d, t = self.descriptions[nn][n]
				if 'ObjectService' in t:
					self._call(nn, n, 'addDescription', 'method', args)
				descriptions.append((nn, n, d, t, location['data binder']))
		if descriptions and name == 'Object Service':
			args = (descriptions,)
			self._call(nodename, name, 'addDescriptions', 'method', args)

class Locker(Object):
	def lock(self):
		pass

	def unlock(self):
		pass

class TEM(Locker):
	def resetDefocus(self):
		pass

	def getMagnificationIndex(self):
		pass

	def setMagnificationIndex(self, index):
		pass

