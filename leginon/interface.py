
import xmlrpcserver
import xmlrpclib
import threading
import code
import inspect


xmlrpctypes = ('boolean', 'integer', 'float', 'string', 'array', 'struct', 'date', 'binary')


class Server(xmlrpcserver.xmlrpcserver):
	def __init__(self, id=()):
		xmlrpcserver.xmlrpcserver.__init__(self)
		self.funcdict = {}
		self.funclist = []
		self.server.register_function(self.uiMethods, 'methods')
		self.id = id
		self.server.register_function(self.uiID, 'id')

	def registerFunction(self, func, argspec, alias=None):
		if not alias:
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
			if xmlrpctype not in xmlrpctypes:
				if type(xmlrpctype) not in (tuple,list):
					raise RuntimeError('bad xmlrpctype')

		self.funcdict[alias] = {'func': func, 'argspec':argspec}
		self.funclist.append(alias)
		self.server.register_function(func, alias)

	def uiMethods(self):
		'makes some of self.funcdict public to rpc clients'
		funcstruct = {}
		fdict = {}
		for key,value in self.funcdict.items():
			fdict[key] = {}
			fdict[key]['argspec'] = value['argspec']
		funcstruct['dict'] = fdict
		funcstruct['list'] = self.funclist
		return funcstruct

	def uiID(self):
		return self.id

class ClientComponent(object):
	def __init__(self, parent, name, argspec):
		self.parent = parent
		self.name = name
		self.init_args(argspec)

	def init_args(self, argspec):
		self.argspec = argspec
		self.argnameslist = []
		self.argvaluesdict = {}
		self.argtypesdict = {}
		self.argaliasdict = {}
		for arg in argspec:
			argname = arg['name']
			self.argnameslist.append(argname)
			self.argtypesdict[argname] = arg['type']
			if 'alias' in arg:
				self.argaliasdict[argname] = arg['alias']
			else:
				self.argaliasdict[argname] = argname
			if 'default' in arg:
				self.argvaluesdict[argname] = arg['default']
			else:
				self.argvaluesdict[argname] = None

	def execute(self):
		args = self.argvalues()
		return getattr(self.parent.proxy, self.name)(*args)

	def argnames(self):
		return tuple(self.argnameslist)

	def argvalues(self):
		arglist = []
		for argname in self.argnameslist:
			arglist.append(self.argvaluesdict[argname])
		return tuple(arglist)

	def argtypes(self):
		arglist = []
		for argname in self.argnameslist:
			arglist.append(self.argtypesdict[argname])
		return tuple(arglist)

	def argtype(self, argname):
		return self.argtypesdict[argname]

	def argalias(self, argname):
		return self.argaliasdict[argname]

	def argvalue(self, argname):
		return self.argvaluesdict[argname]

	def setarg(self, argname, argvalue):
		self.argvaluesdict[argname] = argvalue

	def __setitem__(self, key, value):
		self.argvaluesdict[key] = value

	def __getitem__(self, key):
		return self.argvaluesdict[key]


class Client(object):
	def __init__(self, hostname, port):
		uri = 'http://%s:%s' % (hostname, port)
		self.proxy = xmlrpclib.ServerProxy(uri)
		self.id = self.proxy.id()

	def getMethods(self):
		self.funcdict = {}
		self.funclist = []
		f = self.proxy.methods()
		fdict = f['dict']
		self.funclist = f['list']
		for key,value in fdict.items():
			c = ClientComponent(self, key, value['argspec'])
			self.funcdict[key] = c

	def execute(self, funcname):
		args = self.funcdict[funcname].argvalues()
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
