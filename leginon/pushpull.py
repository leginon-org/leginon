#!/usr/bin/env python
## client/server model in which the client pushes data and server
##  handles the data
import leginonobject
import datalocal
import datatcp
import threading
import datahandler

class Server(leginonobject.LeginonObject):
	def __init__(self, dhclass = datahandler.SimpleDataKeeper, dhargs = ()):
		leginonobject.LeginonObject.__init__(self)
		self.datahandler = apply(dhclass, dhargs)
		self.servers = {}
#		self.servers[datalocal.PushPullServer] = datalocal.PushPullServer(self.datahandler)
		self.servers[datatcp.PushPullServer] = datatcp.PushPullServer(self.datahandler)
		thread = threading.Thread(None, self.servers[datatcp.PushPullServer].serve_forever, None, (), {})
		thread.setDaemon(1)
		thread.start()

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc['datatcp port'] = self.servers[datatcp.PushPullServer].port
		return loc

if __name__ == '__main__':
	class MyServer(Server):
		def __init__(self):
			Server.__init__(self)
			self.data = {'0' : 'foo', '1' : 'bar'}
		def datatoid(self, data_id, data):
			self.data[data_id] = data
			print "self.data =", `self.data`

	foo = MyServer()
	print foo.servers[datatcp.PushPullServer].server_address

