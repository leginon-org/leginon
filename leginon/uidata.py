import copy
import xmlrpclib
import Numeric
import Image
import cStringIO
import Mrc

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
	def __init__(self, name):
		UIObject.__init__(self, name)
		self.uiobjectdict = {}
		self.uiobjectlist = []

	def addUIObject(self, uiobject):
		if uiobject.name not in self.uiobjectdict:
			if isinstance(uiobject, UIObject):
				uiobject.setParent(self)
				if hasattr(uiobject, 'value'):
					value = uiobject.value
				else:
					value = ''
				if hasattr(uiobject, 'read'):
					read = uiobject.read
				else:
					read = False
				if hasattr(uiobject, 'write'):
					write = uiobject.write
				else:
					write = False
				self.addUIObjectCallback((uiobject.name,), uiobject.typelist,
																		value, read, write)
				if isinstance(uiobject, UIContainer):
					uiobject.addUIObjectsCallback()
				self.uiobjectdict[uiobject.name] = uiobject
				self.uiobjectlist.append(uiobject)
			else:
				raise TypeError('value must be a UIObject instance')
		else:
			raise ValueError('name already exists in UI Object mapping')

	def addUIObjectsCallback(self):
		#for uiobject in self.uiobjectdict.values():
		for uiobject in self.uiobjectlist:
			if hasattr(uiobject, 'value'):
				value = uiobject.value
			else:
				value = ''
			if hasattr(uiobject, 'read'):
				read = uiobject.read
			else:
				read = False
			if hasattr(uiobject, 'write'):
				write = uiobject.write
			else:
				write = False
			self.addUIObjectCallback((uiobject.name,), uiobject.typelist,
																	value, read, write)
			if isinstance(uiobject, UIContainer):
				uiobject.addUIObjectsCallback()

	def addUIObjects(self, uiobjects):
		for uiobject in uiobjects:
			self.addUIObject(uiobject)

	def deleteUIObject(self, name):
		# update "spec"?
		try:
			uiobject = self.uiobjectdict[name]
			del self.uiobjectdict[name]
			self.uiobjectlist.remove(uiobject)
			self.deleteUIObjectCallback((uiobject.name,))
			uiobject.setParent(None)
		except KeyError:
			raise ValueError('cannot delete object not in UI Object mapping')

	def addUIObjectCallback(self, namelist, typelist, value, read, write):
		if self.parent is not None:
			self.parent.addUIObjectCallback((self.name,) + namelist,
																			typelist, value, read, write)
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
				#for uiobject in self.uiobjectdict.values():
				for uiobject in self.uiobjectlist:
					try:
						return uiobject.getUIObjectFromList(namelist[1:])
					except ValueError:
						pass
				raise ValueError('cannot get object, not in child UI Object mappings')
		else:
			raise ValueError('cannot get object from list, not parent of UI object')

class UISmallContainer(UIContainer):
	typelist = UIContainer.typelist + ('small',)

class UIMediumContainer(UIContainer):
	typelist = UIContainer.typelist + ('medium',)

class UILargeContainer(UIContainer):
	typelist = UIContainer.typelist + ('large',)

class UIClientContainer(UILargeContainer):
	typelist = UILargeContainer.typelist + ('client',)
	def __init__(self, name, location):
		self.value = location
		UILargeContainer.__init__(self, name)

class UIMethod(UIObject):
	typelist = UIObject.typelist + ('method',)
	def __init__(self, name, method):
		UIObject.__init__(self, name)
		if not callable(method):
			raise TypeError('method must be callable')
		self.method = method

class UIData(UIObject):
	permissionsvalues = ('r', 'w', 'rw', 'wr')
	typelist = UIObject.typelist + ('data',)
	nonevalue = None
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

		self.set(value)

	def _set(self, value):
		if self.write:
			self.set(value)
		else:
			raise PermissionsError('cannot set, permission denied')

	def set(self, value, callback=True):
		value = copy.deepcopy(value)
		if self.validate(value):
			# should call in constructor?
			if callback and self.callback is not None:
				callbackvalue = self.callback(value)
				if self.validate(callbackvalue):
					self.value = callbackvalue
			else:
				self.value = value
			if self.nonevalue is not None and self.value is None:
				self.value = self.nonevalue
		else:
			raise TypeError('invalid data value for type')
		if self.parent is not None:
			self.parent.setUIObjectCallback((self.name,), self.value)

	# needs reversal of _get/get like set
	def get(self):
		if self.read:
			return self._get()
		else:
			raise PermissionsError('cannot get, permission denied')

	def _get(self):
		# to be sure, perhaps not necessary
		if self.nonevalue is not None and self.value == self.nonevalue:
			value = None
		else:
			value = self.value
		if self.validate(value):
#			if self.callback is not None:
#				callbackvalue = self.callback()
#				if self.validate(callbackvalue):
#					value = callbackvalue
			return value
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

class UIProgress(UIInteger):
	typelist = UIInteger.typelist + ('progress',)

class UISingleSelectFromList(UIContainer):
	typelist = UIContainer.typelist + ('single select from list',)
	def __init__(self, name, listvalue, selectedindex, callback=None):
		UIContainer.__init__(self, name)
		self.list = UIArray('List', listvalue, 'r')
		self.selected = UIInteger('Selected', selectedindex, 'rw', callback)
		self.addUIObject(self.list)
		self.addUIObject(self.selected)

	def set(self, listvalue, selectedindex):
		self.setList(listvalue)
		self.setSelected(selectedindex)

	def getList(self):
		return self.list.get()

	def setList(self, listvalue):
		self.list.set(listvalue)

	def getSelected(self):
		return self.selected.get()

	def setSelected(self, selectedvalue):
		self.selected.set(selectedvalue)

	def getSelectedValue(self, selected=None):
		valuelist = self.getList()
		if selected is None:
			selected = self.getSelected()
		return valuelist[selected]

class UISelectFromList(UIContainer):
	typelist = UIContainer.typelist + ('select from list',)
	# callback
	def __init__(self, name, listvalue, selectedvalue,
											permissions='r', callback=None):
		UIContainer.__init__(self, name)
		self.list = UIArray('List', listvalue, permissions)
		self.selected = UIArray('Selected', selectedvalue, 'rw', callback)
		self.addUIObject(self.list)
		self.addUIObject(self.selected)

	def set(self, listvalue, selectedvalue):
		self.setList(listvalue)
		self.setSelected(selectedvalue)

	def getList(self):
		return self.list.get()

	def setList(self, listvalue):
		self.list.set(listvalue)

	def getSelected(self):
		return self.selected.get()

	def setSelected(self, selectedvalue):
		self.selected.set(selectedvalue)

	def getSelectedValue(self, selected=None):
		value = []
		valuelist = self.getList()
		if selected is None:
			selected = self.getSelected()
		for i in selected:
			value.append(valuelist[i])
		return value

class UISelectFromStruct(UIContainer):
	typelist = UIContainer.typelist + ('select from struct',)
	# callback
	def __init__(self, name, structvalue, selectedvalue, permissions='r'):
		UIContainer.__init__(self, name)
		self.struct = UIStruct('Struct', structvalue, permissions)
		self.selected = UIArray('Selected', selectedvalue, 'rw')
		self.addUIObject(self.struct)
		self.addUIObject(self.selected)

	def set(self, structvalue, selectedvalue):
		self.setStruct(structvalue)
		self.setSelected(selectedvalue)

	def getStruct(self):
		return self.struct.get()

	def setStruct(self, structvalue):
		self.struct.set(structvalue)

	def getSelected(self):
		return self.selected.get()

	def setSelected(self, selectedvalue):
		self.selected.set(selectedvalue)

class UIBinary(UIData):
	typelist = UIData.typelist + ('binary',)
	def __init__(self, name, value, permissions='r', callback=None):
#		if type(value) is str:
#			value = xmlrpclib.Binary(value)
		UIData.__init__(self, name, value, permissions, callback)

	def set(self, value):
		if type(value) is str:
			value = xmlrpclib.Binary(value)
		UIData.set(self, value)

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
	nonevalue = ''
	def __init__(self, name, value, permissions='r', callback=None):
#		if isinstance(value, Numeric.arraytype):
#			value = self.array2image(value)
		UIBinary.__init__(self, name, value, permissions, callback)

	# needs optimization
	def array2image(self, a):
		return Mrc.numeric_to_mrcstr(a)

	def set(self, value):
		if isinstance(value, Numeric.arraytype):
			value = xmlrpclib.Binary(self.array2image(value))
		else:
			value = xmlrpclib.Binary(value)
		UIData.set(self, value)

class UIClickImage(UIContainer):
	typelist = UIContainer.typelist + ('click image',)
	def __init__(self, name, clickcallback, image, permissions='r'):
		self.clickcallback = clickcallback
		UIContainer.__init__(self, name)
		self.image = UIImage('Image', image, 'r')
		self.coordinates = UIArray('Coordinates', [], 'rw')
		self.method = UIMethod('Click', self.doClickCallback)
		self.addUIObject(self.coordinates)
		self.addUIObject(self.method)
		self.addUIObject(self.image)

	def setImage(self, value):
		self.image.set(value)

	def doClickCallback(self):
		self.clickcallback(tuple(self.coordinates.get()))

class UITargetImage(UIContainer):
	typelist = UIContainer.typelist + ('target image',)
	# callback
	def __init__(self, name, image, permissions='r'):
		UIContainer.__init__(self, name)
		self.targets = {}
		self.image = UIImage('Image', image, 'r')
		self.addUIObject(self.image)

	def addTargetType(self, name, targets=[]):
		if name in self.targets:
			raise ValueError('Target type already exists')
		self.targets[name] = UIArray(name, targets, 'rw')
		self.addUIObject(self.targets[name])

	def deleteTargetType(self, name):
		try:
			self.deleteUIObject(self.targets[name])
			del self.targets[name]
		except KeyError:
			raise ValueError('No such target type')

	def getTargetType(self, name):
		try:
			return self.targets[name].get()
		except KeyError:
			raise ValueError('No such target type')

	def setTargetType(self, name, value):
		try:
			self.targets[name].set(value)
		except KeyError:
			raise ValueError('No such target type')

	def setTargets(self, value):
		for targetarray in self.targets.values():
			targetarray.set(value)

	def getTargets(self):
		value = {}
		for name in self.targets:
			value[name] = self.targets[name].get()
		return value

	def setImage(self, value):
		self.image.set(value)

