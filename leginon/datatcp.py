#!/usr/bin/env python

import SocketServer
import cPickle
import socket
import leginonobject
import data

class PullHandler(SocketServer.StreamRequestHandler, leginonobject.LeginonObject):
	def __init__(self, request, server_address, server):
		# not sure it needs to be a LeginonObject
		leginonobject.LeginonObject.__init__(self)
		SocketServer.StreamRequestHandler.__init__(self, request, server_address, server)

	def handle(self):
		# needs error checking
		data_id = cPickle.load(self.rfile)

		# pickle the data from data_id (w/o the trailing newline char)
		data = self.server.datahandler.query(data_id)
		cPickle.dump(data, self.wfile)

class PushHandler(SocketServer.StreamRequestHandler, leginonobject.LeginonObject):
	def __init__(self, request, server_address, server):
		# not sure it needs to be a LeginonObject
		leginonobject.LeginonObject.__init__(self)
		SocketServer.StreamRequestHandler.__init__(self, request, server_address, server)

	def handle(self):
		# needs error checking, cPickle attempt
		# data_id needs to be send with a newline
		newdata = cPickle.load(self.rfile)
		self.server.datahandler.insert(newdata)

class PushPullHandler(SocketServer.StreamRequestHandler, leginonobject.LeginonObject):
	def __init__(self, request, server_address, server):
		# not sure it needs to be a LeginonObject
		leginonobject.LeginonObject.__init__(self)
		SocketServer.StreamRequestHandler.__init__(self, request, server_address, server)

	def handle(self):
		# needs error checking
		idata = cPickle.load(self.rfile)
		if isinstance(idata, data.Data):
			# data_id needs to be send with a newline
			self.server.datahandler.insert(idata)
		else: # 'tis an id and nothing more or at least until there is an id class
			# pickle the data from data_id (w/o the trailing newline char)
			wdata = self.server.datahandler.query(idata)
			cPickle.dump(wdata, self.wfile)

class Server(SocketServer.ThreadingTCPServer, leginonobject.LeginonObject):
	def __init__(self, dh, handler, port=None):
		leginonobject.LeginonObject.__init__(self)
		self.datahandler = dh
		# instantiater can choose a port or we'll choose one for them
		if port:
			SocketServer.ThreadingTCPServer.__init__(self, ('', port), handler)
		else:
			# range define by IANA as dynamic/private or so says Jim
			portrange = (49152,65536)
			# start from the bottom
			port = portrange[0]
			# iterate to the top or until unused port is found
			while port <= portrange[1]:
				try:
					SocketServer.ThreadingTCPServer.__init__(self, ('', port), handler)
					break
				except Exception, var:
					# socket error, address already in use
					if (var[0] == 98 or var[0] == 10048):
						port += 1
					else:
						raise
			self.port = port

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc['port'] = self.port
		return loc

class PullServer(Server):
	def __init__(self, server, port=None):
		Server.__init__(self, server, PullHandler, port)

class PushServer(Server):
	def __init__(self, server, port=None):
		Server.__init__(self, server, PushHandler, port)

class PushPullServer(Server):
	def __init__(self, server, port=None):
		Server.__init__(self, server, PushPullHandler, port)

class Client(leginonobject.LeginonObject):
	def __init__(self, hostname, port, buffer_size = 1024):
		self.buffer_size = buffer_size 
		leginonobject.LeginonObject.__init__(self)
		self.hostname = hostname
		self.port = port

class PullClient(Client):
	def pull(self, data_id, family = socket.AF_INET, type = socket.SOCK_STREAM):
		print 'PullClient.pull data_id = %s' % data_id
		data = ""
		s = socket.socket(family, type)
		s.connect((self.hostname, self.port)) # Connect to server
		idpickle = cPickle.dumps(data_id)
		s.send(idpickle)

		while 1:
		  r = s.recv(self.buffer_size) # Receive up to buffer_size bytes
		  if not r:
		    break
		  data += r
		s.close()
		# needs cPickle attempt
		return cPickle.loads(data)

class PushClient(Client):
	def push(self, idata, family = socket.AF_INET, type = socket.SOCK_STREAM):
		# needs to account for different data_id datatypes
		s = socket.socket(family, type)
		s.connect((self.hostname, self.port)) # Connect to server
		s.send(cPickle.dumps(idata))
		s.close()

if __name__ == '__main__':
	import threading

	class dummyServer:
		def datafromid(self, data_id):
			return {data_id : 'foo bar'}
		def datatoid(self, data_id, data):
			print `{data_id : data}`

	pullserver = PullServer(dummyServer())
	pushserver = PushServer(dummyServer())
	print 'pull server at:', pullserver.server_address
	print 'push server at:', pushserver.server_address
	t1 = threading.Thread(None, pullserver.serve_forever, None, (), {})
	t2 = threading.Thread(None, pushserver.serve_forever, None, (), {})
	t1.start()
	t2.start()

