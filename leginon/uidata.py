import copy
import xmlrpclib
import Numeric
import Image
import cStringIO
import Mrc

# Exceptions
# maybe overdone
class Error(Exception):
	pass

class ObjectError(Error):
	pass

class DataError(ObjectError):
	pass

class PermissionsError(DataError):
	pass

# UI Objects
class Object(object):
	typelist = ('object',)
	def __init__(self, name):
		if type(name) is str:
			self.name = name
		else:
			raise TypeError('name must be a string')
		self.parent = None

	def setParent(self, parent):
		if parent is not None and not isinstance(parent, Container):
			raise TypeError('parent must be a Container or None')
		else:
			self.parent = parent

	def getObjectFromList(self, namelist):
		if len(namelist) == 1 and namelist[0] == self.name:
			return self
		else:
			raise ValueError('connect get Object from list, no such Object')

class Container(Object):
	typelist = Object.typelist + ('container',)
	def __init__(self, name):
		Object.__init__(self, name)
		self.uiobjectdict = {}
		self.uiobjectlist = []

	def addObject(self, uiobject):
		if uiobject.name not in self.uiobjectdict:
			if isinstance(uiobject, Object):
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
				self.addObjectCallback((uiobject.name,), uiobject.typelist,
																		value, read, write)
				if isinstance(uiobject, Container):
					uiobject.addObjectsCallback()
				self.uiobjectdict[uiobject.name] = uiobject
				self.uiobjectlist.append(uiobject)
			else:
				raise TypeError('value must be a Object instance')
		else:
			raise ValueError('name already exists in Object mapping')

	def addObjectsCallback(self):
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
			self.addObjectCallback((uiobject.name,), uiobject.typelist,
																	value, read, write)
			if isinstance(uiobject, Container):
				uiobject.addObjectsCallback()

	def addObjects(self, uiobjects):
		for uiobject in uiobjects:
			self.addObject(uiobject)

	def deleteObject(self, name):
		# update "spec"?
		try:
			uiobject = self.uiobjectdict[name]
			del self.uiobjectdict[name]
			self.uiobjectlist.remove(uiobject)
			self.deleteObjectCallback((uiobject.name,))
			uiobject.setParent(None)
		except KeyError:
			raise ValueError('cannot delete Object, not in Object mapping')

	def addObjectCallback(self, namelist, typelist, value, read, write):
		if self.parent is not None:
			self.parent.addObjectCallback((self.name,) + namelist,
																			typelist, value, read, write)
		else:
			pass
			#raise RuntimeError('cannot add object to container without parent')

	def setObjectCallback(self, namelist, value):
		if self.parent is not None:
			self.parent.setObjectCallback((self.name,) + namelist, value)

	def deleteObjectCallback(self, namelist):
		if self.parent is not None:
			self.parent.deleteObjectCallback((self.name,) + namelist)

	def getObjectFromList(self, namelist):
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
						return uiobject.getObjectFromList(namelist[1:])
					except ValueError:
						pass
				raise ValueError('cannot get object, not in child Object mappings')
		else:
			raise ValueError('cannot get object from list, not parent of Object')

class SmallContainer(Container):
	typelist = Container.typelist + ('small',)

class MediumContainer(Container):
	typelist = Container.typelist + ('medium',)

class LargeContainer(Container):
	typelist = Container.typelist + ('large',)

class ExternalContainer(Container):
	typelist = Container.typelist + ('external',)

class ClientContainer(LargeContainer):
	typelist = LargeContainer.typelist + ('client',)
	def __init__(self, name, location):
		self.value = location
		LargeContainer.__init__(self, name)

class Method(Object):
	typelist = Object.typelist + ('method',)
	def __init__(self, name, method):
		Object.__init__(self, name)
		if not callable(method):
			raise TypeError('method must be callable')
		self.method = method

class Data(Object):
	permissionsvalues = ('r', 'w', 'rw', 'wr')
	typelist = Object.typelist + ('data',)
	nonevalue = None
	def __init__(self, name, value, permissions='r', callback=None):
		Object.__init__(self, name)
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

		self.setCallback(callback)

		self.set(value)

	def setCallback(self, callback):
		if callable(callback):
			self.callback = callback
		elif callback is None:
			self.callback = None
		else:
			raise TypeError('callback must be callable or None')

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
			self.parent.setObjectCallback((self.name,), self.value)

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

class Boolean(Data):
	typelist = Data.typelist + ('boolean',)

class Integer(Data):
	typelist = Data.typelist + ('integer',)

class Float(Data):
	typelist = Data.typelist + ('float',)

class String(Data):
	typelist = Data.typelist + ('string',)

class Array(Data):
	typelist = Data.typelist + ('array',)

class Struct(Data):
	typelist = Data.typelist + ('struct',)

class Date(Data):
	typelist = Data.typelist + ('date',)

class Progress(Integer):
	typelist = Integer.typelist + ('progress',)

class SingleSelectFromList(Container):
	typelist = Container.typelist + ('single select from list',)
	def __init__(self, name, listvalue, selectedindex, callback=None):
		Container.__init__(self, name)
		self.list = Array('List', listvalue, 'r')
		self.selected = Integer('Selected', selectedindex, 'rw', callback)
		self.addObject(self.list)
		self.addObject(self.selected)

	def setCallback(self, callback):
		self.selected.setCallback(callback)

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
		try:
			return valuelist[selected]
		except IndexError:
			return None

class SelectFromList(Container):
	typelist = Container.typelist + ('select from list',)
	def __init__(self, name, listvalue, selectedvalues, permissions='r',
								callback=None):
		Container.__init__(self, name)
		self.list = Array('List', listvalue, permissions)
		self.selected = Array('Selected', selectedvalues, 'rw', callback)
		self.addObject(self.list)
		self.addObject(self.selected)

	def setCallback(self, callback):
		self.selected.setCallback(callback)

	def set(self, listvalue, selectedvalues):
		self.setList(listvalue)
		self.setSelected(selectedvalues)

	def getList(self):
		return self.list.get()

	def setList(self, listvalue):
		self.list.set(listvalue)

	def getSelected(self):
		return self.selected.get()

	def setSelected(self, selectedvalues):
		self.selected.set(selectedvalues)

	def getSelectedValues(self, selected=None):
		value = []
		valuelist = self.getList()
		if selected is None:
			selected = self.getSelected()
		for i in selected:
			value.append(valuelist[i])
		return value

class SelectFromStruct(Container):
	typelist = Container.typelist + ('select from struct',)
	# callback
	def __init__(self, name, structvalue, selectedvalue, permissions='r'):
		Container.__init__(self, name)
		self.struct = Struct('Struct', structvalue, permissions)
		self.selected = Array('Selected', selectedvalue, 'rw')
		self.addObject(self.struct)
		self.addObject(self.selected)

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

class Binary(Data):
	typelist = Data.typelist + ('binary',)
	def __init__(self, name, value, permissions='r', callback=None):
#		if type(value) is str:
#			value = xmlrpclib.Binary(value)
		Data.__init__(self, name, value, permissions, callback)

	def set(self, value):
		if type(value) is str:
			value = xmlrpclib.Binary(value)
		Data.set(self, value)

class Dialog(Container):
	typelist = Container.typelist + ('message dialog',)
	def __init__(self, name):
		Container.__init__(self, name)

	def destroy(self):
		self.parent.deleteObject(self.name)

class MessageDialog(Dialog):
	typelist = Dialog.typelist + ('message',)
	def __init__(self, name, label):
		Dialog.__init__(self, name)
		self.addObject(String('Message', label, 'r'))
		self.addObject(Method('OK', self.ok))

	def ok(self):
		self.destroy()

class Image(Binary):
	typelist = Binary.typelist + ('image',)
	nonevalue = ''
	def __init__(self, name, value, permissions='r', callback=None):
#		if isinstance(value, Numeric.arraytype):
#			value = self.array2image(value)
		Binary.__init__(self, name, value, permissions, callback)

	# needs optimization
	def array2image(self, a):
		return Mrc.numeric_to_mrcstr(a)

	def set(self, value):
		if isinstance(value, Numeric.arraytype):
			value = xmlrpclib.Binary(self.array2image(value))
		else:
			value = xmlrpclib.Binary(value)
		Data.set(self, value)

class ClickImage(Container):
	typelist = Container.typelist + ('click image',)
	def __init__(self, name, clickcallback, image, permissions='r'):
		self.clickcallback = clickcallback
		Container.__init__(self, name)
		self.image = Image('Image', image, 'r')
		self.coordinates = Array('Coordinates', [], 'rw')
		self.method = Method('Click', self.doClickCallback)
		self.addObject(self.coordinates)
		self.addObject(self.method)
		self.addObject(self.image)

	def setImage(self, value):
		self.image.set(value)

	def doClickCallback(self):
		self.clickcallback(tuple(self.coordinates.get()))

class TargetImage(Container):
	typelist = Container.typelist + ('target image',)
	# callback
	def __init__(self, name, image, permissions='r'):
		Container.__init__(self, name)
		self.targets = {}
		self.image = Image('Image', image, 'r')
		self.addObject(self.image)

	def addTargetType(self, name, targets=[]):
		if name in self.targets:
			raise ValueError('Target type already exists')
		self.targets[name] = Array(name, targets, 'rw')
		self.addObject(self.targets[name])

	def deleteTargetType(self, name):
		try:
			self.deleteObject(self.targets[name])
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

