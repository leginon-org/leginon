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
			print 'SSSS'
			t1 = time.clock()
			obj = cPickle.load(self.rfile)
			t2 = time.clock()
			tdiff = t2 - t1
			print 'TTTT cPickle.load', tdiff
		except EOFError:
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
				print 'socketstreamserver dumping 111', tdiff
				t1 = time.clock()
				cPickle.dump(e, self.wfile, 1)
				t2 = time.clock()
				tdiff = t2 - t1
				print 'TTTT cPickle.dump Data instance', tdiff
			except IOError:
				print('write failed when acknowledging push')
		else:
			try:
				print 'datahandler query'
				newdata = self.server.datahandler.query(obj)
				print 'datahandler query done'

				print 'socketstreamserver dumping 222'
				t1 = time.clock()
				cPickle.dump(newdata, self.wfile, 1)
				t2 = time.clock()
				tdiff = t2 - t1
				print 'TTTT cPickle.dump not Data instance', tdiff
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
	def __init__(self, id, location, buffer_size = 1024):
		leginonobject.LeginonObject.__init__(self, id)
		self.serverlocation = location
		self.socket = None
		self.buffer_size = buffer_size

	def pull(self, id):
		self.connect()

		print 'SSSS'
		t1 = time.clock()
		idpickle = cPickle.dumps(id, 1)
		t2 = time.clock()
		tdiff = t2 - t1
		print 'TTTT cPickle.dumps pull idpickle', tdiff

		self.send(idpickle)
		print 'receive'
		data = self.receive()
		print 'receive done'
		self.close()

		print 'SSSS'
		t1 = time.clock()
		p = cPickle.loads(data)
		t2 = time.clock()
		tdiff = t2 - t1
		print 'TTTT cPickle.loads pull data', tdiff

		return p

	def push(self, idata):
		self.connect()

		print 'SSSS'
		t1 = time.clock()
		p = cPickle.dumps(idata, 1)
		t2 = time.clock()
		tdiff = t2 - t1
		print 'TTTT cPickle.dumps push data', tdiff

		self.send(p)
		r = self.receive()

		print 'SSSS'
		t1 = time.clock()
		serverexception = cPickle.loads(r)
		t2 = time.clock()
		tdiff = t2 - t1
		print 'TTTT cPickle.loads push data', tdiff

		self.close()
		if serverexception is not None:
			self.printerror('server failed to be pushed')
			raise IOError

	def connect(self, family, type = socket.SOCK_STREAM):
		raise NotImplementedError

	def send(self, odata):
		if self.socket is not None:
			self.socket.send(odata)
		else:
			self.printerror('no socket available')
			raise IOError

	def receive(self):
		data = ""
		if self.socket is not None:
			while 1:
			  r = self.socket.recv(self.buffer_size) # Receive up to buffer_size bytes
			  if not r:
			    break
			  data += r
			return data
		else:
			self.printeror('no socket available')
			raise IOError

	def close(self):
		if self.socket is not None:
			self.socket.close()
		else:
			self.printerror('no socket available')
			raise IOError


