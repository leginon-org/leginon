import xmlrpclib

class Location(object):
        def __init__(self, hostname, rpcport, pid):
                self.hostname = hostname
                self.rpcport = rpcport
                self.pid = pid

	def getURI(self):
		return "http://%s:%d" % (self.hostname, self.rpcport)

	def rpc(self, method, args=()):
			uri = self.getURI()
			proxy = xmlrpclib.ServerProxy(uri)
			ret = apply(getattr(proxy,method), args)
			return ret

	def tostring(self):
		return "PID %d on %s:%d" % (self.pid, self.hostname, self.rpcport)

	def __str__(self):
		ret = 'Host: %s,  RPC Port: %s,  PID: %s' % (self.hostname, self.rpcport, self.pid)
		return ret

	def xmlrpc_repr(self):
		repr = {'host':self.hostname, 'rpcport':self.rpcport, 'pid': self.pid}
		return repr

class NodeLocation(Location):
        def __init__(self, hostname, rpcport, pid, dataport):
                Location.__init__(self, hostname, rpcport, pid)
                self.dataport = dataport

	def __str__(self):
		ret = Location.__str__(self)
		ret += ',  Data Port: %s' % self.dataport
		return ret

	def xmlrpc_repr(self):
		repr = Location.xmlrpc_repr(self)
		repr['dataport'] = self.dataport
		return repr
