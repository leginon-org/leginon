#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import sinedon
import sinedon.data
import sinedon.sqldict
import threading
import logging
import _mysql_exceptions
import MySQLdb.constants.CR

debug = False
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
			self.dbd = sinedon.sqldict.SQLDict(**kwargs)
		except _mysql_exceptions.OperationalError, e:
			raise DatabaseError(e.args[-1])
		#self.mysqldb = self.dbd.db
		self.lock = threading.RLock()
		self.columns_created = {}
		self.imported_data = {}

	def connect_kwargs(self):
		return self.dbd.connect_kwargs()

	def ping(self):
		self.dbd.ping()

	def close(self):
		self.dbd.close()

	def direct_query(self, dataclass, id, readimages=False):
		if id is None:
			raise ValueError('id must be specified, not None')
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
			myresult = myresult[0]
			myresult.dbconfig = self.connect_kwargs()
			return myresult
		else:
			raise RuntimeError('direct_query should only return a single result')

	def delete(self, dataobject):
		datainfo = self.datainfo(dataobject)
		print 'DATAINFO', datainfo
		queryinfo = datainfo[0]
		self.lock.acquire()
		try:
			self.dbd.delete(queryinfo)
		finally:
			self.lock.release()

	def _reconnect(self):
		try:
			self.dbd = sinedon.sqldict.SQLDict()
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
		for x in result:
			x.dbconfig = self.connect_kwargs()
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
		if isinstance(mydata, sinedon.data.DataReference):
			myclassname = mydata.dataclass.__name__
			if self in mydata.mappings:
				dbid = mydata.mappings[self]
				myid = myclassname+str(dbid)
			else:
				mydata = mydata.getData()
				myid = id(mydata)
		elif isinstance(mydata, sinedon.data.Data):
			myid = id(mydata)
			myclassname = mydata.__class__.__name__
		else:
			raise RuntimeError('need Data or DataReference: %s' % (mydata.__class__,))
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
		if isinstance(mydata, sinedon.data.DataReference):
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
		elif self in mydata.mappings:
			## this instance is from the database
			dbid = mydata.mappings[self]
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

				elif isinstance(value, (sinedon.data.Data, sinedon.data.DataReference)):
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

		info['dbdk'] = self
		info['dbconfig'] = self.connect_kwargs()

		finalinfo = {myid: info}
		return [finalinfo]

	def accumulateData(self, originaldata, memo=None, timelimit=None, limit=None):
		d = id(originaldata)

		if memo is None:
			memo = {}
		if memo.has_key(d):
			return None

		myresult = []

		if isinstance(originaldata, sinedon.data.Data):
			for key,value in originaldata.items(dereference=False):
				if isinstance(value, sinedon.data.DataReference):
					if self not in value.mappings:
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

	def insert(self, newdata, force=False, archive=False):
		self.lock.acquire()
		try:
			while True:
				try:
					self._insert(newdata, force=force, archive=archive)
					break
				except Reconnect:
					self._reconnect()
		finally:
			self.lock.release()

	def initImported(self, source_host, source_db):
		confkey = source_host,source_db
		self.imported_data[confkey] = {}
		source_confdata = sinedon.importdata.ImportDBConfigData(host=source_host, db=source_db)
		dest_config = self.connect_kwargs()
		dest_host = dest_config['host']
		dest_db = dest_config['db']
		dest_confdata = sinedon.importdata.ImportDBConfigData(host=dest_host, db=dest_db)
		mappingdata = sinedon.importdata.ImportMappingData(source_config=source_confdata, destination_config=dest_confdata)
		mappingdata = mappingdata.query()
		for m in mappingdata:
			classname = m['class_name']
			old_dbid = m['old_dbid']
			if classname not in self.imported_data[confkey]:
				self.imported_data[confkey][classname] = {}
			self.imported_data[confkey][classname][old_dbid] = m['new_dbid']

	def queryImported(self, source_host, source_db, dataclass, source_dbid):
		import sinedon.importdata
		confkey = source_host,source_db
		if confkey not in self.imported_data:
			self.initImported(source_host, source_db)

		try:
			return self.imported_data[confkey][dataclass][source_dbid]
		except KeyError:
			return None

	def copyImportMapping(self, obj1, obj2):
		'''
		Import obj2 into this db, but give it the same import mapping as
		obj1.
		'''
		dataclass = obj1.__class__.__name__
		# dbcopy wants the new id
		new_dbid = obj1.mappings[self]
		# archive change but it does not get used ??? see revision c4609d22
		#new_dbid = obj2.dbid
		for source_dbdk, source_dbid in obj1.mappings.items():
			if source_dbdk is self:
				continue
			if source_dbdk not in obj2.mappings:
				continue
			source_dbid = obj2.mappings[source_dbdk]
			source_conf = source_dbdk.connect_kwargs()
			source_host = source_conf['host']
			source_db = source_conf['db']

			## insert mapping into the importdata db
			self.insertImported(source_host, source_db, dataclass, source_dbid, new_dbid)
			## fake that obj2 was inserted into this db
			obj2.setPersistent(self.connect_kwargs(), new_dbid)

	def insertImported(self, source_host, source_db, dataclass, source_dbid, new_dbid):
		import sinedon.importdata
		confkey = source_host,source_db
		if confkey not in self.imported_data:
			self.initImported(source_host, source_db)
		if dataclass in self.imported_data[confkey] and source_dbid in self.imported_data[confkey][dataclass]:
			return
		source_confdata = sinedon.importdata.ImportDBConfigData(host=source_host, db=source_db)
		dest_config = self.connect_kwargs()
		dest_host = dest_config['host']
		dest_db = dest_config['db']
		dest_confdata = sinedon.importdata.ImportDBConfigData(host=dest_host, db=dest_db)
		mappingdata = sinedon.importdata.ImportMappingData(source_config=source_confdata, destination_config=dest_confdata, old_dbid=source_dbid, new_dbid=new_dbid, class_name=dataclass)
		mappingdata.insert()
		if dataclass not in self.imported_data[confkey]:
			self.imported_data[confkey][dataclass] = {}
		self.imported_data[confkey][dataclass][source_dbid] = new_dbid

	def recursiveInsert(self, newdata, force=False, archive=False):
		'''
		recursive insert will insert an objects children before
		inserting an object
		'''
		### get out of here if already mapped to this database
		if self in newdata.mappings:
			return

		### check for existing mappings, which indicates that we are
		### copying data form other db to this db.
		dataclass = newdata.__class__.__name__
		dbinfo = self.connect_kwargs()
		for other_db, other_dbid in newdata.mappings.items():
			if other_db is self:
				continue
			other_config = other_db.connect_kwargs()
			new_id = self.queryImported(other_config['host'], other_config['db'], dataclass, other_dbid)
			if new_id is None:
				# Need to import
				doimport = True
				# Keep force recursively when archiving
				if not archive:
					force = True
				writeimages = False
			else:
				# Already imported
				newdata.setPersistent(dbinfo, new_id)
				return

		## insert children if they are Data instances
		for value in newdata.values(dereference=False):
			if isinstance(value, sinedon.data.DataReference):
				# is there a way to check if already done before getData()?
				if True:
					dat = value.getData()
					# The result could be None
					if dat:
						dat.insert(force=force,archive=archive)
					#self.recursiveInsert(dat)

		## insert this object
		dbinfo = self.connect_kwargs()
		dbid = self.flatInsert(newdata, force=force, archive=archive)
		if debug:
			print "recursive insert flatInsert got dbid", dataclass, dbid
		for other_db, other_dbid in newdata.mappings.items():
			if other_db is self:
				continue
			other_config = other_db.connect_kwargs()
			self.insertImported(other_config['host'], other_config['db'], dataclass, other_dbid, dbid)
		newdata.setPersistent(dbinfo, dbid)

	def _insert(self, newdata, force=False, archive=False):
		self.dbd.ping()
		try:
			return self.recursiveInsert(newdata, force=force, archive=archive)
		except _mysql_exceptions.OperationalError, e:
			if e.args[0] == MySQLdb.constants.CR.SERVER_LOST:
				raise Reconnect(e.args[-1])
			raise InsertError(e.args[-1])

	def flatInsert(self, newdata, force=False, skipinsert=False, fail=True, archive=False):
		dbconf = self.connect_kwargs()
		dbname = dbconf['db']
		tablename = newdata.__class__.__name__
		table = (dbname, tablename)
		if debug and archive:
			print 'newdata dbid at flatinsert at start',tablename,newdata.dbid
			#newdata.new_dbid = newdata.dbid
		definition, formatedData = sinedon.sqldict.dataSQLColumns(newdata, self, fail, archive)
		## check for any new columns that have not been created
		if table not in self.columns_created:
			self.columns_created[table] = {}
		# FIX ME: columns_created need to be initializaed. Otherwise the
		# first time this is called will always want to create table
		# even though the table does exist.
		if table not in columns_created:
			columns_created[table] = {}
		fields = [d['Field'] for d in definition]
		for field in formatedData.keys():
			if field not in fields:
				del formatedData[field]
		create_table = False
		for field in fields:
			if field not in self.columns_created[table]:
				self.columns_created[table][field] = None
				create_table = True
		if create_table:
			self.dbd.createSQLTable(table, definition)
		myTable = self.dbd.Table(table)
		if skipinsert is True:
			return None
		if debug:
			print 'newdata dbid at flatinsert before myTable insert',newdata.dbid
		newid = myTable.insert([formatedData], force=force, archive=archive)
		return newid

	def diffData(self, newdata):
		table = newdata.__class__.__name__
		definition, formated = sinedon.sqldict.dataSQLColumns(newdata, self)
		return self.dbd.diffSQLTable(table, definition)
	

	# don't bother with these for now
	def remove(self, id):
		pass

	def ids(self):
		pass

