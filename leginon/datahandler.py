import leginonobject
import data
import threading
import os
import shelve
import time

class DataHandler(leginonobject.LeginonObject):
	def __init__(self, id):
		leginonobject.LeginonObject.__init__(self, id)

	def query(self, id):
		raise NotImplementedError

	def insert(self, newdata):
		raise NotImplementedError

	def remove(self, id):
		raise NotImplementedError

	def ids(self):
		raise NotImplementedError

	def exit(self):
		pass

class DictDataKeeper(DataHandler):
	def __init__(self, id):
		DataHandler.__init__(self, id)
		self.datadict = {}
		self.datadictlock = threading.Lock()

	def query(self, id):
		self.datadictlock.acquire()
		try:
			result = self.datadict[id]
		except KeyError:
			result = None
		self.datadictlock.release()
		return result

	def insert(self, newdata):
		if not issubclass(newdata.__class__, data.Data):
			raise TypeError
		self.datadictlock.acquire()
		self.datadict[newdata.id] = newdata
		self.datadictlock.release()

	def remove(self, id):
		self.datadictlock.acquire()
		try:
			del self.datadict[id]
		except KeyError:
			pass
		self.datadictlock.release()

	def ids(self):
		self.datadictlock.acquire()
		result = self.datadict.keys()
		self.datadictlock.release()
		return result

class ShelveDataKeeper(DataHandler):
	def __init__(self, id, filename = None, path = '.'):
		DataHandler.__init__(self, id)

		# there is an issue if done too quick, try to open existing file
		# needs another attempt
		if filename == None:
			r = xrange(0, 2**16 - 1)
			files = os.listdir(path)
			for i in r:
				filename = "shelf.%d" % i
				if filename in files:
					filename = None
				else:
					break
			if filename == None:
				raise IOError
		self.filename = path + '/' + filename
		self.shelf = shelve.open(self.filename)
		self.shelflock = threading.Lock()

	def __del__(self):
		self.exit()

	def exit(self):
		os.remove(self.filename)

	def query(self, id):
		self.shelflock.acquire()
		try:
			result = self.shelf[str(id)]
		except KeyError:
			result = None
		self.shelflock.release()
		return result

	def insert(self, idata):
		if not issubclass(idata.__class__, data.Data):
			raise TypeError
		self.shelflock.acquire()
		self.shelf[str(idata.id)] = idata
		self.shelflock.release()

	def remove(self, id):
		self.shelflock.acquire()
		try:
			del self.shelf[str(id)]
		except KeyError:
			pass
		self.shelflock.release()

	def ids(self):
		self.shelflock.acquire()
		result = self.shelf.keys()
		self.shelflock.release()
		return result

# I'm reasonably sure this works, but it hasn't been fully tested
class CachedDictDataKeeper(DataHandler):
	def __init__(self, id, age = 600.0, timeout = 60.0, filename = None, path = '.'):
		DataHandler.__init__(self, id)

		self.datadict = {}
		self.lock = threading.Lock()

		if filename == None:
			r = xrange(0, 2**16 - 1)
			files = os.listdir(path)
			for i in r:
				filename = "shelf.%d" % i
				if filename in files:
					filename = None
				else:
					break
			if filename == None:
				raise IOError
		self.filename = path + '/' + filename
		self.shelf = shelve.open(self.filename)
		self.age = age
		self.timeout = timeout
		self.timer = threading.Timer(self.timeout, self.writeoutcache)
		self.timer.setDaemon(1)
		self.timer.start()

	def __del__(self):
		self.exit()

	def exit(self):
		os.remove(self.filename)

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
			if self.datadict[newdata.id]['cached']:
				del self.shelf[str(newdata.id)]
		except KeyError:
			pass
		self.datadict[newdata.id] = {'cached' : 0, 'ts' : time.time(), 'data' : newdata}
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
		self.timer.setDaemon(1)
		self.timer.start()
		now = time.time()
		for k in self.datadict.keys():
			if now - self.datadict[k]['ts'] > self.age:
				self.cache(k)

	def cache(self, id):
		if not self.datadict[id]['cached']:
			self.shelf[str(id)] = self.datadict[id]['data']
			self.datadict[id]['cached'] = 1
			del self.datadict[id]['data']

	def ids(self):
		self.lock.acquire()
		result = self.datadict.keys()
		self.lock.release()
		return result

class SimpleDataKeeper(CachedDictDataKeeper):
	pass

class DataBinder(DataHandler):
	def __init__(self, id):
		DataHandler.__init__(self, id)
		self.bindings = {}

	def insert(self, newdata):
		# now send data to a type specific handler function
		dataclass = newdata.__class__
		for bindclass in self.bindings:
			if issubclass(dataclass, bindclass):
				if self.bindings[bindclass]:
					args = (newdata,)
					for func in self.bindings[bindclass]:
#						try:
						apply(func, args)
#						except:
#							pass

	def setBinding(self, dataclass, func=None):
		'func must take data instance as first arg'
		if func == None:
			if dataclass in self.bindings:
				del self.bindings[dataclass]
		if dataclass in self.bindings:
				self.bindings[dataclass].append(func)
		else:
			self.bindings[dataclass] = [func]

