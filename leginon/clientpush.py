#!/usr/bin/env python
## client/server model in which the client pushes data and server
##  handles the data
import leginonobject
import datalocal
import datatcp
import threading
import datahandler

class Client(leginonobject.LeginonObject):
  # hostname/port -> location
	def __init__(self, hostname, port):
		leginonobject.LeginonObject.__init__(self)
		self.clients = {}
		#self.clients[datalocal.PushClient] = datalocal.PushClient()
		self.clients[datatcp.PushClient] = datatcp.PushClient(hostname, port)

	def push(self, data):
		# testing, needs to be smart
		self.clients[datatcp.PushClient].push(data)

class Server(leginonobject.LeginonObject):
	def __init__(self, dkclass = datahandler.SimpleDataKeeper):
		leginonobject.LeginonObject.__init__(self)
		self.bindings = Bindings()
		self.datahandler = dkclass()
		self.servers = {}
		#self.servers[datalocal.PushServer] = datalocal.PushServer(self.datahandler)
		self.servers[datatcp.PushServer] = datatcp.PushServer(self.datahandler)
		thread = threading.Thread(None, self.servers[datatcp.PushServer].serve_forever, None, (), {})
		# this isn't working right now
		thread.setDaemon(1)
		thread.start()

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc['datatcp port'] = self.servers[datatcp.PushServer].port
		return loc


	def handle_data(self, newdata):
		print 'handling %s' % newdata


if __name__ == '__main__':
	class MyServer(Server):
		def __init__(self):
			Server.__init__(self)
			self.data = {'0' : 'foo', '1' : 'bar'}
		def datatoid(self, data_id, data):
			self.data[data_id] = data
			print "self.data =", `self.data`

	foo = MyServer()
	print foo.servers[datatcp.PushServer].server_address

