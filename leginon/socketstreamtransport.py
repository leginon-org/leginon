import SocketServer
import cPickle
import socket
import leginonobject
import data
import threading
import time

class Handler(SocketServer.StreamRequestHandler):
	def __init__(self, request, server_address, server):
		SocketServer.StreamRequestHandler.__init__(self, request, server_address, server)

	def handle(self):
		try:
			obj = cPickle.load(self.rfile)
		except (cPickle.UnpicklingError, EOFError):
			print('no data to read, handle socket connection failed')
			return

		if isinstance(obj, data.Data):
			# if is data, then pushed
			e = None
			try:
				self.server.datahandler.insert(obj)
			except Exception, e:
				print('failed to insert pushed data')
				raise
			try:
				# returns exception if error, else None
				cPickle.dump(e, self.wfile, 1)
			except IOError:
				print('write failed when acknowledging push')
		else:
			try:
				newdata = self.server.datahandler.query(obj)

				s = cPickle.dumps(newdata, 1)
				self.wfile.write(s)

			except IOError:
				print('write failed when returning requested data')

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
	def __init__(self, id, location):
		leginonobject.LeginonObject.__init__(self, id)
		self.serverlocation = location
		self.socket = None

	def pull(self, id):
		self.connect()
		idpickle = cPickle.dumps(id, 1)
		self.send(idpickle)
		data = self.receive()
		self.close()
		p = cPickle.loads(data)
		return p

	def push(self, idata):
		self.connect()
		p = cPickle.dumps(idata, 1)
		self.send(p)
		r = self.receive()
		serverexception = cPickle.loads(r)

		self.close()
		if serverexception is not None:
			self.printerror('server failed to be pushed')
			raise IOError

	def connect(self, family, type = socket.SOCK_STREAM):
		raise NotImplementedError

	def send(self, odata):
		try:
			if self.socket is not None:
				self.socket.send(odata)
			else:
				raise Exception('no socket available')
		except Exception, e:
			self.printerror('socket send exception: %s' % str(e))
			raise IOError

	def OLDreceive(self):
		data = ""
		if self.socket is not None:
			while 1:
			  r = self.socket.recv(self.buffer_size) # Receive up to buffer_size bytes
			  if not r:
			    break
			  data += r
			return data
		else:
			self.printerror('no socket available')
			raise IOError

	def receive(self):
		data = ""
		if self.socket is not None:
			## this seems to set up buffering in an optimized way
			## without having to manually specify it
			f = self.socket.makefile('r')
			data = f.read()
			f.close()
			return data
		else:
			self.printerror('no socket available')
			raise IOError

	def close(self):
		if self.socket is not None:
			self.socket.close()
		else:
			self.printerror('no socket available')
			raise IOError
