import code
import leginonobject
import event
import datatransport
import datahandler

class Client(datatransport.Client):
	def __init__(self, hostname, port):
		datatransport.Client.__init__(self, hostname, port)

	def push(self, ievent):
		if isinstance(ievent, event.Event):
			datatransport.Client.push(self, ievent)
		else:
			raise InvalidEventError('event must be Event instance')

class NodeDataHandler(datahandler.SimpleDataKeeper, datahandler.DataBinder):
	def __init__(self):
		# this will call LeginonObject constructor twice I think
		datahandler.SimpleDataKeeper.__init__(self)
		datahandler.DataBinder.__init__(self)

	def insert(self, idata):
		if isinstance(idata, event.Event):
			datahandler.DataBinder.insert(self, idata)
		else:
			#raise InvalidEventError('event must be Event instance')
			datahandler.SimpleDataKeeper.insert(self, idata)

	# def query(self, id): is inherited from SimpleDataKeeper

	# used to be 'bind', changed to match datahandler.DataBinder
	def setBinding(self, eventclass, func):
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise InvalidEventError('eventclass must be Event subclass')

class Node(leginonobject.LeginonObject):
	def __init__(self, nodeid, managerloc = None, dh = NodeDataHandler, dhargs = (), clientclass = Client):
		leginonobject.LeginonObject.__init__(self)

		# added from eventhandler
		self.clients = {}
		self.distmap = {}
		self.registry = {'outputs':[], 'inputs':[]}

		self.server = datatransport.Server(dh, dhargs)
		self.clientclass = clientclass

		self.nodeid = nodeid
		self.managerloc = managerloc
		if managerloc:
			self.addManager()

	def addManager(self):
		managerhost = self.managerloc['hostname']
		managerport = self.managerloc['port']
		self.addEventClient('manager', managerhost, managerport)
		self.announce(event.NodeReadyEvent())

	def main(self):
		'''this is the node's parent method'''
		raise NotImplementedError()

	def announce(self, ievent):
		self.mark_data(ievent)
		self.clients['manager'].push(ievent)

	def publish(self, idata, eventclass=event.PublishEvent):
		self.mark_data(idata)
		if not issubclass(eventclass, event.PublishEvent):
			raise TypeError('PublishEvent subclass required')
		self.server.datahandler.insert(idata)
		self.announce(eventclass(idata.id))

	def mark_data(self, data):
		data.origin['id'] = self.nodeid
		data.origin['location'] = self.location()

	def research(self, creator, dataid):
		hostname, port = creator
		client = self.clientclass(hostname, port)
		return client.pull(dataid)

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc['port'] = self.server.location()['tcp port']
		return loc

	def interact(self):
		banner = "Starting interpreter for %s" % self.__class__
		readfunc = raw_input
		local = locals()
		code.interact(banner,readfunc,local)

  # down from here is from EventHandler
	def addEventClient(self, newid, hostname, port):
		self.clients[newid] = self.clientclass(hostname, port)

	def delEventClient(self, newid):
		if newid in self.clients:
			del self.clients[newid]

	def addEventInput(self, eventclass, func):
		self.server.datahandler.setBinding(eventclass, func)
		if eventclass not in self.registry['inputs']:
			self.registry['inputs'].append(eventclass)

	def delEventInput(self, eventclass):
		self.server.datahandler.setBinding(eventclass, None)
		if eventclass in self.registry['inputs']:
			self.registry['inputs'].remove(eventclass)

	def addEventOutput(self, eventclass):
		if eventclass not in self.registry['outputs']:
			self.registry['outputs'].append(eventclass)
		
	def delEventOutput(self, eventclass):
		if eventclass in self.registry['outputs']:
			self.registry['outputs'].remove(eventclass)

