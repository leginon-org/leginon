#!/usr/bin/env python

import threading
import node, event
import Queue
import uidata

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

	def __init__(self, id, session, nodelocations, watchfor=event.PublishEvent, lockblocking=None, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.watchfor = watchfor
		self.lockblocking = lockblocking
		self.handlelock = threading.Lock()
		self.datanow = 1

		self.eventqueue = Queue.Queue(0)
		self.dataqueue = Queue.Queue(0)

		self.addEventInput(self.watchfor, self.handleEvent)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		self.uiwatchflag = uidata.Boolean('Watching', True, 'rw')
		self.uidataqueueflag = uidata.Boolean('Data Queue', False, 'rw')
		processdatamethod = uidata.Method('Process from Queue',
																				self.uiProcessData)
		cleardatamethod = uidata.Method('Clear Queue', self.uiClearQueue)
		container = uidata.MediumContainer('Watcher')
		container.addObjects((self.uiwatchflag, self.uidataqueueflag,
														processdatamethod, cleardatamethod))
		self.uiserver.addObject(container)

	## the event queue could be put in node.py or datahandler.DataBinder
	def handleEvent(self, pubevent):
		if not self.uiwatchflag.get():
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
		if self.datanow:
			## get data now
			self.getData(pubevent)
		else:
			## put event in queue and get data later
			self.eventqueue.put(pubevent)

	def getData(self, pubevent):
		dataid = pubevent['dataid']
		newdata = self.researchByDataID(dataid)
		if self.uidataqueueflag.get():
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
			return 1
		except Queue.Empty:
			print 'Queue is empty, no data processed'
			return 0

	## maybe this should start a new thread?
	def uiProcessData(self):
		self.processDataFromQueue(blocking=0)

	def uiClearQueue(self):
		while 1:
			try:
				self.dataqueue.get(0)
			except Queue.Empty:
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
