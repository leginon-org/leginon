## defines the Event and EventHandler classes

import leginonobject
import clientpush
import data


class Event(data.Data):
	def __init__(self):
		data.Data.__init__(self)


class EventClient(clientpush.Client):
	def __init__(self):
		clientpush.Client.__init__(self)

	def put(self, event):
		if type(event) != Event:
			raise InvalidEventError('event must be Event instance')
		clientpush.Client.put(self, event)


class EventServer(clientpush.Server):
	def __init__(self):
		clientpush.Server.__init__(self)


class EventHandler(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.client = EventClient()
		self.server = EventServer()

	def announce(self):
		pass


## event related exceptions

class InvalidEventError(Exception):
	pass
