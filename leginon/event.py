## defines the Event and EventHandler classes

import leginonobject
import clientpush
import data


class Event(data.Data):
	def __init__(self, creator=None, content=None):
		data.Data.__init__(self, creator, content)


class EventClient(clientpush.Client):
	def __init__(self, hostname, port):
		clientpush.Client.__init__(self, hostname, port)

	def push(self, event):
		if isinstance(event, Event):
			print 'EventClient.push is calling clientpush.Client.push'
			clientpush.Client.push(self, event)
		else:
			raise InvalidEventError('event must be Event instance')


class EventServer(clientpush.Server):
	def __init__(self):
		clientpush.Server.__init__(self)

	def bind(self, eventclass, func):
		if issubclass(eventclass, Event):
			clientpush.Server.bind(self, eventclass, func)
		else:
			raise InvalidEventError('eventclass must be Event subclass')


class EventHandler(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.server = EventServer()
		self.port = self.server.location()['datatcp port']
		self.distributor = 
		self.clients = {}
		self.distmap = {}
		self.registry = {'outputs':[], 'inputs':[]}

	def addClient(self, hostname, port):
		print 'EventHandler.ADDCLIENT %s %s' % (hostname, port)
		self.clients[hostname,port] = EventClient(hostname, port)

	def delClient(self, hostname, port):
		if (hostname,port) in self.clients:
			del self.clients[hostname,port]

	def addInput(self, eventclass, func):
		self.server.bind(eventclass, func)
		if eventclass not in self.registry['inputs']:
			self.registry['inputs'].append(eventclass)

	def delInput(self, eventclass):
		self.server.bind(eventclass, None)
		if eventclass in self.registry['inputs']:
			self.registry['inputs'].remove(eventclass)

	def addOutput(self, eventclass):
		if eventclass not in self.registry['outputs']:
			self.registry['outputs'].append(eventclass)
		
	def delOutput(self, eventclass):
		if eventclass in self.registry['outputs']:
			self.registry['outputs'].remove(eventclass)

	def addDistmap(self, eventclass, from_node=None, to_node=None):
		if eventclass not in self.distmap:
			self.distmap[eventclass] = {}
		if from_node not in self.distmap[eventclass]:
			self.distmap[eventclass][from_node] = []
		if to_node noe in self.distmap[eventclass][from_node];
			self.distmap[eventclass][from_node].append(to_node)

	def distribute(self, event):
		'''push event to event servers based on event class and source'''
		eventclass = event.__class__
		from_node = event.creator
		done = []
		for distclass,fromnodes in self.distmap.items():
		  if issubclass(eventclass, distclass):
		    for fromnode in (event.creator, None):
		      if fromnode in fromnodes:
		        for to_node in fromnodes[from_node]:
		          if to_node:
		            self.handler.push(to_node, event)				
		            done.append(to_node)
		          else:
			    for to_node in self.handler.clients:
		            self.handler.push(to_node, event)

	def push(self, client, event):
		print 'EventHandler.push to client %s, event %s' % (client,event)
		self.clients[client].push(event)

## Standard Event Types:
##
## Event
##	PublishEvent
##	ControlEvent

class PublishEvent(Event):
	def __init__(self, creator, dataid):
		Event.__init__(self, creator, content=dataid)

class ControlEvent(Event):
	def __init__(self, creator, param):
		### to prevent abuse of this event, only a few simple python
		### number types are allowed for the content
		allowedtypes = (int, long, float)
		if type(param) in allowedtypes:
			Event.__init__(self, creator, content=param)
		else:
			raise TypeError('ControlEvent content must be in %s' % allowedtypes)


## event related exceptions

class InvalidEventError(TypeError):
	pass



