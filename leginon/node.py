import threading
import code
import leginonobject
import event
import datatransport
import datahandler
import interface
import sys
import copy

# False is not defined in early python 2.2
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

class DataHandler(datahandler.SimpleDataKeeper, datahandler.DataBinder):
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

	def setBinding(self, eventclass, func):
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise event.InvalidEventError('eventclass must be Event subclass')

class Node(leginonobject.LeginonObject):
	def __init__(self, id, nodelocations = {}, dh = DataHandler,
								dhargs = (), clientclass = Client):
		leginonobject.LeginonObject.__init__(self, id)

		self.nodelocations = nodelocations

		self.eventmapping = {'outputs':[], 'inputs':[]}

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
		self.addEventInput(event.ConfirmationEvent, self.handleConfirmedEvent)
		self.addEventInput(event.ManagerAvailableEvent, self.handleAddManager)

		if 'manager' in self.nodelocations:
			try:
				self.addManager(self.nodelocations['manager'])
			except:
				print 'Node: exception in addManager'
				raise
			else:
				print 'Node: %s connected to manager' % (self.id,)
		self.die_event = threading.Event()

	# main, start/stop methods
	def main(self):
		raise NotImplementedError()

	def exit(self):
		self.outputEvent(event.NodeUnavailableEvent(self.ID()))
		self.server.exit()
		print "Node: %s exited" % (self.id,)

	def die(self, ievent=None):
		self.die_event.set()

	def start(self):
		#interact_thread = self.interact()

		self.main()

		# wait until the interact thread terminates
		#interact_thread.join()
		self.die_event.wait()
		self.exit()

	# location method

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc.update(self.server.location())
		loc['UI port'] = self.uiserver.port
		return loc

	# event input/output/blocking methods

	def outputEvent(self, ievent, wait=0):
		try:
			self.managerclient.push(ievent)
		except KeyError:
			print 'Node: cannot output event %s' % ievent
			return
		if wait:
			self.waitEvent(ievent)

	def addEventInput(self, eventclass, func):
		self.server.datahandler.setBinding(eventclass, func)
		if eventclass not in self.eventmapping['inputs']:
			self.eventmapping['inputs'].append(eventclass)

	def delEventInput(self, eventclass):
		self.server.datahandler.setBinding(eventclass, None)
		if eventclass in self.eventmapping['inputs']:
			self.eventmapping['inputs'].remove(eventclass)

	def addEventOutput(self, eventclass):
		if eventclass not in self.eventmapping['outputs']:
			self.eventmapping['outputs'].append(eventclass)
		
	def delEventOutput(self, eventclass):
		if eventclass in self.eventmapping['outputs']:
			self.eventmapping['outputs'].remove(eventclass)

	def confirmEvent(self, ievent):
		self.outputEvent(event.ConfirmationEvent(self.ID(), ievent.id))

	def waitEvent(self, ievent):
		if not ievent.id in self.confirmwaitlist:
			self.confirmwaitlist[ievent.id] = threading.Event()
		self.confirmwaitlist[ievent.id].wait()

	def handleConfirmedEvent(self, ievent):
		# this is bad since it will fill up with lots of events
		if not ievent.content in self.confirmwaitlist:
			self.confirmwaitlist[ievent.content] = threading.Event()
		self.confirmwaitlist[ievent.content].set()
		#del self.confirmwaitlist[ievent.content]

	# data publish/research methods
	
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
		dataid = idata.id
		nodeiddata = self.researchByLocation(self.nodelocations['manager'], dataid)
		if nodeiddata is None:
			print "Node: publishRemote, no such data ID %s" % dataid
			raise IOError
		for nodeid in nodeiddata.content:
			nodelocation = self.researchByLocation(self.nodelocations['manager'],
				nodeid)
			client = self.clientclass(self.ID(), nodelocation.content)
			client.push(idata)

	def researchByLocation(self, loc, dataid):
		client = self.clientclass(self.ID(), loc)
		cdata = client.pull(dataid)
		return cdata

	def researchByDataID(self, dataid):
		nodeiddata = self.managerclient.pull(dataid)

		if nodeiddata is None:
			print "Node: researchByDataID, no such data ID %s" % dataid
			raise IOError

		# should interate over nodes, be crafty, etc.
		datalocationdata = self.managerclient.pull(nodeiddata.content[-1])

		return self.researchByLocation(datalocationdata.content, dataid)

	# methods for setting up the manager

	def addManager(self, loc):
		self.managerclient = self.clientclass(self.ID(), loc)
		newid = self.ID()
		myloc = self.location()
		available_event = event.NodeAvailableEvent(newid, myloc)
		self.outputEvent(ievent=available_event, wait=True)

	def handleAddManager(self, ievent):
		self.addManager(ievent.content)

	# utility methods

	def interact(self):
		banner = "Starting interpreter for %s" % self.__class__
		readfunc = self.raw_input
		local = locals()
		t = threading.Thread(name='interact thread', target=code.interact,
													args=(banner, readfunc, local))
		t.setDaemon(1)
		t.start()
		return t

	def raw_input(self, prompt):
		newprompt = '%s%s' % (str(self.id), prompt)
		return raw_input(newprompt)

	# UI methods

	def registerUIMethod(self, func, name, argspec, returnspec=None):
		return self.uiserver.registerMethod(func, name, argspec, returnspec)

	def registerUIData(self, name, xmlrpctype, permissions=None,
												choices=None, default=None):
		return self.uiserver.registerData(name, xmlrpctype, permissions,
																				choices, default)

	def registerUIContainer(self, name=None, content=()):
		return self.uiserver.registerContainer(name, content)

	def registerUISpec(self, name=None, content=()):
		return self.uiserver.registerSpec(name, content)

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

	def uiExit(self):
		self.die()
		return ''

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

		exitspec = self.registerUIMethod(self.uiExit, 'Exit', ())

		idspec = self.registerUIData('ID', 'array', 'r', default=self.id)
		classspec = self.registerUIData('Class', 'string', 'r',
																		default=self.__class__.__name__)
		locationspec = self.registerUIData('Location', 'struct', 'r',
																	default=self.location())

		datatree = self.registerUIData('Data', 'struct', permissions='r')
		datatree.set(self.uiDataDict)

		containerspec = self.registerUIContainer('Node',
								(exitspec, idspec, classspec, locationspec, datatree))

		return containerspec

