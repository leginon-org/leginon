import copy
import cPickle
import threading
import datahandler
import sqldict
import data
import Mrc

class DBDataKeeper(datahandler.DataHandler):
	def __init__(self, id, session):
		datahandler.DataHandler.__init__(self, id, session)
		# leginon object id = id
		# session id = session
		self.dbd = sqldict.SQLDict()

	def query(self, idata, indices, results=0):
		# idata: instance of a Data class 
		# indices: {field:value, ... } for the WHERE clause
		#print 'querying'
		
		table = idata.__class__.__name__
#		select = sqldict.sqlColumnsSelect(idata)
#		self.dbd.myTable = self.dbd.Table(table,select)
		self.dbd.myTable = self.dbd.Table(table)
		sqlindices = sqldict.sqlColumnsFormat(indices)
		self.dbd.myTable.myIndex = self.dbd.myTable.Index(sqlindices.keys(),
															orderBy = {'fields':('DEF_timestamp',),'sort':'DESC'})
		# return a list of dictionnaries for all matching rows
		if results > 0:
			result = self.dbd.myTable.myIndex[sqlindices.values()].fetchmany(results)
		else:
			result = self.dbd.myTable.myIndex[sqlindices.values()].fetchall()
		result = map(sqldict.sql2data, result)
		for i in range(len(result)):
			del result[i]['DEF_id']
			del result[i]['DEF_timestamp']
			newid = result[i]['id']
			del result[i]['id']
			try:
				result[i] = idata.__class__(newid, result[i])
			except KeyError, e:
				self.printerror('cannot convert database result to data instance')
				del result[i]
		map(self.file2image, result)
		#print 'querying done'
		return result

		# return an instance
		# result =  self.dbd.myTable.Index[indices.values()].fetchone()
		# val = data.update((sqldict.sql2data(result))
		# return val

		# to return one match only:
		# result = self.db.myTable.Index[indices.values()].fetchone()
		# return sqldict.sql2data(result)
	
		# images with be converted from an mrc file here, an instance of Data
		# will have to be created here.

	def insert(self, newdata):
		newdatacopy = copy.deepcopy(newdata)
		self.image2file(newdatacopy)
		table = newdatacopy.__class__.__name__
		definition = sqldict.sqlColumnsDefinition(newdatacopy)
		formatedData = sqldict.sqlColumnsFormat(newdatacopy)
		self.dbd.createSQLTable(table,definition)
		self.dbd.myTable = self.dbd.Table(table)
		
		return self.dbd.myTable.insert([formatedData])

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

	def image2file(self, idata):
		if isinstance(idata, data.ImageData):
			if idata['image'] is not None:
				# filename = ???
				filename = './images/%s-%s.mrc' % (self.session, idata['id'])
				try:
					Mrc.numeric_to_mrc(idata['image'], filename)
				except:
					self.printerror('error converting image to file')
				idata['database filename'] = filename
				idata['image'] = None

		types = idata.types()
		for key in types:
			if issubclass(types[key], data.ImageData):
				if idata[key]['image'] is not None:
					# filename = ???
					filename = './images/%s-%s-%s.mrc' % (self.session, idata['id'], key)
					try:
						Mrc.numeric_to_mrc(idata[key]['image'], filename)
					except:
						self.printerror('error converting image to file')
					idata[key]['database filename'] = filename
					idata[key]['image'] = None

	def file2image(self, idata):
		if isinstance(idata, data.ImageData):
			if idata['database filename'] is not None:
				try:
					idata['image'] = Mrc.mrc_to_numeric(idata['database filename'])
				except:
					self.printerror('error converting image from file')
				idata['database filename'] = None

		types = idata.types()
		for key in types:
			if issubclass(types[key], data.ImageData):
				if idata[key]['database filename'] is not None:
					try:
						idata[key]['image'] = Mrc.mrc_to_numeric(
																					idata[key]['database filename'])
					except:
						self.printerror('error converting image from file')
					idata[key]['database filename'] = None

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

