
import code
import leginonobject
import event
import clientpull
import clientpush
import pushpull
import datahandler

class NodePushClient(clientpush.Client):
	def __init__(self, hostname, port):
		clientpush.Client.__init__(self, hostname, port)

	def push(self, ievent):
		if isinstance(ievent, event.Event):
			clientpush.Client.push(self, ievent)
		else:
			raise InvalidEventError('event must be Event instance')

class NodePullClient(clientpull.Client):
	def __init__(self, hostname, port):
		clientpull.Client.__init__(self, hostname, port)

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
	def __init__(self, nodeid, managerloc = None, dh = NodeDataHandler, dhargs = (), pushclientclass = NodePushClient, pullclientclass = NodePullClient):
		leginonobject.LeginonObject.__init__(self)

		# added from eventhandler
		self.clients = {}
		self.distmap = {}
		self.registry = {'outputs':[], 'inputs':[]}

#		self.pushserver = clientpush.Server(dh, dhargs)
#		self.pullserver = clientpull.Server(dh, dhargs)
		self.pushpullserver = pushpull.Server(dh, dhargs)
		self.pushclientclass = pushclientclass
		self.pullclientclass = pullclientclass

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
		self.pushpullserver.datahandler.insert(idata)
		self.announce(eventclass(idata.id))

	def mark_data(self, data):
		data.origin['id'] = self.nodeid
		data.origin['location'] = self.location()

	def research(self, creator, dataid):
		hostname, port = creator
		client = self.pullclientclass(hostname, port)
		return client.pull(dataid)

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc['port'] = self.pushpullserver.location()['datatcp port']
		return loc

	def interact(self):
		banner = "Starting interpreter for %s" % self.__class__
		readfunc = raw_input
		local = locals()
		code.interact(banner,readfunc,local)

  # down from here is from EventHandler
	def addEventClient(self, newid, hostname, port):
		self.clients[newid] = self.pushclientclass(hostname, port)

	def delEventClient(self, newid):
		if newid in self.clients:
			del self.clients[newid]

	def addEventInput(self, eventclass, func):
		self.pushpullserver.datahandler.setBinding(eventclass, func)
		if eventclass not in self.registry['inputs']:
			self.registry['inputs'].append(eventclass)

	def delEventInput(self, eventclass):
		self.pushpullserver.datahandler.setBinding(eventclass, None)
		if eventclass in self.registry['inputs']:
			self.registry['inputs'].remove(eventclass)

	def addEventOutput(self, eventclass):
		if eventclass not in self.registry['outputs']:
			self.registry['outputs'].append(eventclass)
		
	def delEventOutput(self, eventclass):
		if eventclass in self.registry['outputs']:
			self.registry['outputs'].remove(eventclass)

	def addEventDistmap(self, eventclass, from_node=None, to_node=None):
		if eventclass not in self.distmap:
			self.distmap[eventclass] = {}
		if from_node not in self.distmap[eventclass]:
			self.distmap[eventclass][from_node] = []
		if to_node not in self.distmap[eventclass][from_node]:
			self.distmap[eventclass][from_node].append(to_node)

	def distribute(self, ievent):
		'''push event to eventclients based on event class and source'''
		#print 'DIST', event.origin
		eventclass = ievent.__class__
		from_node = ievent.origin['id']
		done = []
		for distclass,fromnodes in self.distmap.items():
			if issubclass(eventclass, distclass):
				for fromnode in (from_node, None):
					if fromnode in fromnodes:
						for to_node in fromnodes[from_node]:
							if to_node:
								if to_node not in done:
									self.clients[to_node].push(ievent)
									done.append(to_node)
							else:
								for to_node in self.handler.clients:
									if to_node not in done:
										self.clients[to_node].push(ievent)
										done.append(to_node)

