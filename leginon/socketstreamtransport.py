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

def localHack(obj):
	try:
		location = obj['location']
	except KeyError:
		location = obj['manager location']

	try:
		ltinstance = location['data binder']['local transport']['instance']
		del location['data binder']['local transport']['instance']
	except KeyError:
		ltinstance = None
	try:
		uiinstance = location['UI']['instance']
		del location['UI']['instance']
	except KeyError:
		uiinstance = None

	p = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)

	if ltinstance is not None:
		location['data binder']['local transport']['instance'] = ltinstance
	if uiinstance is not None:
		location['UI']['instance'] = uiinstance

	return p

class ExitException(Exception):
	pass

class Handler(SocketServer.StreamRequestHandler):
	def __init__(self, request, server_address, server):
		SocketServer.StreamRequestHandler.__init__(self, request,
																								server_address, server)

	def handle(self):
		try:
			obj = pickle.load(self.rfile)
		except (pickle.UnpicklingError, EOFError):
			print 'unpickling error'
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
				pickle.dump(e, self.wfile, pickle.HIGHEST_PROTOCOL)
			except IOError:
				print 'write failed when acknowledging push'
		else:
			### request for data
			o = self.server.datahandler.query(obj)
			try:
				p = pickle.dumps(o, pickle.HIGHEST_PROTOCOL)
			except:
				p = localHack(o)
			self.wfile.write(p)

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
		except (IOError, EOFError):
			pass

class Client(object):
	def __init__(self, location):
		self.serverlocation = location
		self.socket = None

	def pull(self, id):
		self.connect()
		self.send(pickle.dumps(id, pickle.HIGHEST_PROTOCOL))
		data = self.receive()
		self.close()
		try:
			return pickle.loads(data)
		except:
			raise IOError

	def push(self, idata):
		try:
			self.connect()
		except socket.error, e:
			raise IOError('connect to server failed')
		try:
			p = pickle.dumps(idata, pickle.HIGHEST_PROTOCOL)
		except:
			p = localHack(idata)
		self.send(p)
		serverexception = pickle.loads(self.receive())
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
