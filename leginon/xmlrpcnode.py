#!/usr/bin/env python

from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import threading, xmlrpclib, os, socket, inspect
from Tkinter import *
import location

## range defined by IANA as dynamic/private
portrange = range(49152,65536)

class xmlrpcserver(SimpleXMLRPCServer):
	"""
	A SimpleXMLRPCServer that figures out its own host and port
	Sets self.host and self.port accordingly
	Also defines a _dispatch method that only exposes methods
	prefixed with EXPORT_
	"""
	# is there some way to handle unmarshalable data by catching an
	# exception and then pickling? there would have to be something
	# client side mabye
	def __init__(self, port=None):
		hostname = socket.gethostname()
		if port:
			# this exception will fall through if __init__ fails
			SimpleXMLRPCServer.__init__(self,(hostname,port))
			self._start_serving()
			return

		## find a port in range defined by IANA as dynamic/private
		for port in portrange:
			try:
				SimpleXMLRPCServer.__init__(self,(hostname,port))
				break
			except Exception, var:
				if var[0] == 98:
					continue
				else:
					raise
		if not port:
			raise RuntimeError('no ports available')
		self.location = location.Location(hostname,
						port,
						os.getpid())
		self._start_serving()

	def _start_serving(self):
		hostname = self.location.hostname
		port = self.location.port
		print 'xml-rpc server %s:%s' % (hostname,port)
		self.register_instance(self)
		th = threading.Thread(target=self.serve_forever)
		th.setDaemon(1)
		th.start()
		self.serverthread = th

	def argspec(self, method):
		args = inspect.getargspec(method.im_func)
		argnames = args[0][1:]
		return argnames

	def _dispatch(self, method, params):
		meth = getattr(self, 'EXPORT_' + method)

		## truncate args to the specs of the method
		argnames = self.argspec(meth)
		arglen = len(argnames)
		params2 = params[:arglen]

		ret = apply(meth, params2)
		if ret == None:
			return ''
		else:
			return ret

	def EXPORT_methods(self):
		methlist = inspect.getmembers(self, inspect.ismethod)
		rpcmethdict = {}
		for methtup in methlist:
			methname = methtup[0]
			meth = methtup[1]
			if methname[:7] == 'EXPORT_':
				shortname = methname[7:]

				methargs = self.argspec(meth)
				rpcmethdict[shortname] = {'args':methargs}

		# exclude this function
		del(rpcmethdict['methods'])

		return rpcmethdict


class xmlrpcnode(xmlrpcserver):
	"""
	xmlrpcserver that also acts as an xmlrpc client to other servers
	"""
	def __init__(self):
		xmlrpcserver.__init__(self)
		self.proxies = {}

	def addProxy(self, id, uri):
		proxy = xmlrpclib.ServerProxy(uri)
		self.proxies[id] = proxy

	def deleteProxy(self, id):
		try:
			del(self.proxies[id])
		except KeyError:
			pass

	def callProxy(self, id, method, args=()):
		proxy = self.proxies[id]
		#return getattr(proxy,method)(*args)
		return apply(getattr(proxy,method), args)

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
		ret = getattr(self.proxy, self.name)(*args)
		print ret


class xmlrpcgui(Frame):
	def __init__(self, parent, host, port):
		Frame.__init__(self, parent)
		uri = 'http://' + host + ':' + `port`
		self.proxy = xmlrpclib.ServerProxy(uri)
		meths = self.proxy.methods()
		for meth in meths:
			name = meth
			args = meths[meth]['args']
			callerbut(self, self.proxy, name, args).pack(anchor=W)

if __name__ == '__main__':
	import signal

	class mynode(xmlrpcnode):
		def __init__(self):
			xmlrpcnode.__init__(self)

		def EXPORT_test(self, jim, bob):
			print 'this is a test', jim, bob


	m = mynode()
	print 'started mynode on port %s' % m.port


	top = Tk()
	mgui = xmlrpcgui(top, m.host, m.port)
	mgui.pack()


	top.mainloop()


