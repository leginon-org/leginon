import xmlrpclib

class client(xmlrpclib.Server):
    def __init__(self, uri):
        xmlrpclib.Server.__init__(self, uri)
    def __repr__(self):
        return self.export__repr__() 
    def __cmp__(self, dict):
        return self.export__cmp__(dict)
    def __len__(self):
         return self.export__len__()
    def __getitem__(self, key):
        return self.export__getitem__(key)
    def __setitem__(self, key, item):
        return self.export__setitem__(key, item)
    def __delitem__(self, key):
        return self.export__delitem__(key)
    def __contains__(self, key):
        return self.export__contains__(key)
    def __iter__(self):
        return self.export__iter__()
    def copy(self):
        return self.exportcopy()

