
import leginonobject
import event
import clientpull
import datahandler

class Node(leginonobject.LeginonObject):
	def __init__(self, managerloc = None):
		leginonobject.LeginonObject.__init__(self)
		self.eventhandler = event.EventHandler()
		self.datahandler = NodeDataHandler()
		self.managerloc = managerloc
		if managerloc:
			managerhost = managerloc['hostname']
			managerport = managerloc['event port']
			self.eventhandler.addClient(managerhost, managerport)

	def main(self):
		'''this is the node's parent method'''
		raise NotImplementedError()

	def announce(self, event):
		# mark event with info about the creator
		loc = self.location()
		hostname = loc['hostname']
		port = loc['event port']
		event.creator = (hostname, port)

		client = (self.managerloc['hostname'], self.managerloc['event port'])
		self.eventhandler.push(client, event)

	def publish(self, data):
		self.datahandler.insert(data)

	def research(self, dataid):
		return self.datahandler.pull(dataid)

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc['event port'] = self.eventhandler.port
		loc['data port'] = self.datahandler.port
		return loc

	def addEventIn(self, eventclass, func):
		self.eventhandler.addInput(eventclass, func)

	def delEventIn(self, eventclass):
		self.eventhandler.delInput(eventclass)

	def addEventOut(self, eventclass):
		self.eventhandler.addOutput(eventclass)
		
	def delEventOut(self, eventclass):
		self.eventhandler.delOutput(eventclass)


class NodeDataHandler(clientpull.Client, clientpull.Server):
	def __init__(self):
		clientpull.Server.__init__(self, datahandler.SimpleDataKeeper)
		loc = clientpull.Server.location(self)
		self.port = loc['datatcp port']

	def insert(self, newdata):
		self.datahandler.insert(newdata)
