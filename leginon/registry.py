import time

class Registry(object):
        def __init__(self):
                self.id = -1
                self.entries = {}

        def addEntry(self, entry):
                id = self.makeUniqueID()
                entry.id = id
		entry.time = self.makeTimeStamp()
                self.entries[id] = entry
                return id

        def delEntry(self, id):
                del self.entries[id]

        def makeUniqueID(self):
                # placeholder
                self.id += 1
                return self.id

	def makeTimeStamp(self):
		return time.localtime()

	def __str__(self):
		ret = ''
		for id in self.entries:
			ret += 'ID %s: ' % id
			ret += '%s\n' % self.entries[id]
		return ret

	def xmlrpc_repr(self):
		repr = {}
		for key in self.entries:
			repr[key] = self.entries[key].xmlrpc_repr()
		return repr

class RegistryEntry(object):
        def __init__(self):
                self.id = None
		self.time = None

	def __str__(self):
		str = ''
		str += 'ID:  %s\n' % self.id
		if self.time:
			time_str = time.strftime("%a %d %b %Y %H:%M:%S", self.time)
		else:
			time_str = self.time
		str += 'Entry Time:  %s\n' % time_str
		return str

	def xmlrpc_repr(self):
		"return a legal xml-rpc structure representation"
		repr = {}
		repr['id'] = self.id
		repr['entry time'] = self.entry_time
		return repr

class NodeRegistryEntry(RegistryEntry):
        def __init__(self, methods, events, location):
		str = RegistryEntry.__init__(self)
                self.methods = methods
                self.events = events
                self.location = location

	def __str__(self):
		str = RegistryEntry.__str__(self)
		str += 'Location:  %s\n' % self.location
		str += 'Methods:  %s\n' % self.methods
		str += 'Events:  %s\n' % self.events
		return str

	def xmlrpc_repr(self):
		repr = RegistryEntry.__repr__(self)
		repr['location'] = self.location.xmlrpc_repr()
		repr['methods'] = self.methods
		repr['events'] = self.events
		return repr

class DataRegistryEntry(RegistryEntry):
	def __init__(self, type, source, creation_time):
		str = RegistryEntry.__init__(self)
		self.type = type
		self.source = source
		self.creation_time = creation_time

	def __str__(self):
		str = RegistryEntry.__str__(self)
		str += 'Type:  %s\n' % self.type
		str += 'Source:  %s\n' % self.source
		if self.time:
			time_str = time.strftime("%a %d %b %Y %H:%M:%S", self.creation_time)
		else:
			time_str = self.creation_time
		str += 'Creation Time:  %s\n' % time_str
		return str

	def xmlrpc_repr(self):
		repr = RegistryEntry.__repr__(self)
		repr['type'] = self.type
		repr['source'] = self.source.xmlrpc_repr()
		repr['creation time'] = self.creation_time
		return repr

