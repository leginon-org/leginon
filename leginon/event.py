## defines the Event and EventHandler classes

import leginonobject
import clientpush
import data
import datahandler


class Event(data.Data):
	def __init__(self, creator=None, content=None):
		data.Data.__init__(self, creator, content)


class EventClient(clientpush.Client):
	def __init__(self, hostname, port):
		clientpush.Client.__init__(self, hostname, port)

	def push(self, event):
		if isinstance(event, Event):
			clientpush.Client.push(self, event)
		else:
			raise InvalidEventError('event must be Event instance')


class EventServer(clientpush.Server):
	def __init__(self):
		clientpush.Server.__init__(self, datahandler.DataBinder)

	def bind(self, eventclass, func):
		if issubclass(eventclass, Event):
			self.datahandler.setBinding(eventclass, func)
		else:
			raise InvalidEventError('eventclass must be Event subclass')


class EventHandler(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.server = EventServer()
		self.port = self.server.location()['datatcp port']
		self.clients = {}
		self.distmap = {}
		self.registry = {'outputs':[], 'inputs':[]}

	def addClient(self, hostname, port):
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
		if to_node not in self.distmap[eventclass][from_node]:
			self.distmap[eventclass][from_node].append(to_node)

	def distribute(self, event):
		print 'distribute %s' % event
		'''push event to eventclients based on event class and source'''
		eventclass = event.__class__
		from_node = event.creator
		done = []
		for distclass,fromnodes in self.distmap.items():
		  if issubclass(eventclass, distclass):
		    print '%s is subclass of %s' % (eventclass, distclass)
		    for fromnode in (event.creator, None):
		      if fromnode in fromnodes:
		        for to_node in fromnodes[from_node]:
		          if to_node:
			    if to_node not in done:
		              self.push(to_node, event)
		              done.append(to_node)
		          else:
			    for to_node in self.handler.clients:
			      if to_node not in done:
		                self.push(to_node, event)
		                done.append(to_node)

	def push(self, client, event):
		self.clients[client].push(event)

## Standard Event Types:
##
## Event
##	PublishEvent
##	ControlEvent

class PublishEvent(Event):
	def __init__(self, creator = None, dataid=None):
		Event.__init__(self, creator, content=dataid)

class ControlEvent(Event):
	def __init__(self, creator=None, param=None):
		### to prevent abuse of this event, only a few simple python
		### number types are allowed for the content
		allowedtypes = (int, long, float)
		print 'CONTROLEVENT init param %s' % param
		if type(param) in allowedtypes:
			Event.__init__(self, creator, content=param)
		else:
			raise TypeError('ControlEvent content must be in %s' % allowedtypes)


## event related exceptions

class InvalidEventError(TypeError):
	pass



