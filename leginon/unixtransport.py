#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import SocketServer
import socket
import leginonobject
import socketstreamtransport
import os
import sys

class Server(SocketServer.ThreadingUnixStreamServer, socketstreamtransport.Server):
	def __init__(self, id, dh, filename = None, path = '.'):
		socketstreamtransport.Server.__init__(self, id, dh)
		if filename is None:
			r = xrange(0, 2**16 - 1)
			files = os.listdir(path)
			for i in r:
				filename = "pipe.%d" % i
				if filename in files:
					filename = None
				else:
					break
			if filename is None:
				raise IOError
		self.filename = path + '/' + filename
		
		SocketServer.ThreadingUnixStreamServer.__init__(self, self.filename, \
				socketstreamtransport.Handler)

	def location(self):
		loc = socketstreamtransport.Server.location(self)
		loc['UNIX pipe filename'] = self.filename
		return loc

	def exit(self):
		os.remove(self.filename)

class Client(socketstreamtransport.Client):
	def __init__(self, id, location, buffer_size = 1024):
		if sys.platform == 'win32':
			raise ValueError
		socketstreamtransport.Client.__init__(self, id, location, buffer_size)

	def connect(self, family = socket.AF_UNIX, type = socket.SOCK_STREAM):
		self.socket = socket.socket(family, type)
		# needs error handling
		try:
			self.socket.connect(self.serverlocation['UNIX pipe filename'])
		except Exception, e:
			if isinstance(e, KeyError):
				raise IOError
			# socket error, connection refused
			if (e[0] == 111 or e[0] == 2):
				self.socket = None
				raise IOError
			else:
				raise


