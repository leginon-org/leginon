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

class RegisterEntry(object):
        def __init__(self, methods, events, location):
                self.id = None
                self.methods = methods
                self.events = events
                self.location = location

