import copy
import threading
import datahandler

# poor subsitute for database, making autoincrement type things without one
# big file (which is bad too) takes some doing.
# other worries are this is only meant to be opened once a sesssion
# mainly (read/write) by one manager, node, whatever

picklefilename = './datapickle'

class PickleDataKeeper(datahandler.DataHandler):
	def __init__(self, id, sessionid):
		datahandler.DataHandler.__init__(self, id)
		self.lock = threading.Lock()
		self.filename = picklefilename
		self._new()
		self.data = self.db['data'][sessionid]

	def _new(self, sessionid):
		try:
			self._read()
			if sessionid in self.db['sessions']:
				raise ValueError
		# assuming this is a no such file exists
		except IOError:
			self.db = {'sessions': [sessionid], 'data': {sessionid: {}}}
			self.write()
		self.sessionid = sessionid

	# needs to use session id
	def query(self, id, sessionid):
		self.lock.acquire()
		# let exception fall through?
		try:
			# does copy happen elsewhere?
			# taking latest result, need to be able to specify
			result = copy.deepcopy(self.db['data'][id][-1])
		except KeyError:
			result = None
		self.lock.release()

	# needs to use session id
	def insert(self, newdata):
		self.lock.acquire()
		if newdata.id not in self.db['data']:
			self.db['data'][newdata.id] = []
		# does copy happen elsewhere?
		self.db['data'][newdata.id].append(copy.deepcopy(newdata))
		self.lock.release()

	# necessary?
	def remove(self, id):
		self.lock.acquire()
		# all?
		del self.db['data'][id]
		self.lock.release()

	# necessary?
	def ids(self):
		self.lock.acquire()
		return self.db['data'].keys()
		self.lock.release()

	def exit(self):
		self._write()
		self.lock.acquire()
		del self.db

	def _read(self):
		self.lock.acquire()
		try:
			file = open(self.filename, 'rb')
			self.db = cPickle.load(file)
			self.db['session id'] += 1
			file.close()
		except:
			self.lock.release()
			raise
		self.lock.release()

	def _write(self):
		self.lock.acquire()
		try:
			file = open(self.filename, 'wb')
			cPickle.dump(self.db, file, bin=True)
			file.close()
		except IOError:
			self.lock.release()
			raise
		self.lock.release()

