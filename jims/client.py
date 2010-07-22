#!/usr/bin/env python

import socket
import utility

class Client(object):
	def __init__(self, host, port=utility.JIMS_PORT):
		self.host = host
		self.port = port

	def process(self, **kwargs):
		request = utility.kwargs_to_request(**kwargs)
		result = self.do_request(request)
		return result

	def do_request(self, request):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((self.host, self.port))
		wfile = sock.makefile('wb')
		rfile = sock.makefile('rb')
		wfile.write(request)
		wfile.write('\n')
		wfile.flush()
		response = rfile.read()
		sock.close()
		return response

def test_cli_request():
	import sys
	c = Client('', utility.JIMS_PORT)
	result = c.do_request(sys.argv[1])
	sys.stdout.write(result)

if __name__ == '__main__':
	test_cli_request()
