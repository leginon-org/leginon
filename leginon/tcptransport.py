import SocketServer
import cPickle
import socket
import leginonobject
import data
import threading
import copy
import time

class Handler(SocketServer.StreamRequestHandler):
	def __init__(self, request, server_address, server):
		SocketServer.StreamRequestHandler.__init__(self, request, server_address, server)

	def handle(self):
		try:
			obj = cPickle.load(self.rfile)
		except EOFError:
			return
		if isinstance(obj, data.Data):
			# if is data, then push
			self.server.datahandler.insert(obj)
		else:
			# (elif when ID has a type) its and ID -> pull (query) by ID
			#idata = self.server.datahandler.query(obj)
			#starttime = time.time()
			#cPickle.dump(idata, self.wfile)
			#print "tcptransport.py, cPickle dumps", time.time() - starttime, "secs."
			try:
				cPickle.dump(self.server.datahandler.query(obj), self.wfile)
			except IOError:
				print "tcptransport: write failed"

class Server(SocketServer.ThreadingTCPServer, leginonobject.LeginonObject):
	def __init__(self, id, dh, port=None):
		leginonobject.LeginonObject.__init__(self, id)
		self.datahandler = dh
		# instantiater can choose a port or we'll choose one for them
		if port:
			SocketServer.ThreadingTCPServer.__init__(self, ('', port), Handler)
		else:
			# range define by IANA as dynamic/private or so says Jim
			portrange = (49152,65536)
			# start from the bottom
			port = portrange[0]
			# iterate to the top or until unused port is found
			while port <= portrange[1]:
				try:
					SocketServer.ThreadingTCPServer.__init__(self, ('', port), Handler)
					break
				except Exception, var:
					# socket error, address already in use
					if (var[0] == 98 or var[0] == 10048):
						port += 1
					else:
						raise
			self.port = port

	def start(self):
		self.thread = threading.Thread(None, self.serve_forever, None, (), {})
		self.thread.setDaemon(1)
		self.thread.start()

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc['TCP port'] = self.port
		return loc

class Client(leginonobject.LeginonObject):
	def __init__(self, id, location, buffer_size = 1024):
		self.buffer_size = buffer_size 
		leginonobject.LeginonObject.__init__(self, id)
		self.serverlocation = location

	def pull(self, id, family = socket.AF_INET, type = socket.SOCK_STREAM):
		data = ""
		s = socket.socket(family, type)
		s.connect((self.serverlocation['hostname'],self.serverlocation['TCP port']))
		idpickle = cPickle.dumps(id)
		s.send(idpickle)

		while 1:
		  r = s.recv(self.buffer_size) # Receive up to buffer_size bytes
		  if not r:
		    break
		  data += r
		s.close()
		# needs cPickle attempt
		return cPickle.loads(data)

	def push(self, idata, family = socket.AF_INET, type = socket.SOCK_STREAM):
		# needs to account for different data_id datatypes
		s = socket.socket(family, type)
		try:
			s.connect((self.serverlocation['hostname'], self.serverlocation['TCP port']))
		except Exception, var:
			# socket error, connection refused
			if (var[0] == 111):
				print "tcptransport: unable to connect to", self.serverlocation['hostname'], "port", self.serverlocation['TCP port']
		else:
			s.send(cPickle.dumps(idata))
			s.close()

