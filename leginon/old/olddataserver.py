#!/usr/bin/env python

import BaseHTTPServer
import os, threading
import cPickle

portrange = range(49152,65536)

class DataServer(BaseHTTPServer.HTTPServer):
	def __init__(self, dataroot):

		self.host = hostname = os.environ['HOSTNAME']
		self.dataroot = dataroot

		self.port = None
		for port in portrange:
			address = (hostname, port)
			try:
				BaseHTTPServer.HTTPServer.__init__(self, address, DataRequestHandler)
				self.port = port
				break
			except Exception, var:
				if var[0] == 98:
					continue
				else:
					raise
		if not self.port:
			raise RuntimeError('no ports available')

		print 'running dataserver on port %s' % self.port
		self._start_serving()

	def _start_serving(self):
		th = threading.Thread(target=self.serve_forever)
		th.setDaemon(1)
		th.start()
		self.serverthread = th

class DataRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def __init__(self, req, add, serv):
		BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, req, add, serv)
		self.server = serv
		print 'request for ', self.path

	def do_GET(self):
		dataid = self.path[1:]
		ob = getattr(self.server.dataroot, dataid)

		self.send_response(200)
		self.send_header('Content-Type', 'application/octet-stream')
		self.end_headers()
		cPickle.dump(ob, self.wfile, 1)


if __name__ == '__main__':
	address = ('bnc16', 49152)
	class myclass(object):
		def __init__(self):
			self.aaa = 9
			self.bbb = {'a':555, 'b':999}

	dataroot = myclass()
	d = DataServer(dataroot)
	d.serve_forever()
