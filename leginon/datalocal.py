#!/usr/bin/env python
import leginonobject
import copy

class Server(leginonobject.LeginonObject):
	def __init__(self, dh):
		leginonobject.LeginonObject.__init__(self)
		self.datahandler = dh

class PullServer(Server):
	pass

class PushServer(Server):
	pass

class Client(leginonobject.LeginonObject):
	def __init__(self, server):
		leginonobject.LeginonObject.__init__(self)
		self.server = server

class PullClient(Client):
	def pull(self, id):
		return copy.deepcopy(self.server.datahandler.query(id))

class PushClient(Client):
	def push(self, idata):
		return self.server.datahandler.insert(copy.deepcopy(idata))

if __name__ == '__main__':
	pass
