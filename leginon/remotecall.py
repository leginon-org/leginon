# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/remotecall.py,v $
# $Revision: 1.5 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-18 18:50:17 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import inspect
import datatransport
import types

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
		interface = {}
		for key in dir(self):
			try:
				value = getattr(self, key)
			except Exception, e:
				continue
			if isinstance(value, types.MethodType):
				if key[:1] != '_':
					if key[:3] == 'get':
						name = key[3:]
						if name:
							if name not in interface:
								interface[name] = {}
							interface[name]['r'] = value
					elif key[:3] == 'set':
						name = key[3:]
						if name:
							if name not in interface:
								interface[name] = {}
							interface[name]['w'] = value
					if key not in interface:
						interface[key] = {}
					interface[key]['method'] = value
		return interface

	def _register(self):
		self._types = inspect.getmro(self.__class__)
		self._interface = self._query()
		self._description = self._getDescription()

	def _execute(self, name, type, args=(), kwargs={}):
		try:
			result = self._interface[name][type](*args, **kwargs)
		except KeyError:
			result = TypeError('invalid execution name')
		except Exception, result:
			pass
		return result

	def _getDescription(self):
		description = {}
		for name, methods in self._interface.items():
			description[name] = {}
			for method in methods:
				description[name][method] = True
		return description

class ObjectCallProxy(object):
	def __init__(self, call, args):
		self.call = call
		self.args = args

	def __call__(self, *args, **kwargs):
		args = self.args + (args, kwargs)
		self.call(*args)

class ObjectProxy(object):
	def __init__(self, objectservice, nodename, name):
		self.__objectservice = objectservice
		self.__nodename = nodename
		self.__name = name

	def __getattr__(self, name):
		d, t = self.__objectservice.descriptions[self.__nodename][self.__name]
		try:
			description = d[name]
		except KeyError:
			raise ValueError('no method %s in object description' % name)
		if 'method' in description:
			args = (self.__nodename, self.__name, name, 'method')
			return ObjectCallProxy(self.__objectservice._call, args)
		elif 'r' in description:
			return self.__objectservice._call(self.__nodename, self.__name, name, 'r')
		else:
			raise TypeError('attribute %s is not readable' % name)

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

	def removeDescription(self, nodename, name):
		try:
			del self.descriptions[nodename][name]
		except KeyError:
			pass

	def addDescriptions(self, descriptions):
		for description in descriptions:
			self.addDescription(*description)

	def removeDescriptions(self, descriptions):
		for description in descriptions:
			self.removeDescription(*description)

	def _call(self, node, name, attributename, type, args=(), kwargs={}):
		request = Request(self.node.name, node, name, attributename, type,
											args, kwargs)
		try:
			return self.clients[node].send(request)
		except KeyError:
			raise ValueError('no client for node %s' % node)

	def _addObject(self, name, interface):
		self.node.databinder.addRemoteCallObject(self.node.name, name, interface)

	def _removeObject(self, name):
		self.node.databinder.removeRemoteCallObject(self.node.name, name)

	def getObjectProxy(self, nodename, name):
		return ObjectProxy(self, nodename, name)

	def getObjectsByType(self, type):
		objects = []
		for nodename in self.descriptions:
			for name in self.descriptions[nodename]:
				description, types = self.descriptions[nodename][name]
				if type in types:
					objects.append((nodename, name))
		return objects

	def _exit(self):
		pass

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

	def _removeObject(self, name):
		args = (self.node.name, name)
		self._call('Manager', 'Object Service', 'removeDescription', 'method', args)
		ObjectService._removeObject(self, name)

	def _exit(self):
		args = (self.node.name,)
		self._call('Manager', 'Object Service', 'removeNode', 'method', args)

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
			for n in self.descriptions[nn]:
				d, t = self.descriptions[nn][n]
				if 'ObjectService' in t:
					self._call(nn, n, 'addDescription', 'method', args)
				descriptions.append((nn, n, d, t, location['data binder']))
		if descriptions and name == 'Object Service':
			args = (descriptions,)
			self._call(nodename, name, 'addDescriptions', 'method', args)

	def removeDescription(self, nodename, name):
		args = (nodename, name)
		for nn in self.descriptions:
			if nn == nodename:
				continue
			for n in self.descriptions[nn]:
				d, t = self.descriptions[nn][n]
				if 'ObjectService' in t:
					self._call(nn, n, 'removeDescription', 'method', args)
		ObjectService.removeDescription(self, nodename, name)

	def removeNode(self, nodename):
		names = self.descriptions[nodename].keys()
		descriptions = zip([nodename]*len(names), names)
		args = (descriptions,)
		for nn in self.descriptions:
			if nn == nodename:
				continue
			for n in self.descriptions[nn]:
				d, t = self.descriptions[nn][n]
				if 'ObjectService' in t:
					self._call(nn, n, 'removeDescriptions', 'method', args)

class Locker(Object):
	def lock(self):
		pass

	def unlock(self):
		pass

class TEM(Locker):
	pass

class CCDCamera(Locker):
	pass

