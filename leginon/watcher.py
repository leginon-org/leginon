#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import threading
import node, event
import Queue

class WatcherQueue(Queue.Queue):
	def __init__(self, callback, maxsize=0):
		self.callback = callback
		Queue.Queue.__init__(self, maxsize)

	def _put(self, item):
		Queue.Queue._put(self, item)
		if callable(self.callback):
			self.callback(self.queue)

	def _get(self):
		item = Queue.Queue._get(self)
		if callable(self.callback):
			self.callback(self.queue)
		return item

	def pause(self):
		self.mutex.acquire()

	def resume(self):
		self.mutex.release()

	def clear(self):
		if not self.esema.acquire(0):
			return
		self.mutex.acquire()
		was_full = self._full()
		self.queue = []
		if callable(self.callback):
			self.callback(self.queue)
		if was_full:
			self.fsema.release()
		self.mutex.release()

class Watcher(node.Node):
	'''
	Base class for a node that watches for data to be published
	and then retreives that data and does some processing on it.
	watchfor = class of PublishEvents to watch for
	locking determines how to handle a new event when a previous
	event is still being handled:
		0 = non blocking lock:  events are dropped if not handled
		1 = blocking lock:  events wait until previous is handled
		None = no lock:  each event handled in own thread
	'''

	eventinputs = node.Node.eventinputs + [event.PublishEvent]

	def __init__(self, id, session, managerlocation, watchfor=[event.PublishEvent], lockblocking=1, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.lockblocking = lockblocking
		self.handlelock = threading.Lock()

		self.eventqueue = WatcherQueue(self.eventcallback, 0)
		self.dataqueue = WatcherQueue(self.datacallback, 0)

		for eventclass in watchfor:
			self.addEventInput(eventclass, self.handleEvent)

		self.ignoreevents = False
		self.queueevents = False
		self.queuedata = False

	def eventcallback(self, value):
		pass

	def datacallback(self, value):
		pass

	## the event queue could be put in node.py or databinder.DataBinder
	def handleEvent(self, pubevent):
		if self.ignoreevents:
			return

		## get lock if necessary
		if self.lockblocking == 0:
			havelock = self.handlelock.acquire(0)
			if not havelock:
				## should we do this?
				#self.confirmEvent(pubevent)
				return
		elif self.lockblocking == 1:
			havelock = self.handlelock.acquire(1)
		else:
			havelock = 0

		self.processEvent(pubevent)

		## release lock if necessary
		if havelock:
			self.handlelock.release()

		self.confirmEvent(pubevent)

	def processEvent(self, pubevent):
		if self.queueevents:
			## put event in queue and get data later
			self.eventqueue.put(pubevent)
		else:
			## get data now
			self.getData(pubevent)

	def getData(self, pubevent):
		# need to ignore datahandlers, so check reference first
		ref = pubevent.special_getitem('data', dereference=False)
		if ref.datahandler:
			return
		newdata = pubevent['data']
		if newdata is not None:
			if self.queuedata:
				self.dataqueue.put(newdata)
			else:
				self.processData(newdata)

	def processData(self, datainstance):
		raise NotImplementedError()

	def processEventFromQueue(self, blocking=0):
		try:
			newevent = self.eventqueue.get(blocking)
			self.getData(newevent)
			return True
		except Queue.Empty:
			return False

	def processDataFromQueue(self, blocking=0):
		try:
			newdata = self.dataqueue.get(blocking)
			self.processData(newdata)
			return True
		except Queue.Empty:
			return False

