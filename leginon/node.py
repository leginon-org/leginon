import code
import leginonobject
import event
import datatransport
import datahandler
import sys
if sys.platform == 'win32':
	sys.coinit_flags = 0

class Client(datatransport.Client):
	def __init__(self, location):
		datatransport.Client.__init__(self, location)

	def push(self, ievent):
		if isinstance(ievent, event.Event):
			datatransport.Client.push(self, ievent)
		else:
			raise event.InvalidEventError('event must be Event instance')

class NodeDataHandler(datahandler.SimpleDataKeeper, datahandler.DataBinder):
	def __init__(self):
		# this will call LeginonObject constructor twice I think
		datahandler.SimpleDataKeeper.__init__(self)
		datahandler.DataBinder.__init__(self)

	def insert(self, idata):
		if isinstance(idata, event.Event):
			datahandler.DataBinder.insert(self, idata)
		else:
			raise InvalidEventError('event must be Event instance')

	# use this to insert into your own server
	def _insert(self, idata):
		if isinstance(idata, event.Event):
			datahandler.DataBinder.insert(self, idata)
		else:
			datahandler.SimpleDataKeeper.insert(self, idata)

	# def query(self, id): is inherited from SimpleDataKeeper

	# used to be 'bind', changed to match datahandler.DataBinder
	def setBinding(self, eventclass, func):
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise event.InvalidEventError('eventclass must be Event subclass')

class Node(leginonobject.LeginonObject):
	def __init__(self, nodeid, managerloc = None, dh = NodeDataHandler, dhargs = (), clientclass = Client):
		leginonobject.LeginonObject.__init__(self)

		# added from eventhandler
		self.clients = {}
		self.registry = {'outputs':[], 'inputs':[]}

		self.server = datatransport.Server(dh, dhargs)
		self.clientclass = clientclass

		self.nodeid = nodeid
		if managerloc:
			self.addManager(managerloc)

	def addManager(self, loc):
		self.managerloc = loc
		self.addEventClient('manager', loc)
		self.announce(event.NodeReadyEvent())

	def main(self):
		'''this is the node's parent method'''
		raise NotImplementedError()

	def announce(self, ievent):
		self.mark_data(ievent)
		#print ievent.content
		self.clients['manager'].push(ievent)

	def publish(self, idata, eventclass=event.PublishEvent):
		self.mark_data(idata)
		if not issubclass(eventclass, event.PublishEvent):
			raise TypeError('PublishEvent subclass required')
		self.server.datahandler._insert(idata)
		self.announce(eventclass(idata.id))

	def publishRemote(self, nodeid, idata):
		# perhaps an event can be generated in this too
		self.clients[nodeid].insert(idata)

	def mark_data(self, data):
		data.origin['id'] = self.nodeid
		data.origin['location'] = self.location()

	def research(self, location, dataid):
		client = self.clientclass(location)
		return client.pull(dataid)

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc.update(self.server.location())
		return loc

	def interact(self):
		banner = "Starting interpreter for %s" % self.__class__
		readfunc = raw_input
		local = locals()
		code.interact(banner,readfunc,local)

  # down from here is from EventHandler
	def addEventClient(self, newid, location):
		self.clients[newid] = self.clientclass(location)

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

