#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

class MethodDictMixin(object):
	def _getMethods(self, key):
		try:
			return self.methodmapping[key]
		except (KeyError, AttributeError):
			raise KeyError(key)

	def _getMethodName(self, key, methodtype):
		methods = self._getMethods(key)
		try:
			return methods[methodtype]
		except KeyError:
			raise AttributeError('"%s" does not has method "%s"' % (key, methodtype))

	def _hasMethodType(self, key, methodtype):
		try:
			self._getMethodName(key, methodtype)
		except AttributeError:
			return False
		else:
			return True

	def getPermissions(self, key):
		try:
			return self._getMethodName(key, 'permissions')
		except AttributeError:
			return 'rw'

	def setPermissions(self, key, permissions):
		methods = self._getMethods(key)
		if permissions is None and 'permissions' in methods:
			del methods['permissions']
		else:
			methods['permissions'] = permissions

	def readable(self, key):
		return self._hasMethodType(key, 'get') and 'r' in self.getPermissions(key)

	def writable(self, key):
		return self._hasMethodType(key, 'set') and 'w' in self.getPermissions(key)

	def __getitem__(self, key):
		if self.readable(key):
			return getattr(self, self._getMethodName(key, 'get'))()
		else:
			raise AttributeError('"%s" is not readable' % key)

	def __setitem__(self, key, value):
		if self.writable(key):
			return getattr(self, self._getMethodName(key, 'set'))(value)
		else:
			raise AttributeError('"%s" is not writable' % key)
		
	def readkeys(self):
		keys = []
		try:
			for key in self.methodmapping.keys():
				if self.readable(key):
					keys.append(key)
		except AttributeError:
			pass
		return keys

	def writekeys(self):
		keys = []
		try:
			for key in self.methodmapping.keys():
				if self.writable(key):
					keys.append(key)
		except AttributeError:
			pass
		return keys

	def readwritekeys(self):
		keys = []
		try:
			for key in self.methodmapping.keys():
				if self.readable(key) and self.writable(key):
					keys.append(key)
		except AttributeError:
			pass
		return keys

	def keys(self):
		return self.readkeys()

	def values(self):
		return map(lambda key: self.__getitem__(key), self.keys())

	def items(self):
		return map(lambda key: (key, self.__getitem__(key)), self.keys())

	def iterkeys(self):
		return iter(self.keys())

	def itervalues(self):
		return iter(self.values())

	def iteritems(self):
		return iter(self.items())

	def update(self, dict):
		map(lambda item: apply(self.__setitem__, item), dict.items())

	def has_key(self, key):
		if key in self.keys():
			return True
		return False

	def __contains__(self, key):
		return self.has_key(key)

	def __len__(self):
		return len(self.keys())

	def copy(self):
		copy = {}
		for key, value in self.items():
			copy[key] = value
		return copy

	def __iter__(self):
		return iter(self.copy())

	def __repr__(self):
		return repr(self.copy())

	def __cmp__(self, dict):
		raise AttributeError('__cmp__ not supported by method dict')

	def __delitem__(self, key):
		raise AttributeError('__delitem__ not supported by method dict')

	def clear(self):
		raise AttributeError('clear not supported by method dict')

	def fromkeys(self, seq, value=None):
		raise AttributeError('fromkeys not supported by method dict')

	def get(self, key, failobj=None):
		raise AttributeError('get not supported by method dict')

	def pop(self, key, x=None):
		raise AttributeError('pop not supported by method dict')

	def popitem(self):
		raise AttributeError('popitem not supported by method dict')

	def setdefault(self, key, failobj=None):
		raise AttributeError('setdefault not supported by method dict')
		
def factory(mixinclass):
	class MethodDictFactoryClass(mixinclass, MethodDictMixin):
		pass
	return MethodDictFactoryClass

