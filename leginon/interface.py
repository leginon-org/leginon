import leginonobject
import xmlrpcserver
import xmlrpclib
import threading
import inspect
import copy

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
	def __init__(self, id, server, name, xmlrpctype, permissions=None, choices=None, default=None, pyname=None, callback=None):
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
		self.choices = choices
		self.uidata = None
		self.pyname = pyname
		if callback is not None:
			self.registerCallback(callback)
		else:
			self.callback = None
#		self.default = False
		if default is not None:
			self.set(default)
#			self.default = True

	def registerCallback(self, callback):
		if callable(callback):
			self.callback = callback
		else:
			raise TypeError('callback must be callable')

	def get(self):
		if self.callback is None:
			return copy.deepcopy(self.uidata)
		else:
			return copy.deepcopy(self.callback())

	def set(self, value):
		valuecopy = copy.deepcopy(value)
		if self.callback is None:
			self.uidata = valuecopy
			self.server.uiServerPush(self.dict()['id'], valuecopy)
			return copy.deepcopy(self.uidata)
		else:
			d = self.callback(valuecopy)
			self.server.uiServerPush(self.dict()['id'], d)
			return copy.deepcopy(d)

	def dict(self):
		d = SpecObject.dict(self)
		d['name'] = self.name
		d['xmlrpctype'] = self.xmlrpctype
		if self.permissions is not None:
			d['permissions'] = self.permissions

		if self.choices is not None:
			idstr = str(self.choices.id)
			type = self.choices.xmlrpctype
			d['choices'] = {'id':idstr, 'type':type}

#		d['default'] = self.default
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

	def __iadd__(self, other):
		'''
		ContainerSpec concatenation
		allows this container to absorb contents of another
		'''
		if not isinstance(other, ContainerSpec):
			raise TypeError('can only concatenate ContainerSpec to ContainerSpec')
		self.content += other.content
		return self

class Server(xmlrpcserver.xmlrpcserver):
	def __init__(self, id, port=None):
		xmlrpcserver.xmlrpcserver.__init__(self, id, port=port)
		self.uidata = {}
		self.uiclients = []
		#self.server.register_function(self.uiMethods, 'methods')
		self.server.register_function(self.uiSpec, 'spec')
		self.server.register_function(self.uiClientPull, 'GET')
		self.server.register_function(self.uiClientPush, 'SET')
		self.server.register_function(self.uiServer, 'SERVER')

	def uiClientPull(self, idstr):
		'''this is how a UI client gets a data value'''
		data = self.uidata[idstr]
		value = data.get()
		if value is None:
			return ''
		else:
			return value

	def uiClientPush(self, idstr, value):
		'''this is how a UI client sets a data value'''
		data = self.uidata[idstr]
		data.set(value)
		return data.get()

	def uiServerPush(self, id, value):
		uiclients = copy.copy(self.uiclients)
		for client in uiclients:
			if client.execute('SET', (id, value)) == 0:
				self.uiclients.remove(client)

	def uiServer(self, hostname, port):
		self.uiclients.append(Client(hostname, port))
		return ''

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
			try:
				arg.pyname = argnames[ind]
			except:
				raise RuntimeError('argument problem in %s, %s' % (func, name))
			ind += 1
		m = MethodSpec(id, name, argspec, returnspec)
		return m

	def registerData(self, name, xmlrpctype, permissions=None, choices=None, default=None, pyname=None, callback=None):
		id = self.ID()
		d = DataSpec(id, self, name, xmlrpctype, permissions, choices, default, pyname, callback)
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
	def __init__(self, hostname, port, server=None):
		uri = 'http://%s:%s' % (hostname, port)
		self.proxy = xmlrpclib.ServerProxy(uri)
		if server is not None:
			self.execute('SERVER', (server.hostname, server.port))

	def getSpec(self):
		#self.spec = self.proxy.spec()
		self.spec = self.execute('spec')
		return self.spec

	def execute(self, funcname, args=()):
		try:
			ret = getattr(self.proxy, funcname)(*args)
		except xmlrpclib.ProtocolError, detail:
			print 'ProtocolError during XML-RPC call:', funcname
			print 'Note:  this usually means an attempt was made'
			print ' to send unsupported types, like NoneType or'
			print ' something other than a string as a dict key.'
			print ' Check the return value of the remote method.'
			print 'ProtocolError detail:', detail.errmsg
			ret = None
		except xmlrpclib.Fault, detail:
			print 'Received the following exception from XML-RPC Server during call to %s:' % funcname
			print detail.faultString
			ret = None
		return ret

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
