import SocketServer
import cPickle
import socket
import leginonobject
import data

class Handler(SocketServer.StreamRequestHandler):
	def __init__(self, request, server_address, server):
		SocketServer.StreamRequestHandler.__init__(self, request, server_address, server)

	def read(self):
		return cPickle.load(self.rfile)

	def write(self, o):
		cPickle.dump(o, self.wfile)

class PushHandler(Handler):
	def __init__(self, request, server_address, server):
		Handler.__init__(self, request, server_address, server)

	def _handle(self, idata):
		self.server.datahandler.insert(idata)

	def handle(self):
		idata = self.read()
		self._handle(idata)

class PullHandler(Handler):
	def __init__(self, request, server_address, server):
		Handler.__init__(self, request, server_address, server)

	def _handle(self, id):
		self.write(self.server.datahandler.query(id))

	def handle(self):
		id = self.read()
		self._handle(id)

class PushPullHandler(PushHandler, PullHandler):
	def __init__(self, request, server_address, server):
		PushHandler.__init__(self, request, server_address, server)
		#PullHandler.__init__(self, request, server_address, server)

	def handle(self):
		obj = self.read()
		if isinstance(obj, data.Data):
			# if is data, then push
			PushHandler._handle(self, obj)
		else:
			# (elif when ID has a type) its and ID -> pull (query) by ID
			PullHandler._handle(self, obj)

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
	def pull(self, id, family = socket.AF_INET, type = socket.SOCK_STREAM):
		print 'PullClient.pull id = %s' % id
		data = ""
		s = socket.socket(family, type)
		s.connect((self.hostname, self.port)) # Connect to server
		idpickle = cPickle.dumps(id)
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

class PushPullClient(PushClient, PullClient):
	pass

