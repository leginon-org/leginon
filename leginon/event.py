## defines the Event and EventHandler classes

import leginonobject
import clientpush
import data


class Event(data.Data):
	def __init__(self, creator=None):
		data.Data.__init__(self, creator)


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
		self.clients = {}

	def addClient(self, hostname, port):
		print 'EventHandler.ADDCLIENT %s %s' % (hostname, port)
		self.clients[hostname,port] = EventClient(hostname, port)

	def delClient(self, hostname, port):
		if (hostname,port) in self.clients:
			del self.clients[hostname,port]

	def bind(self, eventclass, func):
		self.server.bind(eventclass, func)

	def push(self, client, event):
		print 'EventHandler.push to client %s, event %s' % (client,event)
		self.clients[client].push(event)


## event related exceptions

class EventTypeError(TypeError):
	pass
