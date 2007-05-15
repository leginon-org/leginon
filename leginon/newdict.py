import numarray
import os

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
		self.data = None

	def read(self):
		if self.path is None:
			raise RuntimeError('no path set for %s' % (self.filename,))
		if self.data is not None:
			#print 'already read', self.filename
			return self.data
		#print 'reading image', self.filename
		fullname = os.path.join(self.path, self.filename)
		self.data = self.loader(fullname)
		self.data.fileref = self
		return self.data

	def setPath(self, path):
		self.path = path

class OrderedDict(dict):
	def __init__(self, initializer={}):
		try:
			items = initializer.items()
		except AttributeError:
			items = list(initializer)
		self.__keys = [i[0] for i in items]
		dict.__init__(self, initializer)

	## definining __reduce__ allows unpickler to call __init__ 	 
	def __reduce__(self): 	 
		state = dict(self.__dict__) 	 
		## giving the new object an initializer has a lot of 	 
		## duplicate information to what is given in the 	 
		## state dict, but it is necessary to get the dict 	 
		## base class to have its items set 	 
		initializer = dict(self.items()) 	 
		return (self.__class__, (initializer,), state)

	def __setitem__(self, key, value):
		if not dict.__contains__(self, key):
			self.__keys.append(key)
		dict.__setitem__(self, key, value)

	def __delitem__(self, key):
		dict.__delitem__(self, key)
		self.__keys.remove(key)

	def update(self, other):
		for key in other.keys():
			self[key] = other[key]

	def keys(self):
		return list(self.__keys)

	def values(self):
		return map(super(OrderedDict, self).__getitem__, self.__keys)

	def items(self):
		values = OrderedDict.values(self)
		return zip(self.__keys, values)

	def __str__(self):
		'''
		imitate dict.__str__ but with items in proper order
		'''
		itemlist = []
		for key,value in self.items():
			if type(value) is numarray.ArrayType:
				valuestr = '(ArrayType,shape=%s)' % (value.shape,)
			else:
				valuestr = str(value)
			itemstr = "%s: %s" % (str(key), valuestr)
			itemlist.append(itemstr)
		joinedstr = ', '.join(itemlist)
		finalstr = '{%s}' % (joinedstr,)
		return finalstr


### types used in TypedDict must have valicators
### Two ways to register a validator for a given type:
###     1)   call registerValidator
###	2)   for user defined classes, define classmethod called 'validator'
validators = {}
def registerValidator(type, validator):
	validators[type] = validator

class DBNull(object):
	pass
NULL = DBNull()

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
		if (value is not None) and (value is not NULL):
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

## most common types are their own validator
for t in (bool, complex, dict, float, int, list, long, type(None), str, tuple):
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
class MRCArrayType(numarray.ArrayType):
	pass
class DatabaseArrayType(numarray.ArrayType):
	pass

### and here's the validator for it
def validateArrayType(obj):
	'''
	if obj is a numarray array or a FileReference, then return obj
	else raise excpetion.
	'''
	if isinstance(obj, FileReference):
		return obj

	### if it's a numarray array, it should have the type() attribute
	try:
		obj.type
	except AttributeError:
		raise TypeError()
	return obj

registerValidator(MRCArrayType, validateArrayType)
registerValidator(DatabaseArrayType, validateArrayType)
