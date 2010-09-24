#!/usr/bin/env python

import SocketServer
import logging

# local
import redux.utility
from redux.pipelines import StandardPipeline

### set up logging
logger = logging.getLogger('redux')
logger.setLevel(logging.DEBUG)
stderr_handler = logging.StreamHandler()
logger.addHandler(stderr_handler)

class RequestHandler(SocketServer.StreamRequestHandler):
	def handle(self):
		#for request in self.rfile:
		#	self.run_process(request)
		request = self.rfile.readline().strip()
		logger.info('REQUEST: %s' % (request,))
		self.run_process(request)

	def run_process(self, request):
		kwargs = redux.utility.request_to_kwargs(request)
		result = StandardPipeline().process(**kwargs)
		self.wfile.write(result)
		self.wfile.flush()

#class Server(SocketServer.ForkingMixIn, SocketServer.TCPServer):
class Server(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	allow_reuse_address = True

def start_server(host, port):
	server = Server((host,port), RequestHandler)
	logger.info('host: %s,  port: %s' % server.server_address)
	server.serve_forever()

def test_request():
	import sys
	import time
	request = sys.argv[2]
	kwargs = redux.utility.request_to_kwargs(request)
	t0 = time.time()
	result = StandardPipeline().process(**kwargs)
	t1 = time.time()
	sys.stderr.write('TIME: %s\n' % (t1-t0))
	print result

if __name__ == '__main__':
	start_server('', redux.utility.REDUX_PORT)
