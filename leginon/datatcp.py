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
		pickle.dump(self.server.datafromid(data_id[:-1]), self.wfile)

class PushHandler(SocketServer.StreamRequestHandler, leginonobject.LeginonObject):
	def __init__(self, request, server_address, server):
		# not sure it needs to be a LeginonObject
		leginonobject.LeginonObject.__init__(self)
		SocketServer.StreamRequestHandler.__init__(self, request, server_address, server)

	def handle(self):
		# needs error checking, cPickle attempt
		# data_id needs to be send with a newline
		data = pickle.load(self.rfile)
		# temporarily making data a dictionary w/ actual data and data id
		self.server.datatoid(data['data id'], data['data'])

class Server(SocketServer.ThreadingTCPServer, leginonobject.LeginonObject):
	def __init__(self, server, handler, port=None):
		leginonobject.LeginonObject.__init__(self)
		self.server = server
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

	def datafromid(self, data_id):
		return self.server.datafromid(data_id)

	def datatoid(self, data_id, data):
		return self.server.datatoid(data_id, data)

# pull is a function for now, until a client class seems reasonable
class Client(leginonobject.LeginonObject):
	def __init__(self, hostname, port, buffer_size = 1024):
		self.buffer_size = buffer_size 
		leginonobject.LeginonObject.__init__(self)
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def pull(self, data_id):
		data = ""
		self.socket.connect((hostname, port)) # Connect to server
		# needs to account for different data_id datatypes
		self.socket.send("%s\n" % data_id)
		while 1:
		  r = self.socket.recv(self.buffer_size) # Receive up to buffer_size bytes
		  if not r:
		    break
		  data += r
		self.socket.close()
		# needs cPickle attempt
		return pickle.loads(data)

	def push(self, data):
		# needs to account for different data_id datatypes
		self.socket.connect((hostname, port)) # Connect to server
		self.socket.send(pickle.dumps(data))
		self.socket.close()

if __name__ == '__main__':
	import threading

	class dummyServer:
		def datafromid(self, data_id):
			return {data_id : 'foo bar'}
		def datatoid(self, data_id, data):
			print `{data_id : data}`

	pullserver = Server(dummyServer(), PullHandler)
	pushserver = Server(dummyServer(), PushHandler)
	print 'pull server at:', pullserver.server_address
	print 'push server at:', pushserver.server_address
	t1 = threading.Thread(None, pullserver.serve_forever, None, (), {})
	t2 = threading.Thread(None, pushserver.serve_forever, None, (), {})
	t1.start()
	t2.start()

