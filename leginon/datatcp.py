#!/usr/bin/env python

import SocketServer
import pickle
import socket
import leginonobject

class PullHandler(SocketServer.StreamRequestHandler, leginonobject.LeginonObject):
	def __init__(self, request, server_address, server):
		# not sure it needs to be a LeginonObject
		leginonobject.LeginonObject.__init__(self)
		SocketServer.StreamRequestHandler.__init__(self, request, server_address, server)

	def handle(self):
		# needs error checking, cPickle attempt
		# data_id needs to be send with a newline
		data_id = self.rfile.readline()
		# pickle the data from data_id (w/o the trailing newline char)
		data = self.server.datakeeper.query(data_id)
		pickle.dump(data, self.wfile)

class PushHandler(SocketServer.StreamRequestHandler, leginonobject.LeginonObject):
	def __init__(self, request, server_address, server):
		# not sure it needs to be a LeginonObject
		leginonobject.LeginonObject.__init__(self)
		SocketServer.StreamRequestHandler.__init__(self, request, server_address, server)

	def handle(self):
		# needs error checking, cPickle attempt
		# data_id needs to be send with a newline
		newdata = pickle.load(self.rfile)
		print 'received newdata %s' % newdata
		self.server.datakeeper.insert(newdata)
		#self.server.server.handle_data(newdata)
		# temporarily making data a dictionary w/ actual data and data id
		#self.server.datatoid(data['data id'], data['data'])

class Server(SocketServer.ThreadingTCPServer, leginonobject.LeginonObject):
	def __init__(self, dk, handler, port=None):
		leginonobject.LeginonObject.__init__(self)
		self.datakeeper = dk
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
					if var[0] == 98: # socket error, address already in use
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

# pull is a function for now, until a client class seems reasonable
class Client(leginonobject.LeginonObject):
	def __init__(self, hostname, port, buffer_size = 1024):
		self.buffer_size = buffer_size 
		leginonobject.LeginonObject.__init__(self)
		self.hostname = hostname
		self.port = port

class PullClient(Client):
	def pull(self, data_id):
		data = ""
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.hostname, self.port)) # Connect to server
		# needs to account for different data_id datatypes
		s.send("%s\n" % data_id)
		while 1:
		  r = s.recv(self.buffer_size) # Receive up to buffer_size bytes
		  if not r:
		    break
		  data += r
		s.close()
		# needs cPickle attempt
		return pickle.loads(data)

class PushClient(Client):
	def push(self, data):
		# needs to account for different data_id datatypes
		print 'socket connect:  %s %s' % (self.hostname, self.port)
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.hostname, self.port)) # Connect to server
		s.send(pickle.dumps(data))
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

