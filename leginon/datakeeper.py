import leginonobject
import data
import threading

class DataKeeper(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)

	def query(self, id):
		raise NotImplementedError

	def insert(self, newdata):
		raise NotImplementedError

class SimpleDataKeeper(DataKeeper):
	def __init__(self):
		DataKeeper.__init__(self)
		self.datadict = {}
		self.datadictlock = threading.RLock()

	def query(self, id):
		self.datadictlock.acquire()
		try:
			result = self.datadict[id]
		except KeyError:
			result = None
		self.datadictlock.release()
		return result

	def insert(self, newdata):
		if type(newdata) != data.Data:
			raise TypeError
		self.datadictlock.acquire()
		self.datadict[newdata.id] = newdata
		self.datadictlock.release()

