# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import leginonconfig
try:
	import numarray as Numeric
except:
	import Numeric
import newdict
import warnings
import types
import threading
import dbdatakeeper
import copy
import tcptransport
import weakref
import os

class DataError(Exception):
	pass
class DataManagerOverflowError(DataError):
	pass
class DataAccessError(DataError):
	pass
class DataDuplicateError(DataError):
	pass


#### version 1.3 database check
import sqldb
import sys
testdb = sqldb.connect()
cur = testdb.cursor()
try:
	cur.execute('describe UserData')
except:
	## most likely no UserData table
	pass
else:
	fields = cur.fetchall()
	for field in fields:
		if field[0] == 'DEF_id':
			continue
		if field[2] != 'YES':
			print '******************************************************'
			print 'Database not compatible with Leginon 1.3'
			print 'Backup your database, then run the datasync.py script.'
			print '******************************************************'
			sys.exit()


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
		self.dblock = threading.RLock()
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

	def getDataFromDB(self, dbhost, dbname, dataclass, dbid, **kwargs):
		self.dblock.acquire()
		try:
			dbkey = (dbhost, dbname)
			if dbkey in self.db:
				db = self.db[dbkey]
			else:
				name = dbdatakeeper.DBDataKeeper.__name__
				db = dbdatakeeper.DBDataKeeper(name, host=dbhost, db=dbname)
				self.db[dbkey] = db

			### try to get data from dbcache before doing query
			try:
				dat = self.dbcache[dbhost, dbname, dataclass, dbid]
			except KeyError:
				dat = db.direct_query(dataclass, dbid, **kwargs)
			return dat
		finally:
			self.dblock.release()

	def setPersistent(self, datainstance):
		if datainstance is None or datainstance.dbid is None:
			return
		dbhost = datainstance.dbhost
		dbname = datainstance.dbname
		dbid = datainstance.dbid
		dataclass = datainstance.__class__
		self.dblock.acquire()
		try:
			self.dbcache[dbhost, dbname, dataclass, dbid] = datainstance
		finally:
			self.dblock.release()

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
				dbhost = datareference.dbhost
				dbname = datareference.dbname
				referent = self.getDataFromDB(dbhost, dbname, dataclass, dbid, **kwargs)
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
		if isinstance(datainstance, DataHandler):
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
	def __init__(self, datareference=None, referent=None, dataclass=None, dmid=None, dbid=None, dbhost=None, dbname=None):
		self.datahandler = False
		self.wr = None
		if datareference is not None:
			self.dataclass = datareference.dataclass
			self.dmid = datareference.dmid
			self.dbid = datareference.dbid
			self.dbhost = datareference.dbhost
			self.dbname = datareference.dbname
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
			self.dbhost = dbhost
			self.dbname = dbname
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
			self.dbhost = o.dbhost
			self.dbname = o.dbname

	def getData(self, **kwargs):
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
		s = 'DataReference(%s), class: %s, dmid: %s, dbhost: %s, dbname: %s, dbid: %s' % (id(self), self.dataclass, self.dmid, self.dbhost, self.dbname, self.dbid)
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

		## Database info:  host, database, primary key
		## If these are None, then this data has not
		## been inserted into the database
		self.dbhost = None
		self.dbname = None
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

	def setPersistent(self, dbhost, dbname, dbid):
		self.dbhost = dbhost
		self.dbname = dbname
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
			else:
				# Keep FileReference.
				# Make sure FileReference does not hold image array:
				fileref.data = None
		return value

	def dumpArray(self, key):
		'''
		If the value for this item is an image array,
		replace it with the file reference to save memory.
		'''
		value = self.special_getitem(key, dereference=False)
		if type(value) is Numeric.ArrayType:
			if hasattr(value, 'fileref'):
				self.__setitem__(key, value.fileref, force=True)
			else:
				self.__setitem__(key, None)

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
		elif type(value) is Numeric.ArrayType:
			return value.size() * value.itemsize()
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
				s = 'array(shape: %s, type: %s)' % (shape,value.type())
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
##		typemap = classmethod(typemap)
##   - typemap() should return a sequence mapping, usually a list
##		of tuples:   [ (key, type), (key, type),... ]
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
		return Data.typemap() + (
			('name', str),
			('description', str)
		)
	typemap = classmethod(typemap)
	
class UserData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('full name', str),
			('group', GroupData)
		)
	typemap = classmethod(typemap)

class InstrumentData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('hostname', str),
			#('type', str),
		)
	typemap = classmethod(typemap)

class MagnificationsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('instrument', InstrumentData),
			('magnifications', list),
		)
	typemap = classmethod(typemap)

class MainScreenScaleData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('instrument', InstrumentData),
			('scale', float),
		)
	typemap = classmethod(typemap)

class SessionData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('user', UserData),
			('image path', str),
			('comment', str),
		)
	typemap = classmethod(typemap)

class InSessionData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', SessionData),
		)
	typemap = classmethod(typemap)

class QueueData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('label', str),
		)
	typemap = classmethod(typemap)

class EMData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('system time', float),
		)
	typemap = classmethod(typemap)

scope_params = (
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
	('main screen magnification', int),
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
)
camera_params = (
	('dimension', dict),
	('binning', dict),
	('offset', dict),
	('exposure time', float),
	('exposure type', str),
	('image data', newdict.MRCArrayType),
	('inserted', bool),
	('dump', bool),
	('pixel size', dict),
	('energy filtered', bool),
	('energy filter', bool),
	('energy filter width', float),
)

class ScopeEMData(EMData):
	def typemap(cls):
		return EMData.typemap() + scope_params + (
			('tem', InstrumentData),
		)
	typemap = classmethod(typemap)

class CameraEMData(EMData):
	def typemap(cls):
		return EMData.typemap() + camera_params + (
			('ccdcamera', InstrumentData),
		)
	typemap = classmethod(typemap)

class DriftMonitorRequestData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('emtarget', EMTargetData),
			('presetname', str),
			('threshold', float),
		)
	typemap = classmethod(typemap)

class DriftMonitorResultData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('status', str),
			('final', DriftData),
		)
	typemap = classmethod(typemap)

class CameraConfigData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('dimension', dict),
			('binning', dict),
			('offset', dict),
			('exposure time', float),
			('exposure type', str),
			('correct', int),
			('auto square', int),
			('auto offset', int),
		)
	typemap = classmethod(typemap)

class LocationData(InSessionData):
	pass

class NodeLocationData(LocationData):
	def typemap(cls):
		return LocationData.typemap()  + (
			('location', dict),
			('class string', str),
		)
	typemap = classmethod(typemap)

class NodeClassesData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('nodeclasses', tuple),
		)
	typemap = classmethod(typemap)

class DriftData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('rows', float),
			('cols', float),
			('rowmeters', float),
			('colmeters', float),
			('interval', float),
			('target', AcquisitionImageTargetData),
			('scope', ScopeEMData),
			('camera', CameraEMData),
		)
	typemap = classmethod(typemap)

class DriftDeclaredData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('system time', float),
			('type', str),
		)
	typemap = classmethod(typemap)

class TransformData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('rotation', float),
			('scale', float),
			('translation', dict),
		)
	typemap = classmethod(typemap)

class LogPolarTransformData(TransformData):
	def typemap(cls):
		return TransformData.typemap() + (
			('RS peak value', float),
			('T peak value', float),
		)
	typemap = classmethod(typemap)

class LogPolarGridTransformData(LogPolarTransformData):
	def typemap(cls):
		return LogPolarTransformData.typemap() + (
			('grid 1', GridData),
			('grid 2', GridData),
		)
	typemap = classmethod(typemap)

class CalibrationData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('tem', InstrumentData),
			('ccdcamera', InstrumentData),
		)
	typemap = classmethod(typemap)

class CameraSensitivityCalibrationData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('high tension', int),
			('sensitivity', float),
		)
	typemap = classmethod(typemap)

class MagDependentCalibrationData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('magnification', int),
			('high tension', int),
		)
	typemap = classmethod(typemap)

class PixelSizeCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		return MagDependentCalibrationData.typemap() + (
			('pixelsize', float),
			('comment', str),
		)
	typemap = classmethod(typemap)

class EucentricFocusData(MagDependentCalibrationData):
	def typemap(cls):
		return MagDependentCalibrationData.typemap() + (
			('focus', float),
		)
	typemap = classmethod(typemap)

class RotationCenterData(MagDependentCalibrationData):
	def typemap(cls):
		return MagDependentCalibrationData.typemap() + (
			('beam tilt', dict),
		)
	typemap = classmethod(typemap)

class MatrixCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		return MagDependentCalibrationData.typemap() + (
			('type', str),
			('matrix', newdict.DatabaseArrayType),
		)
	typemap = classmethod(typemap)

class MoveTestData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('move pixels x', float),
			('move pixels y', float),
			('move meters x', float),
			('move meters y', float),
			('error pixels x', float),
			('error pixels y', float),
			('error meters x', float),
			('error meters y', float),
		)
	typemap = classmethod(typemap)

class MatrixMoveTestData(MoveTestData):
	def typemap(cls):
		return MoveTestData.typemap() + (
			('calibration', MatrixCalibrationData),
		)
	typemap = classmethod(typemap)

class ModeledStageMoveTestData(MoveTestData):
	def typemap(cls):
		return MoveTestData.typemap() + (
			('model', StageModelCalibrationData),
			('mag only', StageModelMagCalibrationData),
		)
	typemap = classmethod(typemap)

class StageModelCalibrationData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('label', str),
			('axis', str),
			('period', float),
			('a', newdict.DatabaseArrayType),
			('b', newdict.DatabaseArrayType),
		)
	typemap = classmethod(typemap)

class StageModelMagCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		return MagDependentCalibrationData.typemap() + (
			('label', str),
			('axis', str),
			('angle', float),
			('mean',float),
		)
	typemap = classmethod(typemap)

class StageMeasurementData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('label', str),
			('high tension', int),
			('magnification', int),
			('axis', str),
			('x',float),
			('y',float),
			('delta',float),
			('imagex',float),
			('imagey',float),
		)
	typemap = classmethod(typemap)

class PresetData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('number', int),
			('name', str),
			('magnification', int),
			('spot size', int),
			('intensity', float),
			('image shift', dict),
			('beam shift', dict),
			('defocus', float),
			('defocus range min', float),
			('defocus range max', float),
			('dimension', dict),
			('binning', dict),
			('offset', dict),
			('exposure time', int),
			('removed', bool),
			('hasref', bool),
			('dose', float),
			('film', bool),
			('tem', InstrumentData),
			('ccdcamera', InstrumentData),
			('energy filter', bool),
			('energy filter width', float),
			('pre exposure', float),
			('skip', bool),
		)
	typemap = classmethod(typemap)

class NewPresetData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
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
		)
	typemap = classmethod(typemap)

class ImageData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', newdict.MRCArrayType),
			('label', str),
			('filename', str),
			('list', ImageListData),
			('queue', QueueData),
		)
	typemap = classmethod(typemap)

	def getpath(self):
		'''return image path for this image'''
		try:
			impath = self['session']['image path']
			impath = leginonconfig.mapPath(impath)
		except:
			raise
			impath = os.path.abspath(os.path.curdir)
		return impath

	def mkpath(self):
		'''
		create a directory for this image file if it does not exist.
		return the full path of this directory.
		'''
		impath = self.getpath()
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
		return ImageData.typemap() + (
			('images', ImageListData),
			('scale', float),
		)
	typemap = classmethod(typemap)

class CameraImageData(ImageData):
	def typemap(cls):
		return ImageData.typemap() + (
			('scope', ScopeEMData),
			('camera', CameraEMData),
			('correction channel', int),
		)
	typemap = classmethod(typemap)

class CameraImageStatsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', CameraImageData),
			('min', float),
			('max', float),
			('mean', float),
			('stdev', float),
		)
	typemap = classmethod(typemap)

class CorrectedCameraImageData(CameraImageData):
	pass

## the camstate key is redundant (it's a subset of 'camera')
## but for now it helps to query the same way we used to
class CorrectorImageData(ImageData):
	def typemap(cls):
		return ImageData.typemap() + (
			('camstate', CorrectorCamstateData),
			('tem', InstrumentData),
			('ccdcamera', InstrumentData),
			('scope', ScopeEMData),
			('channel', int),
		)
	typemap = classmethod(typemap)

class DarkImageData(CorrectorImageData):
	pass

class BrightImageData(CorrectorImageData):
	pass

class NormImageData(CorrectorImageData):
	pass

class MosaicTileData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('list', ImageListData),
			('image', AcquisitionImageData),
		)
	typemap = classmethod(typemap)

class StageLocationData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('removed', bool),
			('name', str),
			('comment', str),
			('x', float),
			('y', float),
			('z', float),
			('a', float),
			('xy only', bool),
		)
	typemap = classmethod(typemap)

class PresetImageData(CameraImageData):
	'''
	If an image was acquire using a certain preset, use this class
	to include the preset with it.
	'''
	def typemap(cls):
		return CameraImageData.typemap() + (
			('preset', PresetData),
		)
	typemap = classmethod(typemap)

class PresetReferenceImageData(PresetImageData):
	'''
	This is a reference image for getting stats at different presets
	'''
	pass

class AcquisitionImageData(PresetImageData):
	def typemap(cls):
		return PresetImageData.typemap() + (
			('target', AcquisitionImageTargetData),
			('emtarget', EMTargetData),
			('grid', GridData),
			('tilt series', TiltSeriesData),
			('version', int),
			('tiltnumber', int),
		)
	typemap = classmethod(typemap)

class AcquisitionImageStatsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', AcquisitionImageData),
			('min', float),
			('max', float),
			('mean', float),
			('stdev', float),
		)
	typemap = classmethod(typemap)

class AcquisitionImageDriftData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('old image', AcquisitionImageData),
			('new image', AcquisitionImageData),
			('rows', float),
			('columns', float),
			('system time', float),
		)
	typemap = classmethod(typemap)

## actually, this has only some things in common with AcquisitionImageData
## but enough that it is easiest to inherit it
class FilmData(AcquisitionImageData):
	pass

class ProcessedAcquisitionImageData(ImageData):
	'''image that results from processing an AcquisitionImageData'''
	def typemap(cls):
		return ImageData.typemap() + (
			('source', AcquisitionImageData),
		)
	typemap = classmethod(typemap)

class AcquisitionFFTData(ProcessedAcquisitionImageData):
	'''Power Spectrum of AcquisitionImageData'''
	pass

class ScaledAcquisitionImageData(ImageData):
	'''Small version of AcquisitionImageData'''
	pass

class ImageListData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('targets', ImageTargetListData),
		)
	typemap = classmethod(typemap)

class CorrectorPlanData(InSessionData):
	'''
	mosaic data contains data ID of images mapped to their 
	position and state.
	'''
	def typemap(cls):
		return InSessionData.typemap() + (
			('camstate', CorrectorCamstateData),
			('bad_rows', tuple),
			('bad_cols', tuple),
			('bad_pixels', tuple),
			('clip_limits', tuple),
			('ccdcamera', InstrumentData),
		)
	typemap = classmethod(typemap)

class CorrectorCamstateData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('dimension', dict),
			('binning', dict),
			('offset', dict),
		)
	typemap = classmethod(typemap)

class GridData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('grid ID', int),
			('insertion', int),
		)
	typemap = classmethod(typemap)

class ImageTargetData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
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
		)
	typemap = classmethod(typemap)

class AcquisitionImageTargetData(ImageTargetData):
	def typemap(cls):
		return ImageTargetData.typemap() + (
			('image', AcquisitionImageData),
			## this could be generalized as total dose, from all
			## exposures on this target.  For now, this is just to
			## keep track of when we have done the melt ice thing.
			('pre_exposure', bool),
		)
	typemap = classmethod(typemap)

class ReferenceTargetData(ImageTargetData):
	def typemap(cls):
		return ImageTargetData.typemap() + (
			('image', AcquisitionImageData),
		)
	typemap = classmethod(typemap)

class ReferenceRequestData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('preset', str),
		)
	typemap = classmethod(typemap)

class AlignZeroLossPeakData(ReferenceRequestData):
	pass

class MeasureDoseData(ReferenceRequestData):
	pass

class ImageTargetListData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('label', str),
			('mosaic', bool),
			('image', AcquisitionImageData),
			('queue', QueueData),
			('sublist', bool),
		)
	typemap = classmethod(typemap)

class DequeuedImageTargetListData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('queue', QueueData),
			('list', ImageTargetListData),
		)
	typemap = classmethod(typemap)

class FocuserResultData(InSessionData):
	'''
	results of doing autofocus
	'''
	def typemap(cls):
		return InSessionData.typemap() + (
			('target', AcquisitionImageTargetData),
			('defocus', float),
			('stigx', float),
			('stigy', float),
			('min', float),
			('stig correction', int),
			('defocus correction', str),
			('method', str),
			('status', str),
			('drift', DriftData),
		)
	typemap = classmethod(typemap)

class EMTargetData(InSessionData):
	'''
	This is an ImageTargetData with deltas converted to new scope
	'''
	def typemap(cls):
		return InSessionData.typemap() + (
			('preset', PresetData),
			('movetype', str),
			('image shift', dict),
			('beam shift', dict),
			('stage position', dict),
			('target', AcquisitionImageTargetData),
			('delta z', float),
		)
	typemap = classmethod(typemap)

class ApplicationData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('version', int),
		)
	typemap = classmethod(typemap)

class NodeSpecData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('class string', str),
			('alias', str),
			('launcher alias', str),
			('dependencies', list),
			('application', ApplicationData),
		)
	typemap = classmethod(typemap)

class BindingSpecData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('event class string', str),
			('from node alias', str),
			('to node alias', str),
			('application', ApplicationData),
		)
	typemap = classmethod(typemap)

class LaunchedApplicationData(InSessionData):
	'''
	created each time an application is launched
	'''
	def typemap(cls):
		return InSessionData.typemap() + (
			('application', ApplicationData),
			('launchers', list),
		)
	typemap = classmethod(typemap)

class DeviceGetData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('keys', list),
		)
	typemap = classmethod(typemap)

class DeviceData(Data):
	pass


class HoleFinderPrefsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', AcquisitionImageData),
			('user-check', bool),
			('skip-auto', bool),
			('queue', bool),
			('edge-lpf-on', bool),
			('edge-lpf-size', int),
			('edge-lpf-sigma', float),
			('edge-filter-type', str),
			('edge-threshold', float),
			('template-rings', tuple),
			('template-correlation-type', str),
			('template-lpf', float),
			('threshold-value', float),
			('threshold-method', str),
			('blob-border', int),
			('blob-max-number', int),
			('blob-max-size', int),
			('lattice-spacing', float),
			('lattice-tolerance', float),
			('stats-radius', float),
			('ice-zero-thickness', float),
			('ice-min-thickness', float),
			('ice-max-thickness', float),
			('ice-max-stdev', float),
			('template-on', bool),
			('template-focus', tuple),
			('template-acquisition', tuple),
			('template-diameter', int),
			('file-diameter', int),
			('template-filename', str),
		)
	typemap = classmethod(typemap)

class HoleDepthFinderPrefsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', AcquisitionImageData),
			('untilt-hole-image', AcquisitionImageData),
			('tilt-hole-image', AcquisitionImageData),
			('I-image', AcquisitionImageData),
			('I0-image', AcquisitionImageData),
			('edge-lpf-on', bool),
			('edge-lpf-size', int),
			('edge-lpf-sigma', float),
			('edge-filter-type', str),
			('edge-threshold', float),
			('template-rings', tuple),
			('template-correlation-type', str),
			('template-lpf', float),
			('template-tilt-axis', float),
			('threshold-value', float),
			('blob-border', int),
			('blob-max-number', int),
			('blob-max-size', int),
			('stats-radius', float),
			('ice-zero-thickness', float),
		)
	typemap = classmethod(typemap)

class HoleStatsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('prefs', HoleFinderPrefsData),
			('row', int),
			('column', int),
			('mean', float),
			('stdev', float),
			('thickness-mean', float),
			('thickness-stdev', float),
			('good', bool),
		)
	typemap = classmethod(typemap)

class HoleDepthStatsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('prefs', HoleDepthFinderPrefsData),
			('row', int),
			('column', int),
			('mean', float),
			('thickness-mean', float),
			('blobs-axis', float),
			('holedepth', float),
		)
	typemap = classmethod(typemap)

class SquareFinderPrefsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', MosaicImageData),
			('lpf-size', float),
			('lpf-sigma', float),
			('threshold', float),
			('border', int),
			('maxblobs', int),
			('minblobsize', int),
			('maxblobsize', int),
			('mean-min', int),
			('mean-max', int),
			('std-min', int),
			('std-max', int),
		)
	typemap = classmethod(typemap)

class SquareStatsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('prefs', SquareFinderPrefsData),
			('row', int),
			('column', int),
			('mean', float),
			('stdev', float),
			('good', bool),
		)
	typemap = classmethod(typemap)

class SettingsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('name', str),
			('isdefault', bool),
		)
	typemap = classmethod(typemap)

class ConnectToClientsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('clients', list),
			('localhost', str),
			('installation', str),
			('version', str),
		)
	typemap = classmethod(typemap)

class SetupWizardSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('session type', str),
			('selected session', str),
			('limit', bool),
			('n limit', int),
			('connect', bool),
		)
	typemap = classmethod(typemap)

class CameraSettingsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('dimension', dict),
			('offset', dict),
			('binning', dict),
			('exposure time', float),
		)
	typemap = classmethod(typemap)

class MosaicTargetMakerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('preset', str),
			('label', str),
			('radius', float),
			('overlap', float),
			('max targets', int),
			('max size', int),
			('mosaic center', str),
		)
	typemap = classmethod(typemap)

class AtlasTargetMakerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('preset', str),
			('label', str),
			('center', dict),
			('size', dict),
		)
	typemap = classmethod(typemap)

class PresetsManagerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('pause time', float),
			('xy only', bool),
			('stage always', bool),
			('cycle', bool),
			('optimize cycle', bool),
			('mag only', bool),
		)
	typemap = classmethod(typemap)

class CorrectorSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('instruments', dict),
			('n average', int),
			('despike', bool),
			('despike size', int),
			('despike threshold', float),
			('camera settings', CameraSettingsData),
			('combine', str),
			('clip min', float),
			('clip max', float),
			('channels', int),
		)
	typemap = classmethod(typemap)

class NavigatorSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('pause time', float),
			('move type', str),
			('check calibration', bool),
			('complete state', bool),
			('override preset', bool),
			('camera settings', CameraSettingsData),
			('instruments', dict),
			('precision', float),
			('max error', float),
			('cycle each', bool),
			('cycle after', bool),
		)
	typemap = classmethod(typemap)

class DriftManagerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('threshold', float),
			('pause time', float),
			('camera settings', CameraSettingsData),
		)
	typemap = classmethod(typemap)

class FFTMakerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('process', bool),
			('mask radius', float),
			('label', str),
		)
	typemap = classmethod(typemap)

class TargetFinderSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('wait for done', bool),
			('ignore images', bool),
			('queue', bool),
			('user check', bool),
			('queue drift', bool),
		)
	typemap = classmethod(typemap)

class ClickTargetFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('no resubmit', bool),
		)
	typemap = classmethod(typemap)

class MatlabTargetFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('module path', str),
		)
	typemap = classmethod(typemap)

class LowPassFilterSettingsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('on', bool),
			('size', int),
			('sigma', float),
		)
	typemap = classmethod(typemap)

class HoleFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('skip', bool),
			('image filename', str),
			('edge lpf', LowPassFilterSettingsData),
			('edge', bool),
			('edge type', str),
			('edge log size', int),
			('edge log sigma', float),
			('edge absolute', bool),
			('edge threshold', float),
			('template rings', list),
			('template type', str),
			('template lpf', LowPassFilterSettingsData),
			('threshold', float),
			('threshold method', str),
			('blobs border', int),
			('blobs max', int),
			('blobs max size', int),
			('lattice spacing', float),
			('lattice tolerance', float),
			('lattice hole radius', float),
			('lattice zero thickness', float),
			('ice min mean', float),
			('ice max mean', float),
			('ice max std', float),
			('focus hole', str),
			('target template', bool),
			('focus template', list),
			('acquisition template', list),
			('focus template thickness', bool),
			('focus stats radius', int),
			('focus min mean thickness', float),
			('focus max mean thickness', float),
			('focus max stdev thickness', float),
		)
	typemap = classmethod(typemap)

class HoleDepthFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('Hole Untilt filename', str),
			('Hole Tilt filename', str),
			('I filename', str),
			('I0 filename', str),
			('edge lpf', LowPassFilterSettingsData),
			('edge', bool),
			('edge type', str),
			('edge log size', int),
			('edge log sigma', float),
			('edge absolute', bool),
			('edge threshold', float),
			('template rings', list),
			('template type', str),
			('template lpf', LowPassFilterSettingsData),
			('tilt axis', float),
			('threshold', float),
			('blobs border', int),
			('blobs max', int),
			('blobs max size', int),
			('pickhole radius', float),
			('pickhole zero thickness', float),
		)
	typemap = classmethod(typemap)

class JAHCFinderSettingsData(HoleFinderSettingsData):
	def typemap(cls):
		return HoleFinderSettingsData.typemap() + (
			('template diameter', int),
			('file diameter', int),
			('template filename', str),
		)
	typemap = classmethod(typemap)

class RasterFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('publish polygon', bool),
			('image filename', str),
			('raster spacing', int),
			('raster angle', float),
			('raster center x', int),
			('raster center y', int),
			('raster center on image', bool),
			('raster limit', int),
			('select polygon', bool),
			('ice box size', float),
			('ice thickness', float),
			('ice min mean', float),
			('ice max mean', float),
			('ice max std', float),
			('focus convolve', bool),
			('focus convolve template', list),
			('focus constant template', list),
			('acquisition convolve', bool),
			('acquisition convolve template', list),
			('acquisition constant template', list),
		)
	typemap = classmethod(typemap)

class PolyFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('publish polygon', bool),
			('image filename', str),
			('raster spacing', int),
			('raster angle', float),
			('raster center x', int),
			('raster center y', int),
			('raster center on image', bool),
			('raster limit', int),
			('select polygon', bool),
			('ice box size', float),
			('ice thickness', float),
			('ice min mean', float),
			('ice max mean', float),
			('ice max std', float),
			('focus convolve', bool),
			('focus convolve template', list),
			('focus constant template', list),
			('acquisition convolve', bool),
			('acquisition convolve template', list),
			('acquisition constant template', list),
		)
	typemap = classmethod(typemap)

class RegionFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('image filename', str),
			('min region area', float),
			('max region area', float),
			('ve limit', float),
			('raster spacing', float),
			('raster angle', float),
		)
	typemap = classmethod(typemap)

class BlobFinderSettingsData(Data):
	def typemap(cls):
		return SettingsData.typemap() + (
			('on', bool),
			('border', int),
			('max', int),
			('min size', int),
			('max size', int),
			('min mean', float),
			('max mean', float),
			('min stdev', float),
			('max stdev', float),
		)
	typemap = classmethod(typemap)

class SquareFinderSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('lpf', LowPassFilterSettingsData),
			('blobs', BlobFinderSettingsData),
			('threshold', float),
		)
	typemap = classmethod(typemap)

class MosaicClickTargetFinderSettingsData(ClickTargetFinderSettingsData,
																					SquareFinderSettingsData):
	def typemap(cls):
		typemap = ClickTargetFinderSettingsData.typemap()
		typemap += SquareFinderSettingsData.typemap()
		typemap += (
			('calibration parameter', str),
			('scale image', bool),
			('scale size', int),
			('create on tile change', str),
			('min region area', float),
			('max region area', float),
			('axis ratio', float),
			('ve limit', float),
			('min threshold', float),
			('max threshold', float),
			('find section options', str),
			('section area', float),
			('section axis ratio', float),
			('max sections', int),
			('adjust section area', float),
			('section display', bool),
			('raster spacing', float),
			('raster angle', float),
			('autofinder', bool),
			('targetpreset', str),
			('raster overlap', float),
			('black on white', bool),
		)
		return typemap
	typemap = classmethod(typemap)

class TargetWatcherSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('process target type', str),
		)
	typemap = classmethod(typemap)

class AcquisitionSettingsData(TargetWatcherSettingsData):
	def typemap(cls):
		return TargetWatcherSettingsData.typemap() + (
			('pause time', float),
			('move type', str),
			('preset order', list),
			('correct image', bool),
			('display image', bool),
			('save image', bool),
			('wait for process', bool),
			('wait for rejects', bool),
			#('duplicate targets', bool),
			#('duplicate target type', str),
			('wait time', float),
			('iterations', int),
			('adjust for drift', bool),
			('mover', str),
			('move precision', float),
		)
	typemap = classmethod(typemap)

class FocusSequenceData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('node name', str),
			('sequence', list),
		)
	typemap = classmethod(typemap)

class FocusSettingData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('switch', bool),
			('node name', str),
			('name', str),
			('preset name', str),
 			('focus method', str),
			('tilt', float),
			('correlation type', str),
			('fit limit', float),
			('delta min', float),
			('delta max', float),
			('correction type', str),
			('stig correction', bool),
			('stig defocus min', float),
			('stig defocus max', float),
			('check drift', bool),
			('drift threshold', float),
			('reset defocus', bool),
		)
	typemap = classmethod(typemap)

class FocuserSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('melt preset', str),
			('melt time', float),
			('acquire final', bool),
		)
	typemap = classmethod(typemap)

class CalibratorSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('instruments', dict),
			('override preset', bool),
			('camera settings', CameraSettingsData),
			('correlation type', str),
		)
	typemap = classmethod(typemap)

class PixelSizeCalibratorSettingsData(CalibratorSettingsData):
	pass

class DoseCalibratorSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap() + (
			('beam diameter', float),
			('scale factor', float),
		)
	typemap = classmethod(typemap)

class GonModelerSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap() + (
			('measure axis', str),
			('measure points', int),
			('measure interval', float),
			('measure tolerance', float),
			('model axis', str),
			('model magnification', int),
			('model terms', int),
			('model mag only', bool),
			('model tolerance', float),
		)
	typemap = classmethod(typemap)

class BeamTiltCalibratorSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap() + (
			('defocus beam tilt', float),
			('first defocus', float),
			('second defocus', float),
			('stig beam tilt', float),
			('stig delta', float),
			('measure beam tilt', float),
			('correct tilt', bool),
			('settling time', float),
			('comafree beam tilt', float),
			('comafree misalign', float),
		)
	typemap = classmethod(typemap)

class MatrixCalibratorSettingsData(CalibratorSettingsData):
	def typemap(cls):
		parameters = ['image shift', 'beam shift', 'stage position']
		parameterstypemap = []
		for parameter in parameters:
			parameterstypemap.append(('%s tolerance' % parameter, float))
			parameterstypemap.append(('%s shift fraction' % parameter, float))
			parameterstypemap.append(('%s n average' % parameter, int))
			parameterstypemap.append(('%s interval' % parameter, float))
			parameterstypemap.append(('%s current as base' % parameter, bool))
			parameterstypemap.append(('%s base' % parameter, dict))
		return CalibratorSettingsData.typemap() + tuple(parameterstypemap)
	typemap = classmethod(typemap)

class ManualAcquisitionSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('camera settings', CameraSettingsData),
			('screen up', bool),
			('screen down', bool),
			('correct image', bool),
			('save image', bool),
			('loop pause time', float),
			('image label', str),
			('low dose', bool),
			('low dose pause time', float),
			('defocus1switch', bool),
			('defocus1', float),
			('defocus2switch', bool),
			('defocus2', float),
		)
	typemap = classmethod(typemap)

class IntensityMonitorSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('wait time', float),
			('iterations', int),
		)
	typemap = classmethod(typemap)

class RobotSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('column pressure threshold', float),
			('default Z position', float),
			('simulate', bool),
			('turbo on', bool),
			('grid clear wait', bool),
			('pause', bool),
			('grid tray', str),
		)
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

class LoggerRecordData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('name', str),
			('levelno', int),
			('levelname', str),
			('pathname', str),
			('filename', str),
			('module', str),
			('lineno', int),
			('created', float),
			('thread', int),
			('process', int),
			('message', str),
			('exc_info', str),
		)
	typemap = classmethod(typemap)

class DoseMeasurementData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('dose', float),
		)
	typemap = classmethod(typemap)

class TomographySettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('tilt min', float),
			('tilt max', float),
			('tilt start', float),
			('tilt step', float),
			('equally sloped', bool),
			('equally sloped n', int),
			('xcf bin', int),
			('run buffer cycle', bool),
			('align zero loss peak', bool),
			('measure dose', bool),
			('dose', float),
			('min exposure', float),
			('max exposure', float),
			('mean threshold', float),
			('collection threshold', float),
			('tilt pause time', float),
			('measure defocus', bool),
			('integer', bool),
			('intscale', float),
			('pausegroup', bool),
		)
	typemap = classmethod(typemap)

class TomographyPredictionData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('predicted position', dict),
			('predicted shift', dict),
			('position', dict),
			('correlation', dict),
			('correlated position', dict),
			('raw correlation', dict),
			('pixel size', float),
			#('image', TiltSeriesImageData),
			('image', AcquisitionImageData),
			('measured defocus', float),
			('measured fit', float),
		)
	typemap = classmethod(typemap)

class TiltSeriesData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('tilt min', float),
			('tilt max', float),
			('tilt start', float),
			('tilt step', float),
		)
	typemap = classmethod(typemap)

class InternalEnergyShiftData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('before', float),
			('after', float),
		)
	typemap = classmethod(typemap)

class TargetFilterSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('bypass', bool),
		)
	typemap = classmethod(typemap)

class CenterTargetFilterSettingsData(TargetFilterSettingsData):
	def typemap(cls):
		return TargetFilterSettingsData.typemap() + (
			('limit', int),
		)
	typemap = classmethod(typemap)

class RasterTargetFilterSettingsData(TargetFilterSettingsData):
	def typemap(cls):
		return TargetFilterSettingsData.typemap() + (
			('raster spacing', float),
			('raster angle', float),
			('raster preset', str),
			('raster movetype', str),
			('raster overlap', float),
			('raster width', float),
		)
	typemap = classmethod(typemap)

class PolygonRasterSettingsData(TargetFilterSettingsData):
	def typemap(cls):
		return TargetFilterSettingsData.typemap() + (
			('spacing', float),
			('angle', float),
		)
	typemap = classmethod(typemap)

class RCTAcquisitionSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('tilts', str),
			('stepsize', float),
			('sigma', float),
			('minsize', float),
			('maxsize', float),
			('blur', float),
			('sharpen', float),
			('drift threshold', float),
			('drift preset', str),
		)
	typemap = classmethod(typemap)

class ImageAssessorSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('format', str),
			('image directory', str),
			('outputfile', str),
		)
	typemap = classmethod(typemap)

class ReferenceSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('move type', str),
			('pause time', float),
			('interval time', float),
		)
	typemap = classmethod(typemap)

class TimerData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('node', str),
			('label', str),
			('t', float),
			('t0', TimerData),
			('diff', float),
		)
	typemap = classmethod(typemap)
