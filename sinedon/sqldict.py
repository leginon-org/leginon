#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
debug = False
"""
sqldict: 

This creates a database interface which works pretty much like a
Python dictionary. The data are stored in a sql table.

>>> from sqldict import *
>>> db = SQLDict()

The optional keyword arguments are:
		host	= "DB_HOST"
		user	= "DB_USER"
		db	= "DB_NAME"
		passwd	= "DB_PASS"
By default, this is in the config.py file

>>> db = SQLDict(host="YourHost")

DEFINE / CREATE A TABLE
-----------------------

presetDefinition = [{'Field': 'id', 'Type': 'int(16)', 'Key': 'PRIMARY', 'Extra':'auto_increment'},
				{'Field': 'Name', 'Type': 'varchar(30)'},
				{'Field': 'Width', 'Type': 'int(11)'},
				{'Field': 'Height','Type': 'int(11)'},
				{'Field': 'Binning', 'Type': 'int(11)'},
				{'Field': 'ExpTime', 'Type': 'float(10,4)'},
				{'Field': 'Dose', 'Type': 'float(10,4)'},
				{'Field': 'BeamCurrent', 'Type': 'float'},
				{'Field': 'LDButton', 'Type': 'varchar(20)'},
				{'Field': 'Mag', 'Type': 'int(11)'},
				{'Field': 'PixelSize', 'Type': 'float(10,4)'},
				{'Field': 'Defocus', 'Type': 'int(11)'},
				{'Field': 'SpotSize', 'Type': 'int(11)'},
				{'Field': 'Intensity', 'Type': 'float(10,4)'},
				{'Field': 'BShiftX', 'Type': 'float(10,4)'},
				{'Field': 'BShiftY', 'Type': 'float(10,4)'},
				{'Field': 'IShiftX', 'Type': 'float(10,4)'},
				{'Field': 'IShiftY', 'Type': 'float(10,4)'}]

>>> db.createSQLTable('PRESET', presetDefinition)

DEFINE A MEMBER
---------------

Next, define the tables and columns of interest. It is NOT
necessary to define all columns of a particular table, only those
you need.

>>> db.Preset= db.Table('PRESET', [ 'Name', 'Width', 'Height', 'Binning', 'ExpTime', 'Dose',
			'BeamCurrent', 'LDButton', 'Mag', 'PixelSize', 'Defocus', 'SpotSize',
			'Intensity', 'BShiftX', 'BShiftY', 'IShiftX', 'IShiftY' ])
['focus2', 256, 256, 1, 0.3000, 41.6200, 0,'search', 66000, 0.2994, -2000, 3, 42414.5117, 106.9400, 28.7300, 198.0000, 4542.0000]



This defines a new member Preset of db, which describes the table
PRESET as having the columns 'Name', 'Width', 'Height', 'Binning', 'ExpTime', 'Dose',
'BeamCurrent', 'LDButton', 'Mag', 'PixelSize', 'Defocus', 'SpotSize',
'Intensity', 'BShiftX', 'BShiftY', 'IShiftX', 'IShiftY'

ACCESSING DATA
--------------

>>> db.Preset.Name= db.Preset.Index(['Name'])

This defines an index member to Preset called 'Name', which allows
searching by 'Name'. 

>>> db.Preset.NameDesc= db.Preset.Index(['Name'], orderBy = {'fields':('id',),'sort':'DESC'})

This defines an index member to Preset called 'Name', which allows
searching by 'Name'. Also the result is sorted by id in reverse order.
Note: The default value of 'sort' is 'ASC'


Accessing your data is very similar to using dictionaries. To
retrieve information:

>>> db.Preset.Name['focus'].fetchone()

Note that the [] (__getitem__) operation returns a special cursor
with some extended properties; more on that latter.

>>> db.Preset.NameMag= db.Preset.Index(['Name', Mag'])

SQL equivalent
Make your own class to directly load and store
into the database. Assuming a pre-defined Preset object:

>>> class Preset(ObjectBuilder):
...	 table = "PRESET"
...	columns = [ 'Name', 'Defocus', 'Dose', 'Mag' ]
...	 indices = [ ('Name', ['Name'], {'orderBy':{'fields':('id',)}}),
...			('NameMag', ['Name', 'Mag']) ]
...

>>> myPreset = Preset().register(db)



p2 = Preset('exposure', -2000, 0.34565, 66000)

INSERT
------

Data are inserted as a list of dictionaries:

>>> myPreset.insert([p2.dumpdict()])

OR

>>> db.Preset.insert([p2.dumpdict()])

Note: Each insert returns the last inserted ID.

UPDATE
------

Data to update are define in a dictionary. The keys from this
dictionary must match the SQL table column names.

>>> db.Preset.NameMag['focus2', 66000 ] = {'Defocus': -200}

OR

>>> myPreset.NameMag['focus2', 66000 ] = {'Defocus': -200, 'Mag': 66000 }


DELETE
------

>>> del myPreset.Name['exposure']

OR

>>> del db.Preset.Name['exposure']

"""


import sys
import sqlexpr
import copy
import sqldb
import string
import datetime
import re
import numpy
import MySQLdb.cursors
from types import *
import newdict
import data
import sinedon
import pyami.mrc
import os
import dbconfig
import cPickle
from pyami import weakattr

class SQLDict(object):

	"""SQLDict: An object class which implements something resembling
	a Python dictionary on top of an SQL DB-API database."""

	def __init__(self, **kwargs):
		"""
		Create a new SQLDict object.
		db: an SQL DB-API database connection object.
		The optional keyword arguments are:
			host	= "DB_HOST"
			user	= "DB_USER"
			db	= "DB_NAME"
			passwd	= "DB_PASS"
		"""

		try:
			self.db = sqldb.connect(**kwargs)
			self.connected = True
		except Exception,e:
			self.db = None
			self.connected = False
			self.sqlexception = e
			raise

	def ping(self):
		if self.db.stat() == 'MySQL server has gone away':
			self.db = sqldb.connect(**self.db.kwargs)

	def connect_kwargs(self):
		return self.db.kwargs

	def isConnected(self):
		return self.connected

	def sqlException(self):
		return self.sqlexception

	def __del__(self):	self.close()

	def close(self):
		try: self.db.close()
		except: pass

	def __getattr__(self, attr):
		# Get any other interesting attributes from the base class.
		return getattr(self.db, attr)

	def Table(self, table, columns=[]):
		"""
		Add a new Table member.
		Usage: db.Table(tablename, columns)
		Where: tablename  = name of table in database
		columns	= tuple containing names of columns of interest
		"""
		return _Table(self.db, table, columns)

	def createSQLTable(self, table, definition):
		"""
		>>> CreateTable('PEOPLE',
		[{'Field': 'id', 'Type': 'int(16)', 'Key': 'PRIMARY', 'Extra':'auto_increment'},
		{'Field': 'Name', 'Type': 'VARCHAR(50)'}])
		"""
		return _createSQLTable(self.db, table, definition)

	def diffSQLTable(self, table, data_definition):
		"""
		Differences beetween Data table structure and Data Class
		"""
		diff = _diffSQLTable(self.db, table, data_definition)
		return diff.diffTable()

	def multipleQueries(self, queryinfo, readimages=True):
		"""
		Execute a list of queries, it will return a list of dictionaries
		"""
		return _multipleQueries(self.db, queryinfo, readimages)

class _Table:

	"""Table handler for a SQLDict object. These should not be created
	directly by user code."""

	def __init__(self, db, table, columns=[]):

		"""Construct a new table definition. Don't invoke this
		directly. Use Table method of SQLDict instead."""

		self.db = db
		self.table = table
		self.columns = columns
		self.fields = tuple(map(lambda col: sqlexpr.Field(self.table,col), self.columns))

	def select(self, where=None, orderBy=None):

		"""Execute a SELECT command based on this Table and Index. The
		required argument i is a tuple containing the values to match
		against the index columns. A string containing a WHERE clause
		should be passed along, but this is technically optional. The
		WHERE clause must have the same number of value placeholders
		(?) as there are values in i. Returns a _Cursor object for the
		matched rows.

		Usually you don't need to call select() directly; this is done
		by the indexing operations (Index.__getitem__)."""

		if orderBy is not None:
			orderBy = copy.deepcopy(orderBy)
			orderBy['fields'] = map(lambda id: sqlexpr.Field(self.table, id), orderBy['fields'])

		c = self.cursor()
		if self.columns:
			q = sqlexpr.Select(items=self.fields, table=self.table, where=where, orderBy=orderBy).sqlRepr()
		else:
			q = sqlexpr.SelectAll(self.table, where=where, orderBy=orderBy).sqlRepr()
		c.execute(q)
		return c

	def insert(self, v=[], force=0):
		"""Insert a list of dictionaries into a SQL table. If the data
		already exist, they won't be inserted again in the table, 
		unless force is true. The function returns the last inserted row
		id for a new insert or an existing primary key."""
		c = self.cursor()

		result = None

		if not force:
			nullfields = []
			equalpairs = []
			for key,value in v[0].items():
				if key[:3] == 'MRC':
					continue
				key = sqlexpr.Field(self.table, key)
				if value is None:
					nullfields.append((key, value))
				else:
					equalpairs.append((key, value))

			whereFormat = sqlexpr.AND_EQUAL(equalpairs)
			whereFormatNULL = sqlexpr.AND_IS(nullfields)

			if whereFormatNULL:
				if whereFormat:
					whereFormat = sqlexpr.AND(whereFormatNULL,whereFormat)
				else:
					whereFormat = whereFormatNULL

			qsel = sqlexpr.SelectAll(self.table, where=whereFormat).sqlRepr()
			## print qsel
			try:
				c.execute(qsel)
				result=c.fetchone()
			except:
				result = None

		if force or not result:
			q = sqlexpr.Insert(self.table, v).sqlRepr()
			if debug:
				print q
			c.execute(q)
			## try the new lastrowid attribute first,
			## then try the old insert_id() method
			try:
				insert_id = c.lastrowid
			except:
				insert_id = c.insert_id()
			return insert_id

		else:
			try:
				return result['DEF_id']
			except KeyError:
				qkey = sqlexpr.Show('INDEX', self.table).sqlRepr()
				c.execute(qkey)
				keys = c.fetchall()
				prikeyfield = None
				for key in keys:
					if key['Key_name']=='PRIMARY':
						prikeyfield = key['Column_name']
						break;
				if prikeyfield:
					return result[prikeyfield]
				else:
					raise KeyError('No Primary Key found')

	def update(self, v, WHERE=''):
		"""Like select(), only it does an UPDATE. It is not usually
		necessary to call this method directly, as it is done by
		the indexing operations (Index.__setitem__)."""
		q = sqlexpr.Update( self.table, v, where=WHERE).sqlRepr()
		c = self.cursor()
		c.execute(q)
		return c

	def delete(self, i=(), WHERE=''):
		"""Like select(), only it does an DELETE. It is not usually
		necessary to call this method directly, as it is done by
		the indexing operations (Index.__delitem__)."""
		q=sqlexpr.Delete(self.table, where=WHERE).sqlRepr()
		c = self.cursor()
		c.execute(q)
		return c

	def load(self, v):
		return v

	def getall(self, where=1, orderBy=None):
		q = sqlexpr.Select(items=self.fields, table=self.table, where=where, orderBy=orderBy).sqlRepr()
		c = self.cursor()
		c.execute(q)
		return c.fetchall()

	def describe(self):
		q = sqlexpr.Describe(self.table).sqlRepr()
		c = self.cursor()
		c.execute(q)
		return c.fetchall()


	def Index(self, indices=[], **kwargs):

		"""Create an index definition for this table.

		Usage: db.table.Index(indices)
		Where: indices   = tuple or list of column names to key on
			 orderBy = optional ORDER BY clause.
			 WHERE	 = optional WHERE clause.
			 WHERE not implemented YET...

		"""

		return _Index(self, indices, **kwargs)

	def cursor(self):
		"""Returns a new _Cursor object which is load-aware and
		otherwise behaves normally."""
		return _Cursor(self.db, self.load, self.columns)


class _Cursor:

	"""A subclass (shadow class?) of a cursor object which knows how to
	load the tuples returned from the database into a more interesting
	object."""

	def __init__(self, db, load, columns):
		db.ping()
		self.cursor = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
		self.columns = columns
		self.load = load
		self.db = db

	def fetchone(self):
		"""Fetch one object from current cursor context."""
		x = self.cursor.fetchone()
		if x: return self.load(x)
		else: return x # only load if we really got something

	def fetchall(self):
		"""Fetch all objects from the current cursor context."""
		return map(self.load, self.cursor.fetchall())

	def fetchmany(self, *size):
		"""Fetch many objects from the current cursor context.
		Can specify an optional size argument for number of rows."""
		return map(self.load, apply(self.cursor.fetchmany, size))

	def __getattr__(self, attr):
		return getattr(self.cursor, attr)

	def __2dict(self,keys,values):
		"""Returns a dictionary from a list or tuple of keys and values."""
		if (values):
			return dict(zip(keys,values))
		else:
			return {}


class _Index:

	"""
	Index handler for a _Table object.
	"""

	def __init__(self, table, indices, **kwargs):
		self.table = table
		self.kwargs= kwargs
		if indices:
			ind = map(lambda id: sqlexpr.Field(self.table.table, id), indices)
		else:
			ind=None
		self.fields = ind

	def __getattr__(self, attr):
		c = self.table.select(where=1, **self.kwargs)
		return getattr(c, attr)

	def __setitem__(self, i=(), v=None):
		"""Update the item in the database matching i
		with the value v."""
		if type(i) == ListType: i = tuple(i)
		elif type(i) != TupleType: i = (i,)
		if self.fields is not None:
			w = sqlexpr.AND_EQUAL(zip(self.fields,i))
		else: w=1
		self.table.update(v, WHERE=w)

	def __getitem__(self, i=()):
		"""Select items in the database matching i."""
		if type(i) == ListType: i = tuple(i)
		elif type(i) != TupleType: i = (i,)
		if self.fields is not None:
			w = sqlexpr.AND_EQUAL(zip(self.fields,i))
		else: w=1
		return self.table.select(where=w, **self.kwargs)

	def __delitem__(self, i):
		"""Delete items in the database matching i."""
		if type(i) == ListType: i = tuple(i)
		elif type(i) != TupleType: i = (i,)
		w = sqlexpr.AND_EQUAL(zip(self.fields,i))
		return self.table.delete(i, WHERE=w)

class _multipleQueries:

	def __init__(self, db, queryinfo, readimages=True):
		self.db = db
		self.queryinfo = queryinfo
		self.readimages = readimages
		#print 'querinfo ', self.queryinfo
		self.queries = setQueries(queryinfo)
		if debug:
			print 'queries ', self.queries
		self.cursors = {}
		self.execute()

	def _cursor(self):
		self.db.ping()
		return self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

	def execute(self):
		for key,query in self.queries.items():
			if isinstance(query, (data.Data,data.DataReference)):
			## if we already have a data instance, then there
			## is no reason to query for it.
				self.cursors[key] = query
				continue
			c = self._cursor()
			try:
				## print '-----------------------------------------------'
				## print 'query =', query
				c.execute(query)
			except (MySQLdb.ProgrammingError, MySQLdb.OperationalError), e:
				errno = e.args[0]
				## some version of mysqlpython parses the exception differently
				if not isinstance(errno, int):
					errno = errno.args[0]
				## 1146:  table does not exist
				## 1054:  column does not exist
				if errno in (1146, 1054):
					pass
					#print 'non-fatal query error:', e
				else:
					raise
			else:
				self.cursors[key] = c

	def fetchmany(self, size):
		cursorresults = {}
		for qikey,cursor in self.cursors.items():
			## if we already have a data instance, then there
			## is no reason to query for it.
			if isinstance(cursor, (data.Data,data.DataReference)):
				cursorresults[qikey] = cursor
				continue
			subfetch = cursor.fetchmany(size)
			cursorresult = self._format(subfetch, qikey)
			cursor.close()
			cursorresults[qikey] = cursorresult

		return self._joinData(cursorresults)

	def fetchall(self):
		cursorresults = {}
		for qikey,cursor in self.cursors.items():
			## if we already have a data instance, then there
			## is no reason to query for it.
			if isinstance(cursor, (data.Data,data.DataReference)):
				cursorresults[qikey] = cursor
				continue
			subfetch = cursor.fetchall()
			cursorresult = self._format(subfetch, qikey)
			cursor.close()
			cursorresults[qikey] = cursorresult

		a = self._joinData(cursorresults)
		return a

	def uniqueFilter(self, results, key):
		if not results or key is None:
			return
		first = results[0]
		keyfield = None
		for field in first.keys():
			parts = field.split('|')
			field_key = parts[-1]
			if field_key == key:
				keyfield = field
				break
		if keyfield is None:
			return
			
		havedict = {}
		filtered = []
		for result in results:
			if result[keyfield] in havedict:
				continue
			filtered.append(result)
			havedict[result[keyfield]] = None
		return filtered

	def _joinData(self, cursorresults):
		if not cursorresults:
			return []

		## some cursorresults are actually data.Data instances
		def test(obj):
			return not isinstance(obj, (data.Data,data.DataReference))
		actualresults = filter(test, cursorresults.values())
		if actualresults:
			numrows = len(actualresults[0])
		else:
			numrows = 0
		all = [{} for i in range(numrows)]

		for i in range(numrows):
			for qikey, cursorresult in cursorresults.items():
				if isinstance(cursorresult, (data.Data,data.DataReference)):
					## cursorresult was known before query
					all[i][qikey] = cursorresult
				elif cursorresult:
					## cursorresult was fetched from query
					all[i][qikey] = cursorresult[i]
				else:
					## does this case ever happen?
					all[i][qikey] = None

		rootlist = []
		for d in all:
			for qikey,v in d.items():
				if self.queryinfo[qikey]['root']:
					theroot = v
					self._connectData(v, d)
			rootlist.append(theroot)

		return rootlist

	def _format(self, sqlresult, qikey):
		"""Convert SQL result to data instances. Create a new data instance
		only if it does not exist.
		"""
		datalist = []
		qikeylist = [qikey for i in range(len(sqlresult))]
		qinfolist = [self.queryinfo for i in range(len(sqlresult))]
		result = map(sql2data, sqlresult, qikeylist, qinfolist)

		dataclass = self.queryinfo[qikey]['class']

		## keep memo to ensure only creating instance once
		memo = {}
		for r in result:
			memokey = (dataclass, r['DEF_id'])
			dbid = r['DEF_id']
			dbtimestamp = r['DEF_timestamp']
			del r['DEF_id']
			del r['DEF_timestamp']

			if memokey in memo:
				newdata = memo[memokey]
			else:
				newdata = dataclass()
				memo[memokey]=newdata
				try:
					## this is friendly_update because
					## there could be columns that
					## are no longer used
					newdata.friendly_update(r)
				except KeyError, e:
					raise

				## add pending dbid for now, actual dbid
				## after all items are set, otherwise __setitem__
				## will reset dbid
				newdata.pending_dbid = dbid
				newdata.timestamp = dbtimestamp

			datalist.append(newdata)
		return datalist

	def _connectData(self, root, pool):
		'''
		This connects the individual data instances together.
		After connecting, it also reads in data from files.
		'''
		if root is None:
			return

		### already done
		if root.dbid is not None:
			return 

		dbinfo = self.db.kwargs

		needpath = []
		for key,value in root.items(dereference=False):
			if isinstance(value, data.UnknownData):
				target = pool[value.qikey]
				root[key] = target
				self._connectData(target, pool)
			elif isinstance(value, newdict.FileReference):
				needpath.append(key)

		### find the path
		if needpath:
			try:
				getpath = root.getpath
			except AttributeError:
				message = '%s object contains file references, needs a getpath() method' % (root.__class__,)
				raise AttributeError(message)
			imagepath = getpath()
		## now set path in FileReferences, read image
		for key in needpath:
			fileref = root.special_getitem(key, dereference=False)
			fileref.setPath(dbconfig.mapPath(imagepath))
			if self.readimages:
				# replace reference with actual data
				root[key] = fileref.read()

		## now the object is final, so we can safely set dbid
		root.setPersistent(root.pending_dbid)
		del root.pending_dbid

class _createSQLTable:

		def __init__(self, db, table, definition):
			self.db = db
			self.table = table
			self.definition = definition
			self.create()

		def _cursor(self):
			self.db.ping()
			return self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

		def create(self):
			q = sqlexpr.CreateTable(self.table, self.definition).sqlRepr()
			c = self._cursor()
			if debug:
				print q
			c.execute(q)
			c.close()
			self._checkTable()

		def formatDescription(self, description):
			newdict = {}
			newdict['Field'] = description['Field']
			if description.has_key('Default'):
				newdict['Default'] = description['Default']
				if description['Default']=='CURRENT_TIMESTAMP':
					newdict['Default'] = None
				elif description['Default']=='NULL':
					newdict['Default'] = None
			else:
				newdict['Default'] = None
			typestr = description['Type'].upper()
			try:
				if re.findall('^TIMESTAMP', typestr):
					ind = typestr.index('(')
					typestr = typestr[:ind]
			except ValueError:
				pass
			newdict['Type'] = typestr
			return newdict

		def _checkTable(self):
			c = self._cursor()
			describeTable = _Table(self.db,self.table).describe()

			describe=[]
			for col in describeTable:
				describe.append(self.formatDescription(col))

			definition=[]
			for col in self.definition:
				definition.append(self.formatDescription(col))

			addcolumns = [col for col in definition if col not in describe]

			for column in addcolumns:
				queries = []
				column['Null'] = 'YES'
				q = sqlexpr.AlterTable(self.table, column, 'ADD').sqlRepr()
				queries.append(q)
				l = re.findall('^REF\%s' %(sep,),column['Field'])
				if l:
					q = sqlexpr.AlterTableIndex(self.table, column).sqlRepr()
					queries.append(q)
				try:
					for q in queries:
						if debug:
							print q
						c.execute(q)
				except MySQLdb.OperationalError, e:
					pass
			c.close()


class _diffSQLTable(_createSQLTable):

		def __init__(self, db, table, definition):
				self.db = db
				self.table = table
				self.definition = definition

		def diffTable(self):
			c = self._cursor()
			describeTable = _Table(self.db,self.table).describe()

			describe=[]
			for col in describeTable:
				describe.append(self.formatDescription(col))

			definition=[]
			for col in self.definition:
				definition.append(self.formatDescription(col))

			## -------- display description from data and from DB -------- ##
			##print '--------------------'
			##print 'describe\n%s' % (describe,)
			##print '--------------------'
			##print 'definition\n%s' % (definition,)
			##print '--------------------'


			for d in definition:
				f = d['Field']
				for e in describe:
					if e['Field']==f:
						if d['Default'] is None:
							d['Default']=e['Default']
						else:
							try:
								if float(d['Default'])==float(e['Default']):
									d['Default']=e['Default']
							except:
								pass
						break

			addcolumns = [col for col in definition if col not in describe]
			dropcolumns = [{'Field':col} for col in [d['Field'] for d in describe] if col not in [f['Field'] for f in definition]]

			queries = []
			for column in dropcolumns:
				q = sqlexpr.AlterTable(self.table, column, 'DROP').sqlRepr()
				queries.append(q)

			for column in addcolumns:
				column['Null']='YES'
				altertype = 'ADD'
				if [col for col in describe if col['Field']==column['Field']]:
					altertype = 'CHANGE'
				q = sqlexpr.AlterTable(self.table, column, altertype).sqlRepr()
				queries.append(q)

			c.close()
			return addcolumns, dropcolumns, queries

class ObjectBuilder:

	"""This class lets you build objects for use with SQLDict, and
	for other purposes. To use, define a new class, subclassing
	ObjectBuilder. Define the following items:

	table: Name of table in SQL database.
	columns: List of columns in table.
	indices: A list of tuples. The first part of the tuple is the name
		of the index. The second part is a list of column names.
	"""

	table = None
	columns = []
	indices = []

	def __init__(self, *args, **kw):
		"""
		Constructor: Accepts an argument list of values, which are assigned in
		the order specified in columns. Also accepts keyword arguments,
		where the keys are from columns.
		"""

		for k in self.columns:
			setattr(self, k, None)
		for i in range(len(args)):
			setattr(self, self.columns[i], args[i])
		self.set_keywords(dict=kw)

	def __format_indices(self, indices):
		nindices=[]
		for indice in indices:
				if len(indice)<3:
						nindices.append(tuple(list(indice)+[{}]))
				else:
						nindices.append(indice)
		return nindices


	def set_keywords(self, skim=0, dict={}):
		"""
		Assign attributes using keyword arguments. If skim=0 (default),
		keywords not present in columns raises AttributeError. Otherwise,
		the keyword is ignored.
		"""
		for k, v in dict.items():
			if k in self.columns: setattr(self, k, v)
			elif not skim: raise AttributeError, k

	def __setattr__(self, key, value):
		try:
			getattr(self, '_set_'+key)(value)
		except AttributeError:
			self.__dict__[key] = value

	def __str__(self):
		l0 = "%s(" % self.__class__.__name__
		l = []
		for k in self.columns:
			l.append("%s=%s" % (k, repr(getattr(self, k))))
		return string.join([l0, join(l, ','), ')'],'')

	def __repr__(self):
		r =  self.dumpdict()
		return "%s( %s )" % (self.__class__.__name__, r)

	def dump(self):
		"""dump as a tuple."""
		l = []
		for k in self.columns:
			v = getattr(self,k)
			l.append(v)
		return tuple(l)

	def dumpdict(self):
		"""dump as a Python dictionary."""
		return dict(zip(self.columns, self.dump()))
		
	def register(self, db):
		"""Register into database."""
		t = db.Table(self.table, self.columns)
		# loader = lambda t, s=self.__class__: apply(s, t)
		# setattr(t, 'load', loader)
		indices = self.__format_indices(self.indices)
		for indexname, columns, args in indices:
			setattr(t, indexname, t.Index(columns, **args))
		return t

#########################################
# Database insert/query  tool functions #
#########################################

# default separator is |
# Note: Check Regular Expression
# in unFlatDict function if changed
sep ='|'

def setQueries(queryinfo):
	"""
	setQueries: Build a list of SQL queries from a queryInfo dictionary.
	"""
	queries = {}
	for key,value in queryinfo.items():
		if value['known'] is not None:
			## If we already have a data instance, then there
			## is no reason to do a query for it.
			## To indicate that, just set the query to be
			## the instance.
			queries[key] = value['known']
		elif type(value) is type({}):
			select = sqlexpr.selectAllFormat(value['alias'])
			query = queryFormatOptimized(queryinfo,value['alias'])
			queries[key]="%s %s" % (select, query)
	return queries

def queryFormatOptimized(queryinfo,tableselect):
	"""
	queryFormat: format the 'SQL WHERE' and figure out the tables to join.
	"""
	sqlquery = ""
	sqlfrom = ""
	sqljoin = []
	sqlwhere = []
	optimizedjoinlist = []
	optimizedjoinonlist = []
	alljoin={}
	joinon={}
	onjoin={}
	alljoinon={}
	wherejoin={}
	listselect=[]
	for key,value in queryinfo.items():
		if value['known']:
			continue
		if type(value) is not type({}):
			continue
		tableclass = value['class']
		a = value['alias']
		j = value['join']
		r = value['root']
		w = value['where']

		if r:
			sqlfrom = sqlexpr.fromFormat(tableclass, a)
			sqlorder = sqlexpr.orderFormat(a)
			sqllimit = sqlexpr.limitFormat(value['limit'])

		for field,id in j.items():
			joinTable = queryinfo[id]
			refclass = joinTable['class']
			joinfield = refFieldName(tableclass, refclass, field)

			## if data to join is already known, then
			## we need to convert the join into a where
			if queryinfo[id]['known'] is not None:
				defid = queryinfo[id]['known'].dbid
				w[joinfield] = defid
				continue

			fieldname = joinFieldName(a, joinfield)
			joinonalias = joinTable['alias']
			alljoinon[joinonalias] = sqlexpr.joinFormat(fieldname, joinTable)
			joinon[joinonalias]=a
			onjoin[a]=joinonalias
			if not joinonalias in optimizedjoinlist:
				optimizedjoinlist.append(joinonalias)

		if w:
			if not a in optimizedjoinlist:
				optimizedjoinlist.append(a)

			sqlexprstr = sqlexpr.whereFormat(value)
			if sqlexprstr:
				sqlwhere.append(sqlexprstr)

	if not tableselect in optimizedjoinlist:
		optimizedjoinlist.append(tableselect)

	for l in optimizedjoinlist:
		if joinon.has_key(l):
			if not joinon[l] in optimizedjoinlist:
				optimizedjoinlist.append(joinon[l])
			if not alljoinon[l] in sqljoin:
				sqljoin.append(alljoinon[l])
		if onjoin.has_key(l):
			if not alljoinon[onjoin[l]] in sqljoin:
				sqljoin.append(alljoinon[onjoin[l]])

	sqljoinstr = ' '.join(sqljoin)
	### convert:	JOIN ... ON (), JOIN ... ON ()
	###			to:		JOIN ( ... ) ON ( ... AND ...)
	reg_ex = 'JOIN[ ]{1,}(.*)[ ]{1,}ON[ ]{1,}\((.*)[ ]{0,}\)'
	p	= re.compile(reg_ex, re.IGNORECASE)
	refjoinlist = []
	fieldjoinlist = []
	for s in sqljoin:
		matches = p.search(s)
		if matches is not None:
			refjoinlist.append(matches.group(1))
			fieldjoinlist.append(matches.group(2))

	### comment the following line to use the orginal: JOIN ... ON (), JOIN ... ON ()
	if len(sqljoin) > 1:
		sqljoinstr = 'JOIN (' + ', '.join(refjoinlist) + ') ON ('+' AND '.join(fieldjoinlist)+')'
		
	if sqlwhere:
		sqlwherestr= 'WHERE ' + ' AND '.join(sqlwhere)
	else:
		sqlwherestr = ''

	sqlquery = "%s %s %s %s %s" % (sqlfrom, sqljoinstr, sqlwherestr, sqlorder, sqllimit)
	return sqlquery

def joinFieldName (refalias, colname):
	"""
	join the fieldname with the right alias.
	"""
	fieldname = "%s.%s" % (sqlexpr.backquote(refalias),sqlexpr.backquote(colname))
	return fieldname

def flatDict(in_dict):
	"""
	This function returns a flat dictionary. For example:
	>>> d = { 'BShift':{'X': 45.0, 'Y': 18.0}, 'IShift':{'X': 8.0, 'Y': 6.0}}
	>>> flatDict(d)

	{'SUBD|IShift|Y': 6.0, 'SUBD|BShift|Y': 18.0, 'SUBD|BShift|X': 45.0, 'SUBD|IShift|X': 8.0}

	The keys of the sub-dictionaries concatenate the parent key.

	"""

	items = {}
	try:
		keys = in_dict.keys()
	
	except AttributeError:
		raise TypeError("Must be a Dictionary") 

	for key in keys:
		value = in_dict[key]
		if type(value) is type({}):
			d = flatDict(value)
			nd={}
			# build the new keys
			for nk in d:
				lfk = ['SUBD',key,nk]
				fk= sep.join(lfk)
				nd.update({fk:d[nk]})

			items.update(nd)
		else:
			items[key] = value	
	return items

def unflatDict(in_dict, join):
	"""
	This function unflat a dictionary. For example:
	>>> d = {'SUBD|scope|SUBD|IShift|Y': 6.0, 'SUBD|scope|SUBD|BShift|Y': 18.0, 'SUBD|scope|SUBD|BShift|X': 45.0, 'SUBD|scope|SUBD|IShift|X': 8.0}
	>>> unflatDict(d)

	{'scope':{ 'BShift':{'X': 45.0, 'Y': 18.0}, 'IShift':{'X': 8.0, 'Y': 6.0}}}
	"""
	items = {}
	try:
		keys = in_dict.keys()
	
	except AttributeError:
		raise TypeError("Must be a Dictionary") 

	allsubdicts = {}
	for key,value in in_dict.items():
		a = key.split(sep)
		if a[0] == 'SUBD':
			name = a[1]
			if not allsubdicts.has_key(name):
				allsubdicts[a[1]]=None
		
		elif a[0] != 'ARRAY':
			items.update(datatype({key:value},join=join))

	for subdict in allsubdicts:
		dm={}
		for key,value in in_dict.items():
			l = re.findall('^SUBD\%s%s' %(sep,subdict,),key)
			if l:
				s = re.sub('^SUBD\%s%s\%s' %(sep,subdict,sep),'',key)
				dm.update({s:value})

		allsubdicts[subdict]=unflatDict(dm, join)

	allsubdicts.update(items)
	return allsubdicts

	
def dict2matrix(in_dict):
	"""
	This function returns a matrix from a dictionary.
	Each key from in_dict must have 2 numbers representing [row][colum].
	They can be separated by any characters.

	{'m|1_1': 1, 'm|1_2': 2, 'm|2_1': 3, 'm|2_2': 4, ..., 'm|i_j':n}
					 _		 _
					|		   |
					| 1   2   j |
					|		   |
		=>			| 3   4   . |
					|	   .   |
					| i   .   n |
					|_		 _|

	example:
	{'ARRAY|matrix|2_1': -1.24684512082676e-10, 'ARRAY|matrix|2_2': 2.0027370335951399e-10, 'ARRAY|matrix|1_2': 1.2226514813724901e-10, 'ARRAY|matrix|1_1': 1.9444897985776799e-10}
	"""

	# Get the shape and size of the matrix
	ij=[]
	for m in in_dict:
		i=eval(re.findall('\d+',m)[0])
		j=eval(re.findall('\d+',m)[1])
		ij.append((i,j))
	shape = max(ij)
	size  = shape[0]*shape[1]

	# Build the matrix
	matrix = numpy.zeros(shape, numpy.float64)
	for m in in_dict:
		i=eval(re.findall('\d+',m)[0])-1
		j=eval(re.findall('\d+',m)[1])-1
		matrix[i][j]=in_dict[m]

	return matrix
		
def matrix2dict(matrix, name=None):
	"""
	This function returns a dictionary which represents a matrix.
	matrix must be at least 2x1 or 1x2 numpy arrays.

	 _		      _
	|		        |
	| 1   2   j |
	|		        |
	| 3   4   . |	=>
	|	   .      |
	| i   .   n |
	|_		     _|

	{'m|1_1': 1, 'm|1_2': 2, 'm|2_1': 3, 'm|2_2': 4, ..., 'm|i_j':n}

	"""

	if name is None:
		name='m'
		
	try:
		if not (matrix.shape >= (1, 1) and len(matrix.shape) > 1):
			raise ValueError("Wrong shape: must be at least 2x1 or 1x2")
	except AttributeError:
		raise TypeError("Must be numpy array") 
	d={}
	i=0
	for row in matrix:
		i+=1
		j=1
		for col in row:
			k = sep.join(['ARRAY',name,'%s_%s'%(i,j)])
			v = float(matrix[i-1,j-1])
			d[k]=v
			j+=1
	return d

def object2sqlColumn(key):
	"""
	Add PICKLE| if value is instance of newdict.AnyObject
	"""
	return "PICKLE%s%s"%(sep,key,)

def seq2sqlColumn(key):
	"""
	Add SEQ|if key is tuple or list
	"""
	return "SEQ%s%s"%(sep,key,)

def sql2data(in_dict, qikey=None, qinfo=None):
	"""
	This function converts any result of an SQL query to an Data type:

	>>> d = {'SUBD|camera|exposure time': 1, 'SUBD|camera|SUBD|binning|x': 1,
				 'SUBD|camera|SUBD|binning|y': 1, 'SUBD|scope|SUBD|gun shift|y': 1,
				 'SUBD|scope|SUBD|gun shift|x': 1,
				 'ARRAY|matrix|1_1': 1.9444897985776799e-10,
				 'SUBD|scope|dark field mode': 1, 'ARRAY|matrix|2_1': -1.24684512082676e-10,
				 'SEQ|id': "('manager', 'corrector', 49)",
				 'ARRAY|matrix|2_2': 2.0027370335951399e-10,
				 'SUBD|camera|SUBD|camera size|y': 1, 'SUBD|camera|SUBD|camera size|x': 1,
				 'SUBD|camera|SUBD|dimension|y': 1, 'SUBD|camera|SUBD|dimension|x': 1,
				 'ARRAY|matrix|1_2': 1.2226514813724901e-10, 'SUBD|camera|SUBD|offset|y': 1,
				 'SUBD|camera|SUBD|offset|x': 1, 'database filename': 1}
		>>> sql2data(d)
	{'camera': {'exposure time': 1, 'camera size': {'y': 1, 'x': 1},
		 'dimension': {'y': 1, 'x': 1}, 'binning': {'y': 1, 'x': 1},
		 'offset': {'y': 1, 'x': 1}},
	 'matrix': array([[  1.94448980e-10,   1.22265148e-10], 
			 [ -1.24684512e-10,   2.00273703e-10]]),
	 'database filename': 1,
	 'scope': {'gun shift': {'y': 1, 'x': 1}, 'dark field mode': 1},
	 'id': ('manager', 'corrector', 49)}
	"""
	content={}
	allsubdicts={}

	if None in (qikey,qinfo):
		join = None
	else:
		join = qinfo[qikey]['join']
		parentclass = qinfo[qikey]['class']
	content = datatype(in_dict, join=join, parentclass=parentclass)

	return content

## get rid of this function when field names are converted to have full
## absolute module name
wrong_names = {}
def findWrongName(modulename):
	## try cache of wrong names
	if modulename in wrong_names:
		return wrong_names[modulename]
	## try sys.modules (last component of each name)
	for sysmodname,sysmod in sys.modules.items():
		if sysmodname.split('.')[-1] == modulename:
			wrong_names[modulename] = sysmod
			return sysmod
	return None

def findDataClass(modulename, classname):
	if modulename in sys.modules:
		mod = sys.modules[modulename]
	else:
		# remove findWrongName when DB is converted
		mod = findWrongName(modulename)
		if mod is None:
			raise RuntimeError('Cannot find class %s. Module %s not loaded.' % (classname, modulename))
	cls = getattr(mod, classname)
	return cls

def datatype(in_dict, join=None, parentclass=None):
	"""
	This function converts a specific string or a SQL type to 
	a python type.
	"""
	content={}
	allarrays={}
	subditems = {}
	for key,value in in_dict.items():
		a = key.split(sep)
		a0 = a[0]
		if a0 == 'ARRAY':
			name = a[1]
			if not allarrays.has_key(name):
				allarrays[name]=None
		elif a0 == 'SEQ':
			if value is None:
				content[a[1]] = None
			else:
				try:
					content[a[1]] = eval(value)
				except SyntaxError:
					content[a[1]] = None
		elif a0 == 'PICKLE':
			## contains a python pickle string,
			## convert it to newdict.AnyObject
			try:
				value = value.tostring()
			except AttributeError:
				pass
			try:
				ob = cPickle.loads(value)
			except:
				ob = None
			content[a[1]] = newdict.AnyObject(ob)
		elif a0 == 'MRC':
			## set up a FileReference, to be used later
			## when we know the full path
			if value is None:
				content[a[1]] = None
			else:
				content[a[1]] = newdict.FileReference(value, pyami.mrc.read)
		elif a0 == 'REF':
			fieldname = a[-1]
			tablename = a[-2]
			# By default, references are to the current database.
			# An extra parameter can indicate a different database.
			if len(a) == 4:
				modulename = a[-3]
			else:
				modulename = parentclass.__module__
			if value == 0 or value is None:
				### NULL reference
				content[fieldname] = None
			elif fieldname in join:
				## referenced data is part of result
				jqikey = join[fieldname]
				content[fieldname] = data.UnknownData(jqikey)
			else:
				## not in result, but create reference
				dclassname = tablename
				dclass = findDataClass(modulename, dclassname)
				if dclass is None:
					continue
				# host and name should come from parent object
				content[fieldname] = data.DataReference(dataclass=dclass, dbid=value)
		elif a0 == 'SUBD':
			subditems[key] = value
		else:
			content[key]=value

	# build dictionaries
	allsubdicts=unflatDict(subditems, join)
	content.update(allsubdicts)

	for matrix in allarrays:
		dm={}
		for key,value in in_dict.items():
			l = re.findall('^ARRAY\%s%s' %(sep,matrix,),key)
			if l:
				dm.update({key:value})
		allarrays[matrix]=dict2matrix(dm)

	content.update(allarrays)
	return content

def sqltype(o):
	return _sqltype(type(o))

def _sqltype(t):
	"""
	Convert a python type to an SQL type
	"""
	if t is str:
		return "TEXT"
	elif issubclass(t, float):
		return "DOUBLE"
	elif t is bool:
		return "TINYINT(1)"
	elif issubclass(t, (int,long)):
		return "INT(20)"
	elif t is datetime.datetime:
		return "TIMESTAMP"
	else:
		return None

def refFieldName(tableclass, refclass, key):
	refmodule = refclass.__module__

	#### XXX remove the following line when absolute modules names are
	#### considered final:
	refmodule = refmodule.split('.')[-1]

	tablename = refclass.__name__
	#### XXX fix following when absolute modules names are
	#### considered final:
	tablemodule = tableclass.__module__.split('.')[-1]
	parts = ['REF']
	if tablemodule != refmodule:
		parts.append(refmodule)
	parts.extend([tablename, key])
	colname = sep.join(parts)
	return colname

def keyMRC(name):
	return sep.join(['MRC', name])

def saveMRC(object, name, path, filename, thumb=False):
	"""
	Save numpy array to MRC file and replace it with filename
	"""
	d={}
	k = keyMRC(name)
	fullname = dbconfig.mapPath(os.path.join(path,filename))
	if object is None or isinstance(object, newdict.FileReference):
		## either there is no image data, or it is already saved
		pass
	else:
		#print 'saving MRC', fullname
		pyami.mrc.write(object, fullname)

	d[k] = filename
	return d

def subSQLColumns(value_dict, data_instance):
	columns = []
	row = {}
	for key, value in value_dict.items():
		value_type = type(value)

		result = type2column(key, value, value_type, data_instance)
		if result is not None:
			columns.append(result[0])
			row.update(result[1])
			continue

		result = type2columns(key, value, value_type, data_instance)
		if result is not None:
			columns += result[0]
			row.update(result[1])
			continue

	return columns, row

def dataSQLColumns(data_instance, fail=True):
	columns = []
	row = {}
	# default columns
	columns.append({
			'Field': 'DEF_id',
			'Type': 'int(16)',
			'Key': 'PRIMARY',
			'Extra':'auto_increment',
	})
	columns.append({
			'Field': 'DEF_timestamp',
			'Type': 'timestamp',
			'Key': 'INDEX',
			'Index': ['DEF_timestamp']
	})

	type_dict = dict(data_instance.typemap())

	for key, value in data_instance.items(dereference=False):
		try:
			value_type = type_dict[key]
		except KeyError:
			raise ValueError, value_type.__name__

		result = type2column(key, value, value_type, data_instance)
		if result is not None:
			columns.append(result[0])
			row.update(result[1])
			continue

		result = type2columns(key, value, value_type, data_instance)
		if result is not None:
			columns += result[0]
			row.update(result[1])
			continue

		if fail is True:
			raise ValueError, value_type.__name__
		else:
			print "ERROR", value_type.__name__

	return columns, row

def type2column(key, value, value_type, parentdata):
	column = {}
	row = {}
	sql_type = _sqltype(value_type)
	if sql_type is not None:
		# simple types
		column['Field'] = key
		column['Type'] = sql_type
		### index all bools
		if column['Type'] == 'TINYINT(1)':
			column['Key'] = 'INDEX'
		row[key] = value
	else:
		try:
			if issubclass(value_type, (sinedon.data.Data, sinedon.data.DataReference)):
				# data.Data reference
				tableclass = parentdata.__class__
				field = refFieldName(tableclass, value_type, key)
				column['Field'] = field
				column['Type'] = 'INT(20)'
				column['Key'] = 'INDEX'
				column['Index'] = [column['Field']]
				if value is None:
					row[field] = None
				else:
					row[field] = value.dbid
			elif issubclass(value_type, newdict.AnyObject):
				field = object2sqlColumn(key)
				column['Field'] = field
				column['Type'] = 'LONGBLOB'
				row[field] = cPickle.dumps(value.o, cPickle.HIGHEST_PROTOCOL)
			else:
				return None
		except TypeError:
			return None

	column['Null'] = 'YES'
	if not ('TEXT' in column['Type'] or 'BLOB' in column['Type']):
		column['Default'] = 'NULL'
	if column['Type'] == 'TINYINT(1)':
		column['Default'] = '0'
	return column, row

def type2columns(key, value, value_type, parentdata):
	if value_type is newdict.DatabaseArrayType:
		if value is None:
			column_dict = value_dict = {}
		else:
			column_dict = value_dict = matrix2dict(value, key)
	elif value_type is newdict.MRCArrayType:
		if value is None:
			column_dict = {keyMRC(key): ''}
			value_dict = {keyMRC(key): None}
		else:
			filename = parentdata.filename()
			path = parentdata.mkpath()
			column_dict = value_dict = saveMRC(value, key, path, filename)
	elif value_type is dict:
		# python dict
		if value is None:
			column_dict = value_dict = {}
		else:
			column_dict = value_dict = flatDict({key: value})
	elif value_type in (tuple, list):
		# python sequences
		if value is None:
			column_dict = value_dict = {}
		else:
			column_dict = value_dict = {seq2sqlColumn(key): repr(value)}
	else:
		return None
	columns, row = subSQLColumns(column_dict, parentdata)
	columns.sort()
	row.update(value_dict)
	return columns, row


if __name__ == '__main__':
	data_instance = data.AcquisitionImageData()
	columns, row = dataSQLColumns(data_instance)
	for column in columns:
		field = column['Field']
		print field
		print column
		if field in ('DEF_id', 'DEF_timestamp'):
			print
			continue
		print row[field]
		print

