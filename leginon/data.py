#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginonconfig
import leginonobject
import Numeric
import strictdict
import warnings
import types
import threading
import dbdatakeeper
import copy
import tcptransport
import weakref

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
		self.db = None
		### maybe dblock will fix some suspicious errors comming
		### from database access
		self.dblock = threading.RLock()
		self.location = None
		self.server = None

		## this lock should be used on access to everything below
		self.lock = threading.RLock()
		self.datadict = strictdict.OrderedDict()
		self.sizedict = {}
		self.dbcache = weakref.WeakValueDictionary()
		self.dmid = 0
		self.size = 0
		### end of things that need to be locked

		self.limitreached = False
		megs = 512
		self.maxsize = megs * 1024 * 1024

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
			### never remove datahandler
			if isinstance(self.datadict[dmid], DataHandler):
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
				if self.size <= self.maxsize:
					break
				if not self.limitreached:
					self.limitreached = True
					print '************************************************************************'
					print '***** DataManager size reached, removing data as needed ******'
					print '************************************************************************'
				self.remove(key)
		finally:
			self.lock.release()

	def getDataFromDB(self, dataclass, dbid):
		self.dblock.acquire()
		try:
			if self.db is None:
				self.db = dbdatakeeper.DBDataKeeper()
			### try to get data from dbcache before doing query
			try:
				dat = self.dbcache[dataclass,dbid]
			except KeyError:
				dat = self.db.direct_query(dataclass, dbid)
			return dat
		finally:
			self.dblock.release()

	def setPersistent(self, datainstance):
		if datainstance is None or datainstance.dbid is None:
			return
		dbid = datainstance.dbid
		dataclass = datainstance.__class__
		self.dblock.acquire()
		try:
			self.dbcache[dataclass,dbid] = datainstance
		finally:
			self.dblock.release()

	def getRemoteData(self, datareference):
		dmid = datareference.dmid
		location = {'hostname': dmid[0][0], 'port': dmid[0][1]}
		client = tcptransport.Client(location)
		datainstance = client.pull(datareference)
		### this is a new instance from a pickle
		### now register it locally
		self.insert(datainstance)
		datainstance.sync()
		return datainstance

	def getData(self, datareference):
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
				referent = self.getDataFromDB(dataclass, dbid)
			if referent is None:
				### try remote location
				if dmid is not None and dmid[0] != self.location:
					## in remote memory
					referent = self.getRemoteData(datareference)

		## if sill None, then must not exist anymore
		if referent is None:
			raise DataAccessError('Referenced data can not be found: %s' % (datareference,))

		return referent

	def query(self, datareference):
		### this is how tcptransport server accesses this data manager
		datainstance = self.getData(datareference)
		### in case of getData returning new DataReference:
		### or should we just return new DataReference and let
		### remote caller try again?
		if isinstance(datainstance, DataReference):
			datainstance = datainstance.getData()
		if isinstance(datainstance, DataHandler):
			datainstance = datainstance.getData()
		return datainstance

datamanager = DataManager()

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
			## Data or DataHandler
			if isinstance(referent, Data):
				self.dataclass = referent.__class__
			elif isinstance(referent, DataHandler):
				self.dataclass = referent.dataclass
				self.datahandler = True
			else:
				raise ValueError('referent must be either Data instance or DataHandler instance')
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
		sync my dmid and dbid with my referent, either directly
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

	def getData(self):
		referent = None
		#### Try weak reference, return referent if found
		if self.wr is not None:
			referent = self.wr()
			if isinstance(referent, DataHandler):
				referent = referent.getData()

		if referent is None:
			#### Try DataManager but do not return referent
			#### instead, return new reference to referent
			#### to signify that this reference is defunct
			goodref = False
			referent = datamanager.getData(self)
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


class DataDict(strictdict.TypedDict):
	'''
	A wrapper around TypedDict that adds a class method: typemap()
	This class method is used to create the type_map_or_seq argument
	that is normally passed during instantiation.  We then remove this
	argument from the init method.  In other words,
	we are hard coding the TypedDict types into the class and making
	it easy to override these types in a subclass.

	The typemap() method should return the same information as the 
	types() method already provided by TypedDict.  The difference is
	that (as of now) types() returns a KeyedDict and typedict() 
	returns a list of tuples mapping.  Maybe this can be unified soon.
	Another key difference is that since typemap() is a class method,
	we can inquire about the types of a DataDict's contents without
	actually having an instance.  This might be useful for something
	like a database interface that needs to create tables from these
	classes.
	'''
	def __init__(self, map_or_seq=None):
		strictdict.TypedDict.__init__(self, map_or_seq, type_map_or_seq=self.typemap())

	def typemap(cls):
		'''
		Returns the mapping of keys to types for this class.
		  [(key, type), (key, type), ...]
		Override this in subclasses to specialize the contents
		of this type of data.
		'''
		return []
	typemap = classmethod(typemap)

	def getFactory(self, valuetype):
		if valuetype is DataDict:
			f = valuetype
		else:
			f = strictdict.TypedDict.getFactory(self, valuetype)
		return f

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

class Data(DataDict, leginonobject.LeginonObject):
	'''
	Combines DataDict and LeginonObject to create the base class
	for all leginon data.  This can be initialized with keyword args
	as long as those keys are declared in the specific subclass of
	Data.  The special keyword 'initializer' can also be used
	to initialize with a dictionary.  If a key exists in both
	initializer and kwargs, the kwargs value is used.
	'''
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
		DataDict.__init__(self)

		## Database ID (primary key)
		## If this is None, then this data has not
		## been inserted into the database
		self.dbid = None

		## DataManager ID
		## this is None, then this data has not
		## been inserted into the DataManager
		self.dmid = None

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
		#if 'initializer' in kwargs:
		#	self.update(kwargs['initializer'])
		#	del kwargs['initializer']
		if initializer is not None:
			self.update(initializer)

		# additional keyword arguments also update my values
		# (overriding anything set by initializer)
		self.update(kwargs)

		leginonobject.LeginonObject.__init__(self)

	def update(self, other):
		'''
		needs to not dereference
		'''
		if isinstance(other, Data):
			for k in other.keys():
				self[k] = other.special_getitem(k, dereference=False)
		else:
			super(Data, self).update(other)

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
					self[key] = val
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
					self[key] = val
					# use new reference
					val = val.getData()
			else:
				val = value
			deref.append(val)
		return deref

	def special_getitem(self, key, dereference):
		'''
		'''
		## actual value
		value = super(Data, self).__getitem__(key)

		## do we need to dereference
		if not dereference:
			return value
		if isinstance(value, DataReference):
			value = value.getData()
			### if got new DataReference, replace existing one
			if isinstance(value, DataReference):
				# replace my reference with new one
				self.__setitem__(key, value, force=True)
				# use new reference
				value = value.getData()
		return value

	def __getitem__(self, key):
		return self.special_getitem(key, dereference=True)

	def __setitem__(self, key, value, force=False):
		'''
		'''
		if not hasattr(self, 'initdone'):
			super(Data, self).__setitem__(key, value)
			return

		if hasattr(self, 'dbid') and self.dbid is not None and not force:
			raise RuntimeError('persistent data cannot be modified, try to create a new instance instead, or use toDict() if a dict representation will do')
		if isinstance(value,Data):
			value = value.reference()
		super(Data, self).__setitem__(key, value)
		if self.resize(key, value):
			datamanager.resize(self)

	def getFactory(self, valuetype):
		## here we add the ability to validate the valuetypes
		## Data and DataReference

		# figure out if valuetype needs to be handled here
		myvaluetype = None
		if type(valuetype) == types.TypeType:
			if issubclass(valuetype, Data):
				myvaluetype = 'data'
			elif issubclass(valuetype, DataReference):
				myvaluetype = 'datareference'

		if myvaluetype == 'data':
			### if valuetype is Data, the value can be
			### instance of Data, DataReference, or UnknownData
			def f(value):
				if isinstance(value, DataReference):
					if valuetype == value.dataclass:
						return value
					else:
						raise ValueError('must by type %s' % (valuetype,))
				if isinstance(value, valuetype):
					return value
				elif isinstance(value, UnknownData):
					return value
				else:
					raise ValueError('must be type %s' % (valuetype,))
		elif myvaluetype == 'datareference':
			### if valuetype is DataReference, value must be
			### DataReference
			def f(value):
				if isinstance(value, valuetype):
					return value
				else:
					raise ValueError('must by type %s' % (valuetype,))
		else:
			f = DataDict.getFactory(self, valuetype)
		return f

	def toDict(self, noNone=False, dereference=False):
		return data2dict(self, noNone, dereference)

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
		elif type(value) is Numeric.ArrayType:
			return reduce(Numeric.multiply, value.shape) * value.itemsize()
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
		if type(value) is Numeric.ArrayType:
			shape = value.shape
			if max(shape) > 2:
				s = 'array(shape: %s, type: %s)' % (shape,value.typecode())
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

class DataHandler(object):
	'''
	Can be referenced just like Data, but the result of 
	reference.getData() is generated on the fly.

	Must be initialized with the type of data it will handle
	and the callback functions for getting and setting data
	'''
	def __init__(self, dataclass, getdata=None, setdata=None):
		self.dataclass = dataclass
		self._getData = getdata
		self._setData = setdata

		## should always be None for DataHandler
		self.dbid = None

		## DataManager ID
		## this is None, then this data has not
		## been inserted into the DataManager
		self.dmid = None

		self._reference = DataReference(referent=self)

		datamanager.insert(self)
		self.sync()

	def sync(self):
		'''
		synchronize my reference with me
		becuase either dmid or dbid changed
		'''
		self._reference.sync(self)

	def getData(self):
		return self._getData()

	def setData(self, value):
		self._setData(value)

	def reference(self):
		return self._reference

	def size(self):
		return 0

## for queries, setting item to None will ignore item in query
## setting item to NULL(dataclass) will only return results where the item
## is specifically NULL in the database
def NULL(dataclass):
	d = dataclass()
	d.setPersistent(0)
	return d

'''
## How to define a new leginon data type:
##   - Inherit Data or a subclass of Data.
##   - do not overload the __init__ method (unless you have a good reason)
##   - Override the typemap(cls) class method
##   - make sure typemap is defined as a classmethod:
##      typemap = classmethod(typemap)
##   - typemap() should return a sequence mapping, usually a list
##       of tuples:   [ (key, type), (key, type),... ]
## Examples:
class NewData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('stuff', int), ('thing', float), ]
		return t
	typemap = classmethod(typemap)

class OtherData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('newdata', NewData), ('mynum', int),]
		return t
	typemap = classmethod(typemap)

class MoreData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('newdata1', NewData), ('newdata2', NewData), ('otherdata', OtherData),]
		return t
	typemap = classmethod(typemap)

'''

class GroupData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('name', str),
					('description', str)]
		return t
	typemap = classmethod(typemap)
	
class UserData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('name', str),
					('full name', str),
					('group', GroupData)]
		return t
	typemap = classmethod(typemap)

class InstrumentData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('name', str),
					('description', str),
					('scope', str),
					('camera', str),
					('hostname', str),
					('camera size', int),
					('camera pixel size', float)]
		return t
	typemap = classmethod(typemap)

class SessionData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('name', str),
					('user', UserData),
					('instrument', InstrumentData),
					('image path', str),
					('comment', str)]
		return t
	typemap = classmethod(typemap)

class InSessionData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('session', SessionData)]
		return t
	typemap = classmethod(typemap)

class EMData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [ ('system time', float)]
		return t
	typemap = classmethod(typemap)

scope_params = [
	('magnification', int),
	('spot size', int),
	('intensity', float),
	('image shift', dict),
	('beam shift', dict),
	('defocus', float),
	('focus', float),
	('reset defocus', int),
	('screen current', float), 
	('beam blank', str), 
	('stigmator', dict),
	('beam tilt', dict),
	('corrected stage position', int),
	('stage position', dict),
	('holder type', str),
	('holder status', str),
	('stage status', str),
	('vacuum status', str),
	('column valves', str),
	('column pressure', float),
	('turbo pump', str),
	('high tension', int),
	('main screen position', str),
	('small screen position', str),
	('low dose', str),
	('low dose mode', str),
	('film stock', int),
	('film exposure number', int),
	('pre film exposure', bool),
	('post film exposure', bool),
	('film exposure', bool),
	('film exposure type', str),
	('film exposure time', float),
	('film manual exposure time', float),
	('film automatic exposure time', float),
	('film text', str),
	('film user code', str),
	('film date type', str),
]
camera_params = [
	('dimension', dict),
	('binning', dict),
	('offset', dict),
	('exposure time', float),
	('exposure type', str),
	('image data', strictdict.NumericArrayType),
	('inserted', bool),
	('dump', bool),
]

class ScopeEMData(EMData):
	def typemap(cls):
		t = EMData.typemap()
		t += scope_params
		return t
	typemap = classmethod(typemap)

class CameraEMData(EMData):
	def typemap(cls):
		t = EMData.typemap()
		t += camera_params
		return t
	typemap = classmethod(typemap)

class PresetTargetData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('emtarget', EMTargetData),
		      ('preset', str)]
		return t
	typemap = classmethod(typemap)

class DriftDetectedData(PresetTargetData):
	pass

class CameraConfigData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('dimension', dict),
			('binning', dict),
			('offset', dict),
			('exposure time', float),
			('exposure type', str),
			('correct', int),
			('auto square', int),
			('auto offset', int),
		]
		return t
	typemap = classmethod(typemap)

class LocationData(InSessionData):
	pass

class NodeLocationData(LocationData):
	def typemap(cls):
		t = LocationData.typemap()
		t += [ ('location', dict), ]
		t += [ ('class string', str), ]
		return t
	typemap = classmethod(typemap)

class NodeClassesData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [ ('nodeclasses', tuple), ]
		return t
	typemap = classmethod(typemap)

class DriftData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
		  ('rows', float),
		  ('cols', float),
		  ('rowmeters', float),
		  ('colmeters', float),
		  ('interval', float),
		]
		return t
	typemap = classmethod(typemap)

class CalibrationData(InSessionData):
	pass

class CameraSensitivityCalibrationData(CalibrationData):
	def typemap(cls):
		t = CalibrationData.typemap()
		t += [
			('high tension', int),
			('sensitivity', float),
		]
		return t
	typemap = classmethod(typemap)

class MagDependentCalibrationData(CalibrationData):
	def typemap(cls):
		t = CalibrationData.typemap()
		t += [
			('magnification', int),
			('high tension', int),
		]
		return t
	typemap = classmethod(typemap)

class PixelSizeCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		t = MagDependentCalibrationData.typemap()
		t += [ ('pixelsize', float), ('comment', str)]
		return t
	typemap = classmethod(typemap)

class EucentricFocusData(MagDependentCalibrationData):
	def typemap(cls):
		t = MagDependentCalibrationData.typemap()
		t += [ ('focus', float)]
		return t
	typemap = classmethod(typemap)

class MatrixCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		t = MagDependentCalibrationData.typemap()
		t += [ ('type', str), ('matrix', strictdict.NumericArrayType), ]
		return t
	typemap = classmethod(typemap)

class MoveTestData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('move pixels x', float),
			('move pixels y', float),
			('move meters x', float),
			('move meters y', float),
			('error pixels x', float),
			('error pixels y', float),
			('error meters x', float),
			('error meters y', float),
		]
		return t
	typemap = classmethod(typemap)

class MatrixMoveTestData(MoveTestData):
	def typemap(cls):
		t = MoveTestData.typemap()
		t += [
			('calibration', MatrixCalibrationData),
		]
	typemap = classmethod(typemap)

class ModeledStageMoveTestData(MoveTestData):
	def typemap(cls):
		t = MoveTestData.typemap()
		t += [
			('model', StageModelCalibrationData),
			('mag only', StageModelMagCalibrationData),
		]
	typemap = classmethod(typemap)

class StageModelCalibrationData(CalibrationData):
	def typemap(cls):
		t = CalibrationData.typemap()
		t += [
			('label', str),
			('axis', str),
			('period', float),
			('a', strictdict.NumericArrayType),
			('b', strictdict.NumericArrayType)
		]
		return t
	typemap = classmethod(typemap)

class StageModelMagCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		t = MagDependentCalibrationData.typemap()
		t += [ ('label', str), ('axis', str), ('angle', float), ('mean',float)]
		return t
	typemap = classmethod(typemap)

class StageMeasurementData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('label', str),
			('high tension', int),
			('magnification', int),
			('axis', str),
			('x',float),
			('y',float),
			('delta',float),
			('imagex',float),
			('imagey',float),
		]
		return t
	typemap = classmethod(typemap)

class PresetData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('number', int),
			('name', str),
			('magnification', int),
			('spot size', int),
			('intensity', float),
			('image shift', dict),
			('beam shift', dict),
			('defocus', float),
			('dimension', dict),
			('binning', dict),
			('offset', dict),
			('exposure time', int),
			('removed', int),
			('hasref', bool),
			('dose', float),
			('film', bool),
		]
		return t
	typemap = classmethod(typemap)

class NewPresetData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('name', str),
			('magnification', int),
			('spot size', int),
			('intensity', float),
			('image shift', dict),
			('beam shift', dict),
			('defocus', float),
			('dimension', dict),
			('binning', dict),
			('offset', dict),
			('exposure time', float),
		]
		return t
	typemap = classmethod(typemap)

class ImageData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('image', strictdict.NumericArrayType),
			('label', str),
			('filename', str),
			('list', ImageListData),
		]
		return t
	typemap = classmethod(typemap)

	def path(self):
		'''
		create a directory for this image file if it does not exist.
		return the full path of this directory.
		'''
		impath = self['session']['image path']
		impath = leginonconfig.mapPath(impath)
		leginonconfig.mkdirs(impath)
		return impath

	def filename(self):
		if not self['filename']:
			raise RuntimeError('"filename" not set for this image')
		return self['filename'] + '.mrc'

## this is not so important now that mosaics are created dynamically in
## DB viewer
class MosaicImageData(ImageData):
	'''Image of a mosaic'''
	def typemap(cls):
		t = ImageData.typemap()
		t += [ ('images', ImageListData), ]
		t += [ ('scale', float), ]
		return t
	typemap = classmethod(typemap)

class CameraImageData(ImageData):
	def typemap(cls):
		t = ImageData.typemap()
		t += [ ('scope', ScopeEMData), ('camera', CameraEMData), ]
		return t
	typemap = classmethod(typemap)

class CorrectedCameraImageData(CameraImageData):
	pass


## the camstate key is redundant (it's a subset of 'camera')
## but for now it helps to query the same way we used to
class CorrectorImageData(ImageData):
	def typemap(cls):
		t = ImageData.typemap()
		t += [ ('camstate', CorrectorCamstateData), ]
		return t
	typemap = classmethod(typemap)

class DarkImageData(CorrectorImageData):
	pass

class BrightImageData(CorrectorImageData):
	pass

class NormImageData(CorrectorImageData):
	pass

class MosaicTileData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('list', ImageListData),
			('image', AcquisitionImageData),
		]
		return t
	typemap = classmethod(typemap)

class StageLocationData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('removed', bool),
			('name', str),
			('comment', str),
			('x', float),
			('y', float),
			('z', float),
			('a', float),
			('xy only', bool),
		]
		return t
	typemap = classmethod(typemap)

class PresetImageData(CameraImageData):
	'''
	If an image was acquire using a certain preset, use this class
	to include the preset with it.
	'''
	def typemap(cls):
		t = CameraImageData.typemap()
		t += [ ('preset', PresetData), ]
		return t
	typemap = classmethod(typemap)

class PresetReferenceImageData(PresetImageData):
	'''
	This is a reference image for getting stats at different presets
	'''
	pass

class AcquisitionImageData(PresetImageData):
	def typemap(cls):
		t = PresetImageData.typemap()
		t += [ ('target', AcquisitionImageTargetData), ]
		t += [('grid', GridData)]
		return t
	typemap = classmethod(typemap)

class AcquisitionImageStatsData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('image', AcquisitionImageData),
			('min', float),
			('max', float),
			('mean', float),
			('stdev', float),
		]
		return t
	typemap = classmethod(typemap)

## actually, this has only some things in common with AcquisitionImageData
## but enough that it is easiest to inherit it
class FilmData(AcquisitionImageData):
	pass

class ProcessedAcquisitionImageData(ImageData):
	'''image that results from processing an AcquisitionImageData'''
	def typemap(cls):
		t = ImageData.typemap()
		t += [ ('source', AcquisitionImageData), ]
		return t
	typemap = classmethod(typemap)

class AcquisitionFFTData(ProcessedAcquisitionImageData):
	'''Power Spectrum of AcquisitionImageData'''
	pass

class ScaledAcquisitionImageData(ImageData):
	'''Small version of AcquisitionImageData'''
	pass

class ImageListData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [ ('targets', ImageTargetListData), ]
		return t
	typemap = classmethod(typemap)

class CorrectorPlanData(InSessionData):
	'''
	mosaic data contains data ID of images mapped to their 
	position and state.
	'''
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('camstate', CorrectorCamstateData),
			('bad_rows', tuple),
			('bad_cols', tuple),
			('clip_limits', tuple)
		]
		return t
	typemap = classmethod(typemap)

class CorrectorCamstateData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('dimension', dict),
			('binning', dict),
			('offset', dict),
		]
		return t
	typemap = classmethod(typemap)

class MosaicTargetData(InSessionData):
	'''
	this is an alias for an AcquisitionImageTargetData which is used
	to show a target in a full mosaic image
	'''
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
		  ('row', int),
		  ('column', int),
		  ('target', AcquisitionImageTargetData),
		]
		return t
	typemap = classmethod(typemap)

class GridData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('grid ID', int)]
		return t
	typemap = classmethod(typemap)

class ImageTargetData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			# pixel delta to target from state in row, column
		  ('delta row', int),
		  ('delta column', int),
		  ('scope', ScopeEMData),
		  ('camera', CameraEMData),
		  ('preset', PresetData),
		  ('type', str),
		  ('version', int),
		  ('number', int),
		  ('status', str),
		  ('grid', GridData),
		  ('list', ImageTargetListData),
		]
		return t
	typemap = classmethod(typemap)

class ImageTargetShiftData(InSessionData):
	'''
	This keeps a dict of target shifts for a set of images.
	'''
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('shifts', dict),
			('requested', bool),
		]
		return t
	typemap = classmethod(typemap)

class AcquisitionImageTargetData(ImageTargetData):
	def typemap(cls):
		t = ImageTargetData.typemap()
		t += [
		  ('image', AcquisitionImageData),
		  ## this could be generalized as total dose, from all
		  ## exposures on this target.  For now, this is just to
		  ## keep track of when we have done the melt ice thing.
		  ('pre_exposure', bool),
		]
		return t
	typemap = classmethod(typemap)

class ImageTargetListData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
		  ('label', str),
		  ('mosaic', bool),
		  ('image', AcquisitionImageData),
		]
		return t
	typemap = classmethod(typemap)

class FocuserResultData(InSessionData):
	'''
	results of doing autofocus
	'''
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
		  ('target', AcquisitionImageTargetData),
		  ('defocus', float),
		  ('stigx', float),
		  ('stigy', float),
		  ('min', float),
		  ('stig correction', int),
		  ('defocus correction', str),
		  ('pre manual check', bool),
		  ('post manual check', bool),
		  ('auto measured', bool),
		  ('auto status', str),
		]
		return t
	typemap = classmethod(typemap)

class EMTargetData(InSessionData):
	'''
	This is an ImageTargetData with deltas converted to new scope
	'''
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
		  ('preset', PresetData),
		  ('movetype', str),
		  ('image shift', dict),
		  ('stage position', dict),
		]
		return t
	typemap = classmethod(typemap)

class ApplicationData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('name', str),
					('version', int)]
		return t
	typemap = classmethod(typemap)

class NodeSpecData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('class string', str),
					('alias', str),
					('launcher alias', str),
					('dependencies', list),
					('application', ApplicationData)]
		return t
	typemap = classmethod(typemap)

class BindingSpecData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('event class string', str),
					('from node alias', str),
					('to node alias', str),
					('application', ApplicationData)]
		return t
	typemap = classmethod(typemap)

class DeviceGetData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('keys', list)]
		return t
	typemap = classmethod(typemap)

class DeviceData(Data):
	def typemap(cls):
		t = Data.typemap()
		return t
	typemap = classmethod(typemap)

# for testing
class DiaryData(InSessionData):
	'''
	User's diary entry
	'''
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
		  ('message', str),
		]
		return t
	typemap = classmethod(typemap)

class UIData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [('object', tuple),
			('value', strictdict.AnyObject)]
		return t
	typemap = classmethod(typemap)

class Request(type):
	def __new__(cls, dataclass):
		return type.__new__(cls, 'Request' + dataclass.__name__, (Data,),
												{'datamanager': datamanager})

	def _typePair(cls, typepair):
		if issubclass(typepair[1], Data):
			t = Request(typepair[1])
		else:
			t = bool
		return (typepair[0], t)

	def __init__(cls, dataclass):
		cls._typemap = map(cls._typePair, dataclass.typemap())
		cls._dataclass = dataclass
		cls.typemap = classmethod(lambda cls: cls._typemap)
		super(Request, cls).__init__('Request' + dataclass.__name__, (Data,),
																	{'datamanager': datamanager})

########## for testing

# new class of data
class MyData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('other', MyOtherData)]
		return t
	typemap = classmethod(typemap)

class MyOtherData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('stuff', int)]
		t += [('encore', str)]
		return t
	typemap = classmethod(typemap)
