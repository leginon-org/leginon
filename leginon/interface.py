
import leginonobject
import xmlrpcserver
import xmlrpclib
import threading
import code
import inspect

XMLRPCTYPES = ('boolean', 'integer', 'float', 'string', 'array', 'struct', 'date', 'binary')
PERMISSIONS = (None, 'r', 'w', 'rw', 'wr')

class SpecObject(object):
	def __init__(self, spectype):
		self.spectype = spectype


class DataSpec(SpecObject):
	"""
	This describes a piece of data for an xml-rpc client
	The client can use this description to define the data presentation
	"""
	def __init__(self, name, xmlrpctype, permissions=None, enum=None, default=None):
		SpecObject.__init__(self, 'data')

		self.name = name
		if xmlrpctype in XMLRPCTYPES:
			self.xmlrpctype = xmlrpctype
		else:
			raise RuntimeError('invalid xmlrpctype %s' % xmlrpctype)
		if permissions in PERMISSIONS:
			self.permissions = permissions
		else:
			raise RuntimeError('invalid permissions %s' % permissions)
		self.enum = enum
		self.default = default

	def dict(self):
		d = {}
		d['spectype'] = self.spectype
		d['name'] = self.name
		d['xmlrpctype'] = self.xmlrpctype
		if self.permissions is not None:
			d['permissions'] = self.permissions

		if self.enum is not None:
			d['enum'] = self.enum

		if self.default is not None:
			d['default'] = self.default
		return d


class MethodSpec(SpecObject):
	def __init__(self, name, argspec, returnspec=None):
		SpecObject.__init__(self, 'method')

		self.name = name
		self.argspec = argspec
		self.returnspec = returnspec

	def dict(self):
		d = {}
		d['spectype'] = self.spectype
		d['name'] = self.name
		d['argspec'] = []
		for arg in self.argspec:
			d['argspec'].append(arg.dict())
		if self.returnspec is not None:
			d['returnspec'] = self.returnspec.dict()
		return d

class ContainerSpec(SpecObject):
	def __init__(self, name=None, content=()):
		SpecObject.__init__(self, 'container')
		self.name = name
		self.content = []
		if type(content) in (list, tuple):
			for thing in content:
				self.add_content(thing)
		else:
			self.add_content(content)

	def add_content(self, new_content):
		if isinstance(new_content, SpecObject):
			self.content.append(new_content)
		else:
			raise RuntimeError('invalid content %s' % new_content)

	def dict(self):
		d = {}
		d['spectype'] = self.spectype
		if self.name is not None:
			d['name'] = self.name
		d['content'] = []
		for thing in self.content:
			d['content'].append(thing.dict())
		return d

class Server(xmlrpcserver.xmlrpcserver):
	def __init__(self, id=()):
		xmlrpcserver.xmlrpcserver.__init__(self)
		self.uidata = {}
		#self.server.register_function(self.uiMethods, 'methods')
		self.server.register_function(self.uiSpec, 'spec')
		self.server.register_function(self.uiGet, 'GET')
		self.server.register_function(self.uiSet, 'SET')

	def uiGet(self, name):
		'''this is how a UI client gets uidata'''
		data = self.getData(name)
		if data is None:
			return 'None'
		else:
			return data

	def uiSet(self, name, value):
		'''this is how a UI client sets uidata'''
		self.setData(name,value)
		return self.uiGet(name)

	def setData(self, name, value):
		'''this is how something with access to this server sets uidata'''
		self.uidata[name] = value

	def getData(self, name):
		'''this is how something with access to this server gets uidata'''
		return self.uidata[name]

	def registerMethod(self, func, name, argspec, returnspec=None):
		self.server.register_function(func, name)
		m = MethodSpec(name, argspec, returnspec)
		return m

	def registerData(self, name, xmlrpctype, permissions=None, enum=None, default=None):
		## permissions = None means it is not maintained on the server
		## should probably keep track of permission in uidata also
		if permissions is not None:
			if default is not None:
				self.uidata[name] = default
		d = DataSpec(name, xmlrpctype, permissions, enum, default)
		return d

	def registerContainer(self, name=None, content=()):
		c = ContainerSpec(name, content)
		return c

	def registerSpec(self, name=None, content=()):
		self.spec = ContainerSpec(name, content)
		return self.spec

	def uiSpec(self):
		return self.spec.dict()


class Client(object):
	def __init__(self, hostname, port):
		uri = 'http://%s:%s' % (hostname, port)
		self.proxy = xmlrpclib.ServerProxy(uri)
		#self.getMethods()
		self.spec = self.getSpec()

	def getSpec(self):
		self.spec = self.proxy.spec()
		return self.spec

	def execute(self, funcname, args=()):
		return getattr(self.proxy, funcname)(*args)


class TestNode(object):
	def __init__(self):
		self.uiserver = Server()
		argspec = (
			{'name':'mynum', 'type':'integer', 'default':1},
			{'name':'mystr', 'type':'string', 'default':'hello'},
			{'name':'selection', 'type':('red','green','blue'), 'default':'blue'}
			)
		self.registerUIFunction(self.asdf, argspec, 'Asdf')

	def asdf(self, mynum, mystr, selection):
		print 'mynum', mynum
		print 'mystr', mystr
		print 'selection', selection
		return mynum * mystr + selection
