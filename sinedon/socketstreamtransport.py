#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import pickle
import socketserver as SocketServer
import threading
from pyami import mysocket

class ExitException(Exception):
	pass

class TransportError(IOError):
	pass

class Handler(SocketServer.StreamRequestHandler):
	def __init__(self, request, server_address, server):
		SocketServer.StreamRequestHandler.__init__(self, request,
																								server_address, server)

	def handle(self):
		try:
			request = pickle.load(self.rfile)
		except Exception as e:
			estr = 'error reading request, %s' % e
			try:
				self.server.datamanager.logger.exception(estr)
			except AttributeError:
				pass
			return

		if isinstance(request, ExitException):
			result = None
		else:
			try:
				result = self.server.datamanager.handle(request)
			except Exception as e:
				estr = 'error handling request, %s' % e
				try:
					self.server.datamanager.logger.exception(estr)
				except AttributeError:
					pass
				result = e

		try:
			pickle.dump(result, self.wfile, pickle.HIGHEST_PROTOCOL)
			self.wfile.flush()
		except Exception as e:
			estr = 'error responding to request, %s' % e
			try:
				self.server.datamanager.logger.exception(estr)
			except AttributeError:
				pass
			return

class Server(object):
	def __init__(self, datamanager):
		self.exitevent = threading.Event()
		self.exitedevent = threading.Event()
		self.datamanager = datamanager
		self.hostname = mysocket.gethostname().lower()

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
		except Exception as e:
			raise TransportError('error creating socket file, %s' % e)
			
		try:
			pickle.dump(request, sfile, pickle.HIGHEST_PROTOCOL)
		except Exception as e:
			raise TransportError('error pickling request, %s' % e)

		try:
			sfile.flush()
		except Exception as e:
			raise TransportError('error flushing socket file buffer, %s' % e)

		result = pickle.load(sfile)

		try:
			sfile.close()
		except:
			pass

		return result

	def connect(self):
		raise NotImplementedError

Server.clientclass = Client
Client.serverclass = Server

