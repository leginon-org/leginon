#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import sqldict
import threading
import extendedlogging
import _mysql_exceptions

class DBDataKeeper(object):
	def __init__(self, loggername=None):
		self.logger = extendedlogging.getLogger(self.__class__.__name__, loggername)
		try:
			self.dbd = sqldict.SQLDict()
		except _mysql_exceptions.OperationalError, e:
			raise RuntimeError(e.args[1])
		self.lock = threading.RLock()

	def direct_query(self, dataclass, id):
		dummy = dataclass()
		dummy.isRoot = True
		datainfo = self.datainfo(dummy, dbid=id)
		queryinfo = datainfo[0]
		self.lock.acquire()
		try:
			result  = self.dbd.multipleQueries(queryinfo)
			myresult = result.fetchall()
		finally:
			self.lock.release()
		if len(myresult) == 0:
			return None
		elif len(myresult) == 1:
			return myresult[0]
		else:
			raise RuntimeError('direct_query should only return a single result')

	def query(self, idata, results=None, readimages=True):
		self.logger.info('query %s' % idata)
		self.lock.acquire()
		try:
			ret = self._query(idata, results, readimages=readimages)
		finally:
			self.lock.release()
		return ret

	def _query(self, idata, results=None, readimages=True):
		'''
		query using a partial Data instance
		'''
		# idata: instance of a Data class 
		# results: number of rows wanted
		queryinfo = self.queryInfo(idata)
		result  = self.dbd.multipleQueries(queryinfo, readimages=readimages)

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

	def qid(self, mydata):
		### what are the chances that there will be a conflict
		### because a dbid is the same as a python id?
		if isinstance(mydata, data.DataReference):
			myclassname = mydata.dataclass.__name__
			if mydata.dbid is not None:
				myid = myclassname+str(mydata.dbid)
			else:
				mydata = mydata.getData()
				if isinstance(mydata, data.DataReference):
					raise RuntimeError('I was not expecting this to happen, so we need to implement handling a replaced DataReference')
				myid = id(mydata)
		elif isinstance(mydata, data.Data):
			myid = id(mydata)
			myclassname = mydata.__class__.__name__
		else:
			raise RuntimeError('need Data or DataReference')
		return {'id': myid, 'class name': myclassname, 'data': mydata}

	def datainfo(self, mydata, dbid=None):
		'''
		function that should be called in data.accumulateData
		'''
		stuff = self.qid(mydata)
		myalias = stuff['class name'] + str(stuff['id'])
		myid = stuff['id']
		info = {}
		info['class name'] = stuff['class name']
		info['alias'] = myalias

		if dbid is not None:
			## force a simple query on DEF_id
			wheredict = {'DEF_id':dbid}
			info['where'] = wheredict
			info['known'] = None
			info['join'] = {}
		elif mydata.dbid is not None:
			## this instance is from the database
			dbid = mydata.dbid
			## now I don't think we even need to set wheredict
			## becuase it will not query if known
			wheredict = {'DEF_id':dbid}
			info['where'] = wheredict
			info['known'] = mydata
			info['join'] = {}
		else:
			## this instance will be used to create a query
			wheredict = {}
			joindict = {}
			for key,value in mydata.items(dereference=False):
				if value is None:
					pass

				elif isinstance(value, (data.Data, data.DataReference)):
					stuff = self.qid(value)
					joindict[key] = stuff['id']
				else:
					wheredict[key] = value
			info['where'] = wheredict
			info['join'] = joindict
			info['known'] = None

		isroot=0
		if hasattr(mydata, 'isRoot'):
			isroot = 1
			del mydata.isRoot

		info['root'] = isroot

		finalinfo = {myid: info}
		return [finalinfo]

	def accumulateData(self, originaldata, memo=None):
		d = id(originaldata)

		if memo is None:
			memo = {}
		if memo.has_key(d):
			return None

		myresult = []

		if isinstance(originaldata, data.Data):
			for key,value in originaldata.items(dereference=False):
				if isinstance(value, data.DataReference):
					if value.dbid is None:
						value = value.getData()
						if isinstance(value, data.DataReference):
							value = value.getData()
					childresult = self.accumulateData(value, memo)
					if childresult is not None:
						myresult += childresult

		myresult = self.datainfo(originaldata) + myresult

		memo[d] = myresult
		return myresult

	def queryInfo(self, idata):
		'''
		Items of idata that are None, should be ignored.
		'''
		idata.isRoot=1
		mylist = self.accumulateData(idata)
		finaldict = {}
		for d in mylist:
			finaldict.update(d)
		return finaldict

	def insert(self, newdata, force=False):
		self.lock.acquire()
		try:
			self._insert(newdata, force=force)
		finally:
			self.lock.release()

	def recursiveInsert(self, newdata, force=False):
		'''
		recursive insert will insert an objects children before
		inserting an object
		'''
		### get out of here if already in database
		if newdata.dbid is not None:
			return

		## insert children if they are Data instances
		## and have never been inserted
		## Look at reference first to avoid unecessary getData()
		for value in newdata.values(dereference=False):
			if isinstance(value, data.DataReference):
				if value.dbid is None:
					dat = value.getData()
					## check if DataReference replaced
					if isinstance(dat, data.DataReference):
						dat = dat.getData()
					self.recursiveInsert(dat)

		## insert this object
		dbid = self.flatInsert(newdata, force=force)
		newdata.setPersistent(dbid)

	def _insert(self, newdata, force=False):
		#self.flatInsert(newdata)
		return self.recursiveInsert(newdata, force=force)

	def flatInsert(self, newdata, force=False):
		table = newdata.__class__.__name__
		definition = sqldict.sqlColumnsDefinition(newdata)
		formatedData = sqldict.sqlColumnsFormat(newdata)
		self.dbd.createSQLTable(table, definition)
		myTable = self.dbd.Table(table)
		newid = myTable.insert([formatedData], force=force)
		return newid

	# don't bother with these for now
	def remove(self, id):
		pass

	def ids(self):
		pass

