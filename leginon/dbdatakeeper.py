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

	def query(self, idata, results=None):
		'''
		query using a partial Data instance
		'''
		# idata: instance of a Data class 
		# results: number of rows wanted
		queryinfo = self.queryInfo(idata)
		result  = self.dbd.multipleQueries(queryinfo)

		if results is not None:
			myresult = result.fetchmany(results)
		else:
			myresult = result.fetchall()
		return myresult

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
		isroot=0
		if hasattr(mydata, 'isRoot'):
			isroot = 1
			del mydata.isRoot

		info['root'] = isroot

		finalinfo = {myid: info}

		return [finalinfo]

	def queryInfo(self, idata):
		'''
		Items of idata that are None, should be ignored.
		Items of idata that are DataReferences refer to another Data
		Other items are normal comparisons for the WHERE clause
		'''
		idata.isRoot=1
		mylist = data.accumulateData(idata, self.datainfo)
		finaldict = {}
		for d in mylist:
			finaldict.update(d)
		return finaldict

	def insert(self, newdata):
		#self.flatInsert(newdata)
		self.recursiveInsert(newdata)

	def flatInsert(self, newdata):
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
			self.printException()
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

