import copy

# Exceptions
# maybe overdone
class UIError(Exception):
	pass

class UIObjectError(UIError):
	pass

class UIDataError(UIObjectError):
	pass

class PermissionsError(UIDataError):
	pass

# UI Objects
class UIObject(object):
	typename = 'object'
	def __init__(self, name):
		if type(name) is str:
			self.name = name
		else:
			raise TypeError('name must be a string')
		self.parent = None

	def setParent(self, parent):
		if parent is not None and not isinstance(parent, UIContainer):
			raise TypeError('parent must be a UIContainer or None')
		else:
			self.parent = parent

	def getUIObjectFromList(self, namelist):
		if len(namelist) == 1 and namelist[0] == self.name:
			return self
		else:
			raise ValueError('incorrect UI object')

class UIContainer(UIObject):
	typename = 'container'
	# don't keep
	value = ''
	def __init__(self, name):
		UIObject.__init__(self, name)
		self.uiobjectdict = {}

	def addUIObject(self, uiobject):
		# update "spec" somehow?
		if uiobject.name not in self.uiobjectdict:
			if isinstance(uiobject, UIObject):
				uiobject.setParent(self)
				self.addUIObjectCallback((uiobject.name,), uiobject.typename,
																											uiobject.value)
				self.uiobjectdict[uiobject.name] = uiobject
			else:
				raise TypeError('value must be a UIObject instance')
		else:
			raise ValueError('name already exists in UI Object mapping')

	def deleteUIObject(self, name):
		# update "spec" somehow?
		try:
			uiobject = self.uiobjectdict[name]
			del self.uiobjectdict[name]
			self.deleteUIObjectCallback((uiobject.name,))
			uiobject.setParent(None)
		except KeyError:
			raise ValueError('name does not exist in UI Object mapping')

	def addUIObjectCallback(self, namelist, typename, value):
		if self.parent is not None:
			self.parent.addUIObjectCallback((self.name,) + namelist, typename, value)
		else:
			raise RuntimeError('cannot add object to container without parent')

	def setUIObjectCallback(self, namelist, value):
		if self.parent is not None:
			self.parent.setUIObjectCallback((self.name,) + namelist, value)

	def deleteUIObjectCallback(self, namelist):
		if self.parent is not None:
			self.parent.deleteUIObjectCallback((self.name,) + namelist)

	def getUIObjectFromList(self, namelist):
		if type(namelist) not in (list, tuple):
			raise TypeError('name hierarchy must be a list')
		if not namelist:
			raise ValueError('no widget name[s] specified')
		if namelist[0] == self.name:
			if len(namelist) == 1:
				return self
			else:
				for uiobject in self.uiobjectdict.values():
					try:
						return uiobject.getUIObjectFromList(namelist[1:])
					except ValueError:
						pass
				raise ValueError('name does not exist in UI Object mapping')
		else:
			raise ValueError('name does not exist in UI Object mapping')

#	def addUIObjects(self, namedict, uiobject):
#		for name in namedict:
#			if name in self.uiobjectdict:
#				self.addUIObject(name, namedict[name])
#				if uiobject, UIContainer
#			uiobject = namedict[name]
#		try:
#			container = self.getUIObjectFromList(namelist[:-1])
#		except ValueError:
#			raise ValueError('container name does not exist in UI Object mapping')
#		container.addUIObject(namelist[-1], uiobject)

#	def deleteUIObjectFromList(self, namelist):
#		try:
#			container = self.getUIObjectFromList(namelist[:-1])
#		except ValueError:
#			raise ValueError('container name does not exist in UI Object mapping')
#		container.deleteUIObject(namelist[-1], uiobject)

	# setUIObject?
	# getUIObject?

class UIMethod(UIObject):
	typename = 'method'
	pass

class UIData(UIObject):
	permissionsvalues = ('r', 'w', 'rw', 'wr')
	typename = 'data'
	def __init__(self, name, value, permissions='r', callback=None):
		UIObject.__init__(self, name)
		if permissions in self.permissionsvalues:
			if 'r' in permissions:
				self.read = True
			else:
				self.read = False
			if 'w' in permissions:
				self.write = True
			else:
				self.write = False
		else:
			raise ValueError('invalid permissions value')

		if callable(callback):
			self.callback = callback
		elif callback is None:
			self.callback = None
		else:
			raise TypeError('callback must be callable or None')

		self._set(value)

	def set(self, value):
		if self.write:
			self._set(value)
		else:
			raise PermissionsError('cannot set, permission denied')
		if self.parent is not None:
			self.parent.setUIObjectCallback((self.name,), value)

	def _set(self, value):
		value = copy.deepcopy(value)
		if self.validate(value):
			# should call in constructor?
			if self.callback is not None:
				callbackvalue = self.callback(value)
				if self.validate(callbackvalue):
					self.value = callbackvalue
			else:
				self.value = value
		else:
			raise TypeError('invalid data value for type')

	def get(self):
		if self.read:
			return self._get()
		else:
			raise PermissionsError('cannot get, permission denied')

	def _get(self):
		# to be sure, perhaps not necessary
		if self.validate(self.value):
			if self.callback is not None:
				callbackvalue = self.callback()
				if self.validate(callbackvalue):
					self.value = callbackvalue
			return self.value
		else:
			raise TypeError('internal error, invalid data value for type')

	def validate(self, value):
		#return False
		return True

class UIBoolean(UIData):
	typename = 'boolean'
	pass

class UIInteger(UIData):
	typename = 'integer'
	pass

class UIFloat(UIData):
	typename = 'float'
	pass

class UIString(UIData):
	typename = 'string'
	pass

class UIArray(UIData):
	typename = 'array'
	pass

class UIStruct(UIData):
	typename = 'struct'
	pass

class UIDate(UIData):
	typename = 'date'
	pass

class UIBinary(UIData):
	typename = 'binary'
	pass

