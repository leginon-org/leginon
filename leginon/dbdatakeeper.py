import copy
import cPickle
import threading
import datahandler
import sqldict

class DBDataKeeper(datahandler.DataHandler):
	def __init__(self, id, session):
		datahandler.DataHandler.__init__(self, id, session)
		# leginon object id = id
		# session id = session
		# connect?
		self.dbd = sqldict.SQLDict()

	def query(self, idata, indices):
		# idata: instance of a Data class 
		# indices: {field:value, ... } for the WHERE clause
		
		table = data.__class__.__name__
		select = sqldict.sqlColumnsSelect(idata)
		self.dbd.myTable = self.dbd.Table(table,select)
		sqlindices = map(sqldict.sqlColumnsFormat, indices.keys())
		self.dbd.myTable.Index = self.dbd.Table(sqlindices,
					orderBy = {'fields':('DEF_timestamp',),'sort':'DESC'})

		# return a list of dictionnaries for all matching rows
		result =  self.dbd.myTable.Index[indices.values()].fetchalldict()
		return map(sqldict.sql2data, result)

		# return an instance
		# result =  self.dbd.myTable.Index[indices.values()].fetchonedict()
		# val = data.update((sqldict.sql2data(result))
		# return val

		# to return one match only:
		# result = self.db.myTable.Index[indices.values()].fetchonedict()
		# return sqldict.sql2data(result)
	
		# WHERE stuff
		# return instance of the necessary Data class or optionally a list of
		# matching instances

		# images with be converted from an mrc file here, an instance of Data
		# will have to be created here.

	def insert(self, newdata):
		data = copy.deepcopy(newdata)
		table = data.__class__.__name__
		definition = sqldict.sqlColumnsDefinition(data)
		formatedData = sqldict.sqlColumnsFormat(data)
		self.db.createSQLTable(table,definition)
		self.db.myTable = self.db.Table(table)
		
		return self.db.myTable.insert([formatedData])

		# images with be converted to an mrc file here, the filename will be
		# available. What should the path of the file be?

	# you can clean up with this if you want
	def exit(self):
		pass
		# disconnect?

	# don't bother with these for now
	def remove(self, id):
		pass
	def ids(self):
		pass

# Ignore for now

# doens't really lock across processes
# bad things could happen with have multiple sessions and don't specify session

picklefilename = './DataPickle'

class PickleDataKeeper(datahandler.DataHandler):
	def __init__(self, id, session=None):
		datahandler.DataHandler.__init__(self, id)
		self.lock = threading.Lock()
		self.filename = picklefilename
		self.db = {}
		if session is not None:
			self.newSession(session)
		else:
			self._read()
			self.session = self.db['sessions'][-1]

	def newSession(self, session):
		self.lock.acquire()
		self._read()
		self.session = session
		if 'sessions' not in self.db:
			self.db['sessions'] = []
		if 'data' not in self.db:
			self.db['data'] = {}
		if session not in self.db['sessions']:
			self.db['sessions'].append(self.session)
			self.db['data'][self.session] = {}
		self.data = self.db['data'][self.session]
		self._write()
		self.lock.release()

	def query(self, **kwargs):
		self.lock.acquire()
		try:
			session = kwargs['session']
		except KeyError:
			session = self.session
		try:
			id = kwargs['id']
		except KeyError:
			self.printerror('failed to specify ID in query')
			raise ValueError

		self._read()

		# let exception fall through?
		try:
			# does copy happen elsewhere?
			# taking latest result, need to be able to specify
			result = copy.deepcopy(self.db['data'][session][id])
		except KeyError:
			result = None
		self.lock.release()
		return result

	# needs to use session id
	def insert(self, newdata):
		self.lock.acquire()
		self._read()
		# does copy happen elsewhere?
#		self.db['data'][self.session][newdata['id']] = copy.deepcopy(newdata)
		# old style
		self.db['data'][self.session][newdata.id] = copy.deepcopy(newdata)
		self._write()
		self.lock.release()

	# necessary?
	def remove(self, id):
		self.lock.acquire()
		# all?
		self._read()
		del self.db['data'][self.session][id]
		self._write()
		self.lock.release()

	# necessary?
	def ids(self):
		self.lock.acquire()
		self._read()
		return self.db['data'][self.session].keys()
		self.lock.release()

	def exit(self):
		self.lock.acquire()

	def _read(self):
		#self.lock.acquire()
		try:
			file = open(self.filename, 'rb')
			self.db = cPickle.load(file)
			file.close()
		except:
			self.printerror('cannot read from %s' % self.filename)
		#self.lock.release()

	def _write(self):
		#self.lock.acquire()
		try:
			file = open(self.filename, 'wb')
			cPickle.dump(self.db, file, True)
			file.close()
		except IOError:
			self.printerror('cannot write to %s' % self.filename)
		#self.lock.release()

