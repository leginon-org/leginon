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

locationkey = 'TCP transport'

class Server(socketstreamtransport.Server, SocketServer.ThreadingTCPServer):
	def __init__(self, dh, port=None):
		socketstreamtransport.Server.__init__(self, dh)

		# instantiater can choose a port or we'll choose one for them
		if port is not None:
			SocketServer.ThreadingTCPServer.__init__(self, ('', port),
																								socketstreamtransport.Handler)
		else:
			# range define by IANA as dynamic/private or so says Jim
			portrange = (49152,65536)
			# start from the bottom
			port = portrange[0]
			# iterate to the top or until unused port is found
			while port <= portrange[1]:
				try:
					SocketServer.ThreadingTCPServer.__init__(self, ('', port),
																									socketstreamtransport.Handler)
					break
				except Exception, var:
					# socket error, address already in use
					if var[0] in [48, 98, 112, 10048]:
						port += 1
					else:
						raise
		self.request_queue_size = 15
		self.port = port

	def location(self):
		location = socketstreamtransport.Server.location(self)
		location['hostname'] = socket.gethostname().lower()
		location['port'] = self.port
		return location

	def exit(self):
		socketstreamtransport.Server.exit(self)
		self.server_close()

class Client(socketstreamtransport.Client):
	def __init__(self, location):
		socketstreamtransport.Client.__init__(self, location)

	def connect(self, family=socket.AF_INET, type=socket.SOCK_STREAM):
		s = socket.socket(family, type)
		try:
			hostname = self.serverlocation['hostname']
			port = self.serverlocation['port']
		except KeyError:
			raise IOError('cannot get location')
		try:
			s.connect((hostname, port))
		except Exception, e:
			if e[0] in [111, 10061]:
				raise IOError('unable to connect to %s:%s' % (hostname, port))
			else:
				raise
		return s

Server.clientclass = Client
Client.serverclass = Server

