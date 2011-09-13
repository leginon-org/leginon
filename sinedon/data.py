# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import numpy
import newdict
import warnings
import types
import threading
import dbdatakeeper
import copy
import tcptransport
import weakref
import os
import connections
from pyami import weakattr
import itertools

class DataError(Exception):
	pass
class DataManagerOverflowError(DataError):
	pass
class DataAccessError(DataError):
	pass
class DataDuplicateError(DataError):
	pass


'''
How DataManager manages references between Data
-----------------------------------------------
Take the case of one Data instance referencing another Data instance:
	iii = ImageData()
	sss = SessionData()
	iii['session'] = sss
In this example, there is no direct reference between sss and iii.
Instead, iii['session'] actually contains a DataReference object.
If we try to access iii['session'], the DataManager will use the
DataReference to find the actual data (sss).  This dereferencing
operation happens automatically, for example:
	mysession = iii['session']
Now mysession is sss.

If dereferencing is not desired, Data objects have a special method:
	myref = iii.special_getitem('session', dereference=False)
will return a reference to sss instead of sss.

pickling and deepcopying are optimized because they do not dereference.
If iii is pickled or deepcopied, sss is not.
If iii is stored in the database, sss will be stored only if it is not already.
If iii and sss are in the database, and iii is queried, only iii is returned.
sss will be queried automatically when accessing iii['session']
'''

## manages references between data instances
## References between Data objects are strong until an object is inserted
## to the DB.  Then the strong reference is converted to weak ref.
class DataManager(object):
	def __init__(self):
		self.startServer()

		self.weakcache = weakref.WeakValueDictionary()
		self.dbcache = weakref.WeakValueDictionary()

		self.nextdmid = itertools.izip(itertools.repeat(self.location), itertools.count()).next

		self.holdimages = True

	def holdImages(self, value):
		self.holdimages = value

	def exit(self):
		if self.server is not None:
			self.server.exit()
			self.server = None

	def startServer(self):
		self.server = tcptransport.Server(self)
		self.server.start()
		port = self.server.port
		hostname = self.server.hostname
		self.location = (hostname, port)

	def cacheInsert(self, datainstance):
		## if datainstance has no dmid, give it one
		if not hasattr(datainstance, 'dmid') or datainstance.dmid is None:
			datainstance.dmid = self.nextdmid()

		## keep in the weak cache
		self.weakcache[datainstance.dmid] = datainstance

	def getDataFromDB(self, dataclass, dbid, **kwargs):
		dbmodulename = dataclass.__module__
		db = connections.getConnection(dbmodulename)

		### try to get data from dbcache before doing query
		try:
			dat = self.dbcache[dataclass, dbid]
		except KeyError:
			dat = db.direct_query(dataclass, dbid, **kwargs)
		return dat

	def setPersistent(self, datainstance):
		if datainstance is None or datainstance.dbid is None:
			return
		dbid = datainstance.dbid
		dataclass = datainstance.__class__
		self.dbcache[dataclass, dbid] = datainstance

	def getRemoteData(self, datareference):
		dmid = datareference.dmid
		location = {'hostname': dmid[0][0], 'port': dmid[0][1]}
		client = tcptransport.Client(location)
		datainstance = client.send(datareference)
		### this is a new instance from a pickle
		### now register it locally
		self.cacheInsert(datainstance)
		datainstance.sync()
		return datainstance

	def getRemoteFile(self, filereference, dmid):
		location = {'hostname': dmid[0][0], 'port': dmid[0][1]}
		client = tcptransport.Client(location)
		readobject = client.send(filereference)
		return readobject

	def getData(self, datareference, **kwargs):
		dataclass = datareference.dataclass
		referent = None
		dmid = datareference.dmid
		dbid = datareference.dbid

		#### try local weakrefs
		try:
			referent = self.weakcache[dmid]
			return referent
		except:
			pass

		#### try DB
		if dbid is not None:
			## in database
			try:
				referent = self.getDataFromDB(dataclass, dbid, **kwargs)
				return referent
			except:
				pass

		### if dmid indicates, try remote location
		if dmid is not None and dmid[0] != self.location:
			## in remote memory
			# TODO: kwargs
			referent = self.getRemoteData(datareference)
			return referent

		## must not exist anymore
		raise DataAccessError('referenced data can not be found: %s' % (datareference,))

	def query(self, datareference):
		# this is how socketstreamtransport server accesses this data manager
		datainstance = self.getData(datareference)
		return datainstance

	def readFile(self, filereference):
		return filereference.read()

	def handle(self, request):
		if isinstance(request, Data):
			return self.cacheInsert(request)
		elif isinstance(request, DataReference):
			return self.query(request)
		elif isinstance(request, newdict.FileReference):
			return self.readFile(request)
		else:
			print 'bad request:', request

datamanager = DataManager()

def holdImages(value):
	datamanager.holdImages(value)

class DataReference(object):
	'''
	initialized with one of these three:
		datarefernce (become a copy of an existing data reference)
		datainstance (become a reference an existing data instance)
		dataclass (become a reference to a non-existing data instance)
	if using dataclass, also specify either a dmid or a dbid
	'''
	def __init__(self, datareference=None, referent=None, dataclass=None, dmid=None, dbid=None):
		self.dataclass = None
		self.referent = None
		self.dmid = None
		self.dbid = None
		if datareference is not None:
			self.dataclass = datareference.dataclass
			self.dmid = datareference.dmid
			self.dbid = datareference.dbid
		elif referent is not None:
			## Data
			if isinstance(referent, Data):
				self.dataclass = referent.__class__
			else:
				raise ValueError('referent must be Data instance')
			self.sync(referent)
		elif dataclass is not None:
			if dmid is None and dbid is None:
				raise DataError('DataReference has neither a dmid nor a dbid')
			self.dataclass = dataclass
			self.dmid = dmid
			self.dbid = dbid
		elif dmid is not None:
			self.dmid = dmid
		else:
			raise DataError('DataReference needs more info for initialization')

	def __getstate__(self):
		## for pickling, do not include referent
		state = dict(self.__dict__)
		state['referent'] = None
		return state

	def sync(self, o=None):
		'''
		sync my db info with my referent, either directly
		(if given the optional argument which is the referent)
		or through a weak reference to the referent
		'''
		if o is None:
			if self.referent is None:
				return
			o = self.referent()
		if o is not None:
			if o.dbid is None:
				self.referent = o
			else:
				self.referent = weakref.ref(o)
			self.dmid = o.dmid
			self.dbid = o.dbid
			o.references[id(self)] = self

	def getData(self, **kwargs):
		referent = None
		#### Try strong and weak reference
		if isinstance(self.referent, weakref.ref):
			referent = self.referent()
		elif isinstance(self.referent, Data):
			referent = self.referent

		#### Try DataManager, update me with ref to new data
		if referent is None:
			referent = datamanager.getData(self, **kwargs)
			self.sync(referent)

		return referent

	def __str__(self):
		if isinstance(self.referent, weakref.ref):
			ref = 'weak'
		elif isinstance(self.referent, Data):
			ref = 'strong'
		else:
			ref = 'None'
		if self.dataclass is None:
			cls = 'unknown'
		else:
			cls = self.dataclass.__name__
		s = 'DataReference[class: %s, dmid: %s, dbid: %s, referent: %s]' % (cls, self.dmid, self.dbid, ref)
		return s

class UnknownData(object):
	'''
	this is a place holder for a Data instance that is not yet known
	'''
	def __init__(self, qikey):
		self.qikey = qikey

def data2dict(idata, noNone=False, dereference=False):
	d = {}
	for key,value in idata.items(dereference=dereference):
		if isinstance(value, Data):
			subd = data2dict(value, noNone)
			if subd:
				d[key] = subd
		else:
			if not noNone or value is not None:
				d[key] = value
	return d

def dict2data(d, datatype):
	instance = datatype()
	if d is None:
		return instance
	for key, subtype in datatype.typemap():
		try:
			if issubclass(subtype, Data):
				instance[key] = dict2data(d[key], subtype)
			else:
				instance[key] = d[key]
		except (KeyError, TypeError):
			pass
	return instance

class Data(newdict.TypedDict):
	'''
	Combines DataDict and LeginonObject to create the base class
	for all leginon data.  This can be initialized with keyword args
	as long as those keys are declared in the specific subclass of
	Data.  The special keyword 'initializer' can also be used
	to initialize with a dictionary.  If a key exists in both
	initializer and kwargs, the kwargs value is used.
	'''
	def validator(cls, value):
		if isinstance(value, DataReference):
			if value.dataclass is cls:
				return value
			else:
				raise ValueError('need instance of %s, got %s instead' % (cls, value.dataclass))
		if isinstance(value, cls):
			return value
		elif isinstance(value, UnknownData):
			return value
		else:
			raise ValueError('need instance of %s, got %s instead' % (cls, type(value),))
	validator = classmethod(validator)

	def __init__(self, initializer=None, **kwargs):
		####################################################
		# remember:  pickle and copy do not call __init__
		# when they regenerate an instance
		#  Below we have defined a special __deepcopy__
		#  so that the new copy gets a new dmid.
		#  I would still suggest not using deepcopy.
		#  Pickle is left alone because dmid should stay 
		#  the same.  However, DataManager should do some
		#  dmid tracking when getting remote data (via pickle)
		####################################################

		## dbid is the primary key for the database
		## If this is None, then this data has not
		## been inserted into the database
		self.dbid = None

		## Set timestamp to None to have the DB automatically set it
		self.timestamp = None

		## DataManager ID
		## this is None, then this data has not
		## been inserted into the DataManager
		self.dmid = None

		newdict.TypedDict.__init__(self)

		self.references = weakref.WeakValueDictionary()

		### insert into datamanager and sync my reference
		### this also needs to be done in cases where this
		### method is not called, like unpickling
		datamanager.cacheInsert(self)

		self.sync()

		# if initializer was given, update my values
		if initializer is not None:
			self.update(initializer)

		# additional keyword arguments also update my values
		# (overriding anything set by initializer)
		self.update(kwargs)

	## definining __reduce__ allows unpickler to call __init__ 	 
	## which is necessary to register data with datamanager 	 
	## This overrides OrderedDict.__reduce__ with the only difference
	## being that we don't want to dereference the items
	def __reduce__(self): 	 
		state = dict(self.__dict__) 	 
		del state['references']
		## giving the new object an initializer has a lot of 	 
		## duplicate information to what is given in the 	 
		## state dict, but it is necessary to get the dict 	 
		## base class to have its items set 	 
		initializer = dict(self.items(dereference=False)) 	 
		return (self.__class__, (initializer,), state)

	def insert(self, **kwargs):
		modulename = self.__module__
		db = connections.getConnection(modulename)
		db.insert(self, **kwargs)

	def query(self, **kwargs):
		modulename = self.__module__
		db = connections.getConnection(modulename)
		results = db.query(self, **kwargs)
		return results

	@classmethod
	def is_deletable(cls):
		'''
		Check if this class was defined as "deletable".
		This is true only if there is a class attribute "__deletable" and it
		is set to True.
		'''
		# have to generate mangled name of the "__deletable" attribute
		cls_name = cls.__name__
		deletable_attr = '_' + cls_name + '__deletable'
		if hasattr(cls, deletable_attr) and getattr(cls, deletable_attr):
			return True
		else:
			return False

	def delete(self, **kwargs):
		if not self.is_deletable():
			raise RuntimeError('Attempting to delete object that is not deletable')
		modulename = self.__module__
		db = connections.getConnection(modulename)
		db.delete(self, **kwargs)

	def close(self):
		modulename = self.__module__
		db = connections.getConnection(modulename)
		db.close()

	def direct_query(cls, dbid, **kwargs):
		modulename = cls.__module__
		db = connections.getConnection(modulename)
		result = db.direct_query(cls, dbid, **kwargs)
		return result
	direct_query = classmethod(direct_query)

	def update(self, other):
		'''
		needs to not dereference
		'''
		if isinstance(other, Data):
			for k in other.keys():
				self[k] = other.special_getitem(k, dereference=False)
		else:
			for k in other.keys():
				self[k] = other[k]
			#super(Data, self).update(other)

	def friendly_update(self, other):
		if isinstance(other, Data):
			for key in other.keys():
				try:
					self[key] = other.special_getitem(key, dereference=False)
				except KeyError:
					pass
		else:
			super(Data, self).friendly_update(other)

	def __copy__(self):
		return self.__class__(initializer=self)

	def copy(self):
		return self.__copy__()

	def setPersistent(self, dbid):
		self.dbid = dbid
		self.sync()
		datamanager.setPersistent(self)

	def items(self, dereference=True):
		original = super(Data, self).items()
		if not dereference:
			return original
		deref = []
		for key,value in original:
			if isinstance(value, DataReference):
				val = value.getData()
			else:
				val = value
			deref.append((key,val))
		return deref

	def values(self, dereference=True):
		original = super(Data, self).values()
		if not dereference:
			return original
		originalitems = super(Data, self).items()
		deref = []
		for key, value in originalitems:
			if isinstance(value, DataReference):
				val = value.getData()
			else:
				val = value
			deref.append(val)
		return deref

	def special_getitem(self, key, dereference, **kwargs):
		'''
		'''
		## actual value
		value = super(Data, self).__getitem__(key)

		## do we need to dereference
		if not dereference:
			return value
		if isinstance(value, DataReference):
			value = value.getData(**kwargs)
		if isinstance(value, newdict.FileReference):
			try:
				value = value.read()
			except:
				print 'Could not read file: %s' % (value,)
				value = None
			# This gives the option of keeping the FileReference rather
			# than the image data, for memory vs. speed tradeoff
			if datamanager.holdimages:
				# Replace FileReference with the actual array
				self.__setitem__(key, value, force=True)
		return value

	def __getitem__(self, key):
		return self.special_getitem(key, dereference=True)

	def __setitem__(self, key, value, force=False):
		'''
		'''
		if hasattr(self, 'dbid') and self.dbid is not None and not force:
			raise RuntimeError('persistent data cannot be modified, try to create a new instance instead, or use toDict() if a dict representation will do')
		if isinstance(value,Data):
			value = value.reference()
		super(Data, self).__setitem__(key, value)

	def toDict(self, noNone=False, dereference=False):
		return data2dict(self, noNone, dereference)

	def fromDict(cls, d):
		return dict2data(d, cls)

	fromDict = classmethod(fromDict)

	def reference(self):
		dr = DataReference(referent=self)
		self.references[id(dr)] = dr
		return dr

	def sync(self):
		'''
		synchronize my references with me
		becuase either dmid or dbid changed
		'''
		for dr in self.references.values():
			dr.sync(self)

	def nstr(self, value):
		if type(value) is numpy.ndarray:
			shape = value.shape
			if max(shape) > 2:
				s = 'array(shape: %s, type: %s)' % (shape,value.dtype)
				return s
		return str(value)

	def __str__(self):
		items = self.items(dereference=False)
		items = map(lambda x: (x[0], self.nstr(x[1])), items)
		items = map(': '.join, items)
		s = ', '.join(items)
		s = '{%s}' % (s,)
		return s
	__repr__ = __str__


## for queries, setting item to None will ignore item in query
## setting item to NULL(dataclass) will only return results where the item
## is specifically NULL in the database
def NULL(dataclass):
	d = dataclass()
	d.setPersistent(0)
	return d

