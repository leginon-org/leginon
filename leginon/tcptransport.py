import SocketServer
import cPickle
import socket
import leginonobject
import data
import threading
import copy
import time

class Handler(SocketServer.StreamRequestHandler):
	def __init__(self, request, server_address, server):
		SocketServer.StreamRequestHandler.__init__(self, request, server_address, server)

	def handle(self):
		try:
			obj = cPickle.load(self.rfile)
		except EOFError:
			print "tcptransport: no data to read, handle TCP connection failed"
			return

		if isinstance(obj, data.Data):
			# if is data, then push
			e = None
			try:
				self.server.datahandler.insert(obj)
			except Exception, e:
				print "tcptransport: failed to insert pushed data"
			try:
				# returns exception if error, else None
				cPickle.dump(e, self.wfile)
			except IOError:
				print "tcptransport: write failed when acknowledging push"
		else:
			try:
				cPickle.dump(self.server.datahandler.query(obj), self.wfile)
			except IOError:
				print "tcptransport: write failed when returning requested data"

class Server(SocketServer.ThreadingTCPServer, leginonobject.LeginonObject):
	def __init__(self, id, dh, port=None):
		leginonobject.LeginonObject.__init__(self, id)
		self.datahandler = dh

		# instantiater can choose a port or we'll choose one for them
		if port:
			SocketServer.ThreadingTCPServer.__init__(self, ('', port), Handler)
		else:
			# range define by IANA as dynamic/private or so says Jim
			portrange = (49152,65536)
			# start from the bottom
			port = portrange[0]
			# iterate to the top or until unused port is found
			while port <= portrange[1]:
				try:
					SocketServer.ThreadingTCPServer.__init__(self, ('', port), Handler)
					break
				except Exception, var:
					# socket error, address already in use
					if (var[0] == 98 or var[0] == 10048 or var[0] == 112):
						port += 1
					else:
						raise
			self.port = port

	def start(self):
		self.thread = threading.Thread(None, self.serve_forever, None, (), {})
		self.thread.setDaemon(1)
		self.thread.start()

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc['TCP port'] = self.port
		return loc

class Client(leginonobject.LeginonObject):
	def __init__(self, id, location, buffer_size = 1024):
		self.buffer_size = buffer_size 
		leginonobject.LeginonObject.__init__(self, id)
		self.serverlocation = location
		self.socket = None

	def pull(self, id, family = socket.AF_INET, type = socket.SOCK_STREAM):
		self.connect()
		idpickle = cPickle.dumps(id)
		self.send(idpickle)
		data = self.receive()
		self.close()
		return cPickle.loads(data)

	def push(self, idata):
		self.connect()
		self.send(cPickle.dumps(idata))
		serverexception = cPickle.loads(self.receive())
		self.close()
		if serverexception != None:
			raise serverexception

	def connect(self, family = socket.AF_INET, type = socket.SOCK_STREAM):
		self.socket = socket.socket(family, type)
		try:
			self.socket.connect((self.serverlocation['hostname'], self.serverlocation['TCP port']))
		except Exception, var:
			# socket error, connection refused
			if (var[0] == 111):
				self.socket = None
				print "tcptransport, receive: unable to connect to", self.serverlocation['hostname'], "port", self.serverlocation['TCP port']
				raise IOError

	def send(self, odata):
		if self.socket:
			self.socket.send(odata)
		else:
			print "tcptransport, send: no socket available"
			raise IOError

	def receive(self):
		data = ""
		if self.socket:
			while 1:
			  r = self.socket.recv(self.buffer_size) # Receive up to buffer_size bytes
			  if not r:
			    break
			  data += r
			return data
		else:
			print "tcptransport, receive: no socket available"
			raise IOError

	def close(self):
		if self.socket:
			self.socket.close()
		else:
			print "tcptransport, close: no socket available"
			raise IOError

