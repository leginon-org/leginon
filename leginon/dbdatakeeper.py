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
		self.lock = threading.RLock()

	def query(self, idata, results=None):
		self.lock.acquire()
		try:
			ret = self._query(idata, results)
		finally:
			self.lock.release()
		return ret

	def _query(self, idata, results=None):
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
		'''
		idata.isRoot=1
		mylist = data.accumulateData(idata, self.datainfo)
		finaldict = {}
		for d in mylist:
			finaldict.update(d)
		return finaldict

	def insert(self, newdata):
		self.lock.acquire()
		try:
			self._insert(newdata)
		finally:
			self.lock.release()

	def recursiveInsert(self, newdata):
		'''
		recursive insert will insert an objects children before
		inserting an object
		'''
		## insert children if they are Data instances
		for value in newdata.values():
			if isinstance(value, data.Data):
				self.recursiveInsert(value)

		## insert this object if is has never been inserted
		if newdata.dbid is None:
			newdata.dbid = self.flatInsert(newdata)

	def _insert(self, newdata):
		#self.flatInsert(newdata)
		return self.recursiveInsert(newdata)

	def flatInsert(self, newdata):
		table = newdata.__class__.__name__
		definition = sqldict.sqlColumnsDefinition(newdata)
		formatedData = sqldict.sqlColumnsFormat(newdata)
		self.dbd.createSQLTable(table, definition)
		myTable = self.dbd.Table(table)
		newid = myTable.insert([formatedData])
		return newid

	def insertWithForeignKeys(self, newdata):
		'''
		inserts a data object that may include some items which
		are references to other data.  Returns a reference to
		this newly inserted data object.
		'''
		insertid = self.flatInsert(newdata)
		newdata.dbid = insertid
		return newdata

	# don't bother with these for now
	def remove(self, id):
		pass

	def ids(self):
		pass

