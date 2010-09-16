#!/usr/bin/env python

import sys
import socket
import utility
from optparse import OptionParser
import jims.core

class Client(object):
	def process_request(self, request):
		raise NotImplementedError()
	def process_kwargs(self, **kwargs):
		raise NotImplementedError()

class NetworkClient(Client):
	def __init__(self, host, port=utility.JIMS_PORT):
		self.host = host
		self.port = port

	def process_request(self, request):
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

	def process_kwargs(self, **kwargs):
		request = utility.kwargs_to_request(**kwargs)
		return self.process_request(request)

class SimpleClient(Client):
	def process_request(self, request):
		kwargs = utility.request_to_kwargs(request)
		return self.process_kwargs(**kwargs)

	def process_kwargs(self, **kwargs):
		return jims.core.process(**kwargs)


def add_option(parser, optname, help):
			dest = optname
			arg = '--%s' % (dest,)
			parser.add_option(arg, action='store', type='string', dest=dest, help=help)

def parse_argv():
	parser = OptionParser()
	for pipe in jims.core.pipe_order:
		pipe_name = pipe.__name__
		if pipe.switch_arg:
			help = '%s: boolean switch to turn it on' % (pipe_name,)
			add_option(parser, pipe.switch_arg, help)
		if pipe.required_args:
			for arg in pipe.required_args:
				help = '%s: required' % (pipe_name,)
				add_option(parser, arg, help)
		if pipe.optional_args:
			for arg in pipe.optional_args:
				help = '%s: optional' % (pipe_name,)
				add_option(parser, arg, help)

	add_option(parser, 'request', 'full request as a single URL option string')
	add_option(parser, 'server_host', 'jims server host name (if not given, will start built-in jims processor)')
	add_option(parser, 'server_port', 'jims server port (if not given, will use default port)')

	(options, args) = parser.parse_args()
	return options.__dict__

def run():
	kwargs = parse_argv()
	if kwargs['server_host'] is None:
		client = SimpleClient()
	else:
		if kwargs['server_port'] is None:
			port = utility.JIMS_PORT
		else:
			port = kwargs['server_port']
		client = NetworkClient(kwargs['server_host'], port)

	if kwargs['request'] is None:
		result = client.process_kwargs(**kwargs)
	else:
		result = client.process_request(kwargs['request'])
		
	sys.stdout.write(result)

if __name__ == '__main__':
	run()
