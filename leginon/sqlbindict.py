"""
sqlbindict: a DB / Python Dictionary module.

This creates a database interface which works pretty much like a
Python dictionary. The keys and values of the dictionary are first
"pickled" and then stored in a sql table as binary blobs. A
string representation of the keys and values are stored as well, so
it can be read by querying directly the database.

"""
import sqldb
import sqlexpr
import cPickle
import md5


class SQLBinDict(object):
	"""
	This creates a dictionary which stores Keys and values as
	binary blobs into a database.
	It assumes that a MySQL database exists somewhere.
	Also, the db user must have the following rights:
		select, insert, delete, update, create, drop.
	By default the db parameters are set in sqldb module:

	Example:
		import sqlbindict
		a=sqlbindict.SQLBinDict('dbdictname')

		or you can set the following keywords:
				host	= "DB_HOST"
				user	= "DB_USER"
				db	= "DB_NAME"
				passwd	= "DB_PASS"

		b=sqlbindict.SQLBinDict('dbdictname', host='[YourHost]')

		"a" creates a new table on the defalut database.
		"b" creates a new table on [YourHost]'s database.

		dbd = sqlbindict.SQLBinDict('dbdictname')
		dbd[1]={'k':'v', 1:'nom'}
		
	"""
	def __init__(self, tablename, **kwargs):
		self.tablename = tablename
		self.table = eval("sqlexpr.table.%s" % (tablename))
		self.kwargs=kwargs
		self.__open_db()
		self.__create()
		self.__close_db()
	
	##
	## methods to convert:
	##
	## 	object -> binary
	## 	binary -> object
	##

	def __pickle_key(self, key):
		return cPickle.dumps(key, 1)

	def __unpickle_key(self, pkey):
		return cPickle.loads(pkey)

	##
	## private methods used to communicate with the database
	##

	def __open_db(self):
		"""
		   Open a DB connection.
			The optional keyword arguments are:
				host	= "DB_HOST"
				user	= "DB_USER"
				db	= "DB_NAME"
				passwd	= "DB_PASS"

			By default, this is in the config.py file.
		"""
		try:
			self.dbc = sqldb.sqlDB(**self.kwargs)
		except Exception, e:
			raise(e)

	def __close_db(self):
		'Close a DB connection.'
		self.dbc.close()

	def __create(self):
		'Create a new object table which stores keys and values of a new SQLBinDict object.'

		tableDefinition = [{'Field': 'id', 'Type': 'int(16)', 'Key': 'PRIMARY', 'Extra':'auto_increment'},
 			{'Field': 'hash', 'Type': 'VARCHAR(64)', 'Key': 'UNIQUE', 'Index': ['hash']},
			{'Field': 'objectKey', 'Type': 'mediumblob', 'Key': 'UNIQUE', 'Index': ['objectKey(255)']},
			{'Field': 'object', 'Type': 'longblob'},
			{'Field': 'objectKeyString', 'Type': 'text'},
			{'Field': 'objectString', 'Type': 'text'}]

		if self.dbc is not None:
	    		q = sqlexpr.CreateTable(self.tablename, tableDefinition).sqlRepr()
			self.dbc.execute(q)


	def __drop(self):
		'Drop an existing object table.'
		if self.dbc is not None:
	    		q = sqlexpr.DropTable(self.table).sqlRepr()
			self.dbc.execute(q)

	def __empty(self):
		'Clear an existing object table.'
		if self.dbc is not None:
	    		q = sqlexpr.Delete(self.table, where=None).sqlRepr()
			self.dbc.execute(q)

	def __del(self, cpickle_blobKey):
		'Delete a row of an existing object table.'
		if self.dbc is not None:
	    		q = sqlexpr.Delete(self.table, where=self.table.objectKey==cpickle_blobKey).sqlRepr()
			val = self.dbc.execute(q)
			return val

	def __length(self):
		'Return number of rows of an existing object table.'
		if self.dbc is not None:
			q = sqlexpr.Select(sqlexpr.const.count(self.table.Id)).sqlRepr()
			return self.dbc.selectone(q)

	def __get_Id(self, cpickle_blobKey):
		'Return an object Id from a table by specifying a key.'
		if self.dbc is not None:
	    		q = sqlexpr.Select(self.table.Id,
				 where=self.table.objectKey==cpickle_blobKey).sqlRepr()
			return self.dbc.selectone(q)

	def __get_hId(self, hash):
		'Return an object Id from a table by specifying a hash.'
		if self.dbc is not None:
	    		q = sqlexpr.Select(self.table.Id,
				 where=self.table.hash==hash).sqlRepr()
			return self.dbc.selectone(q)

	def __keys(self):
		'Return all keys from an existing object table.'
		if self.dbc is not None:
	    		q = sqlexpr.Select(self.table.objectKey).sqlRepr()
			res_tuple = self.dbc.selectall(q)
			return res_tuple

	def __values(self):
		'Return all keys from an existing object table.'
		if self.dbc is not None:
	    		q = sqlexpr.Select(self.table.object).sqlRepr()
			res_tuple = self.dbc.selectall(q)
			return res_tuple

	def __all(self):
		'Return all keys from an existing object table.'
		if self.dbc is not None:
	    		q = sqlexpr.Select([self.table.objectKey, self.table.object]).sqlRepr()
			res_tuple = self.dbc.selectall(q)
			return res_tuple
		
	def __get(self, blobKey):
		'Return a object to the corresponding key.'
		if self.dbc is not None:
			cpickle_blobKey = self.__pickle_key(blobKey)
	    		q = sqlexpr.Select(self.table.object,
				 where=self.table.objectKey==cpickle_blobKey).sqlRepr()
			res_tuple = self.dbc.selectone(q)
			if res_tuple:
				return self.__unpickle_key(res_tuple[0])
			else:
				raise KeyError(blobKey)	

	def __put(self, blobKey, blob):
		'Insert a new object in an existing object table.'
		if self.dbc is not None:
			hash = md5.new("""%s""" % blobKey).hexdigest()
			cpickle_blobKey = self.__pickle_key(blobKey)
			cpickle_blob	= self.__pickle_key(blob)
			blobKey_str="""%s""" % (blobKey,)
			blob_str="""%s""" % (blob,)

			q = sqlexpr.Replace(self.tablename,
			    [hash, cpickle_blobKey, cpickle_blob, blobKey_str, blob_str],
			    template=('hash', 'objectKey', 'object', 'objectKeyString', 'objectString')
			    ).sqlRepr()
			return self.dbc.insert(q)
	##
	## methods to emulate a Python Dictionary
	##


	def drop(self):
		'Drop an existing object table in the database.'
		self.__open_db()
		self.__drop()
		self.__close_db()
		
	def clear(self):
		'Remove all items from an object table.'
		self.__open_db()
		self.__empty()
		self.__close_db()

	def __repr__(self):
		return self.all().__repr__()
		
	def __contains__(self, key):
		'1 if an object table has a key k, else 0'
		return self.has_key(key)
		
	def __len__(self):
		'The number of items in an object table.'
		self.__open_db()
		length = self.__length()
		self.__close_db()
		return length[0]

	def __getitem__(self, key):
		'Get an item from an object table.'
		self.__open_db()
		value = self.__get(key)
		self.__close_db()
		return value

	def __setitem__(self, key, value):
		'Set an item in an object table.'
		self.__open_db()
		self.__put(key,value)
		self.__close_db()
		
	def __delitem__(self, key):
		'Delete an item from an object table.'
		newkey = self.__pickle_key(key)
		self.__open_db()
		if not self.__del(newkey):
			raise KeyError(key)
		self.__close_db()

	def update(self, d):
		for k in d.keys(): self[k] = d[k]

	def has_key(self, key):
		'1 if an object table has a key k, else 0'
		self.__open_db()
		newkey = self.__pickle_key(key)
		result = self.__get_Id(newkey)
		self.__close_db()
		if result:
			return 1 
		else:
			return 0
	def all(self):
		self.__open_db()
		t_pall = self.__all()
		self.__close_db()
		keys = []
		values = []
		for k in t_pall:
			keys.append(self.__unpickle_key(k[0]))
			values.append(self.__unpickle_key(k[1]))
		all = dict(zip(keys,values))
		return all

	def keys(self):
		'dump a list of keys from an object table'
		self.__open_db()
		t_pkeys = self.__keys()
		self.__close_db()
		keys=[]
		for k in t_pkeys:
			keys.append(self.__unpickle_key(k[0]))
		return keys

	def values(self):
		self.__open_db()
		t_pvalues= self.__values()
		self.__close_db()
		values = []
		for v in t_pvalues:
			values.append(self.__unpickle_key(k[0]))
		return values
