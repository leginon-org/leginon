

import leginonobject, dataclient, dataserver
import eventhandler

class Node(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.dataserver = dataserver.DataServer()
		self.dataclient = dataclient.DataClient()
		self.eventhandler = eventhandler.EventHandler()

	def announce(self, event):
		self.eventhandler.send(eventinst)

	def publish(self, data):
		self.dataserver.insert(data)

	def research(self, dataid):
		return self.dataclient.get(dataid)
