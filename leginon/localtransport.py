#!/usr/bin/env python
import leginonobject
import copy
import threading
#import weakref

#_id2obj_dict = weakref.WeakValueDictionary()
localserverdict = {}
localserverdictlock = threading.RLock()

class Server(leginonobject.LeginonObject):
	def __init__(self, nid, dh):
		leginonobject.LeginonObject.__init__(self, nid)
		self.datahandler = dh
		self.pythonid = id(self)
		localserverdictlock.acquire()
		localserverdict[self.pythonid] = self
		localserverdictlock.release()

	def start(self):
		pass

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc['local server python ID'] = self.pythonid
		return loc

	def exit(self):
		localserverdictlock.acquire()
		del localserverdict[self.pythonid]
		localserverdictlock.release()

class Client(leginonobject.LeginonObject):
	def __init__(self, id, location):
		leginonobject.LeginonObject.__init__(self, id)
		if location['hostname'] != self.location()['hostname']:
			raise ValueError
		self.serverlocation = location

	def push(self, idata):
		localserverdictlock.acquire()
		try:
			ret = self._push(idata)
			localserverdictlock.release()
			return ret
		except:
			localserverdictlock.release()
			raise

	def _push(self, idata):
		try:
			server = localserverdict[self.serverlocation['local server python ID']]
		except KeyError:
			raise IOError

		if server is None:
			raise IOError # err...its sort of an IOError
		else:
			idatacopy = copy.deepcopy(idata)
			obj = server.datahandler.insert(idatacopy)
			return obj

	def pull(self, id):
		localserverdictlock.acquire()
		try:
			ret = self._pull(id)
			localserverdictlock.release()
			return ret
		except:
			localserverdictlock.release()
			raise

	def _pull(self, id):
		try:
			server = localserverdict[self.serverlocation['local server python ID']]
		except KeyError:
			raise IOError

		if server is None:
			raise IOError
		else:
			try:
				obj = copy.deepcopy(server.datahandler.query(id))
			except Exception, e:
				raise IOError
			return obj

if __name__ == '__main__':
	pass
