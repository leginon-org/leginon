#!/usr/bin/env python
# client/server model in which client requests data from the server

import leginonobject
import datatcp
import threading

class Client(leginonobject.LeginonObject):
  # hostname/port -> location or whatever
	def __init__(self, hostname, port):
		leginonobject.LeginonObject.__init__(self)
		self.clients = {}
		self.clients[datatcp.Client] = datatcp.Client(hostname, port)

	def pull(self, dataid):
		# testing, needs to be smart
		return self.clients[datatcp.Client].pull(dataid)

class Server(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.servers = {}
		self.servers[datatcp.Server] = datatcp.Server(self, datatcp.PullHandler)
		thread = threading.Thread(None, self.servers[datatcp.Server].serve_forever, None, (), {})
		# this isn't working right now
		#thread.setDaemon(1)
		thread.start()

if __name__ == '__main__':
	class MyServer(Server):
		def __init__(self):
			Server.__init__(self)
			self.data = {'0' : 'foo', '1' : 'bar'}
		def datafromid(self, data_id):
			try:
				return self.data[data_id]
			except KeyError:
				return None

	foo = MyServer()
	print foo.servers[datatcp.Server].server_address

