
import leginonobject
import xmlrpcserver
import xmlrpclib
import threading
import code
import inspect

XMLRPCTYPES = ('boolean', 'integer', 'float', 'string', 'array', 'struct', 'date', 'binary')
PERMISSIONS = ('r', 'rw')

class SpecObject(object):
	def __init__(self, spectype):
		self.spectype = spectype


class DataSpec(SpecObject):
	"""
	This describes a piece of data for an xml-rpc client
	The client can use this description to define the data presentation
	"""
	def __init__(self, name, xmlrpctype, permissions='r', enum=(), default=None):
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
		d['permissions'] = self.permissions
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
		self.funcdict = {}
		self.funclist = []
		#self.server.register_function(self.uiMethods, 'methods')
		self.server.register_function(self.uiSpec, 'spec')

	def registerMethod(self, func, name, argspec, returnspec=None):
		self.server.register_function(func, name)
		m = MethodSpec(name, argspec, returnspec)
		return m

	def registerData(self, name, xmlrpctype, permissions='r', enum=(), default=None):
		d = DataSpec(name, xmlrpctype, permissions, enum, default)
		return d

	def registerContainer(self, name=None, content=()):
		c = ContainerSpec(name, content)
		return c

	def registerSpec(self, name=None, content=()):
		self.spec = ContainerSpec(name, content)
		return self.spec

	def registerFunction(self, func, argspec, alias=None, returntype=None):
		if alias is None:
			alias = func.__name__

### I have commented some things until client makes RPC calls with kwargs dict.
### Until then, there is no need to associate the original arg name
### with the arg.  Instead calls will depend on positional arguments
### Therefore, argspec must be ordered properly and argspec['name'] is ignored
### Also must differentiate between method and function for inspect
#		argnames = inspect.getargspec(method.im_func)[0]
		for argdict in argspec:
			## validate argspec
			
#			if argdict['name'] not in argnames:
#				raise RuntimeError('bad argname in argdict')
			xmlrpctype = argdict['type']
			if xmlrpctype not in XMLRPCTYPES:
				if type(xmlrpctype) not in (dict,tuple,list):
					raise RuntimeError('bad xmlrpctype')

		self.funcdict[alias] = {'func': func, 'argspec':argspec, 'returntype':returntype}
		self.funclist.append(alias)
		self.server.register_function(func, alias)

	def uiMethods(self):
		'makes some of self.funcdict public to rpc clients'
		funcstruct = {}
		fdict = {}
		for key,value in self.funcdict.items():
			fdict[key] = {}
			fdict[key]['argspec'] = value['argspec']
			if value['returntype'] is not None:
				fdict[key]['return'] = value['returntype']
		funcstruct['dict'] = fdict
		funcstruct['list'] = self.funclist
		return funcstruct

	def uiSpec(self):
		return self.spec.dict()


class Client(object):
	def __init__(self, hostname, port):
		uri = 'http://%s:%s' % (hostname, port)
		self.proxy = xmlrpclib.ServerProxy(uri)
		#self.getMethods()
		self.spec = self.getSpec()
		print 'spec', self.spec

	def getSpec(self):
		self.spec = self.proxy.spec()
		return self.spec

	def execute(self, funcname, args):
		#args = self.funcdict[funcname].argvalues()
		return getattr(self.proxy, funcname)(*args)

	def setarg(self, funcname, argname, value):
		self.funcdict[funcname].setarg(argname, value)

	def getargtype(self, funcname, argname):
		return self.funcdict[funcname].type(argname)


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
