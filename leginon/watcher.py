#!/usr/bin/env python

import threading
import node, event

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
	def __init__(self, id, managerlocation, watchfor=event.PublishEvent, lockblocking=None):
		node.Node.__init__(self, id, managerlocation)
		self.watchfor = watchfor
		self.lockblocking = lockblocking
		self.lock = threading.RLock()

		self.addEventInput(self.watchfor, self.handleEvent)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

	def handleEvent(self, pubevent):
		if self.lockblocking == 0:
			if not self.lock.acquire(blocking=0):
				return
			havelock = 1
		elif self.lockblocking == 1:
			self.lock.acquire(blocking=1)
			havelock = 1
		else:
			havelock = 0

		newdata = self.getData(pubevent)
		self.processData(newdata)

		if havelock:
			self.lock.release()

	def getData(self, publishevent):
		dataid = pubevent.content
		newdata = self.researchByDataID(dataid)
		return newdata

	def processData(self, datainstance):
		raise NotImplementedError()


## an example of subclassing Watcher

class TestWatch(Watcher):
	def __init__(self, id, managerlocation):
		watchfor = event.PublishEvent
		lockblocking = 0
		watcher.Watcher.__init__(self, id, managerlocation, watchfor, lockblocking)


	def processData(self, newdata):
		print 'processing newdata %s' % newdata
