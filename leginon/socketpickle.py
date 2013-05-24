#!/usr/bin/env python
#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#

import cPickle as pickle
import socket
import SocketServer
import numpy
import sys
import math

PORT = 55555

class Handler(SocketServer.StreamRequestHandler):
	def handle(self):
			print 'Handling request...'
			size = pickle.load(self.rfile)
			print '  Size requested: ', size
			result = numpy.zeros((size,size), dtype=numpy.int32)
			print '  Sending result...'
			#pickle.dump(result, self.wfile, pickle.HIGHEST_PROTOCOL)
			s = pickle.dumps(result, pickle.HIGHEST_PROTOCOL)
			psize = len(s)
			chunk_size = 8*1024*1024
			nchunks = int(math.ceil(float(psize) / float(chunk_size)))
			print 'NCHUNKS', nchunks
			for i in range(nchunks):
				print 'I', i
				start = i * chunk_size
				end = start + chunk_size
				chunk = s[start:end]
				self.wfile.write(chunk)
			self.wfile.flush()
			print '  Done.'


class Server(SocketServer.ThreadingTCPServer):
	allow_reuse_address = True
	def __init__(self):
		SocketServer.ThreadingTCPServer.__init__(self, ('', PORT), Handler)

class Client(object):
	def __init__(self, host):
		self.host = host

	def getImage(self, size):
		print 'Connecting to server...'
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.host, PORT))
		sfile = s.makefile('rwb')
		print 'Sending request...'
		pickle.dump(size, sfile, pickle.HIGHEST_PROTOCOL)
		sfile.flush()
		print 'Getting result...'
		result = pickle.load(sfile)
		print 'Done.'
		sfile.close()
		return result

def run_server():
	hostname = socket.gethostname()
	port = PORT
	print 'Running Server'
	print '  host: %s' % (hostname,)
	print '  port: %s' % (port,)
	s = Server()
	s.serve_forever()

def run_client():
	server_host = sys.argv[1]
	size = int(sys.argv[2])
	c = Client(server_host)
	im = c.getImage(size)
	print ''
	print 'IMAGE %s:' % (im.shape,)
	print im
	print ''

if sys.argv[1:]:
	run_client()
else:
	run_server()
