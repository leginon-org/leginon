#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import cPickle
import data
import socket
import SocketServer
import threading

class Handler(SocketServer.StreamRequestHandler):
	def __init__(self, request, server_address, server):
		SocketServer.StreamRequestHandler.__init__(self, request,
																								server_address, server)

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
				cPickle.dump(e, self.wfile, True)
			except IOError:
				print('write failed when acknowledging push')
		else:
			try:
				self.wfile.write(cPickle.dumps(self.server.datahandler.query(obj),
																				True))
			except IOError:
				print('write failed when returning requested data')

class Server(object):
	def __init__(self, dh):
		self.datahandler = dh
		self.hostname = socket.gethostname()

	def start(self):
		self.thread = threading.Thread(name='socket server thread',
																		target=self.serve_forever)
		self.thread.setDaemon(1)
		self.thread.start()

	def location(self):
		return {'hostname': self.hostname}

	def exit(self):
		pass

class Client(object):
	def __init__(self, location):
		self.serverlocation = location
		self.socket = None

	def pull(self, id):
		self.connect()
		self.send(cPickle.dumps(id, True))
		data = self.receive()
		self.close()
		return cPickle.loads(data)

	def push(self, idata):
		self.connect()
		self.send(cPickle.dumps(idata, 1))
		serverexception = cPickle.loads(self.receive())
		self.close()
		if serverexception is not None:
			self.printerror('server failed to be pushed')
			raise IOError

	def connect(self, family, type=socket.SOCK_STREAM):
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

	def receive(self):
		data = ''
		if self.socket is not None:
			# this seems to set up buffering in an optimized way
			# without having to manually specify it
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

