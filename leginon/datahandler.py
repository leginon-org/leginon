#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

#import copy
import data
import Queue
import strictdict
import threading
import time
import uidata

class DataHandler(object):
	'''Base class for DataHandlers. Defines virtual functions.'''
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
	def __init__(self):
		DataHandler.__init__(self)
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
	def __init__(self, maxsize=256.0):
		DictDataKeeper.__init__(self)
		self.maxsize = maxsize * 1024 * 1024 * 8
		self.datadict = strictdict.OrderedDict()
		self.size = 0

	def insert(self, newdata):
		if not issubclass(newdata.__class__, data.Data):
			self.datadict['UI server'] = newdata
			return
			#raise TypeError
		self.lock.acquire()

		try:
			self.size += newdata.size()
			#self.datadict[newdata['id']] = copy.deepcopy(newdata)
			self.datadict[newdata['id']] = newdata
			self.clean()
		finally:
			self.lock.release()

	def remove(self, dataid):
		self.lock.acquire()
		try:
			try:
				size = self.datadict[dataid].size()
				del self.datadict[dataid]
				self.size -= size
			except (KeyError, AttributeError):
				pass
		finally:
			self.lock.release()

	def clean(self):
		self.lock.acquire()
		try:
			for removekey in self.datadict.keys():
				if self.size <= self.maxsize:
					break
				self.remove(removekey)
		finally:
			self.lock.release()

class TimeoutDataKeeper(DictDataKeeper):
	'''Keep remove data after a timeout.'''
	def __init__(self, timeout=300.0, interval=30.0):
		DictDataKeeper.__init__(self)
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
	def __init__(self, threaded=True, queueclass=Queue.Queue):
		DataHandler.__init__(self)
		## this is a mapping of data class to function
		## using list instead of dict to preserve order, and also
		## because there may be more than one function for every 
		## data class
		self.threaded = threaded
		self.bindings = strictdict.OrderedDict()

		## a queue to hold incoming data, and a thread
		## to process data from the queue
		self.queue = queueclass()
		t = threading.Thread(name='data binder queue thread',
													target=self.handlerLoop)
		t.setDaemon(1)
		t.start()

	def handlerLoop(self):
		'''
		This executes an infinite loop that dequeues items from
		our received data queue.
		Each of these dequeued items is then handled in a new thread
		by handleData.
		This seems risky to have this many threads created 
		in the same node, all acting on common data and not sure
		which data has proper locks.  For now it works.
		'''
		while True:
			item = self.queue.get(block=True)
			try:
				if self.threaded:
					t = threading.Thread(name='data binder handler thread',
																target=self.handleData, args=(item,))
					t.setDaemon(1)
					t.start()
				else:
					self.handleData(item)
			except Exception, e:
				print 'handlerLoop exception'

	def insert(self, newdata):
		self.queue.put(newdata)

	def handleData(self, newdata):
		'''
		figure out which callback methods to execute on this data
		'''
		dataclass = newdata.__class__
		args = newdata
		for bindclass in self.bindings.keys():
			if issubclass(dataclass, bindclass):
				try:
					methods = self.bindings[bindclass][newdata['destination']]
					for method in methods:
						method(args)
				except KeyError:
					pass
	
	def addBinding(self, dataclass, nodeid, method):
		'method must take data instance as first arg'
		try:
			nodes = self.bindings[dataclass]
			try:
				nodes[nodeid].append(method)
			except KeyError:
				nodes[nodeid] = [method]
		except KeyError:
			self.bindings[dataclass] = {nodeid: [method]}

	def delBinding(self, dataclass, nodeid, method=None):
		try:
			if method is None:
				del self.bindings[dataclass][nodeid]
				if not self.bindings[dataclass]:
					del self.bindings[dataclass]
			else:
				self.bindings[dataclass][nodeid].remove(method)
		except (KeyError, ValueError):
			pass

