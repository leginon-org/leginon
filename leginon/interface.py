
import leginonobject
import xmlrpcserver
import xmlrpclib
import threading
import code
import inspect

XMLRPCTYPES = ('boolean', 'integer', 'float', 'string', 'array', 'struct', 'date', 'binary')
PERMISSIONS = (None, 'r', 'w', 'rw', 'wr')

class SpecObject(leginonobject.LeginonObject):
	def __init__(self, id, spectype):
		leginonobject.LeginonObject.__init__(self, id)
		self.spectype = spectype

	def dict(self):
		d = {}
		d['id'] = str(self.id)
		d['spectype'] = self.spectype
		return d

class DataSpec(SpecObject):
	"""
	This describes a piece of data for an xml-rpc client
	The client can use this description to define the data presentation
	"""
	def __init__(self, id, server, name, xmlrpctype, permissions=None, enum=None, default=None, pyname=None):
		SpecObject.__init__(self, id, 'data')

		self.server = server
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
		self.uidata = default
		self.pyname = pyname

	def get(self):
		if callable(self.uidata):
			return self.uidata()
		else:
			return self.uidata

	def set(self, value):
		if callable(self.uidata):
			self.uidata(value)
		else:
			self.uidata = value

	def dict(self):
		d = SpecObject.dict(self)
		d['name'] = self.name
		d['xmlrpctype'] = self.xmlrpctype
		if self.permissions is not None:
			d['permissions'] = self.permissions

		if self.enum is not None:
			idstr = str(self.enum.id)
			d['enum'] = idstr

		if self.default is not None:
			d['default'] = self.default
		if self.pyname is not None:
			d['python name'] = self.pyname
		return d


class MethodSpec(SpecObject):
	def __init__(self, id, name, argspec, returnspec=None):
		SpecObject.__init__(self, id, 'method')

		self.name = name
		self.argspec = argspec
		self.returnspec = returnspec

	def dict(self):
		d = SpecObject.dict(self)
		d['name'] = self.name
		d['argspec'] = []
		for arg in self.argspec:
			d['argspec'].append(arg.dict())
		if self.returnspec is not None:
			d['returnspec'] = self.returnspec.dict()
		return d

class ContainerSpec(SpecObject):
	def __init__(self, id, name=None, content=()):
		SpecObject.__init__(self, id, 'container')
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
		d = SpecObject.dict(self)
		if self.name is not None:
			d['name'] = self.name
		d['content'] = []
		for thing in self.content:
			d['content'].append(thing.dict())
		return d

class Server(xmlrpcserver.xmlrpcserver):
	def __init__(self, id):
		xmlrpcserver.xmlrpcserver.__init__(self, id)
		self.uidata = {}
		#self.server.register_function(self.uiMethods, 'methods')
		self.server.register_function(self.uiSpec, 'spec')
		self.server.register_function(self.uiGet, 'GET')
		self.server.register_function(self.uiSet, 'SET')

	def uiGet(self, idstr):
		'''this is how a UI client gets a data value'''
		data = self.uidata[idstr]
		value = data.get()
		if value is None:
			return ''
		else:
			return value

	def uiSet(self, idstr, value):
		'''this is how a UI client sets a data value'''
		data = self.uidata[idstr]
		data.set(value)
		return data.get()

	def registerMethod(self, func, name, argspec, returnspec=None):
		id = self.ID()
		self.server.register_function(func, str(id))
		if inspect.isfunction(func):
			funcargspec = inspect.getargspec(func)
			argnames = funcargspec[0]
		elif inspect.ismethod(func):
			funcargspec = inspect.getargspec(func.im_func)
			argnames = funcargspec[0][1:]
		ind = 0
		for arg in argspec:
			arg.pyname = argnames[ind]
			ind += 1
		m = MethodSpec(id, name, argspec, returnspec)
		return m

	def registerData(self, name, xmlrpctype, permissions=None, enum=None, default=None):
		id = self.ID()
		d = DataSpec(id, self, name, xmlrpctype, permissions, enum, default)
		idstr = str(id)
		self.uidata[idstr] = d
		return d

	def registerContainer(self, name=None, content=()):
		c = ContainerSpec(self.ID(), name, content)
		return c

	def registerSpec(self, name=None, content=()):
		self.spec = ContainerSpec(self.ID(), name, content)
		return self.spec

	def uiSpec(self):
		return self.spec.dict()


class Client(object):
	def __init__(self, hostname, port):
		uri = 'http://%s:%s' % (hostname, port)
		self.proxy = xmlrpclib.ServerProxy(uri)

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
