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
		DataHandler.__init__(self)
		self.datadict = {}
		self.datadictlock = threading.RLock()

	def query(self, id):
		print 'Simple...query', id
		print 'query DATADICT', self.datadict
		print 'query DATADICT', id, self.datadict[id]
		self.datadictlock.acquire()
		try:
			result = self.datadict[id]
		except KeyError:
			result = None
		self.datadictlock.release()
		return result

	def insert(self, newdata):
		print 'Simple...insert', newdata.id, newdata
		if not issubclass(newdata.__class__, data.Data):
			raise TypeError
		self.datadictlock.acquire()
		self.datadict[newdata.id] = newdata
		self.datadictlock.release()
		print 'insert DATADICT', self.datadict


class DataBinder(DataHandler):
	def __init__(self):
		DataHandler.__init__(self)
		self.bindings = {}

	def insert(self, newdata):
		# now send data to a type specific handler function
		dataclass = newdata.__class__
		for bindclass in self.bindings:
			if issubclass(dataclass, bindclass):
				func = self.bindings[bindclass]
				args = (newdata,)
				try:
					apply(func, args)
				except:
					pass

	def setBinding(self, dataclass, func=None):
		'func must take data instance as first arg'
		if func == None:
			if dataclass in self.bindings:
				del self.bindings[dataclass]
		else:
			self.bindings[dataclass] = func
