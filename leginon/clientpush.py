## client/server model in which the client pushes data and server
##  handles the data
import leginonobject

class Client(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)

	def push(self, data):
		raise NotImplementedError()


class Server(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.bindings = Bindings()

	def bind(self, dataclass, func=None):
		'func must take data instance as first arg'
		if func == None:
			del self.bindings[dataclass]
		else:
			self.bindings[dataclass] = func


class Bindings(dict, leginonobject.LeginonObject):
	def __init__(self, *args):
		dict.__init__(self, *args)
		leginonobject.LeginonObject.__init__(self)
