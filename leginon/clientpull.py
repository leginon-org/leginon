# client/server model in which client requests data from the server

import leginonobject

class Client(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)

	def pull(self, dataid):
		raise NotImplementedError()


class Server(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
