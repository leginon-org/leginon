#!/usr/bin/env python
import leginonobject
import copy
import weakref

class WeakrefWrapper:
  def __init__(self, ref):
    self.ref = ref
  def __getstate__(self):
    return None

class Server(leginonobject.LeginonObject):
	def __init__(self, dh):
		leginonobject.LeginonObject.__init__(self)
		self.datahandler = dh

	def start(self):
		pass

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc['weakref'] = WeakrefWrapper(weakref.ref(self))
		return loc

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
