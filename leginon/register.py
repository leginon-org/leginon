class Register(object):
        def __init__(self):
                self.id = 0
                self.entries = {}
        def addEntry(self, entry):
                id = self.makeUI()
                entry.id = id
                self.entries[id] = entry
                return id
        def delEntry(self, id):
                del self.entries[id]
        def makeUI(self):
                # placeholder
                self.id += 1
                return self.id

	def __str__(self):
		ret = ''
		for id in self.entries:
			ret += 'ID:  %s\n' % id
			ret += '%s\n' % self.entries[id]
		return ret

	def xmlrpc_repr(self):
		repr = {}
		for key in self.entries:
			repr[key] = self.entries[key].xmlrpc_repr()
		return repr

class RegisterEntry(object):
        def __init__(self, methods, events, location):
                self.id = None
                self.methods = methods
                self.events = events
                self.location = location

	def __str__(self):
		ret = ''
		ret += 'Location:  %s\n' % self.location
		ret += 'Methods:  %s\n' % self.methods
		ret += 'Events:  %s\n' % self.events
		return ret

	def xmlrpc_repr(self):
		"return a legal xml-rpc structure representation"
		repr = {}
		repr['location'] = self.location.xmlrpc_repr()
		repr['methods'] = self.methods
		repr['events'] = self.events
		return repr
