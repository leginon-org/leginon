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

### False is not defined in early python 2.2
False = 0
True = 1

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

		self.managerloc = managerloc
		self.clients = {}

		self.registry = {'outputs':[], 'inputs':[]}

		self.server = datatransport.Server(self.ID(), dh, dhargs)
		self.clientclass = clientclass

		uiserverid = self.ID()
		self.uiserver = interface.Server(uiserverid)
		self.uiactive = 0
		self.defineUserInterface()

		self.confirmwaitlist = {}

		self.addEventOutput(event.PublishEvent)
		self.addEventOutput(event.UnpublishEvent)
		self.addEventOutput(event.NodeAvailableEvent)
		self.addEventOutput(event.NodeUnavailableEvent)
		self.addEventInput(event.KillEvent, self.die)
		self.addEventInput(event.ConfirmationEvent, self.registerConfirmedEvent)
		if self.managerloc is not None:
			print 'adding manager, %s' % self.managerloc
			try:
				self.addManager(self.managerloc)
			except:
				print 'exception in addManager'
				raise
			else:
				print 'no exception'

	def exit(self):
		self.outputEvent(event.NodeUnavailableEvent(self.ID()))
		self.server.exit()

	def die(self, ievent):
		sys.exit()

	def defineUserInterface(self):
		'''
		This is where you register methods that can be accessed
		by a user interface through XML-RPC
		To register a method use:
		   self.registerUIFunction(self.meth, argspec [,alias])
		argspec should be a sequence object like this example:
		(
		  {'name':'mynum', 'alias':MyNum','type':'integer', 'default':1},
		  {'name':'mystr', 'alias':'MyStr', 'type':'string', 'default':'hello'},
		  {'name':'selection', 'alias':'Selection', 'type':('red','green','blue')}
		)
		- name is currently ignored and therefore argspec must be
		  properly ordered for positional arguments
		- arg types are found in interface.xmlrpctypes and this 
		  can also be set to sequence for an enumeration type.
		- alias is the alias that should be used by the UI
		  (defaults to __name__)
		'''
		self.uiactive = 1
		self.clientlist = []
		self.clientdict = {}

		## this is data for ui to read, but not visible
		self.clientlistdata = self.registerUIData('clientlist', 'array', permissions='r')
		self.clientlistdata.set(self.clientlist)


		idspec = self.registerUIData('ID', 'array', permissions='r', default=self.id)
		#idspec.set(self.id)
		classspec = self.registerUIData('Class', 'string', permissions='r', default=self.__class__.__name__)
		#classspec.set(self.__class__.__name__)
		locspec = self.registerUIData('Location', 'struct', permissions='r', default=self.location())
		#locspec.set(self.location())

		c = self.registerUIContainer('Node Info', (idspec,classspec,locspec))
		return c

	def registerUIMethod(self, func, name, argspec, returnspec=None):
		return self.uiserver.registerMethod(func, name, argspec, returnspec)

	def registerUIData(self, name, xmlrpctype, permissions=None, enum=None, default=None):
		return self.uiserver.registerData(name, xmlrpctype, permissions, enum, default)

	def registerUIContainer(self, name=None, content=()):
		return self.uiserver.registerContainer(name, content)

	def registerUISpec(self, name=None, content=()):
		return self.uiserver.registerSpec(name, content)

	def setUIData(self, name, value):
		raise NotImplementedError('should set data directly through data object')
		#self.uiserver.setData(name, value)
		#return self.uiserver.getData(name)

	def getUIData(self, name):
		raise NotImplementedError('should get data directly through data object')
		#return self.uiserver.getData(name)

	def addManager(self, loc):
		print 'addEventClient...'
		self.addEventClient(('manager',), loc)
		print "self.clients =", self.clients
		newid = self.ID()
		myloc = self.location()
		available_event = event.NodeAvailableEvent(newid, myloc)
		self.outputEvent(ievent=available_event, wait=True)

	def main(self):
		raise NotImplementedError()

	def start(self):
		'''this is the node's parent method'''
		interact_thread = self.interact()

		self.main()

		# wait until the interact thread terminates
		interact_thread.join()
		self.exit()

	def outputEvent(self, ievent, wait=0, nodeid=('manager',)):
		try:
			self.clients[nodeid].push(ievent)
		except KeyError:
			#print 'cannot output event %s to %s' % (ievent,nodeid)
			return
		if wait:
			self.waitEvent(ievent)

	def confirmEvent(self, ievent):
		self.outputEvent(event.ConfirmationEvent(self.ID(), ievent.id))

	def waitEvent(self, ievent):
		print "waiting on", ievent.id
		if not ievent.id in self.confirmwaitlist:
			self.confirmwaitlist[ievent.id] = threading.Event()
		self.confirmwaitlist[ievent.id].wait()
		print "done for", ievent.id

	def registerConfirmedEvent(self, ievent):
		# this is bad since it will fill up with lots of events
		if not ievent.content in self.confirmwaitlist:
			self.confirmwaitlist[ievent.content] = threading.Event()
		self.confirmwaitlist[ievent.content].set()
		#del self.confirmwaitlist[ievent.content]

	def publish(self, idata, eventclass=event.PublishEvent, confirm=False):
		if not issubclass(eventclass, event.PublishEvent):
			raise TypeError('PublishEvent subclass required')
		self.server.datahandler._insert(idata)
		# this idata.id is content, I think
		e = eventclass(self.ID(), idata.id, confirm)
		self.outputEvent(e)
		return e

	def unpublish(self, dataid, eventclass=event.UnpublishEvent):
		if not issubclass(eventclass, event.UnpublishEvent):
			raise TypeError('UnpublishEvent subclass required')
		self.server.datahandler.remove(dataid)
		self.outputEvent(eventclass(self.ID(), dataid))

	def publishRemote(self, nodeid, idata):
		# perhaps an event can be generated in this too
		nodelocation = self.researchByLocation(self.managerloc, nodeid).content
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
		cdata = client.pull(dataid)

		return cdata

	def researchByDataID(self, dataid):
		# will change soon
		nodeiddata = self.researchByLocation(self.managerloc, dataid)

		if nodeiddata is None:
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
		if self.uiactive:
			name = newid[-1]
			if name not in self.clientlist:
				self.clientlist.append(name)
			self.clientdict[name] = newid
		self.clientlistdata.set(self.clientlist)

	def delEventClient(self, newid):
		if newid in self.clients:
			del self.clients[newid]

			## this was added to work with interface server
			if self.uiactive:
				name = newid[-1]
				self.clientlist.remove(name)
				del self.clientdict[name]
		self.clientlistdata.set(self.clientlist)

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

