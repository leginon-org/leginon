import leginonobject
import data
import threading
import os
import shelve
import time
import event
import random
import pickle

class DataHandler(leginonobject.LeginonObject):
	'''Base class for DataHandlers. Defines virtual functions.'''
	def __init__(self, id, session):
		leginonobject.LeginonObject.__init__(self, id, session)

	def query(self, id):
		'''Returns data with data ID.'''
		raise NotImplementedError

	def insert(self, newdata):
		'''Stores data.'''
		raise NotImplementedError

	def remove(self, id):
		'''Removes data with data ID.'''
		raise NotImplementedError

	def ids(self):
		'''Return data IDs of all stored data.'''
		raise NotImplementedError

class DictDataKeeper(DataHandler):
	'''Keep data in a dictionary.'''
	def __init__(self, id, session):
		DataHandler.__init__(self, id, session)
		self.datadict = {}
		self.lock = threading.Lock()

	def query(self, id):
		self.lock.acquire()
		try:
			result = self.datadict[id]
		except KeyError:
			result = None
		self.lock.release()
		return result

	def insert(self, newdata):
		if not issubclass(newdata.__class__, data.Data):
			raise TypeError
		self.lock.acquire()
		#self.datadict[newdata.id] = newdata
		self.datadict[newdata['id']] = newdata
		self.lock.release()

	def remove(self, id):
		self.lock.acquire()
		try:
			del self.datadict[id]
		except KeyError:
			pass
		self.lock.release()

	def ids(self):
		self.lock.acquire()
		result = self.datadict.keys()
		self.lock.release()
		return result

class TimeoutDataKeeper(DictDataKeeper):
	'''Keep remove data after a timeout.'''
	def __init__(self, id, session, timeout=300.0, interval=30.0):
		DictDataKeeper.__init__(self, id, session)
		self.timestampdict = {}
		self.setTimeout(timeout)
		self.setInterval(interval)

	def getTimeout(self):
		return self.timeout

	def setTimeout(self, timeout):
		self.timeout = timeout

	def getInterval(self):
		return self.interval

	def setInterval(self, interval):
		self.timer = threading.Timer(interval, self.clean)

	def query(self, id):
		self.lock.acquire()
		try:
			result = self.datadict[id]
			self.timestampdict[id] = time.time()
		except KeyError:
			result = None
		self.lock.release()
		return result

	def insert(self, newdata):
		if not issubclass(newdata.__class__, data.Data):
			raise TypeError
		self.lock.acquire()
		self.datadict[newdata['id']] = newdata
		self.timestampdict[newdata['id']] = time.time()
		self.lock.release()

	def remove(self, id):
		self.lock.acquire()
		try:
			del self.datadict[id]
			del self.timestampdict[id]
		except KeyError:
			pass
		self.lock.release()

	def ids(self):
		self.lock.acquire()
		result = self.datadict.keys()
		self.lock.release()
		return result

	def clean(self):
		now = time.time()
		for id, timestamp in self.timestampdict.items():
			if now - timestamp >= self.timeout:
				self.remove(id)

# I'm reasonably sure this works, but it hasn't been fully tested
class CachedDictDataKeeper(DataHandler):
	'''Keep data in a dictionary. Cache data on disk after timeout has elasped.'''
	def __init__(self, id, session, age = 600.0, timeout = 60.0, filename = None, path = '.'):
		DataHandler.__init__(self, id, session)

		self.datadict = {}
		self.lock = threading.Lock()

		self.openshelf(filename, path)

		self.age = age
		self.timeout = timeout
		self.timer = threading.Timer(self.timeout, self.writeoutcache)
		self.timer.setName('cache timer thread')
		self.timer.setDaemon(1)
		self.timer.start()

	def openshelf(self, filename, path):
		if filename is None:
			randfilename = "shelf.%d" % random.randrange(1024)
			self.filename = path + '/' + randfilename
			try:
				self.shelf = shelve.open(self.filename)
				self.shelflock = threading.Lock()
			except:
				self.openshelf(filename, path)
		else:
			self.filename = path + '/' + randfilename
			self.shelf = shelve.open(self.filename)
			self.shelflock = threading.Lock()

	def exit(self):
		try:
			os.remove(self.filename)
		except:
			print "failed to remove %s" % self.filename

	def query(self, id):
		self.lock.acquire()
		if self.datadict.has_key(id):
			if self.datadict[id]['cached']:
				self.datadict[id]['data'] = self.shelf[str(id)]
				del self.shelf[str(id)]
				self.datadict[id]['cached'] = 0
			self.datadict[id]['ts'] = time.time()
			result = self.datadict[id]['data']
		else:
			result = None
		self.lock.release()
		return result

	def insert(self, newdata):
		if not issubclass(newdata.__class__, data.Data):
			raise TypeError
		self.lock.acquire()
		try:
			#if self.datadict[newdata.id]['cached']:
			#	del self.shelf[str(newdata.id)]
			if self.datadict[newdata['id']]['cached']:
				del self.shelf[str(newdata['id'])]
		except KeyError:
			pass
		self.datadict[newdata['id']] = {'cached' : 0,
																		'ts' : time.time(),
																		'data' : newdata}
		self.lock.release()

	def remove(self, id):
		self.lock.acquire()
		if self.datadict.has_key(id):
			if self.datadict[id]['cached']:
				del self.shelf[str(id)]
			del self.datadict[id]
		self.lock.release()

	def writeoutcache(self):
		self.timer = threading.Timer(self.timeout, self.writeoutcache)
		self.timer.setName('cache timer thread')
		self.timer.setDaemon(1)
		self.timer.start()
		now = time.time()
		for k in self.datadict.keys():
			if now - self.datadict[k]['ts'] > self.age:
				self.cache(k)

	def cache(self, id):
		if not self.datadict[id]['cached']:
			# XXX This raises PicklingError for array type
			try:
				self.shelf[str(id)] = self.datadict[id]['data']
				self.datadict[id]['cached'] = 1
				del self.datadict[id]['data']
			except pickle.PicklingError, detail:
				print 'Warning: CachedDictDataKeeper could not pickle data: %s' % (id,)
				print 'PicklingError detail:', detail

	def ids(self):
		self.lock.acquire()
		result = self.datadict.keys()
		self.lock.release()
		return result

class DataBinder(DataHandler):
	'''Bind data to a function. Used for mapping Events to handlers.'''
	def __init__(self, id, session):
		DataHandler.__init__(self, id, session)
		## this is a mapping of data class to function
		## using list instead of dict to preserve order, and also
		## because there may be more than one function for every 
		## data class
		self.bindings = []

	def insert(self, newdata):
		# this could be threaded, but it would ruin the 'priority' thing
		# now send data to a type specific handler function
		dataclass = newdata.__class__
		args = (newdata,)
		for bindclass, func in self.bindings:
			if issubclass(dataclass, bindclass):
				apply(func, args)

	def addBinding(self, dataclass, func):
		'func must take data instance as first arg'
		binding = (dataclass, func)
		self.bindings.append(binding)

	def delBinding(self, dataclass=None, func=None):
		'''
		remove bindings
		if dataclass and/or func is None, that means wildcard
		'''
		# iterate on a copy, so we can delete from the original
		bindings = list(self.bindings)
		for binding in bindings:
			matchclass = matchfunc = False
			bindclass = binding[0]
			bindfunc = binding[1]
			if dataclass is bindclass or dataclass is None:
				matchclass = True
			if func is bindfunc or func is None:
				matchfunc = True

			if matchclass and matchfunc:
				self.bindings.remove(binding)
