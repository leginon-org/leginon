import leginonobject
import data
import threading
import Queue
import os
import shelve
import time
import event
import random
import pickle
import uidata
import strictdict
import copy

class DataHandler(leginonobject.LeginonObject):
	'''Base class for DataHandlers. Defines virtual functions.'''
	def __init__(self, id, session):
		leginonobject.LeginonObject.__init__(self, id)
		if session is None or isinstance(session, data.SessionData):
			self.session = session
		else:
			raise TypeError('session must be of proper type')

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
		self.lock = threading.RLock()

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

	def UI(self):
		return None

class SizedDataKeeper(DictDataKeeper):
	def __init__(self, id, session, maxsize=18.0):
		DictDataKeeper.__init__(self, id, session)
		self.maxsize = maxsize * 1024 * 1024 * 8
		self.datadict = strictdict.OrderedDict()
		self.size = 0

	def insert(self, newdata):
		if not issubclass(newdata.__class__, data.Data):
			raise TypeError
		self.lock.acquire()
		self.size += newdata.size()
		self.datadict[newdata['id']] = copy.deepcopy(newdata)
		self.clean()
		self.lock.release()

	def remove(self, dataid):
		self.lock.acquire()
		try:
			size = self.datadict[dataid].size()
			del self.datadict[dataid]
			self.size -= size
		except KeyError:
			pass
		self.lock.release()

	def clean(self):
		self.lock.acquire()
		while self.size > self.maxsize:
			try:
				removeid = self.datadict.keys()[0]
				print 'clean: removing', removeid, 'old size =', self.size/1024/1024/8.0, 'M',
				self.remove(removeid)
				print 'new size =', self.size/1024/1024/8.0, 'M'
			except IndexError:
				return
		self.lock.release()

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
		self._setTimeout(timeout)
		if hasattr(self, 'uitimeout'):
			self.uitimeout.set(self.getTimeout())

	def _setTimeout(self, timeout):
		self.timeout = timeout

	def getInterval(self):
		return self.interval

	def setInterval(self, interval):
		self._setInterval(interval)
		if hasattr(self, 'uiinterval'):
			self.uiinterval.set(self.getInterval())

	def _setInterval(self, interval):
		self.interval = interval
		self.timer = threading.Timer(self.interval, self.timerCallback)
		self.timer.start()

	def timeoutCallback(self, value):
		self._setTimeout(value)
		return self.getTimeout()

	def intervalCallback(self, value):
		self._setInterval(value)
		return self.getInterval()

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

	def timerCallback(self):
		self.clean()
		self.timer = threading.Timer(self.interval, self.timerCallback)
		self.timer.start()

	def clean(self):
		now = time.time()
		for id, timestamp in self.timestampdict.items():
			if now - timestamp >= self.timeout:
				self.remove(id)

	# not so great
	def UI(self):
		if not hasattr(self, 'uitimeout'):
			self.uitimeout = uidata.Integer('Timeout', self.getTimeout(),
																			'rw', callback=self.timeoutCallback)
		if not hasattr(self, 'uiinterval'):
			self.uiinterval = uidata.Integer('Interval', self.getInterval(),
																				'rw', callback=self.intervalCallback)
		uiclean = uidata.Method('Clean', self.clean)
		container = uidata.Container('Data Keeper')
		container.addObjects((self.uitimeout, self.uiinterval, uiclean))
		return container

class DataBinder(DataHandler):
	'''Bind data to a function. Used for mapping Events to handlers.'''
	def __init__(self, id, session):
		DataHandler.__init__(self, id, session)
		## this is a mapping of data class to function
		## using list instead of dict to preserve order, and also
		## because there may be more than one function for every 
		## data class
		self.bindings = []

		## a queue to hold incoming data, and a thread
		## to process data from the queue
		self.queue = Queue.Queue()
		t = threading.Thread(target=self.handlerLoop)
		t.setDaemon(1)
		t.start()

	def handlerLoop(self):
		'''
		This executes an infinite loop that calls the callback 
		function on every item that we dequeue.
		'''
		while 1:
			item = self.queue.get(block=True)
			try:
				self.handleData(item)
			except:
				self.printException()

	def insert(self, newdata):
		self.queue.put(newdata)

	def handleData(self, newdata):
		'''
		figure out which callback functions to execute on this data
		'''
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
