#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import cPickle as pickle
import data
import socket
import SocketServer
import threading

class ExitException(Exception):
	pass

class Handler(SocketServer.StreamRequestHandler):
	def __init__(self, request, server_address, server):
		SocketServer.StreamRequestHandler.__init__(self, request,
																								server_address, server)

	def handle(self):
		try:
			request = pickle.load(self.rfile)
		except:
			estr = 'Error reading request'
			try:
				self.server.datahandler.logger.exception(estr)
			except AttributeError:
				pass
			return
		
		try:
			result = self.server.datahandler.handle(request)
		except Exception, e:
			estr = 'Error handling request'
			try:
				self.server.datahandler.logger.exception(estr)
			except AttributeError:
				pass
			result = e

		try:
			pickle.dump(result, self.wfile, pickle.HIGHEST_PROTOCOL)
			self.wfile.flush()
		except:
			estr = 'Error responsing to request'
			try:
				self.server.datahandler.logger.exception(estr)
			except AttributeError:
				pass
			return

class Server(object):
	def __init__(self, datahandler):
		self.exitevent = threading.Event()
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

	def location(self):
		return {}

	def exit(self):
		self.exitevent.set()
		client = self.clientclass(self.location())
		try:
			client.send(ExitException())
		except (IOError, EOFError):
			pass

class Client(object):
	def __init__(self, location):
		self.serverlocation = location

	def send(self, request):
		try:
			s = self.connect()
			sfile = s.makefile('wb')
		except:
			raise

		try:
			pickle.dump(request, sfile, pickle.HIGHEST_PROTOCOL)
			sfile.flush()
		except:
			raise

		try:
			result = pickle.load(sfile)
		except:
			raise

		try:
			sfile.close()
		except:
			raise

		return result

	def connect(self):
		raise NotImplementedError

Server.clientclass = Client
Client.serverclass = Server

