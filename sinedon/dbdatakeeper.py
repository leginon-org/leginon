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
import logging
import _mysql_exceptions
import MySQLdb.constants.CR
import dbconfig

columns_created = {}

class DatabaseError(Exception):
	pass

class InsertError(DatabaseError):
	pass

class QueryError(DatabaseError):
	pass

class Reconnect(DatabaseError):
	pass

class DBDataKeeper(object):
	def __init__(self, logger=None, **kwargs):
		self.logger = logger
		try:
			self.dbd = sqldict.SQLDict(**kwargs)
		except _mysql_exceptions.OperationalError, e:
			raise DatabaseError(e.args[-1])
		#self.mysqldb = self.dbd.db
		self.lock = threading.RLock()

	def connect_kwargs(self):
		return self.dbd.connect_kwargs()

	def ping(self):
		self.dbd.ping()

	def close(self):
		self.dbd.close()

	def direct_query(self, dataclass, id, readimages=False):
		dummy = dataclass()
		dummy.isRoot = True
		datainfo = self.datainfo(dummy, dbid=id)
		queryinfo = datainfo[0]
		self.lock.acquire()
		try:
			result  = self.dbd.multipleQueries(queryinfo, readimages=readimages)
			myresult = result.fetchall()
		finally:
			self.lock.release()
		if len(myresult) == 0:
			return None
		elif len(myresult) == 1:
			return myresult[0]
		else:
			raise RuntimeError('direct_query should only return a single result')

	def _reconnect(self):
		try:
			self.dbd = sqldict.SQLDict()
		except _mysql_exceptions.OperationalError, e:
			raise DatabaseError(e.args[-1])

	def query(self, idata, results=None, readimages=False, timelimit=None):
		if self.logger is not None:
			self.logger.info('query %s' % idata)
		self.lock.acquire()
		try:
			args = (idata,)
			kwargs = {'readimages': readimages, 'timelimit': timelimit, 'limit': results}
			while True:
				try:
					result = self._query(*args, **kwargs)
					break
				except Reconnect:
					self._reconnect()
		finally:
			self.lock.release()
		return result

	def _query(self, idata, readimages=True, timelimit=None, limit=None):
		'''
		query using a partial Data instance
		'''
		# idata: instance of a Data class 
		# results: number of rows wanted
		queryinfo = self.queryInfo(idata, timelimit=timelimit, limit=limit)
		self.dbd.ping()
		try:
			result  = self.dbd.multipleQueries(queryinfo, readimages=readimages)
		except _mysql_exceptions.OperationalError, e:
			if e.args[0] == MySQLdb.constants.CR.SERVER_LOST:
				raise Reconnect(e.args[-1])
			raise QueryError(e.args[-1])

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
				myid = id(mydata)
		elif isinstance(mydata, data.Data):
			myid = id(mydata)
			myclassname = mydata.__class__.__name__
		else:
			raise RuntimeError('need Data or DataReference')
		return {'id': myid, 'data': mydata}

	def datainfo(self, mydata, dbid=None, timelimit=None, limit=None):
		'''
		function that should be called in data.accumulateData
		'''
		stuff = self.qid(mydata)
		classname = mydata.__class__.__name__
		myalias = classname + str(stuff['id'])
		myid = stuff['id']
		info = {}
		if isinstance(mydata, data.DataReference):
			info['class'] = mydata.dataclass
		else:
			info['class'] = mydata.__class__
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
			if timelimit is not None:
				info['where']['DEF_timelimit'] = timelimit
			info['limit'] = limit
			isroot = 1
			del mydata.isRoot

		info['root'] = isroot

		finalinfo = {myid: info}
		return [finalinfo]

	def accumulateData(self, originaldata, memo=None, timelimit=None, limit=None):
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
					childresult = self.accumulateData(value, memo=memo, timelimit=timelimit, limit=limit)
					if childresult is not None:
						myresult += childresult

		myresult = self.datainfo(originaldata, timelimit=timelimit, limit=limit) + myresult

		memo[d] = myresult
		return myresult

	def queryInfo(self, idata, timelimit=None, limit=None):
		'''
		Items of idata that are None, should be ignored.
		'''
		idata.isRoot=1
		mylist = self.accumulateData(idata, timelimit=timelimit, limit=limit)
		finaldict = {}
		for d in mylist:
			finaldict.update(d)
		return finaldict

	def insert(self, newdata, force=False):
		self.lock.acquire()
		try:
			while True:
				try:
					self._insert(newdata, force=force)
					break
				except Reconnect:
					self._reconnect()
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
					self.recursiveInsert(dat)

		## insert this object
		dbinfo = self.connect_kwargs()
		dbid = self.flatInsert(newdata, force=force)
		newdata.setPersistent(dbid)

	def _insert(self, newdata, force=False):
		#self.flatInsert(newdata)
		self.dbd.ping()
		try:
			return self.recursiveInsert(newdata, force=force)
		except _mysql_exceptions.OperationalError, e:
			if e.args[0] == MySQLdb.constants.CR.SERVER_LOST:
				raise Reconnect(e.args[-1])
			raise InsertError(e.args[-1])

	def flatInsert(self, newdata, force=False, skipinsert=False, fail=True):
		dbname = dbconfig.getConfig(newdata.__module__)['db']
		tablename = newdata.__class__.__name__
		table = (dbname, tablename)
		definition, formatedData = sqldict.dataSQLColumns(newdata, fail)
		## check for any new columns that have not been created
		if table not in columns_created:
			columns_created[table] = {}
		fields = [d['Field'] for d in definition]
		for field in formatedData.keys():
			if field not in fields:
				del formatedData[field]
		create_table = False
		for field in fields:
			if field not in columns_created[table]:
				columns_created[table][field] = None
				create_table = True
		if create_table:
			self.dbd.createSQLTable(table, definition)
		myTable = self.dbd.Table(table)
		if skipinsert is True:
			return None
		newid = myTable.insert([formatedData], force=force)
		return newid

	def diffData(self, newdata):
		table = newdata.__class__.__name__
		definition, formated = sqldict.dataSQLColumns(newdata)
		return self.dbd.diffSQLTable(table, definition)
	

	# don't bother with these for now
	def remove(self, id):
		pass

	def ids(self):
		pass

