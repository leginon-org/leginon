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
			print "socket transport: no data to read, handle socket connection failed"
			return

		if isinstance(obj, data.Data):
			# if is data, then pushed
			e = None
			try:
				self.server.datahandler.insert(obj)
			except Exception, e:
				print "socket transport: failed to insert pushed data"
				raise
			try:
				# returns exception if error, else None
				cPickle.dump(e, self.wfile, 1)
			except IOError:
				print "socket transport: write failed when acknowledging push"
		else:
			try:
				cPickle.dump(self.server.datahandler.query(obj), self.wfile, 1)
			except IOError:
				print "socket transport: write failed when returning requested data"

class Server(leginonobject.LeginonObject):
	def __init__(self, id, dh):
		leginonobject.LeginonObject.__init__(self, id)
		self.datahandler = dh

	def start(self):
		self.thread = threading.Thread(name='socket server thread', target=self.serve_forever)
		self.thread.setDaemon(1)
		self.thread.start()

	def location(self):
		return leginonobject.LeginonObject.location(self)

	def exit(self):
		pass

class Client(leginonobject.LeginonObject):
	def __init__(self, id, location, buffer_size = 1024):
		leginonobject.LeginonObject.__init__(self, id)
		self.serverlocation = location
		self.socket = None
		self.buffer_size = buffer_size

	def pull(self, id):
		self.connect()
		idpickle = cPickle.dumps(id, 1)
		self.send(idpickle)
		data = self.receive()
		self.close()
		return cPickle.loads(data)

	def push(self, idata):
		self.connect()
		self.send(cPickle.dumps(idata, 1))
		serverexception = cPickle.loads(self.receive())
		self.close()
		if serverexception is not None:
			print "socket transport, push: server failed to be pushed"
			raise IOError

	def connect(self, family, type = socket.SOCK_STREAM):
		raise NotImplementedError

	def send(self, odata):
		if self.socket:
			self.socket.send(odata)
		else:
			print "socket transport, send: no socket available"
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
			print "socket transport, receive: no socket available"
			raise IOError

	def close(self):
		if self.socket:
			self.socket.close()
		else:
			print "socket transport, close: no socket available"
			raise IOError

