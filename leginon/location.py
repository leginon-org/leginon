class Location(object):
        def __init__(self, hostname, port, pid):
                self.hostname = hostname
                self.port = port
                self.pid = pid
	def getURI(self):
		return "http://%s:%d" % (self.hostname, self.port)
	def tostring(self):
		return "PID %d on %s:%d" % (self.pid, self.hostname, self.port)

class NodeLocation(Location):
        def __init__(self, hostname, port, pid, eventport, dataport):
                Location.__init__(self, hostname, port, pid)
                self.eventport = eventport
                self.dataport = dataport
