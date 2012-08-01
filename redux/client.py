#!/usr/bin/env python

import sys
import socket
import utility
from optparse import OptionParser
import redux.pipes
import redux.pipeline
import redux.pipelines

class Client(object):
	def process_request(self, request):
		raise NotImplementedError()
	def process_kwargs(self, **kwargs):
		raise NotImplementedError()

class NetworkClient(Client):
	def __init__(self, host, port=utility.REDUX_PORT):
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
		if 'pipeline' in kwargs:
			pl = redux.pipeline.pipeline_by_preset(kwargs['pipeline'])
		elif 'pipes' in kwargs:
			pl = redux.pipeline.pipeline_by_string(kwargs['pipes'])		
		else:
			pl = redux.pipeline.pipeline_by_preset('standard')
		return pl.process(**kwargs)

def add_option(parser, optname, help):
			dest = optname
			arg = '--%s' % (dest,)
			parser.add_option(arg, action='store', type='string', dest=dest, help=help)

def parse_argv():
	parser = OptionParser()
	pipes = redux.pipelines.registered['all']
	for name,clsname in pipes:
		cls = redux.pipes.registered[clsname]
		if cls.switch_arg:
			help = '%s: boolean switch to turn it on' % (name,)
			add_option(parser, cls.switch_arg, help)
		if cls.required_args:
			for arg in cls.required_args:
				if not parser.has_option('--%s' % arg):
					help = '%s: required' % (name,)
					add_option(parser, arg, help)
		if cls.optional_args:
			for arg in cls.optional_args:
				if not parser.has_option('--%s' % arg):
					help = '%s: optional' % (name,)
					add_option(parser, arg, help)

	add_option(parser, 'request', 'full request as a single URL option string')
	add_option(parser, 'server_host', 'redux server host name (if not given, will start built-in redux processor)')
	add_option(parser, 'server_port', 'redux server port (if not given, will use default port)')
	add_option(parser, 'pipeline', 'pipeline preset to use')
	add_option(parser, 'pipes', 'pipeline defined by sequence of pipes:  name:cls,namecls,...')

	(options, args) = parser.parse_args()


	kwargs = {}
	for key,value in options.__dict__.items():
		if value is not None:
			kwargs[key] = value
	if not kwargs:
		parser.print_help(sys.stderr)
		sys.exit(0)
	return kwargs

def run():
	kwargs = parse_argv()
	if 'server_host' in kwargs and kwargs['server_host']:
		if 'server_port' in kwargs and kwargs['server_port']:
			port = int(kwargs['server_port'])
		else:
			port = utility.REDUX_PORT
		client = NetworkClient(kwargs['server_host'], port)
	else:
		client = SimpleClient()

	if 'request' in kwargs and kwargs['request']:
		result = client.process_request(kwargs['request'])
	else:
		result = client.process_kwargs(**kwargs)
		
	sys.stdout.write(result)

if __name__ == '__main__':
	run()
