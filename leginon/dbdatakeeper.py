import copy
import cPickle
import threading
import datahandler
import sqldict
import data
import Mrc
import os
import strictdict

class DBDataKeeper(datahandler.DataHandler):
	def __init__(self, id, session):
		datahandler.DataHandler.__init__(self, id, session)
		# leginon object id = id
		# session id = session
		self.dbd = sqldict.SQLDict()

	def OLDquery(self, idata, indices, results=None):
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
		if results is not None:
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

	def query(self, idata, results=None):
		'''
		query using a partial Data instance
		'''
		# idata: instance of a Data class 
		# indices: {field:value, ... } for the WHERE clause
		#print 'querying'

		queryinfo = self.queryInfo(idata)
		print 'QUERYINFO'
		print queryinfo

		return
		### now we need to access multiple tables, not just one

		table = self.makeTableName(idata)
		self.dbd.myTable = self.dbd.Table(table)
		sqlindices = sqldict.sqlColumnsFormat(indices)
		self.dbd.myTable.myIndex = self.dbd.myTable.Index(sqlindices.keys(), orderBy = {'fields':('DEF_timestamp',),'sort':'DESC'})

		# return a list of dictionnaries for all matching rows
		if results is not None:
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

	def makeTableName(self, idata):
		'''
		Make a name for a table.
		'''
		classname = idata.__class__.__name__
		return classname

	def makeTableAlias(self, idata):
		'''
		Make an alias for a table.
		'''
		classname = idata.__class__.__name__
		alias = classname + str(id(idata))
		return alias

	def datainfo(self, mydata):
		'''
		function that should be called in data.accumulateData
		'''
		myid = id(mydata)
		myclassname = mydata.__class__.__name__
		myalias = myclassname + str(myid)

		info = {}
		info['class name'] = myclassname
		info['alias'] = myalias
		#info['python id'] = myid

		wheredict = {}
		joindict = {}
		for key,value in mydata.items():
			if value is None:
				pass
			elif isinstance(value, data.Data):
				joindict[key] = id(value)
			else:
				wheredict[key] = value
		info['where'] = wheredict
		info['join'] = joindict

		finalinfo = {myid: info}

		return [finalinfo]

	def queryInfo(self, idata):
		'''
		Items of idata that are None, should be ignored.
		Items of idata that are DataReferences refer to another Data
		Other items are normal comparisons for the WHERE clause
		'''
		mylist = data.accumulateData(idata, self.datainfo)
		finaldict = {}
		for d in mylist:
			finaldict.update(d)
		return finaldict

	def insert(self, newdata):
		#self.flatInsert(newdata)
		self.recursiveInsert(newdata)

	def flatInsert(self, newdata):
		print 'flatInsert'
		print newdata
		newdatacopy = copy.deepcopy(newdata)
		table = newdatacopy.__class__.__name__
		definition = sqldict.sqlColumnsDefinition(newdatacopy)
		formatedData = sqldict.sqlColumnsFormat(newdatacopy)
		self.dbd.createSQLTable(table, definition)
		self.dbd.myTable = self.dbd.Table(table)
		return self.dbd.myTable.insert([formatedData])

	def recursiveInsert(self, newdata):
		'''
		split up and insert newdata and its children individually
		'''
		newdata.replaceData(self.insertWithForeignKeys)

	def insertWithForeignKeys(self, newdata):
		'''
		inserts a data object that may include some items which
		are references to other data.  Returns a reference to
		this newly inserted data object.
		'''
		## make certain replacements
		mycopy = self.replacements(newdata)

		### insert the data object and return a DataReference to it
		dr = data.DataReference()
		dr['id'] = self.flatInsert(mycopy)
		dr['target'] = newdata
		return dr

	def ref2lastid(self, datareference):
		return datareference['id']

	def lastid2ref(self, lastid):
		dr = data.DataReference()
		dr['id'] = lastid
		return dr

	def replacements(self, newdata):
		'''
		Perform certain replacements on the data to prepare it
		for insertion.  Right now we do these:
		   - save images and replace with None
		   - replace instances of DataReference with the sql id

		After replacements, the returned object may not be of the
		exact same type as the input object.
		'''
		## shallow copy!  reassign but don't modify values!
		mycopy = copy.copy(newdata)

		if isinstance(mycopy, data.ImageData):
			## save the image to file
			mycopy.save()
			## replace image with None
			mycopy['image'] = None

		return mycopy

	# you can clean up with this if you want
	def exit(self):
		pass
		# disconnect?

	# don't bother with these for now
	def remove(self, id):
		pass

	def ids(self):
		pass

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

