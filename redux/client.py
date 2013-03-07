#!/usr/bin/env python

import sys
import socket
import utility
from optparse import OptionParser
import redux.pipes
import redux.pipeline
import redux.reduxconfig

class Client(object):
	def process_request(self, request):
		raise NotImplementedError()
	def process_kwargs(self, **kwargs):
		raise NotImplementedError()

class NetworkClient(Client):
	def __init__(self, host=None, port=None):
		if host is None:
			host = redux.reduxconfig.config['server host']
		if port is None:
			port = redux.reduxconfig.config['server port']
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
	def __init__(self, *args, **kwargs):
		import redux.pipeline
		Client.__init__(self, *args, **kwargs)
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

def add_option(parser, optname, pipename, help):
	optnames = [optname]
	if pipename:
		optnames.append(pipename+'.'+optname)
	for name in optnames:
		arg = '--%s' % (name,)
		if parser.has_option(arg):
			continue
		parser.add_option(arg, action='store', type='string', dest=name, help=help)

def dummy_callback(option, opt, value, parser):
	pass

def parse_argv():
	# initial parse to determine pipeline, with help and errors disabled
	'''
	parser = OptionParser()
	add_option(parser, 'pipeline', None, 'pipeline preset to use')
	add_option(parser, 'pipes', None, 'pipeline defined by sequence of pipes:  name:cls,name:cls,...')

	parser.remove_option('-h')
	parser.add_option('-h', action='callback', callback=dummy_callback)
	parser.error = lambda x: None
	(options, args) = parser.parse_args()
	if options.pipeline is not None:
		pipes = redux.pipeline.pipes_by_preset(options.pipeline)
	elif options.pipes is not None:
		pipes = redux.pipeline.pipes_by_string(options.pipes)
	else:
		pipes = []
	'''
	pipes = redux.pipeline.pipes_by_preset('standard')

	# final parse
	parser = OptionParser()
	add_option(parser, 'pipeline', None, 'pipeline preset to use')

	add_option(parser, 'request', None, 'full request as a single URL option string')
	add_option(parser, 'server_host', None, 'redux server host name (if not given, will start built-in redux processor)')
	add_option(parser, 'server_port', None, 'redux server port (if not given, will use default port)')
	add_option(parser, 'pipes', None, 'pipeline defined by sequence of pipes:  name:cls,name:cls,...')
	add_option(parser, 'cache', None, 'set to "no" to disable cache for this request')

	for pipename,clsname in pipes:
		cls = redux.pipes.registered[clsname]
		if cls.switch_arg:
			help = '%s: boolean switch to turn it on' % (pipename,)
			add_option(parser, cls.switch_arg, pipename, help)
		if cls.required_args:
			for arg in cls.required_args:
				help = '%s: required' % (pipename,)
				add_option(parser, arg, pipename, help)
		if cls.optional_args:
			for arg in cls.optional_args:
				help = '%s: optional' % (pipename,)
				add_option(parser, arg, pipename, help)

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
			port = redux.reduxconfig.config['server port']
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
