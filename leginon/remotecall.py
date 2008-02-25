# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/remotecall.py,v $
# $Revision: 1.24 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-25 22:24:15 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import inspect
import datatransport
import types
import threading

class LockingError(Exception):
	pass

class LockError(LockingError):
	pass

class UnlockError(LockingError):
	pass

class NotLockedError(LockingError):
	pass

class TimeoutError(LockingError):
	pass

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

class MultiRequest(Request):
	def __init__(self, origin, node, name, attributenames, types,
								args=None, kwargs=None):
		n = len(attributenames)
		if len(types) != n:
			raise ValueError
		if args is None:
			args = [()]*len(attributenames)
		if kwargs is None:
			kwargs = [{}]*len(attributenames)
		if len(args) != n or len(kwargs) != n:
			raise ValueError
		Request.__init__(self, origin, node, name, attributenames, types,
											args, kwargs)

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
		self._types = [c.__name__ for c in inspect.getmro(self.__class__)]
		self._interface = self._query()
		self._description = self._getDescription()

	def _execute(self, origin, name, type, args=(), kwargs={}):
		if name not in self._interface:
			result = TypeError('invalid execution name \'%s\'' % (name,))
		elif type not in self._interface[name]:
			result = TypeError('invalid execution type for name \'%s\' (%s)' % (name, type))
		else:
			try:
				result = self._interface[name][type](*args, **kwargs)
			except Exception, result:
				#import sys
				#excinfo = sys.exc_info()
				#sys.excepthook(*excinfo)
				pass
		return result

	def _getDescription(self):
		description = {}
		for name, methods in self._interface.items():
			description[name] = {}
			for method in methods:
				description[name][method] = True
		return description

	def handleMultiRequest(self, request):
		results = []
		usemulticall = 'multicall' in self._interface
		if usemulticall:
			calls = []
		for i, attributename in enumerate(request.attributename):
			type = request.type[i]
			args = request.args[i]
			kwargs = request.kwargs[i]
			if usemulticall:
				### NEW WAY
				method = self._interface[attributename][type]
				calls.append({'method':method, 'args':args, 'kwargs':kwargs})
			else:
				### OLD WAY
				try:
					results.append(self._execute(request.origin, attributename, request.type[i], request.args[i], request.kwargs[i]))
				except Exception, e:
					results.append(e)
		if usemulticall:
			results = self._interface['multicall']['method'](calls)
		return results

	def _handleRequest(self, request):
		if isinstance(request, MultiRequest):
			results = self.handleMultiRequest(request)
			return results
		else:
			return self._execute(request.origin,
														request.attributename,
														request.type,
														request.args,
														request.kwargs)

class Locker(Object):
	def __init__(self):
		self.locknode = None
		self._lock = threading.Condition()
		Object.__init__(self)

	def _execute(self, origin, name, type, args=(), kwargs={}):
		# handle lock and unlock directly
		self._lock.acquire()
		haslock = self.locknode == origin
		if not haslock:
			if self.locknode is not None:
				self._lock.wait()
			self.locknode = origin
		if name in ['lock', 'unlock']:
			result = None
		else:
			result = Object._execute(self, origin, name, type, args, kwargs)
		if (not haslock and name != 'lock') or (haslock and name == 'unlock'):
			self.locknode = None
			self._lock.notify()
		self._lock.release()
		return result

	def lock(self, name):
		self._lock.acquire()
		if self.locknode != name:
			if self.locknode is not None:
				self._lock.wait()
			self.locknode = name
		self._lock.release()

	def unlock(self, name):
		self._lock.acquire()
		if self.locknode != name:
			self._lock.release()
			raise UnlockError
		else:
			self.locknode = None
		self._lock.notify()
		self._lock.release()

class ObjectCallProxy(object):
	def __init__(self, call, args):
		self.call = call
		self.args = args

	def __call__(self, *args, **kwargs):
		args = self.args + (args, kwargs)
		return self.call(*args)

class ObjectProxy(object):
	def __init__(self, objectservice, nodename, name):
		# to avoid using __setattr__ below, use base class methods
		object.__setattr__(self, '_nodename', nodename)
		object.__setattr__(self, '_name', name)
		object.__setattr__(self, '_objectservice', objectservice)

	def __getattr__(self, name):
		d, t = self._objectservice.descriptions[self._nodename][self._name]
		try:
			description = d[name]
		except KeyError:
			raise AttributeError('attribute %s not in descripition' % name)
		if 'method' in description:
			args = (self._nodename, self._name, name, 'method')
			return ObjectCallProxy(self._objectservice._call, args)
		elif 'r' in description:
			return self._objectservice._call(self._nodename, self._name, name, 'r')
		else:
			raise TypeError('attribute %s is not readable' % name)

	def __setattr__(self, name, value):
		try:
			d, t = self._objectservice.descriptions[self._nodename][self._name]
		except KeyError:
			raise RuntimeError('object %s not in objectservice' % self._name)
		try:
			description = d[name]
		except KeyError:
			raise AttributeError('attribute %s not in descripition' % name)
		if 'w' in description:
			args = (self._nodename, self._name, name, 'w', (value,))
			return self._objectservice._call(*args)
		else:
			raise TypeError('attribute %s is not writeable' % name)

	def hasAttribute(self, name):
		d, t = self._objectservice.descriptions[self._nodename][self._name]
		if name in d:
			return True
		return False

	def getAttributeTypes(self, name):
		d, t = self._objectservice.descriptions[self._nodename][self._name]
		try:
			return d[name].keys()
		except KeyError:
			return []

	def multiCall(self, names, types, args=None, kwargs=None):
		args = (self._nodename, self._name, names, types, args, kwargs)
		return self._objectservice._multiCall(*args)

#class ObjectService(Object):
class ObjectService(Locker):
	def __init__(self, node):
		self.descriptions = {}
		self.clients = {}
		self.node = node
		self.addhandlers = []
		self.removehandlers = []
		#Object.__init__(self)
		Locker.__init__(self)
		self._addObject('Object Service', self)

	def _addDescriptionHandler(self, add=None, remove=None):
		self.lock(self.node.name)
		if add is not None:
			self.addhandlers.append(add)
			for args in self._getDescriptions():
				add(*args)
		if remove is not None:
			self.removehandlers.append(remove)
		self.unlock(self.node.name)

	def _removeDescriptionHandler(self, add=None, remove=None):
		self.lock(self.node.name)
		if add is not None:
			self.addhandlers.remove(add)
		if remove is not None:
			self.removehandlers.remove(remove)
		self.unlock(self.node.name)

	def _addHandler(self, nodename, name, description, types):
		for handler in self.addhandlers:
			handler(nodename, name, description, types)

	def _removeHandler(self, nodename, name):
		for handler in self.removehandlers:
			handler(nodename, name)

	def _getDescriptions(self):
		args = []
		for nodename in self.descriptions:
			for name in self.descriptions[nodename]:
				args.append((nodename, name) + self.descriptions[nodename][name])
		return args

	def addDescription(self, nodename, name, description, types, location):
		if (nodename not in self.clients or
				self.clients[nodename].serverlocation != location):
			self.clients[nodename] = datatransport.Client(location,
																										self.node.clientlogger)

		if nodename not in self.descriptions:
			self.descriptions[nodename] = {}
		self.descriptions[nodename][name] = (description, types)
		self._addHandler(nodename, name, description, types)

	def removeDescription(self, nodename, name):
		self._removeDescription(self, nodename, name)

	def _removeDescription(self, nodename, name):
		try:
			del self.descriptions[nodename][name]
			if not self.descriptions[nodename]:
				del self.descriptions[nodename]
			self._removeHandler(nodename, name)
		except KeyError:
			pass

	def addDescriptions(self, descriptions):
		for description in descriptions:
			self.addDescription(*description)

	def removeDescriptions(self, descriptions):
		for description in descriptions:
			self.removeDescription(*description)
		
	def _removeDescriptions(self, descriptions):
		for description in descriptions:
			self._removeDescription(*description)

	def removeNode(self, nodename):
		try:
			descriptions = []
			for name in self.descriptions[nodename]:
				descriptions.append((nodename, name))
			self._removeDescriptions(descriptions)
		except KeyError:
			pass
		try:
			del self.clients[nodename]
		except KeyError:
			pass

	def _call(self, node, name, attributename, type, args=(), kwargs={}):
		request = Request(self.node.name, node, name, attributename, type,
											args, kwargs)
		if node not in self.clients:
			raise ValueError('no client for node %s' % node)
		return self.clients[node].send(request)

	def _multiCall(self, node, name, attributenames, types,
									args=None, kwargs=None):
		request = MultiRequest(self.node.name, node, name, attributenames, types,
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
		try:
			self._call('Manager', 'Object Service', 'removeNode', 'method', args)
		except datatransport.TransportError:
			pass

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
			try:
				location = self.node.nodelocations[nn]['location']
			except KeyError:
				raise RuntimeError('cannot get location of \'%s\'' % (nn,))
			for n in self.descriptions[nn]:
				d, t = self.descriptions[nn][n]
				if 'ObjectService' in t:
					if 'ObjectService' not in types:
						self._call(nn, n, 'addDescription', 'method', args)
				else:
					descriptions.append((nn, n, d, t, location['data binder']))
		if descriptions and 'ObjectService' in types:
			self._call(nodename, name, 'addDescriptions', 'method', (descriptions,))

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
		args = (nodename,)
		for nn in self.descriptions:
			if nn == nodename:
				continue
			for n in self.descriptions[nn]:
				d, t = self.descriptions[nn][n]
				if 'ObjectService' in t:
					self._call(nn, n, 'removeNode', 'method', args)
		ObjectService.removeNode(self, nodename)

