#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from SimpleXMLRPCServer import SimpleXMLRPCServer
import threading, xmlrpclib, os, socket, inspect
import leginonobject

False=0
True=1

## range defined by IANA as dynamic/private
portrange = range(49152,65536)

class xmlrpcserver(leginonobject.LeginonObject):
	"""
	A SimpleXMLRPCServer that figures out its own host and port
	Sets self.host and self.port accordingly
	Also defines a _dispatch method that only exposes methods
	prefixed with the string self.prefix_name
	"""
	# is there some way to handle unmarshalable data by catching an
	# exception and then pickling? there would have to be something
	# client side mabye
	def __init__(self,  id, object_instance=None, port=None):
		leginonobject.LeginonObject.__init__(self, id)
		self.object_instance = object_instance 
		self.port = port
		self.hostname = socket.gethostname().lower()
		if self.port is not None:
			# this exception will fall through if __init__ fails
			self.server = SimpleXMLRPCServer((self.hostname,self.port), logRequests=False)
			self._start_serving()
			return

		## find a port in range defined by IANA as dynamic/private
		for self.port in portrange:
			try:
				self.server = SimpleXMLRPCServer((self.hostname,self.port), logRequests=False)
				break
			except Exception, var:
				if (var[0] == 98 or var[0] == 10048 or var[0] == 112):
					continue
				else:
					raise
		if self.port is None:
			raise RuntimeError('no ports available')

		self._start_serving()

	def _start_serving(self):
		self.server.register_function(self.RPCmethods)
		if self.object_instance is not None:
			self.server.register_instance(self.object_instance)
		th = threading.Thread(name='xmlrpcserver thread', target=self.server.serve_forever)
		th.setDaemon(1)
		th.start()
		self.serverthread = th

	def argspec(self, method):
		args = inspect.getargspec(method.im_func)
		argnames = args[0][1:]
		return argnames

	def old_dispatch(self, method, params):
		try:
			meth = getattr(self.object_instance,
					self.prefix_name + method)
		except AttributeError:
			meth = getattr(self, self.prefix_name + method)

		## truncate args to the specs of the method
		argnames = self.argspec(meth)
		arglen = len(argnames)
		params2 = params[:arglen]


		print 'APPLY', meth, params2
		ret = apply(meth, params2)
		print 'RETURN', ret

		if ret is None:
			return ''
		else:
			return ret

	def RPCmethods(self):
		#methlist = inspect.getmembers(self, inspect.ismethod)
		methlist = inspect.getmembers(self.object_instance,
						inspect.ismethod)
		rpcmethdict = {}
		for methtup in methlist:
			methname = methtup[0]
			meth = methtup[1]
			#if methname[:len(self.prefix_name)] == self.prefix_name:
			#	shortname = methname[len(self.prefix_name):]
			#	methargs = self.argspec(meth)
			#	rpcmethdict[shortname] = {'args':methargs}

			## methods with leading _ are not public
			if methname[0] != '_':
				methargs = self.argspec(meth)
				rpcmethdict[methname] = {'args':methargs}

		return rpcmethdict


if __name__ == '__main__':
	import signal

	class mynode(object):
		def __init__(self):
			self.server = xmlrpcserver(self)

		def EXPORT_test(self, jim, bob):
			print 'this is a test', jim, bob


	m = mynode()
