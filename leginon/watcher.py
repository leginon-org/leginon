#!/usr/bin/env python

import threading
import node, event
reload(node)

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
	def __init__(self, id, nodelocations, watchfor=event.PublishEvent, lockblocking=None):
		node.Node.__init__(self, id, nodelocations)
		self.watchfor = watchfor
		self.lockblocking = lockblocking
		self.lock = threading.RLock()

		self.addEventInput(self.watchfor, self.handleEvent)
		self.watchOn()

	def defineUserInterface(self):
		nui = node.Node.defineUserInterface(self)
		
		toggle = self.registerUIData('Watcher On', 'boolean', permissions = 'rw', default=1)
		toggle.set(self.uiWatchToggleCallback)

		myspec = self.registerUISpec('Watcher', (toggle,))
		myspec += nui

		return myspec

	def uiWatchToggleCallback(self, value=None):
		if value is not None:
			self.watchvalue = value
		if self.watchvalue:
			self.watchOn()
		else:
			self.watchOff()
		return self.watchvalue

	def die(self):
		node.Node.die(self)

	def watchOn(self):
		self.watch = 1

	def watchOff(self):
		self.watch = 0

	def handleEvent(self, pubevent):
		if not self.watch:
			return
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

	def getData(self, pubevent):
		dataid = pubevent.content
		newdata = self.researchByDataID(dataid)
		return newdata

	def processData(self, datainstance):
		raise NotImplementedError()

	def aaaa(self):
		pass


## an example of subclassing Watcher

class TestWatch(Watcher):
	def __init__(self, id, nodelocations):
		watchfor = event.PublishEvent
		lockblocking = 0
		Watcher.__init__(self, id, nodelocations, watchfor, lockblocking)

	def processData(self, newdata):
		numarray = newdata.content
		print 'processing newdata:'
		print numarray
