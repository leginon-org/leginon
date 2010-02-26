#!/usr/bin/env python
'''
Defines the pyscope server and client protocol.

Test
'''

import SocketServer
import socket
import config
import cPickle
import pyscope.tem
import pyscope.ccdcamera
import traceback

SERVER_PORT = 55555

class PyscopeData(object):
	'Base class for all data passed between client and server'
	pass

class InstrumentData(PyscopeData):
	'Base class for instrument specific data'
	def __init__(self, instrument):
		self.instrument = instrument

class CapabilityRequest(PyscopeData):
	pass

class CapabilityResponse(PyscopeData, dict):
	def __init__(self, initializer={}):
		dict.__init__(self, initializer)

class GetRequest(list, InstrumentData):
	def __init__(self, instrument, sequence=[]):
		list.__init__(self, sequence)
		InstrumentData.__init__(self, instrument)

class GetResponse(dict, InstrumentData):
	def __init__(self, instrument, initializer={}):
		dict.__init__(self, initializer)
		InstrumentData.__init__(self, instrument)

class SetRequest(dict, InstrumentData):
	def __init__(self, instrument, initializer={}):
		dict.__init__(self, initializer)
		InstrumentData.__init__(self, instrument)

class SetResponse(dict, InstrumentData):
	def __init__(self, instrument, initializer={}):
		dict.__init__(self, initializer)
		InstrumentData.__init__(self, instrument)

class CallRequest(InstrumentData):
	def __init__(self, instrument, name, *args, **kwargs):
		InstrumentData.__init__(self, instrument)
		self.name = name
		self.args = args
		self.kwargs = kwargs

class CallResponse(InstrumentData):
	def __init__(self, instrument, result):
		InstrumentData.__init__(self, instrument)
		self.result = result

class PickleHandler(object):
	'define self.rfile and self.wfile in subclass'
	def readObject(self):
		obj = cPickle.load(self.rfile)
		return obj

	def writeObject(self, obj):
		cPickle.dump(obj, self.wfile)
		self.wfile.flush()

class PickleRequestHandler(SocketServer.StreamRequestHandler, PickleHandler):
	def handle(self):
		request_object = self.readObject()
		response_object = self.handle_object(request_object)
		self.writeObject(response_object)

	def handle_object(self, object):
		raise NotImplementedError('define handle_object in subclass')

class HandlerError(Exception):
	def __init__(self):
		## traceback cannot be pickled, so convert to string
		info = '######### Server traceback:\n%s########### End server traceback\n' % (traceback.format_exc(),)
		Exception.__init__(self, info)

class InstrumentRequestHandler(PickleRequestHandler):
	def setup(self):
		PickleRequestHandler.setup(self)
		self.instruments = self.server.instruments

	def handle_object(self, request):
		if isinstance(request, GetRequest):
			return self.handle_get(request)
		elif isinstance(request, SetRequest):
			return self.handle_set(request)
		elif isinstance(request, CallRequest):
			return self.handle_call(request)
		elif isinstance(request, CapabilityRequest):
			return self.handle_capability(request)

	def handle_capability(self, request):
		caps = self.instruments.getCapabilities()
		response = CapabilityResponse()
		response.update(caps)
		return response

	def handle_get(self, request):
		instrument = self.instruments[request.instrument]
		response = GetResponse(request.instrument)
		for name in request:
			attr = 'get' + name
			try:
				func = getattr(instrument, attr)
				response[name] = func()
			except:
				response[name] = HandlerError()
		return response

	def handle_set(self, request):
		instrument = self.instruments[request.instrument]
		response = SetResponse(request.instrument)
		for name, value in request.items():
			attr = 'set' + name
			try:
				func = getattr(instrument, attr)
				response[name] = func(value)
			except:
				response[name] = HandlerError()
		return response

	def handle_call(self, request):
		instrument = self.instruments[request.instrument]
		attr = request.name
		args = request.args
		kwargs = request.kwargs
		try:
			func = getattr(instrument, attr)
			result = func(*args, **kwargs)
		except:
			result = HandlerError()
		response = CallResponse(request.instrument, result)

class Server(SocketServer.TCPServer):
	allow_reuse_address = True
	def __init__(self, *args, **kwargs):
		SocketServer.TCPServer.__init__(self, *args, **kwargs)
		self.instruments = Instruments()

class Instruments(dict):
	'''This instantiates all configured instruments'''
	def __init__(self):
		dict.__init__(self)
		for name,cls in config.configured.items():
			self[name] = cls()

	def getCapabilities(self):
		caps = {}
		for name, instrument in self.items():
			caps[name] = {}
			if isinstance(instrument, pyscope.tem.TEM):
				inst_type = 'TEM'
			elif isinstance(instrument, pyscope.ccdcamera.CCDCamera):
				inst_type = 'CCDCamera'
			caps[name]['type'] = inst_type
			caps[name]['caps'] = instrument.getCapabilities()
		return caps

class Client(PickleHandler):
	def __init__(self, host='', port=SERVER_PORT):
		self.host = host
		self.port = port

	def connect(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.host, self.port))
		self.wfile = s.makefile('wb')
		self.rfile = s.makefile('rb')

	def disconnect(self):
		self.wfile.close()
		self.rfile.close()

	def doRequest(self, request):
		self.connect()
		self.writeObject(request)
		response = self.readObject()
		self.disconnect()

		return response

	def getCapabilities(self):
		req = CapabilityRequest()
		caps = self.doRequest(req)
		return caps

	def setOne(self, instrument, property, value):
		req = SetRequest(instrument, {property: value})
		response = self.doRequest(req)
		response = response[property]
		return response

	def getOne(self, instrument, property):
		req = GetRequest(instrument, [property])
		response = self.doRequest(req)
		response = response[property]
		return response

	def setMany(self, instrument, property_dict):
		req = SetRequest(instrument, property_dict)
		response = self.doRequest(req)
		return response

	def getMany(self, instrument, property_list):
		req = GetRequest(instrument, property_list)
		response = self.doRequest(req)
		return response

def startServer():
	addr = ('', 55555)
	server = Server(addr, InstrumentRequestHandler)
	server.serve_forever()

if __name__ == '__main__':
	import sys
	if sys.argv[1] == 'server':
		startServer()
	elif sys.argv[1] == 'client':
		c = Client()
		print c.setOne('Sim TEM', 'StagePosition', {'x':0.0005})
		print c.getOne('Sim TEM', 'StagePosition')

		print c.getMany('Sim TEM', ['StagePosition','SpotSize','dummy'])

