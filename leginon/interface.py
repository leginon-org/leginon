
import xmlrpcserver
import xmlrpclib
import threading
import code
import inspect


xmlrpctypes = ('boolean', 'integer', 'float', 'string', 'array', 'struct', 'date', 'binary')


class Server(xmlrpcserver.xmlrpcserver):
	'''
	- provide info necessary for calling those methods
	- generate proper calls from ui calls
	'''
	def __init__(self):
		xmlrpcserver.xmlrpcserver.__init__(self)
		self.funcdict = {}
		self.server.register_function(self.UIMethods, 'methods')

	def RegisterMethod(self, method, argspec, alias=None):
		if not alias:
			alias = method.__name__

		argnames = inspect.getargspec(method.im_func)[0]

		## validate argspec
		for argdict in argspec:
			if argdict['name'] not in argnames:
				raise RuntimeError('bad argname in argdict')
			xmlrpctype = argdict['type']
			if xmlrpctype not in xmlrpctypes:
				if type(xmlrpctype) not in (tuple,list):
					raise RuntimeError('bad xmlrpctype')

		self.funcdict[alias] = {'func': method, 'argspec':argspec}

		self.server.register_function(method, alias)

	def UIMethods(self):
		'makes some of self.funcdict public to rpc clients'
		funcstruct = {}
		for key,value in self.funcdict.items():
			funcstruct[key] = {}
			funcstruct[key]['argspec'] = value['argspec']

		return funcstruct


class ClientComponent(object):
	def __init__(self, name, argspec):
		self.name = name
		self.init_args(argspec)

	def init_args(self, argspec):
		self.argspec = argspec
		self.argnames = []
		self.argvalues = {}
		self.argtypes = {}
		for arg in argspec:
			argname = arg['name']
			self.argnames.append(argname)
			self.argtypes[argname] = arg['type']
			if 'default' in arg:
				self.argvalues[argname] = arg['default']
			else:
				self.argvalues[argname] = None

	def args(self):
		arglist = []
		for argname in self.argnames:
			arglist.append(self.argvalues[argname])
		return tuple(arglist)

	def type(self, argname):
		return self.argtypes[argname]

	def __setitem__(self, key, value):
		self.argvalues[key] = value

	def __getitem__(self, key):
		return self.argvalues[key]


class Client(object):
	def __init__(self, hostname, port):
		uri = 'http://%s:%s' % (hostname, port)
		self.proxy = xmlrpclib.ServerProxy(uri)

	def getMethods(self):
		self.funcdict = {}
		f = self.proxy.methods()
		for key,value in f.items():
			c = ClientComponent(key, value['argspec'])
			self.funcdict[key] = c

	def execute(self, funcname):
		args = self.funcdict[funcname].args()
		return getattr(self.proxy, funcname)(*args)

	def setarg(self, funcname, argname, value):
		self.funcdict[funcname][argname] = value

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
		self.uiserver.RegisterMethod(self.asdf, argspec, 'Asdf')

	def asdf(self, mynum, mystr, selection):
		print 'mynum', mynum
		print 'mystr', mystr
		print 'selection', selection
		return mynum * mystr + selection


class ManagerUIServer(Server):
	def __init__(self):
		Server.__init__(self)
		self.addInfoKey('nodeclasses')
		self.addInfoKey('nodes')
		self.addInfoKey('eventclasses')
		self.addInfoKey('launchers')
		self.uiUpdateEventclasses()
		self.uiUpdateNodeclasses()

	def uiUpdateEventclasses(self):
		self.ui_info['eventclasses'] = event.eventClasses()

	def uiUpdateNodeclasses(self):
		self.ui_info['nodeclasses'] = common.nodeClasses()

	def uiAddNode(self, node_id):
		node_str = node_id[-1]
		self.ui_info['nodes'][node_str] = node_id

	def uiAddLauncher(self, launcher_id):
		launcher_str = launcher_id[-1]
		self.ui_info['launchers'][launcher_str] = launcher_id

	def uiLaunch(self, name, launcher_str, nodeclass_str, args, newproc):
		"interface to the launchNode method"

		launcher_id = self.ui_info['launchers'][launcher_str]
		nodeclass = self.ui_info['nodeclasses'][nodeclass_str]

		args = '(%s)' % args
		try:
			args = eval(args)
		except:
			print 'problem evaluating args'
			return

		self.launchNode(launcher_id, newproc, nodeclass, name, args)

		## just to make xmlrpc happy
		return ''

	def uiAddDistmap(self, eventclass_str, fromnode_str, tonode_str):
		eventclass = self.ui_info['eventclasses'][eventclass_str]
		fromnode_id = self.ui_info['nodes'][fromnode_str]
		tonode_id = self.ui_info['nodes'][tonode_str]
		self.addEventDistmap(eventclass, fromnode_id, tonode_id)

		## just to make xmlrpc happy
		return ''


