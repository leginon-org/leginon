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
	def __init__(self, id, nodelocations = {}, dh = NodeDataHandler, dhargs = (), clientclass = Client):
		leginonobject.LeginonObject.__init__(self, id)

		self.nodelocations = nodelocations
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
		if 'manager' in self.nodelocations:
			try:
				self.addManager(self.nodelocations['manager'])
			except:
				print 'exception in addManager'
				raise
			else:
				print '%s connected to manager' % (self.id,)
		self.die_event = threading.Event()

	def exit(self):
		self.outputEvent(event.NodeUnavailableEvent(self.ID()))
		self.server.exit()
		print "%s exited" % (self.id,)

	def die(self, ievent):
		self.die_event.set()

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

		datatree = self.registerUIData('Data', 'struct', permissions='r')
		datatree.set(self.uiDataDict)

		c = self.registerUIContainer('Node Info', (idspec, classspec, locspec, datatree))

		return c

	def registerUIMethod(self, func, name, argspec, returnspec=None):
		return self.uiserver.registerMethod(func, name, argspec, returnspec)

	def registerUIData(self, name, xmlrpctype, permissions=None, choices=None, default=None):
		return self.uiserver.registerData(name, xmlrpctype, permissions, choices, default)

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

	def uiDataDict(self, value=None):
		if value is None:
			try:
				return self.key2str(self.server.datahandler.datadict)
			except AttributeError:
				return {}

	def key2str(self, d):
		if type(d) is dict:
			newdict = {}
			for k in d:
				newdict[str(k)] = self.key2str(d[k])
			return newdict
		else:
			return str(d)

	def addManager(self, loc):
		self.addEventClient(('manager',), loc)
		newid = self.ID()
		myloc = self.location()
		available_event = event.NodeAvailableEvent(newid, myloc)
		self.outputEvent(ievent=available_event, wait=True)

	def main(self):
		raise NotImplementedError()

	def start(self):
		'''this is the node's parent method'''
		#interact_thread = self.interact()

		self.main()

		# wait until the interact thread terminates
		#interact_thread.join()
		self.die_event.wait()
		self.exit()

	def outputEvent(self, ievent, wait=0, nodeid=('manager',)):
		try:
			self.clients[nodeid].push(ievent)
		except KeyError:
			print 'cannot output event %s to %s' % (ievent,nodeid)
			return
		if wait:
			self.waitEvent(ievent)

	def confirmEvent(self, ievent):
		self.outputEvent(event.ConfirmationEvent(self.ID(), ievent.id))

	def waitEvent(self, ievent):
		if not ievent.id in self.confirmwaitlist:
			self.confirmwaitlist[ievent.id] = threading.Event()
		self.confirmwaitlist[ievent.id].wait()

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

	def publishRemote(self, idata):
		nodeiddata = self.researchByLocation(self.nodelocations['manager'],idata.id)
		if nodeiddata is None:
			print "node, researchByDataID: no such data ID"
			raise IOError
		for nodeid in nodeiddata.content:
			nodelocation = self.researchByLocation(self.nodelocations['manager'],
				nodeid)
			self.addEventClient(nodeid, nodelocation.content)
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
		cdata = client.pull(dataid)
		return cdata

	def researchByDataID(self, dataid):
		# will change soon
		loc = self.nodelocations['manager']
		nodeiddata = self.researchByLocation(loc, dataid)

		if nodeiddata is None:
			print "node, researchByDataID: no such data ID"
			raise IOError

		# should interate over nodes, be crafty, etc.
		datalocationdata = self.researchByLocation(self.nodelocations['manager'], nodeiddata.content[0])

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

