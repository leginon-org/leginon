import threading
import code
import leginonobject
import event
import datatransport
import datahandler
import interface
import sys
import copy
import time

if sys.platform == 'win32':
	sys.coinit_flags = 0

class Client(datatransport.Client):
	def __init__(self, id, loc):
		datatransport.Client.__init__(self, id, loc)

	def push(self, idata):
#		if isinstance(idata, event.Event):
		datatransport.Client.push(self, idata)
#		else:
#			raise event.InvalidEventError('event must be Event instance')

class NodeDataHandler(datahandler.SimpleDataKeeper, datahandler.DataBinder):
	def __init__(self, id):
		# this will call LeginonObject constructor twice I think
		datahandler.SimpleDataKeeper.__init__(self, id)
		datahandler.DataBinder.__init__(self, id)

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
			datahandler.SimpleDataKeeper.insert(self, copy.deepcopy(idata))

	# def query(self, id): is inherited from SimpleDataKeeper

	# used to be 'bind', changed to match datahandler.DataBinder
	def setBinding(self, eventclass, func):
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise event.InvalidEventError('eventclass must be Event subclass')

class Node(leginonobject.LeginonObject):
	def __init__(self, id, managerloc = None, dh = NodeDataHandler, dhargs = (), clientclass = Client):
		leginonobject.LeginonObject.__init__(self, id)

		self.clients = {}

		# this was added for interface server
		self.clientlist = []
		self.clientdict = {}

		self.registry = {'outputs':[], 'inputs':[]}

		self.server = datatransport.Server(self.ID(), dh, dhargs)
		self.clientclass = clientclass

		self.uiserver = interface.Server()
		self.defineUserInterface()

		if managerloc:
			self.addManager(managerloc)

		self.addEventOutput(event.PublishEvent)
		self.addEventOutput(event.UnpublishEvent)
		self.addEventOutput(event.NodeAvailableEvent)
		self.addEventOutput(event.NodeUnavailableEvent)
		self.addEventInput(event.KillEvent, self.die)

	def __del__(self):
		#self.exit()
		pass

	def die(self, ievent):
		sys.exit()

	def defineUserInterface(self):
		'''
		This is where you register methods that can be accessed
		by a user interface through XML-RPC
		To register a method use:
		   self.uiserver.RegisterMethod(self.meth, argspec [,alias])
		argspec should be a sequence object like this example:
		(
		{'name':'mynum', 'type':'integer', 'default':1},
		{'name':'mystr', 'type':'string', 'default':'hello'},
		{'name':'selection', 'type':('red','green','blue')}
		)
		- arg types are found in interface.xmlrpctypes and this 
		can also be set to sequence for an enumeration type.
		- alias is an optional alias that should be used the the UI
		  (defaults to the method name)
		'''
		pass

	def addManager(self, loc):
		self.managerloc = loc
		self.addEventClient('manager', loc)
		newid = self.ID()
		myloc = self.location()
		self.announce(event.NodeAvailableEvent(newid, myloc))

	def main(self):
		raise NotImplementedError()

	def start(self):
		'''this is the node's parent method'''
		interact_thread = self.interact()

		self.main()

		# wait until the interact thread terminates
		interact_thread.join()
		self.exit()

	def exit(self):
		self.server.exit()
		self.announce(event.NodeUnavailableEvent(self.ID()))

	def announce(self, ievent):
		## no longer have to mark_data becuase id takes care of it
		#self.mark_data(ievent)
		self.clients['manager'].push(ievent)

	def publish(self, idata, eventclass=event.PublishEvent):
		## no longer have to mark_data becuase id takes care of it
		#self.mark_data(idata)

		if not issubclass(eventclass, event.PublishEvent):
			raise TypeError('PublishEvent subclass required')
		self.server.datahandler._insert(idata)
		# this idata.id is content, I think
		self.announce(eventclass(self.ID(), idata.id))

	def unpublish(self, dataid, eventclass=event.UnpublishEvent):
		if not issubclass(eventclass, event.UnpublishEvent):
			raise TypeError('UnpublishEvent subclass required')
		self.server.datahandler.remove(dataid)
		self.announce(eventclass(self.ID(), dataid))

	def publishRemote(self, nodeid, idata):
		# perhaps an event can be generated in this too
		nodelocation = self.researchByLocation(self.managerloc, nodeid)
		# should interate over nodes, be crafty, etc.
		self.addEventClient(nodeid, nodelocation)
		self.clients[nodeid].push(idata)

	## no longer have to mark_data becuase id takes care of it
	#def mark_data(self, data):
	#	data.origin['id'] = self.id
	#	data.origin['location'] = self.location()

	def research(self, loc, dataid):
		# can this determine what to do?
		return self.researchByLocation(loc, dataid)

	def researchByLocation(self, loc, dataid):
		client = self.clientclass(self.ID(), loc)
		#print "data ID =", dataid
		return client.pull(dataid)

	def researchByDataID(self, dataid, timeout = 0.5, retries = 10):
		# will change soon
#		for i in xrange(0, retries):
		nodeiddata = self.researchByLocation(self.managerloc, dataid)
#			if nodeiddata == None:
#				time.sleep(timeout)
#			else:
#				break

		if nodeiddata == None:
			print "node, researchByDataID: no such data ID"
			raise IOError

		# should interate over nodes, be crafty, etc.
		datalocationdata = self.researchByLocation(self.managerloc, nodeiddata.content[0])
		return self.researchByLocation(datalocationdata.content, dataid)

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc.update(self.server.location())
		loc['UI port'] = self.uiserver.port
		return loc

	def interact(self):
		banner = "Starting interpreter for %s" % self.__class__
		readfunc = self.raw_input
		local = locals()
		t = threading.Thread(name='interact thread', target=code.interact, args=(banner, readfunc, local))
		t.setDaemon(1)
		t.start()
		return t

	def raw_input(self, prompt):
		newprompt = '%s%s' % (str(self.id), prompt)
		return raw_input(newprompt)

  # down from here is from EventHandler
	def addEventClient(self, newid, loc):
		self.clients[newid] = self.clientclass(self.ID(), loc)

		## this was added to work with interface server
		self.clientlist.append(newid[-1])
		self.clientdict[newid[-1]] = newid

	def delEventClient(self, newid):
		if newid in self.clients:
			del self.clients[newid]

			## this was added to work with interface server
			self.clientlist.remove(newid[-1])
			del self.clientdict[newid[-1]]

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

