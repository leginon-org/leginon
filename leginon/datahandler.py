#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import extendedlogging
import Queue
import strictdict
import threading
import time
import uidata

class DataHandler(object):
	def __init__(self, loggername=None):
		self.logger = extendedlogging.getLogger(self.__class__.__name__, loggername)

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

	def exit(self):
		pass

class DictDataKeeper(DataHandler):
	'''Keep data in a dictionary.'''
	def __init__(self, loggername=None):
		DataHandler.__init__(self)
		self.datadict = {}
		self.lock = threading.RLock()

	def query(self, id):
		self.lock.acquire()
		try:
			result = self.datadict[id]
			self.logger.info('Queried for data %s' % (id,))
		except KeyError:
			result = None
			self.logger.info('Failed query for data %s' % (id,))
		self.lock.release()
		return result

	def insert(self, newdata):
		if not issubclass(newdata.__class__, data.Data):
			raise TypeError
		self.lock.acquire()
		self.datadict[newdata['id']] = newdata
		self.logger.info('Data %s inserted' % newdata['id'])
		self.lock.release()

	def remove(self, id):
		self.lock.acquire()
		try:
			del self.datadict[id]
			self.logger.info('Deleted data %s' % (id,))
		except KeyError:
			self.logger.info('Failed deletion of data %s' % (id,))
		self.lock.release()

	def ids(self):
		self.lock.acquire()
		result = self.datadict.keys()
		self.lock.release()
		return result

class SizedDataKeeper(DictDataKeeper):
	def __init__(self, maxsize=256.0, loggername=None):
		DictDataKeeper.__init__(self, loggername)
		self.maxsize = maxsize * 1024 * 1024
		self.datadict = strictdict.OrderedDict()
		self.size = 0

	def insert(self, newdata):
		if not issubclass(newdata.__class__, data.Data):
			self.datadict['UI server'] = newdata
			return
			#raise TypeError
		self.lock.acquire()

		try:
			size = newdata.size()
			self.size += size
			if newdata['id'] is not None:
				self.datadict[newdata['id']] = newdata
				self.logger.info(
					'Inserted data %s of size %d, data keeper size is now %d'
														% (newdata['id'], size, self.size))
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
				self.logger.info('Removed %s (size %d), data keeper size is now %d'
														% (dataid, size, self.size))
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
				self.logger.info(
					'data keeper size is %d, max size is %d, try to remove %s'
														% (self.size, self.maxsize, removekey))
				self.remove(removekey)
			self.logger.info('data keeper cleaned, new size is %d (max size is %d)'
												% (self.size, self.maxsize))
		finally:
			self.lock.release()

class ExitException(Exception):
	pass

class DataBinder(DataHandler):
	'''Bind data to a function. Used for mapping Events to handlers.'''
	def __init__(self, threaded=True, queueclass=Queue.Queue, loggername=None):
		DataHandler.__init__(self, loggername)
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

	def exit(self):
		self.queue.put(ExitException())

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
			if isinstance(item, ExitException):
				self.logger.info('Handler loop exited')
				break
			try:
				if self.threaded:
					name = 'data binder handler thread'
					t = threading.Thread(name=name, target=self.handleData, args=(item,))
					t.setDaemon(1)
					self.logger.info('Handling data threaded')
					t.start()
				else:
					self.logger.info('Handling data unthreaded')
					self.handleData(item)
					self.logger.info('Data handled unthreaded')
			except Exception, e:
				print 'handlerLoop exception'

	def insert(self, newdata):
		self.queue.put(newdata)
		try:
			id = newdata['id']
		except KeyError:
			id = ()
		self.logger.info('Data %s of class %s inserted in queue'
											% (id, newdata.__class__.__name__))

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
						self.logger.info('Destination %s handling %s with %s'
															% (newdata['destination'], dataclass, method))
						method(args)
				except KeyError:
					pass
	
	def addBinding(self, nodeid, dataclass, method):
		'method must take data instance as first arg'
		try:
			nodes = self.bindings[dataclass]
			try:
				nodes[nodeid].append(method)
			except KeyError:
				nodes[nodeid] = [method]
		except KeyError:
			self.bindings[dataclass] = {nodeid: [method]}
		self.logger.info('Added binding for %s handling %s with %s'
															% (nodeid, dataclass, method))

	def delBinding(self, nodeid, dataclass=None, method=None):
		if dataclass is None:
			dataclasses = self.bindings.keys()
		else:
			dataclasses = [dataclass]
		for dataclass in dataclasses:
			try:
				if method is None:
					del self.bindings[dataclass][nodeid]
					if not self.bindings[dataclass]:
						del self.bindings[dataclass]
				else:
					self.bindings[dataclass][nodeid].remove(method)
				self.logger.info('Deleted binding for %s handling %s'
													% (nodeid, dataclass))
			except (KeyError, ValueError):
				self.logger.info('Failed to delete binding for %s handling %s'
													% (nodeid, dataclass))

