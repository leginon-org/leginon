import SocketServer
import socket
import leginonobject
import socketstreamtransport

class Server(SocketServer.ThreadingTCPServer, socketstreamtransport.Server):
	def __init__(self, id, dh, port=None):
		socketstreamtransport.Server.__init__(self, id, dh)

		# instantiater can choose a port or we'll choose one for them
		if port:
			SocketServer.ThreadingTCPServer.__init__(self, ('', port), \
				socketstreamtransport.Handler)
		else:
			# range define by IANA as dynamic/private or so says Jim
			portrange = (49152,65536)
			# start from the bottom
			port = portrange[0]
			# iterate to the top or until unused port is found
			while port <= portrange[1]:
				try:
					SocketServer.ThreadingTCPServer.__init__(self, ('', port), socketstreamtransport.Handler)
					break
				except Exception, var:
					# socket error, address already in use
					if (var[0] == 98 or var[0] == 10048 or var[0] == 112):
						port += 1
					else:
						raise
			self.port = port

	def location(self):
		loc = socketstreamtransport.Server.location(self)
		loc['TCP port'] = self.port
		return loc

class Client(socketstreamtransport.Client):
	def __init__(self, id, location, buffer_size = 1024):
		socketstreamtransport.Client.__init__(self, id, location, buffer_size)

	def connect(self, family = socket.AF_INET, type = socket.SOCK_STREAM):
		self.socket = socket.socket(family, type)
		try:
			self.socket.connect((self.serverlocation['hostname'], self.serverlocation['TCP port']))
		except Exception, var:
			# socket error, connection refused
			if (var[0] == 111):
				self.socket = None
				print "tcptransport, receive: unable to connect to", self.serverlocation['hostname'], "port", self.serverlocation['TCP port']
				raise IOError
			else:
				raise
