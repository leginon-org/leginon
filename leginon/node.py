
import leginonobject
import event
import clientpull

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
		print 'announce %s' % event
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

class NodeDataHandler(clientpull.Client, clientpull.Server):
	def __init__(self):
		clientpull.Server.__init__(self)
		loc = clientpull.Server.location(self)
		print 'NodeDataHandler Location: %s' % loc
		self.port = loc['datatcp port']

	def addClient(self, hostname, port):
		clientpull.Client.__init__(self, hostname, port)
