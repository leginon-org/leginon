#!/usr/bin/env python

from SimpleXMLRPCServer import SimpleXMLRPCServer
import threading, xmlrpclib, os, socket, inspect
from Tkinter import *

## range defined by IANA as dynamic/private
portrange = range(49152,65536)

class xmlrpcserver(object):
	"""
	A SimpleXMLRPCServer that figures out its own host and port
	Sets self.host and self.port accordingly
	Also defines a _dispatch method that only exposes methods
	prefixed with the string self.prefix_name
	"""
	# is there some way to handle unmarshalable data by catching an
	# exception and then pickling? there would have to be something
	# client side mabye
	def __init__(self,  object_instance, port=None):
		self.object_instance = object_instance 
		self.port = port
		hostname = socket.gethostname()
		if self.port:
			# this exception will fall through if __init__ fails
			self.server = SimpleXMLRPCServer((hostname,self.port))
			self._start_serving()
			return

		## find a port in range defined by IANA as dynamic/private
		for self.port in portrange:
			try:
				self.server = SimpleXMLRPCServer((hostname,self.port))
				break
			except Exception, var:
				if (var[0] == 98 or var[0] == 10048 or var[0] == 112):
					continue
				else:
					raise
		if not self.port:
			raise RuntimeError('no ports available')

		self._start_serving()

	def _start_serving(self):
		self.server.register_function(self.RPCmethods)
		self.server.register_instance(self.object_instance)
		th = threading.Thread(target=self.server.serve_forever)
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

		if ret == None:
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


class callerbut(Frame):
	def __init__(self, parent, proxy, name, args):
		Frame.__init__(self, parent)

		self.proxy = proxy
		self.name = name
		self.argentries = []

		Button(self, text=name, command=self.butcom).pack(side=LEFT)
		for arg in args:
			Label(self, text=arg).pack(side=LEFT)
			ent = Entry(self, width=10)
			ent.pack(side=LEFT)
			self.argentries.append(ent)

	def butcom(self):
		args = []
		for argentry in self.argentries:
			arg = argentry.get()
			args.append(arg)
			args = tuple(args)
		print 'calling %s on %s with args %s' % (self.name, self.proxy,args)
		ret = getattr(self.proxy, self.name)(*args)
		print ret


class xmlrpcgui(Frame):
	def __init__(self, parent, host, port):
		Frame.__init__(self, parent)
		uri = 'http://' + host + ':' + `port`
		self.proxy = xmlrpclib.ServerProxy(uri)
		meths = self.proxy.RPCmethods()
		for meth in meths:
			name = meth
			args = meths[meth]['args']
			callerbut(self, self.proxy, name, args).pack(anchor=W)

if __name__ == '__main__':
	import signal

	class mynode(object):
		def __init__(self):
			self.server = xmlrpcserver(self)

		def EXPORT_test(self, jim, bob):
			print 'this is a test', jim, bob


	m = mynode()

#	top = Tk()
#	mgui = xmlrpcgui(top, m.host, m.port)
#	mgui.pack()


#	top.mainloop()


