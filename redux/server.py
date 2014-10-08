#!/usr/bin/env python

import SocketServer
import logging
import time
import sys
import traceback

import redux.reduxlog

### set up logging
redux.reduxlog.setup()
logger = redux.reduxlog.logger

import redux.reduxconfig
import redux.utility
import redux.exceptions
import redux.pipeline
import pyami.version

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
			self.wfile.write(result)
		except Exception as e:
			error = 'REDUX ERROR %d %s'%(time.time(), e)
			logger.error(error)
			logger.error(traceback.format_exc())
			self.wfile.write(error)
		finally:
			self.wfile.flush()

# Although we have tried using Forking and Threading servers, there have
# been too many issues with managing concurrent access to cache and also
# concurrent FFTW calculations.  For now this is using the standard server
# which handles requests one at a time.
class Server(SocketServer.TCPServer):
	allow_reuse_address = True

def start_server(host, port):
	server = Server((host,port), RequestHandler)
	ver = pyami.version.getSubversionRevision()
	logger.info('*****************************************')
	logger.info('redux server started: %s' % (time.asctime(),))
	logger.info('subversion revision: %s' % (ver,))
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

def main():
	host = redux.reduxconfig.config['server host']
	port = redux.reduxconfig.config['server port']
	start_server(host, port)

if __name__ == '__main__':
	main()
