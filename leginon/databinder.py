#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import Queue
from pyami import ordereddict
import threading
import datatransport
import leginondata
import remotecall

class DataBinder(object):
	'''Bind data to a function. Used for mapping Events to handlers.'''
	def __init__(self, node, logger, threaded=True, queueclass=Queue.Queue, tcpport=None):
		self.logger = logger
		self.server = datatransport.Server(self, logger, tcpport=tcpport)
		self.node = node
		## this is a mapping of data class to function
		## using list instead of dict to preserve order, and also
		## because there may be more than one function for every 
		## data class
		self.threaded = threaded
		self.bindings = ordereddict.OrderedDict()
		self.remotecallobjects = {}

		## a queue to hold incoming data, and a thread
		## to process data from the queue
		self.exitedevent = threading.Event()
		self.queue = queueclass()
		t = threading.Thread(name='data binder queue thread',
													target=self.handlerLoop)
		#t.setDaemon(1)
		t.start()

	def start(self):
		self.server.start()

	def exit(self):
		self.server.exit()
		self.queue.put(datatransport.ExitException())
		self.exitedevent.wait()

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
			if isinstance(item, datatransport.ExitException):
				self.logger.info('Handler loop exited')
				break
			try:
				if self.threaded:
					name = 'data binder handler thread'
					t = threading.Thread(name=name, target=self.handleData, args=(item,))
					t.setDaemon(1)
					self.logger.info('handling threaded')
					t.start()
				else:
					self.logger.info('handling unthreaded')
					self.handleData(item)
					self.logger.info('handled unthreaded')
			except Exception, e:
				self.logger.exception('handlerLoop exception')
		self.exitedevent.set()

	def handle(self, request):
		if isinstance(request, datatransport.Ping):
			return None
		elif isinstance(request, leginondata.Data):
			return self.insert(request)
		elif isinstance(request, remotecall.Request):
			return self.handleRemoteCall(request)
		else:
			self.logger.warning('unhandled request: %s' % request)
			return

	def handleRemoteCall(self, request):
		try:
			remotecallobject = self.remotecallobjects[request.node][request.name]
		except KeyError:
			estr = 'no remotecallobject %s for node %s' % (request.name, request.node)
			return ValueError(estr)
		try:
			return remotecallobject._handleRequest(request)
		except Exception, e:
			return e

	def addRemoteCallObject(self, nodename, name, remotecallobject):
		if nodename not in self.remotecallobjects:
			self.remotecallobjects[nodename] = {}
		self.remotecallobjects[nodename][name] = remotecallobject

	def removeRemoteCallObject(self, nodename, name):
		try:
			del self.remotecallobjects[nodename][name]
		except:
			raise ValueError('no remotecallobject %s for node %s' % (nodename, name))

	def insert(self, newdata):
		self.queue.put(newdata)
		self.logger.info('inserted in queue (class %s)'
											% (newdata.__class__.__name__,))

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
				except KeyError:
					continue
				for method in methods:
					self.logger.info('%s handling destination %s, method %s'
														% (dataclass, newdata['destination'], method))
					try:
						method(args)
					except:
						self.logger.exception('databinder exception while executing callback %s' % (method.__name__,))
						raise
	
	def addBinding(self, nodename, dataclass, method):
		'method must take data instance as first arg'
		try:
			nodes = self.bindings[dataclass]
			try:
				nodes[nodename].append(method)
			except KeyError:
				nodes[nodename] = [method]
		except KeyError:
			self.bindings[dataclass] = {nodename: [method]}
		self.logger.info('%s binding added for destination %s, method %s'
															% (dataclass, nodename, method))

	def delBinding(self, nodename, dataclass=None, method=None):
		if dataclass is None:
			dataclasses = self.bindings.keys()
		else:
			dataclasses = [dataclass]
		for dataclass in dataclasses:
			try:
				if method is None:
					del self.bindings[dataclass][nodename]
					if not self.bindings[dataclass]:
						del self.bindings[dataclass]
					self.logger.info('%s binding deleted for destination %s'
															% (dataclass, nodename))
				else:
					self.bindings[dataclass][nodename].remove(method)
					self.logger.info('%s binding deleted for destination %s, method %s'
															% (dataclass, nodename, method))
			except (KeyError, ValueError):
					self.logger.warning('%s binding deletion failed for destination %s'
															% (dataclass, nodename))


	def location(self):
		return self.server.location()
