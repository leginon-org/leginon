
import code
import leginonobject
import event
import clientpull
import datahandler

class Node(leginonobject.LeginonObject):
	def __init__(self, nodeid, managerloc = None):
		leginonobject.LeginonObject.__init__(self)
		self.eventhandler = event.EventHandler()
		self.datahandler = NodeDataHandler()
		self.nodeid = nodeid
		self.managerloc = managerloc
		if managerloc:
			self.addManager()

	def addManager(self):
		managerhost = self.managerloc['hostname']
		managerport = self.managerloc['event port']
		self.addEventClient('manager', managerhost, managerport)
		self.announce(event.NodeReadyEvent())

	def main(self):
		'''this is the node's parent method'''
		raise NotImplementedError()

	def announce(self, event):
		self.mark_data(event)
		self.eventhandler.push('manager', event)

	def publish(self, data, eventclass=event.PublishEvent):
		self.mark_data(data)
		if not issubclass(eventclass, event.PublishEvent):
			raise TypeError('PublishEvent subclass required')
		self.datahandler.insert(data)
		self.announce(eventclass(data.id))

	def mark_data(self, data):
		data.origin['id'] = self.nodeid
		data.origin['location'] = self.location()

	def research(self, creator, dataid):
		newdata = self.datahandler.query(creator, dataid)
		return newdata

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc['event port'] = self.eventhandler.port
		loc['data port'] = self.datahandler.port
		return loc

	def addEventClient(self, clientid, host, port):
		self.eventhandler.addClient(clientid, host, port)

	def addEventIn(self, eventclass, func):
		self.eventhandler.addInput(eventclass, func)

	def delEventIn(self, eventclass):
		self.eventhandler.delInput(eventclass)

	def addEventOut(self, eventclass):
		self.eventhandler.addOutput(eventclass)
		
	def delEventOut(self, eventclass):
		self.eventhandler.delOutput(eventclass)

	def interact(self):
		banner = "Starting interpreter for %s" % self.__class__
		readfunc = raw_input
		local = locals()
		code.interact(banner,readfunc,local)


class NodeDataHandler(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.server = clientpull.Server(datahandler.SimpleDataKeeper)
		self.port = self.server.location()['datatcp port']

	def insert(self, newdata):
		self.server.datahandler.insert(newdata)

	def query(self, creator, dataid):
		hostname,port = creator
		client = clientpull.Client(hostname, port)
		return client.pull(dataid)

