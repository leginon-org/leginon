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

## manages weak references between data instances
## DataManager holds strong references to every Data instance that
## is created.  The memory size is restricted such that the first instances
## to be created are the first to be deleted from DataManager.
class DataManager(object):
	def __init__(self):
		## will connect to database before first query
		self.db = {}
		### maybe dblock will fix some suspicious errors comming
		### from database access
		self.dbcachelock = threading.RLock()
		self.location = None
		self.server = None

		## this lock should be used on access to everything below
		self.lock = threading.RLock()
		self.datadict = newdict.OrderedDict()
		self.sizedict = {}
		self.dbcache = weakref.WeakValueDictionary()
		self.dmid = 0
		self.size = 0
		### end of things that need to be locked

		self.limitreached = False
		megs = 300
		self.maxsize = megs * 1024 * 1024
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

	def newid(self):
		self.lock.acquire()
		try:
			self.dmid += 1
			new_dmid = (self.location, self.dmid)
			return new_dmid
		finally:
			self.lock.release()

	def insert(self, datainstance):
		self.lock.acquire()
		try:
			if self.server is None:
				self.startServer()

			## if datainstance has no dmid, give it one
			dmid = datainstance.dmid
			if dmid is None:
				dmid = self.newid()
				datainstance.dmid = dmid

			### if already managing this, then return
			if dmid in self.datadict:
				return

			## insert into datadict and sizedict
			self.datadict[dmid] = datainstance
			self.sizedict[dmid] = 0

			self.resize(datainstance)
		finally:
			self.lock.release()

	def remove(self, dmid):
		self.lock.acquire()
		try:
			if dmid not in self.datadict:
				return
			del self.datadict[dmid]
			self.size -= self.sizedict[dmid]
			del self.sizedict[dmid]
		finally:
			self.lock.release()

	def resize(self, datainstance):
		self.lock.acquire()
		try:
			dmid = datainstance.dmid
			dsize = datainstance.size()
			if dsize > self.maxsize:
				raise DataManagerOverflowError('new size is too big for DataManager')
			## check previous size
			if dmid in self.sizedict:
				oldsize = self.sizedict[dmid]
			else:
				oldsize = 0
			self.size = self.size - oldsize + dsize
			self.sizedict[dmid] = dsize
			if self.size > self.maxsize:
				self.clean()
		finally:
			self.lock.release()

	def clean(self):
		self.lock.acquire()
		try:
			for key in self.datadict.keys():
				if self.size <= self.maxsize/2:
					break
				if not self.limitreached:
					self.limitreached = True
					#print '************************************************************************'
					#print '***** DataManager size reached, removing data as needed ******'
					#print '************************************************************************'
				self.remove(key)
		finally:
			self.lock.release()

	def getDataFromDBCache(self, dataclass, dbid):
		self.dbcachelock.acquire()
		try:
			dat = self.dbcache[dataclass, dbid]
		finally:
			self.dbcachelock.release()
		return dat

	def getDataFromDB(self, dataclass, dbid, **kwargs):
		dbmodulename = dataclass.__module__
		db = connections.getConnection(dbmodulename)

		### try to get data from dbcache before doing query
		try:
			dat = self.getDataFromDBCache(dataclass, dbid)
		except KeyError:
			dat = db.direct_query(dataclass, dbid, **kwargs)
		return dat

	def setPersistent(self, datainstance):
		if datainstance is None or datainstance.dbid is None:
			return
		dbid = datainstance.dbid
		dataclass = datainstance.__class__
		self.dbcachelock.acquire()
		try:
			self.dbcache[dataclass, dbid] = datainstance
		finally:
			self.dbcachelock.release()

	def getRemoteData(self, datareference):
		dmid = datareference.dmid
		location = {'hostname': dmid[0][0], 'port': dmid[0][1]}
		client = tcptransport.Client(location)
		datainstance = client.send(datareference)
		### this is a new instance from a pickle
		### now register it locally
		self.insert(datainstance)
		datainstance.sync()
		return datainstance

	def getData(self, datareference, **kwargs):
		dataclass = datareference.dataclass
		referent = None
		dmid = datareference.dmid

		#### attempt to find referent in local datadict
		self.lock.acquire()
		try:
			if dmid in self.datadict:
				## in local memory
				referent = self.datadict[dmid]
				# access to datadict causes move to front
				del self.datadict[dmid]
				self.datadict[dmid] = referent
		finally:
			self.lock.release()

		#### not found locally, try external locations
		if referent is None:
			### try DB
			dbid = datareference.dbid
			if dbid is not None:
				## in database
				referent = self.getDataFromDB(dataclass, dbid, **kwargs)
			if referent is None:
				### try remote location
				if dmid is not None and dmid[0] != self.location:
					## in remote memory
					# TODO: kwargs
					referent = self.getRemoteData(datareference)

		## if sill None, then must not exist anymore
		if referent is None:
			raise DataAccessError('referenced data can not be found: %s' % (datareference,))

		return referent

	def query(self, datareference):
		# this is how socketstreamtransport server accesses this data manager
		datainstance = self.getData(datareference)
		### in case of getData returning new DataReference:
		### or should we just return new DataReference and let
		### remote caller try again?
		if isinstance(datainstance, DataReference):
			datainstance = datainstance.getData()
		return datainstance

	def handle(self, request):
		if isinstance(request, Data):
			return self.insert(request)
		else:
			return self.query(request)

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
		self.datahandler = False
		self.wr = None
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
		else:
			raise DataError('DataReference needs either DataReference, Data class, or Data instance for initialization')

	def __getstate__(self):
		## for pickling, do not include weak ref attribute
		state = dict(self.__dict__)
		state['wr'] = None
		return state

	def sync(self, o=None):
		'''
		sync my db info with my referent, either directly
		(if given the optional argument which is the referent)
		or through a weak reference to the referent
		'''
		if o is None:
			if self.wr is None:
				return
			o = self.wr()
		if o is not None:
			self.wr = weakref.ref(o)
			self.dmid = o.dmid
			self.dbid = o.dbid

	def getData(self, **kwargs):
		referent = None
		#### Try weak reference, return referent if found
		if self.wr is not None:
			referent = self.wr()

		if referent is None:
			#### Try DataManager but do not return referent
			#### instead, return new reference to referent
			#### to signify that this reference is defunct
			goodref = False
			referent = datamanager.getData(self, **kwargs)
		else:
			goodref = True

		### now we have a referent, or an excpetion was raised

		### if this was a bad reference, return a new one
		if goodref or self.datahandler:
			return referent
		else:
			return referent.reference()

	def __str__(self):
		s = 'DataReference(%s), class: %s, dmid: %s, dbid: %s' % (id(self), self.dataclass, self.dmid, self.dbid)
		if self.datahandler:
			s = s + ' (datahandler)'
		if self.wr is not None:
			o = self.wr()
			if o is not None:
				s = s + ' (weak ref to %s)' % (id(o),)
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
	for key, subtype in datatype.typemap():
		if d is None:
			continue
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

		## DataManager ID
		## this is None, then this data has not
		## been inserted into the DataManager
		self.dmid = None

		newdict.TypedDict.__init__(self)

		self._reference = DataReference(referent=self)
		
		self.__size = 2500
		k = self.keys()
		self.__sizedict = dict(zip(k, [0 for key in k]))

		### insert into datamanager and sync my reference
		### this also needs to be done in cases where this
		### method is not called, like unpickling
		datamanager.insert(self)
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
	## being that we don't wan to dereference the items
	def __reduce__(self): 	 
		state = dict(self.__dict__) 	 
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
				### if got new DataReference, first was bad
				if isinstance(val, DataReference):
					# replace my reference with new one
					#self[key] = val
					# !!! is this ok?
					self.__setitem__(key, value, force=True)
					# use new reference
					val = val.getData()
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
				### if got new DataReference, first was bad
				if isinstance(val, DataReference):
					# replace my reference with new one
					#self[key] = val
					# !!! is this ok?
					self.__setitem__(key, value, force=True)
					# use new reference
					val = val.getData()
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
			### if got new DataReference, replace existing one
			if isinstance(value, DataReference):
				# replace my reference with new one
				self.__setitem__(key, value, force=True)
				# use new reference
				value = value.getData(**kwargs)
		if isinstance(value, newdict.FileReference):
			fileref = value
			value = value.read()
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
		if self.resize(key, value):
			datamanager.resize(self)

	def toDict(self, noNone=False, dereference=False):
		return data2dict(self, noNone, dereference)

	def fromDict(cls, d):
		return dict2data(d, cls)

	fromDict = classmethod(fromDict)

	def size(self):
		return self.__size

	def resize(self, key, newvalue):
		oldsize = self.__sizedict[key]
		newsize = self.sizeof(newvalue)
		self.__sizedict[key] = newsize
		self.__size = self.__size - oldsize + newsize
		if oldsize == newsize:
			return False
		return True

	def sizeof(self, value):
		if value is None:
			## there is only one None object
			return 0
		elif type(value) is numpy.ndarray:
			return value.size * value.itemsize
		else:
			## this is my stupid estimate of size for other objects
			## We could also check for int, str, float, etc.
			## but this is easier
			## This should be something other than 0, but
			## for now it is 0 because otherwise we call 
			## datamanager.resize more often, especially 
			## if update() is called.  Maybe we need a better 
			## update() and friendly_update() that only
			## call datamanager.resize() once.
			return 0

	def reference(self):
		return self._reference

	def sync(self):
		'''
		synchronize my reference with me
		becuase either dmid or dbid changed
		'''
		self._reference.sync(self)

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

