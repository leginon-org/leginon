import SocketServer
import socket
import leginonobject
import socketstreamtransport
import os
import sys

class Server(SocketServer.ThreadingUnixStreamServer, socketstreamtransport.Server):
	def __init__(self, id, dh, filename = None, path = '.'):
		socketstreamtransport.Server.__init__(self, id, dh)
		if filename == None:
			r = xrange(0, 2**16 - 1)
			files = os.listdir(path)
			for i in r:
				filename = "pipe.%d" % i
				if filename in files:
					filename = None
				else:
					break
			if filename == None:
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
		except Exception, var:
			# socket error, connection refused
			if (var[0] == 111):
				self.socket = None
				print "unix transport, receive: unable to connect to", \
						self.serverlocation['UNIX pipe filename']
				raise IOError
			else:
				raise


