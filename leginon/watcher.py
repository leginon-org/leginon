#!/usr/bin/env python

import threading
import node, event
import Queue

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
	def __init__(self, id, nodelocations, watchfor=event.PublishEvent, lockblocking=None, **kwargs):
		node.Node.__init__(self, id, nodelocations, **kwargs)
		self.watchfor = watchfor
		self.lockblocking = lockblocking
		self.handlelock = threading.Lock()
		self.datanow = 1

		self.eventqueue = Queue.Queue(0)
		self.dataqueue = Queue.Queue(0)

		self.addEventInput(self.watchfor, self.handleEvent)

	def defineUserInterface(self):
		nui = node.Node.defineUserInterface(self)
		
		self.watchtoggle = self.registerUIData('Watcher On', 'boolean', permissions = 'rw', default=1)
		self.dataqueuetoggle = self.registerUIData('Data Queue On', 'boolean', permissions='rw', default=0)
		procdata = self.registerUIMethod(self.uiProcessData, 'Process Data From Queue', ())
		cleardata = self.registerUIMethod(self.uiClearQueue, 'Clear Data Queue', ())

		myspec = self.registerUISpec('Watcher', (self.watchtoggle,self.dataqueuetoggle, procdata))
		myspec += nui

		return myspec

	def die(self, ievent=None):
		node.Node.die(self)

	## the event queue could be put in node.py or datahandler.DataBinder
	def handleEvent(self, pubevent):
		if not self.watchtoggle.get():
			return

		## get lock if necessary
		if self.lockblocking == 0:
			havelock = self.handlelock.acquire(0)
			if not havelock:
				return
		elif self.lockblocking == 1:
			havelock = self.handlelock.acquire(1)
		else:
			havelock = 0

		try:
			self.processEvent(pubevent)
		except:
			print 'event %s not processed' % (pubevent,)
			
		## release lock if necessary
		if havelock:
			self.handlelock.release()

	def processEvent(self, pubevent):
		if self.datanow:
			## get data now
			self.getData(pubevent)
		else:
			## put event in queue and get data later
			self.eventqueue.put(pubevent)

	def getData(self, pubevent):
		dataid = pubevent.content
		newdata = self.researchByDataID(dataid)
		if self.dataqueuetoggle.get():
			self.dataqueue.put(newdata)
		else:
			self.processData(newdata)

	def processData(self, datainstance):
		raise NotImplementedError()

	def processDataFromQueue(self, blocking=0):
		if blocking:
			print 'watcher blocking until data ready in queue'
		try:
			newdata = self.dataqueue.get(blocking)
			self.processData(newdata)
		except Queue.Empty:
			print 'Queue is empty, no data processed'

	## maybe this should start a new thread?
	def uiProcessData(self):
		self.processDataFromQueue(blocking=0)
		return ''

	def uiClearQueue(self):
		while 1:
			try:
				self.dataqueue.get(0)
			except Queue.Empty:
				return ''

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
