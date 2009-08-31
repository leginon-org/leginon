#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import threading
import node

class Watcher(node.Node):
	'''
	Base class for a node that watches for data to be published
	and then retreives that data and does some processing on it.
	watchfor = class of PublishEvents to watch for
	Only handles one event at a time.
	'''

	eventinputs = node.Node.eventinputs

	def __init__(self, id, session, managerlocation, watchfor=[], **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.handlelock = threading.Lock()

		for eventclass in watchfor:
			self.addEventInput(eventclass, self.handleEvent)

		self.ignoreevents = False

	def handleEvent(self, pubevent):
		if self.ignoreevents:
			return
		self.handlelock.acquire(1)
		self.processEvent(pubevent)
		self.handlelock.release()
		self.confirmEvent(pubevent)

	def processEvent(self, pubevent):
		#ref = pubevent.special_getitem('data', dereference=False)
		newdata = pubevent['data']
		if newdata is not None:
			self.processData(newdata)

	def processData(self, datainstance):
		raise NotImplementedError()
