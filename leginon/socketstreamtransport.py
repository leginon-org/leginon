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

def localHack(obj):
	try:
		location = obj['location']
	except (KeyError):
		try:
			location = obj['node locations']['manager']
		except (KeyError, IndexError):
			raise

	try:
		ltinstance = location['data transport']['local transport']['instance']
		del location['data transport']['local transport']['instance']
	except KeyError:
		ltinstance = None
	try:
		uiinstance = location['UI']['instance']
		del location['UI']['instance']
	except KeyError:
		uiinstance = None

	pickle = cPickle.dumps(obj, cPickle.HIGHEST_PROTOCOL)

	if ltinstance is not None:
		location['data transport']['local transport']['instance'] = ltinstance
	if uiinstance is not None:
		location['UI']['instance'] = uiinstance

	return pickle

class ExitException(Exception):
	pass

class Handler(SocketServer.StreamRequestHandler):
	def __init__(self, request, server_address, server):
		SocketServer.StreamRequestHandler.__init__(self, request,
																								server_address, server)

	def handle(self):
		try:
			obj = cPickle.load(self.rfile)
		except (cPickle.UnpicklingError, EOFError):
			print 'no data to read, handle socket connection failed'
			return
		
		if isinstance(obj, ExitException):
			return

		if isinstance(obj, data.Data):
			# if is data, then pushed
			e = None
			try:
				self.server.datahandler.insert(obj)
			except Exception, e:
				print 'failed to insert pushed data'
				raise
			try:
				# returns exception if error, else None
				cPickle.dump(e, self.wfile, cPickle.HIGHEST_PROTOCOL)
			except IOError:
				print 'write failed when acknowledging push'
		else:
			try:
				try:
					self.wfile.write(cPickle.dumps(self.server.datahandler.query(obj),
																					cPickle.HIGHEST_PROTOCOL))
				except cPickle.UnpickleableError:
					try:
						self.wfile.write(localHack(self.server.datahandler.query(obj)))
					except:
						print 'cannot transport unpickleable data'
						raise IOError
			except IOError:
				print 'write failed when returning requested data'

class Server(object):
	def __init__(self, dh):
		self.exitevent = threading.Event()
		self.datahandler = dh
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
			client.push(ExitException())
		except EOFError:
			pass

class Client(object):
	def __init__(self, location):
		self.serverlocation = location
		self.socket = None

	def pull(self, id):
		self.connect()
		self.send(cPickle.dumps(id, cPickle.HIGHEST_PROTOCOL))
		data = self.receive()
		self.close()
		try:
			return cPickle.loads(data)
		except:
			raise IOError

	def push(self, idata):
		try:
			self.connect()
		except socket.error, e:
			raise IOError('connect to server failed')
		try:
			self.send(cPickle.dumps(idata, cPickle.HIGHEST_PROTOCOL))
		except cPickle.UnpickleableError:
			try:
				self.send(localHack(idata))
			except:
				raise IOError('cannot push unpickleable data')
		serverexception = cPickle.loads(self.receive())
		self.close()
		if serverexception is not None:
			raise IOError('server failed to be pushed')

	def connect(self, family, type=socket.SOCK_STREAM):
		raise NotImplementedError

	def send(self, odata):
		try:
			if self.socket is not None:
				self.socket.send(odata)
			else:
				raise Exception('no socket available')
		except Exception, e:
			raise IOError('socket send exception: %s' % str(e))

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
			raise IOError('no socket available')

	def close(self):
		if self.socket is not None:
			self.socket.close()
		else:
			raise IOError('no socket available')

Server.clientclass = Client
Client.serverclass = Server
