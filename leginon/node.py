import threading
import code
import leginonobject
import event
import datatransport
import datahandler
import dbdatakeeper
import interface
import sys
import copy
import time

# False is not defined in early python 2.2
False = 0
True = 1

if sys.platform == 'win32':
	sys.coinit_flags = 0

class DataHandler(datahandler.SimpleDataKeeper, datahandler.DataBinder):
	'''Overrides SimpleDataKeeper and DataBinder to combine storing data and mapping events for use by Node.'''
	def __init__(self, id):
		# this will call LeginonObject constructor twice I think
		datahandler.SimpleDataKeeper.__init__(self, id)
		datahandler.DataBinder.__init__(self, id)

	def insert(self, idata):
		'''Insert data into the datahandler. Only events can be inserted from and external source. Events are bound. See setBinding.'''
		if isinstance(idata, event.Event):
			datahandler.DataBinder.insert(self, idata)
		else:
			if idata.id[:-1] == self.id[:-1]:
				datahandler.SimpleDataKeeper.insert(self, copy.deepcopy(idata))
			else:
				raise InvalidEventError('event must be Event instance')

	# def query(self, id): is inherited from SimpleDataKeeper

	def setBinding(self, eventclass, func):
		'''Overides datahandler.DataBinder, making sure it binds Event type only.'''
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise event.InvalidEventError('eventclass must be Event subclass')

class Node(leginonobject.LeginonObject):
	'''Atomic operating unit for performing tasks, creating data and events.'''
	def __init__(self, id, nodelocations = {},
											dh = DataHandler, dhargs = (),
											tcpport=None, xmlrpcport=None,
											clientclass = datatransport.Client, launchlock=None,
											pdkargs = ()):
		leginonobject.LeginonObject.__init__(self, id)

		self.nodelocations = nodelocations
		self.launchlock = launchlock

		self.eventmapping = {'outputs':[], 'inputs':[]}

		self.datahandlers = {}
		self.datahandlers['node'] = apply(dh, (self.ID(),) + dhargs)
		self.datahandlers['pickle'] = apply(dbdatakeeper.PickleDataKeeper,
																							(self.ID(),) + pdkargs)

		self.server = datatransport.Server(self.ID(),
																				self.datahandlers['node'], tcpport)
		self.clientclass = clientclass

		self.uiserver = interface.Server(self.ID(), xmlrpcport)

		self.confirmwaitlist = {}

		self.addEventOutput(event.PublishEvent)
		self.addEventOutput(event.UnpublishEvent)
		self.addEventOutput(event.NodeAvailableEvent)
		self.addEventOutput(event.NodeUnavailableEvent)

		self.addEventInput(event.KillEvent, self.die)
		self.addEventInput(event.ConfirmationEvent, self.handleConfirmedEvent)
		self.addEventInput(event.NodeAvailableEvent, self.handleAddNode)

		if 'manager' in self.nodelocations:
			try:
				self.addManager(self.nodelocations['manager'])
			except:
				self.printerror('exception in addManager')
				raise
			else:
				self.printerror('connected to manager')
		self.die_event = threading.Event()

	def releaseLauncher(self):
		## release the launch lock
		if self.launchlock is not None:
			print self, 'releasing launchlock'
			self.launchlock.release()

	# main, start/stop methods

	def main(self):
		'''The body of taking place when the node is started. See start.'''
		pass

	def exit(self):
		'''Cleans up the node before it dies.'''
		self.outputEvent(event.NodeUnavailableEvent(self.ID()))
		self.server.exit()
		self.printerror('exited')

	def die(self, ievent=None):
		'''Tell the node to finish and call exit.'''
		self.die_event.set()

	def start(self):
		'''Call to make the node active and react to a call to exit. Calls main.'''
		#interact_thread = self.interact()

		self.releaseLauncher()
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
		'''Send the event to the manager to be routed where necessary.'''
		try:
			ievent.confirm = True
			self.managerclient.push(ievent)
		except KeyError:
			self.printerror('cannot output event %s' % ievent)
			return
		if wait:
			self.waitEvent(ievent)

	def addEventInput(self, eventclass, func):
		'''Map a function (event handler) to be called when the specified event is received.'''
#		self.server.datahandler.setBinding(eventclass, func)
		self.datahandlers['node'].setBinding(eventclass, func)
		if eventclass not in self.eventmapping['inputs']:
			self.eventmapping['inputs'].append(eventclass)

	def delEventInput(self, eventclass):
		'''Unmap all functions (event handlers) to be called when the specified event is received.'''
#		self.server.datahandler.setBinding(eventclass, None)
		self.datahandlers['node'].setBinding(eventclass, None)
		if eventclass in self.eventmapping['inputs']:
			self.eventmapping['inputs'].remove(eventclass)

	def addEventOutput(self, eventclass):
		'''Register the ability for the node to output specified event.'''
		if eventclass not in self.eventmapping['outputs']:
			self.eventmapping['outputs'].append(eventclass)
		
	def delEventOutput(self, eventclass):
		'''Unregister the ability for the node to output specified event.'''
		if eventclass in self.eventmapping['outputs']:
			self.eventmapping['outputs'].remove(eventclass)

	def confirmEvent(self, ievent):
		'''Confirm that an event has been received and/or handled.'''
		self.outputEvent(event.ConfirmationEvent(self.ID(), ievent.id))

	def waitEvent(self, ievent):
		'''Block for confirmation of a generated event.'''
		if not ievent.id in self.confirmwaitlist:
			self.confirmwaitlist[ievent.id] = threading.Event()
		self.confirmwaitlist[ievent.id].wait()

	def handleConfirmedEvent(self, ievent):
		'''Handler for ConfirmationEvents. Unblocks the call waiting for confirmation of the event generated.'''
		# this is bad since it will fill up with lots of events
		if not ievent.content in self.confirmwaitlist:
			self.confirmwaitlist[ievent.content] = threading.Event()
		self.confirmwaitlist[ievent.content].set()
		#del self.confirmwaitlist[ievent.content]

	# data publish/research methods

	def publish(self, idata, eventclass=event.PublishEvent, confirm=False):
		'''Make a piece of data available to other nodes.'''
		if not issubclass(eventclass, event.PublishEvent):
			raise TypeError('PublishEvent subclass required')
#		self.server.datahandler._insert(idata)
		self.datahandlers['node'].insert(idata)
		self.datahandlers['pickle'].insert(idata)
		# this idata.id is content, I think
		e = eventclass(self.ID(), idata.id, confirm)
		self.outputEvent(e)
		return e

	def unpublish(self, dataid, eventclass=event.UnpublishEvent):
		'''Make a piece of data unavailable to other nodes.'''
		if not issubclass(eventclass, event.UnpublishEvent):
			raise TypeError('UnpublishEvent subclass required')
#		self.server.datahandler.remove(dataid)
		self.datahandlers['node'].remove(dataid)
		self.outputEvent(eventclass(self.ID(), dataid))

	def publishRemote(self, idata):
		'''Publish a piece of data with the specified data ID, setting all other data with the same data ID to the data value (including other nodes).'''
		dataid = idata.id
		nodeiddata = self.researchByLocation(self.nodelocations['manager'], dataid)
		if nodeiddata is None:
			# try a partial ID lookup
			nodeiddata = self.researchByLocation(self.nodelocations['manager'], dataid[:1])

		if nodeiddata is None:
			raise PublishError('No such Data ID: %s' % (dataid,))

		for nodeid in nodeiddata.content:
			nodelocation = self.researchByLocation(self.nodelocations['manager'],
				nodeid)
			client = self.clientclass(self.ID(), nodelocation.content)
			client.push(idata)

	def researchByLocation(self, loc, dataid):
		'''Get a piece of data with the specified data ID by the location of a node.'''
		client = self.clientclass(self.ID(), loc)
		cdata = client.pull(dataid)
		return cdata

	def researchByDataID(self, dataid):
		'''Get a piece of data with the specified data ID. Currently retrieves the data from the last node to publish it.'''
		nodeiddata = self.managerclient.pull(dataid)

		if nodeiddata is None:
			raise ResearchError('No such Data ID: %s' % (dataid,))

		# should interate over nodes, be crafty, etc.
		datalocationdata = self.managerclient.pull(nodeiddata.content[-1])
		newdata = self.researchByLocation(datalocationdata.content, dataid)
		return newdata

	# methods for setting up the manager

	def addManager(self, loc):
		'''Set the manager controlling the node and notify said manager this node is available.'''
		self.managerclient = self.clientclass(self.ID(), loc)
		available_event = event.NodeAvailableEvent(self.ID(), self.location(),
												self.__class__.__name__)
		self.outputEvent(ievent=available_event, wait=True)

	def handleAddNode(self, ievent):
		'''Event handler calling adddManager with event content. See addManager.'''
		if ievent.content['class'] == 'Manager':
			self.addManager(ievent.content['location'])

	# utility methods

	def interact(self):
		'''Create a prompt with namespace within the class instance for command linecontrol of the node.'''
		banner = "Starting interpreter for %s" % self.__class__
		readfunc = self.raw_input
		local = locals()
		t = threading.Thread(name='interact thread', target=code.interact,
													args=(banner, readfunc, local))
		t.setDaemon(1)
		t.start()
		return t

	def raw_input(self, prompt):
		'''Helper function for interact. See interact.'''
		newprompt = '%s%s' % (str(self.id), prompt)
		return raw_input(newprompt)

	# UI methods

	def registerUIMethod(self, func, name, argspec, returnspec=None):
		'''Register a method with the UI server by function specifying argument and return value specifications.'''
		return self.uiserver.registerMethod(func, name, argspec, returnspec)

	def registerUIData(self, name, xmlrpctype, permissions=None,
												choices=None, default=None, pyname=None, callback=None):
		'''Register a data value with the UI server.'''
		return self.uiserver.registerData(name, xmlrpctype, permissions,
																				choices, default, pyname, callback)

	def registerUIContainer(self, name=None, content=()):
		'''Register a container for data and methods with the UI server.'''
		return self.uiserver.registerContainer(name, content)

	def registerUISpec(self, name=None, content=()):
		'''Register the entire UI specification with the UI server.'''
		return self.uiserver.registerSpec(name, content)

	def uiDataDict(self, value=None):
		'''Generate a dictionary of currently published data and attributes in a XML-RPC compatible format.'''
		if value is None:
			try:
#				return self.key2str(self.server.datahandler.datadict)
				return self.key2str(self.datahandlers['node'].datadict)
#				return self.server.datahandler.datadict
			except AttributeError:
				return {}

	def key2str(self, d):
		'''Helper function for uiDataDict. Makes keys and values into strings. See uiDataDict.'''
		if type(d) is dict:
			newdict = {}
			for k in d:
				newdict[str(k)] = self.key2str(d[k])
			return newdict
		else:
			return str(d)

	def uiExit(self):
		'''UI function calling die. See die.'''
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

		exitspec = self.registerUIMethod(self.uiExit, 'Exit', ())

		idspec = self.registerUIData('ID', 'array', 'r', default=self.id)
		classspec = self.registerUIData('Class', 'string', 'r',
																		default=self.__class__.__name__)
		locationspec = self.registerUIData('Location', 'struct', 'r',
																	default=self.location())

		datatree = self.registerUIData('Data', 'struct', permissions='r')
		datatree.registerCallback(self.uiDataDict)

		cont = self.registerUIContainer('Node', (exitspec, idspec, classspec, locationspec, datatree))

		myspec = self.registerUISpec('Node',
								(cont,))

		return myspec


class ResearchError(Exception):
	pass

class PublishError(Exception):
	pass
