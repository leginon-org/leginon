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
		self.lock = threading.RLock()

	def query(self, idata, results=None):
		self.lock.acquire()
		try:
			ret = self._query(idata, results)
			self.lock.release()
			return ret
		except:
			self.lock.release()
			raise

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
		self.lock.acquire()
		try:
			self._insert(newdata)
			self.lock.release()
		except:
			self.lock.release()
			raise

	def _insert(self, newdata):
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

