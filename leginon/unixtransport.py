#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import SocketServer
import socket
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

	def connect(self, family=socket.AF_UNIX, type=socket.SOCK_STREAM):
		s = socket.socket(family, type)
		try:
			filename = self.serverlocation['UNIX pipe filename']
		except KeyError:
			raise IOError('cannot get location')
		try:
			s.connect(filename)
		except Exception, e:
			if e[0] in [2, 111]:
				raise IOError('unable to connect to %s' % filename)
			else:
				raise
		return s

