import leginonobject
import data
import threading

class DataHandler(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)

	def query(self, id):
		raise NotImplementedError

	def insert(self, newdata):
		raise NotImplementedError


class SimpleDataKeeper(DataHandler):
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


class DataHandler(DataHandler):
	def __init__(self):
		DataKeeper.__init__(self)
		self.bindings = {}

	def insert(self, newdata):
		# now send data to a type specific handler function
		dataclass = newdata.__class__
		if dataclass in self.bindings:
			func = self.bindings[dataclass]
			args = (newdata,)
			try:
				apply(func, args)
			except:
				pass

	def bind(self, dataclass, func=None):
		'func must take data instance as first arg'
		if func == None:
			if dataclass in self.bindings:
				del self.bindings[dataclass]
		else:
			self.bindings[dataclass] = func
