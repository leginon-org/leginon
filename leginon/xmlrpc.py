#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import SimpleXMLRPCServer
import threading
import socket
import extendedxmlrpclib

# range defined by IANA as dynamic/private
portrange = xrange(49152, 65536)

class Server(object):
	"""
	A SimpleXMLRPCServer that figures out its own host and port
	Sets self.host and self.port accordingly
	"""
	def __init__(self, port=None):
		self.hostname = socket.gethostname().lower()

		self.port = port
		if self.port is not None:
			# this exception will fall through if __init__ fails
			self.xmlrpcserver = SimpleXMLRPCServer.SimpleXMLRPCServer(
																	(self.hostname, self.port), logRequests=False)
			self._startServing()
			return

		# find a port in range defined by IANA as dynamic/private
		for self.port in portrange:
			try:
				self.xmlrpcserver = SimpleXMLRPCServer.SimpleXMLRPCServer(
																										(self.hostname, self.port),
																										logRequests=False)
				break
			except Exception, var:
				if var[0] in [48, 98, 112, 10048]:
					continue
				else:
					raise
		if self.port is None:
			raise RuntimeError('no ports available')

		self._startServing()

	def _startServing(self):
		t = threading.Thread(name='UI XML-RPC server thread',
													target=self.xmlrpcserver.serve_forever)
		t.setDaemon(1)
		t.start()
		self.serverthread = t

class Client(object):
	def __init__(self, serverhostname, serverport, port=None):
		self.serverhostname = serverhostname
		self.serverport = serverport
		uri = 'http://%s:%s' % (serverhostname, serverport)
		self.proxy = extendedxmlrpclib.ServerProxy(uri, allow_none=1)

	def execute(self, function_name, args=()):
		try:
			return getattr(self.proxy, function_name)(*args)
		except extendedxmlrpclib.ProtocolError:
			# usually return value not correct type
			raise
		except extendedxmlrpclib.Fault:
			# exception during call of the function
			raise

