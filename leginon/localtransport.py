#!/usr/bin/env python
import leginonobject
import copy

class Server(leginonobject.LeginonObject):
	def __init__(self, dh):
		leginonobject.LeginonObject.__init__(self)
		self.datahandler = dh

	def start(self):
		pass

class Client(leginonobject.LeginonObject):
	def __init__(self, location):
		leginonobject.LeginonObject.__init__(self)
		self.serverlocation = location

	def push(self, idata):
		o = self.serverlocation['weakref']()
		if o is None:
			raise ValueError
		else:
			return o.datahandler.insert(copy.deepcopy(idata))

	def pull(self, id):
		o = self.serverlocation['weakref']()
		if o is None:
			raise ValueError
		else:
			return copy.deepcopy(o.datahandler.query(id))

if __name__ == '__main__':
	pass
