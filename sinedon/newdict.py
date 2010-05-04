import numpy
import os
from pyami.ordereddict import OrderedDict 
from pyami import weakattr
import array

class FileReference(object):
	'''
	this is a place holder for data that is stored in a file
	until we find the full path
	   'filename' is the filename, without a path.
	   'loader' is a function that takes the full path filename and
	     returns the data that was read from file.
	Once you find the path, call read(path) to return the data.
	'''
	def __init__(self, filename, loader):
		self.filename = filename
		self.loader = loader
		self.path = None

	def read(self):
		if self.path is None:
			raise RuntimeError('no path set for %s' % (self.filename,))
		#print 'reading image', self.filename
		fullname = os.path.join(self.path, self.filename)
		d = self.loader(fullname)
		return d

	def exists(self):
		if self.path is None:
			raise RuntimeError('no path set for %s' % (self.filename,))
		fullname = os.path.join(self.path, self.filename)
		return os.path.exists(fullname)

	def setPath(self, path):
		self.path = path


### types used in TypedDict must have valicators
### Two ways to register a validator for a given type:
###     1)   call registerValidator
###	2)   for user defined classes, define classmethod called 'validator'
validators = {}
def registerValidator(type, validator):
	validators[type] = validator

## types of items are set by subclassing and setting typemap
class TypedDict(OrderedDict):
	def typemap(cls):
		return ()
	typemap = classmethod(typemap)

	def __init__(self, initializer={}):
		self.__types = OrderedDict(self.typemap())
		for t in self.__types.values():
			if t not in validators and not hasattr(t, 'validator'):
				raise RuntimeError('no validator for type %s' % (t,))
		## initialize all items defined by typemap
		complete_init = OrderedDict(initializer)
		for key,value in self.__types.items():
			if key not in initializer:
				complete_init[key] = None
		super(TypedDict,self).__init__(complete_init)

	def __setitem__(self, key, value):
		## validate key, new keys not allowed
		t = self.__types[key]
		## validate value	
		if value is not None:
			try:
				validator = validators[t]
			except KeyError:
				validator = t.validator
			value = validator(value)
		super(TypedDict,self).__setitem__(key, value)

	def types(self):
		return OrderedDict(self.__types)

	def friendly_update(self, other):
		for key in other.keys():
			try:
				self[key] = other[key]
			except KeyError:
				pass

def validateStr(obj):
	if isinstance(obj, str):
		return obj
	elif isinstance(obj, array.array):
		return obj.tostring()
	else:
		return str(obj)

registerValidator(str, validateStr)

## most common types are their own validator
for t in (bool, complex, dict, float, int, list, long, type(None), tuple):
	registerValidator(t, t)

## other types we define here, and validators too
class AnyObject(object):
	'''
	The AnyObject type can be used in the typemap and can be initialized
	with any object
	'''
	def __init__(self, new_object):
		if isinstance(new_object, AnyObject):
			self.o = new_object.o
		else:
			self.o = new_object

	def __str__(self):
		return 'AnyObject(%s)' % (self.o,)

registerValidator(AnyObject, AnyObject)

## ArrayType was previously not hashable, but seems to be now
class MRCArrayType(numpy.ndarray):
	pass
class DatabaseArrayType(numpy.ndarray):
	pass
class CallableType(object):
	pass

### and here's the validator for it
def validateArrayType(obj):
	'''
	if obj is a ndarray or a FileReference, then return obj
	else raise excpetion.
	'''
	if isinstance(obj, FileReference):
		return obj

	### if it's a numpy array, it should have the type() attribute
	if isinstance(obj, numpy.ndarray):
		return obj

	raise TypeError(type(obj))

def validateCallable(obj):
	if callable(obj):
		return obj
	raise TypeError(type(obj))

registerValidator(MRCArrayType, validateArrayType)
registerValidator(DatabaseArrayType, validateArrayType)
registerValidator(CallableType, validateCallable)
