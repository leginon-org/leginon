import copy
import xmlrpclib
import Numeric
import Image
import cStringIO

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
	typelist = ('object',)
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
	typelist = UIObject.typelist + ('container',)
	# don't keep
	value = ''
	def __init__(self, name):
		UIObject.__init__(self, name)
		self.uiobjectdict = {}

	def addUIObject(self, uiobject):
		if uiobject.name not in self.uiobjectdict:
			if isinstance(uiobject, UIObject):
				uiobject.setParent(self)
				self.addUIObjectCallback((uiobject.name,), uiobject.typelist,
																										uiobject.value)
				if isinstance(uiobject, UIContainer):
					uiobject.addUIObjectsCallback()
				self.uiobjectdict[uiobject.name] = uiobject
			else:
				raise TypeError('value must be a UIObject instance')
		else:
			raise ValueError('name already exists in UI Object mapping')

	def addUIObjectsCallback(self):
		for uiobject in self.uiobjectdict.values():
			self.addUIObjectCallback((uiobject.name,), uiobject.typelist,
																										uiobject.value)
			if isinstance(uiobject, UIContainer):
				uiobject.addUIObjectsCallback()

	def deleteUIObject(self, name):
		# update "spec"?
		try:
			uiobject = self.uiobjectdict[name]
			del self.uiobjectdict[name]
			self.deleteUIObjectCallback((uiobject.name,))
			uiobject.setParent(None)
		except KeyError:
			raise ValueError('name does not exist in UI Object mapping')

	def addUIObjectCallback(self, namelist, typelist, value):
		if self.parent is not None:
			self.parent.addUIObjectCallback((self.name,) + namelist, typelist, value)
		else:
			pass
			#raise RuntimeError('cannot add object to container without parent')

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

class UIMethod(UIObject):
	typelist = UIObject.typelist + ('method',)
	# don't keep
	value = ''
	def __init__(self, name, method):
		UIObject.__init__(self, name)
		if not callable(method):
			raise TypeError('method must be callable')
		self.method = method

class UIData(UIObject):
	permissionsvalues = ('r', 'w', 'rw', 'wr')
	typelist = UIObject.typelist + ('data',)
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
	typelist = UIData.typelist + ('boolean',)

class UIInteger(UIData):
	typelist = UIData.typelist + ('integer',)

class UIFloat(UIData):
	typelist = UIData.typelist + ('float',)

class UIString(UIData):
	typelist = UIData.typelist + ('string',)

class UIArray(UIData):
	typelist = UIData.typelist + ('array',)

class UIStruct(UIData):
	typelist = UIData.typelist + ('struct',)

class UIDate(UIData):
	typelist = UIData.typelist + ('date',)

class UISelectFromList(UIContainer):
	typelist = UIContainer.typelist + ('select from list',)
	# callback
	def __init__(self, name, listvalue, selectedvalue, permissions='r'):
		UIContainer.__init__(self, name)
		self.list = UIArray('List', listvalue, permissions)
		self.selected = UIArray('Selected', selectedvalue, 'rw')
		self.addUIObject(self.list)
		self.addUIObject(self.selected)

	def select(self, items):
		self.selected.set(items)

class UISelectFromStruct(UIContainer):
	typelist = UIContainer.typelist + ('select from struct',)
	# callback
	def __init__(self, name, structvalue, selectedvalue, permissions='r'):
		UIContainer.__init__(self, name)
		self.struct = UIStruct('Struct', structvalue, permissions)
		self.selected = UIArray('Selected', selectedvalue, 'rw')
		self.addUIObject(self.struct)
		self.addUIObject(self.selected)

	def select(self, items):
		self.selected.set(items)

class UIBinary(UIData):
	typelist = UIData.typelist + ('binary',)
	def __init__(self, name, value, permissions='r', callback=None):
		if type(value) is str:
			value = xmlrpclib.Binary(value)
		UIData.__init__(self, name, value, permissions, callback)

	def _set(self, value):
		if type(value) is str:
			value = xmlrpclib.Binary(value)
		UIData._set(self, value)

class UIDialog(UIContainer):
	typelist = UIContainer.typelist + ('dialog',)
	def __init__(self, name):
		UIContainer.__init__(self, name)

	def destroy(self):
		self.parent.deleteUIObject(self.name)

class UIMessageDialog(UIDialog):
	typelist = UIDialog.typelist + ('message',)
	def __init__(self, name, label):
		UIDialog.__init__(self, name)
		self.addUIObject(UIString('Message', label, 'r'))
		self.addUIObject(UIMethod('OK', self.ok))

	def ok(self):
		self.destroy()

class UIImage(UIBinary):
	typelist = UIBinary.typelist + ('image',)
	def __init__(self, name, value, permissions='r', callback=None):
		if isinstance(value, Numeric.arraytype):
			value = self.array2image(value)
		UIBinary.__init__(self, name, value, permissions, callback)

	def array2image(self, a):
		if a.typecode() == Numeric.UnsignedInt8:
			mode = "L"
		elif a.typecode() == Numeric.Float32:
			mode = "F"
		else:
			raise ValueError('unsupported image mode')
		# most likely a better way is possible
		stream = cStringIO.StringIO()
		Image.fromstring(mode, (a.shape[1],a.shape[0]),
											a.tostring()).save(stream,'PNG')
		return stream.getvalue()

class UITargetImage(UIContainer):
	typelist = UIContainer.typelist + ('target image',)
	# callback
	def __init__(self, name, image, targets=[]):
		UIContainer.__init__(self, name)
		self.image = UIImage('Image', image, 'r')
		self.targets = UIArray('Targets', targets, 'rw')
		self.addUIObject(self.image)
		self.addUIObject(self.targets)

