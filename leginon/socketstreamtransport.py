#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#

import cPickle as pickle
import socket
import SocketServer
import threading
import datatransport


# from Tao of Mac
# Hideous fix to counteract http://python.org/sf/1092502
# (which should have been fixed ages ago.)
def _fixed_socket_read(self, size=-1):
	data = self._rbuf
	if size < 0:
		# Read until EOF
		buffers = []
		if data:
			buffers.append(data)
		self._rbuf = ""
		if self._rbufsize <= 1:
			recv_size = self.default_bufsize
		else:
			recv_size = self._rbufsize
		while True:
			data = self._sock.recv(recv_size)
			if not data:
				break
			buffers.append(data)
		return "".join(buffers)
	else:
		# Read until size bytes or EOF seen, whichever comes first
		buf_len = len(data)
		if buf_len >= size:
			self._rbuf = data[size:]
			return data[:size]
		buffers = []
		if data:
			buffers.append(data)
		self._rbuf = ""
		while True:
			left = size - buf_len
			recv_size = min(self._rbufsize, left)
			data = self._sock.recv(recv_size)
			if not data:
				break
			buffers.append(data)
			n = len(data)
			if n >= left:
				self._rbuf = data[left:]
				buffers[-1] = data[:left]
				break
			buf_len += n
		return "".join(buffers)
#		while True:
#				left = size - buf_len
#				recv_size = min(self._rbufsize, left) # this is the actual fix
#				data = self._sock.recv(recv_size)
#		return "".join(buffers)

# patch the method at runtime
## Newer versions of python already have a fix using StringIO.
## Only apply our fix here if StringIO is not in socket module.
if not hasattr(socket, 'StringIO'):
	socket._fileobject.read = _fixed_socket_read

class ExitException(Exception):
	pass

class TransportError(datatransport.TransportError):
	pass

class Handler(SocketServer.StreamRequestHandler):
	def __init__(self, request, server_address, server):
		SocketServer.StreamRequestHandler.__init__(self, request,
																								server_address, server)

	def handle(self):
		try:
			request = pickle.load(self.rfile)
		except Exception, e:
			estr = 'error reading request, %s' % e
			try:
				self.server.datahandler.logger.exception(estr)
			except AttributeError:
				pass
			return

		if isinstance(request, ExitException):
			result = None
		else:
			try:
				result = self.server.datahandler.handle(request)
			except Exception, e:
				estr = 'error handling request, %s' % e
				try:
					self.server.datahandler.logger.exception(estr)
				except AttributeError:
					pass
				result = e

		try:
			pickle.dump(result, self.wfile, pickle.HIGHEST_PROTOCOL)
			self.wfile.flush()
		except Exception, e:
			estr = 'error responding to request, %s' % e
			try:
				self.server.datahandler.logger.exception(estr)
			except AttributeError:
				pass
			return

class Server(object):
	def __init__(self, datahandler):
		self.exitevent = threading.Event()
		self.exitedevent = threading.Event()
		self.datahandler = datahandler
		self.hostname = socket.gethostname().lower()

	def start(self):
		self.thread = threading.Thread(name='socket server thread',
																		target=self.serve_forever)
		self.thread.setDaemon(1)
		self.thread.start()

	def serve_forever(self):
		while not self.exitevent.isSet():
			self.handle_request()
		self.exitedevent.set()

	def exit(self):
		self.exitevent.set()
		client = self.clientclass(self.location())
		client.send(ExitException())
		self.exitedevent.wait()

	def location(self):
		return {}

class Client(object):
	def __init__(self, location):
		self.serverlocation = location

	def send(self, request):
		s = self.connect()
		try:
			sfile = s.makefile('rwb')
		except Exception, e:
			raise TransportError('error creating socket file, %s' % e)
			
		try:
			pickle.dump(request, sfile, pickle.HIGHEST_PROTOCOL)
		except Exception, e:
			raise TransportError('error pickling request, %s' % e)

		try:
			sfile.flush()
		except Exception, e:
			raise TransportError('error flushing socket file buffer, %s' % e)

		try:
			result = pickle.load(sfile)
		except Exception, e:
			raise TransportError('error unpickling response, %s' % e)

		try:
			sfile.close()
		except:
			pass

		return result

	def connect(self):
		raise NotImplementedError

Server.clientclass = Client
Client.serverclass = Server

