class Location(object):
        def __init__(self, hostname, port, pid):
                self.hostname = hostname
                self.port = port
                self.pid = pid

	def getURI(self):
		return "http://%s:%d" % (self.hostname, self.port)

	def tostring(self):
		return "PID %d on %s:%d" % (self.pid, self.hostname, self.port)

	def __str__(self):
		ret = 'Host: %s,  Port: %s,  PID: %s' % (self.hostname, self.port, self.pid)
		return ret

	def xmlrpc_repr(self):
		repr = {'host':self.hostname, 'port':self.port, 'pid': self.pid}
		return repr

class NodeLocation(Location):
        def __init__(self, hostname, port, pid, dataport):
                Location.__init__(self, hostname, port, pid)
                self.dataport = dataport

	def __str__(self):
		ret = Location.__str__(self)
		ret += ',  Data Port: %s' % self.dataport
		return ret

	def xmlrpc_repr(self):
		repr = Location.xmlrpc_repr(self)
		repr['dataport'] = self.dataport
		return repr
