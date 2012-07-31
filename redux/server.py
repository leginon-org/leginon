#!/usr/bin/env python

import SocketServer
import logging
import time
import sys
import traceback

# local
import redux.utility
import redux.exceptions
import redux.pipeline

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
		try:
			kwargs = redux.utility.request_to_kwargs(request)
			if 'pipeline' in kwargs:
				pipeline = redux.pipeline.pipeline_by_preset(kwargs['pipeline'])
			elif 'pipes' in kwargs:
				pipeline = redux.pipeline.pipeline_by_string(kwargs['pipes'])		
			else:
				pipeline = redux.pipeline.pipeline_by_preset('standard')
			result = pipeline.process(**kwargs)
		except Exception, e:
			timestamp = str(time.time())
			result = 'REDUX ERROR ' + timestamp + ' ' + str(e)
			sys.stderr.write(timestamp+'\n')
			traceback.print_exc(file=sys.stderr)
		finally:
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
	pl = redux.pipeline.pipeline_by_preset('standard')
	result = pl.process(**kwargs)
	t1 = time.time()
	sys.stderr.write('TIME: %s\n' % (t1-t0))
	print result

if __name__ == '__main__':
	start_server('', redux.utility.REDUX_PORT)
