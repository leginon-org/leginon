"""
dbdict: a DB / Python Dictionary module.
"""
import sqldb
import cPickle
import md5


class dbDict(object):
	"""
	This creates a dictionary which stores Keys and values as
	binary blobs into a database.
	It assumes that a MySQL database exists somewhere.
	Also, the db user must have the following rights:
		select, insert, delete, update, create, drop.
	By default the db parameters are:
		hostname='localhost'
		username='usr_object'
		databasename='dbemdata'
	Example:
		import dbdict
		a=dbdict.dbDict('dbdictname')
		b=dbdict.dbDict('dbdictname', hostname='host.domain')


		"a" creates a new table on localhost's database
		"b" creates a new table on host.domain's database

		dbd = dbdict.dbDict('dbdictname', hostname='cronus2')
		dbd[1]={'k':'v', 1:'nom'}
		
	"""
	def __init__(self, tablename, hostname='localhost', username='usr_object', databasename='dbemdata'):
		self.tablename = tablename
		self.hostname=hostname
		self.username=username
		self.databasename=databasename
		self.__open_db()
		self.__create()
		self.__close_db()
	
	def __addSlashes(self, str):
		"""
		Escape single quotes from the string str
		"""
		return repr(str + '"')[:-2] + "'"

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
		'Open a DB connection.'
		self.dbc = sqldb.sqlDB(self.hostname, self.username, self.databasename)

	def __close_db(self):
		'Close a DB connection.'
		self.dbc.close()

	def __create(self):
		'Create a new object table which stores keys and values of a new dbDict object.'
		self.dbc.execute("""
				CREATE TABLE IF NOT EXISTS `%s` (
					Id int(11) NOT NULL auto_increment,
					hash varchar(64) NOT NULL default '',
					objectKey mediumblob NOT NULL,
					object longblob NOT NULL,
					objectKeyString text NOT NULL,
					objectString text NOT NULL,
					PRIMARY KEY  (Id),
					UNIQUE KEY objectKey (objectKey(255)),
					UNIQUE KEY hash (hash)
				) TYPE=MyISAM
				""" % self.tablename )

	def __drop(self):
		'Drop an existing object table.'
		self.dbc.execute("""
				DROP TABLE `%s` 
				""" % self.tablename )

	def __empty(self):
		'Clear an existing object table.'
		if self.dbc is not None:
			return self.dbc.execute("""delete from `%s` """ %
							(self.tablename)
							)

	def __del(self, cpickle_blobKey):
		'Delete a row of an existing object table.'
		if self.dbc is not None:
			val = self.dbc.execute("""delete from `%s`
							where objectKey='%s' """ %
							(self.tablename, cpickle_blobKey)
							)
			return val

	def __length(self):
		'Return number of rows of an existing object table.'
		if self.dbc is not None:
			return self.dbc.selectone("""select count(Id) from `%s` """ %
							(self.tablename)
							)

	def __get_Id(self, cpickle_blobKey):
		'Return an object Id from a table by specifying a key.'
		if self.dbc is not None:
			return self.dbc.selectone("""select Id from `%s`
							where objectKey='%s' """ %
							(self.tablename, cpickle_blobKey)
							)

	def __get_hId(self, hash):
		'Return an object Id from a table by specifying a hash.'
		if self.dbc is not None:
			return self.dbc.selectone("""select Id from `%s`
							where hash='%s' """ %
							(self.tablename, hash)
							)

	def __keys(self):
		'Return all keys from an existing object table.'
		if self.dbc is not None:
			res_tuple = self.dbc.selectall("""select objectKey from `%s` """ %
							self.tablename
						   	)
			return res_tuple
		
	def __get(self, blobKey, type=0):
		"""
		If type=1, the method will query the object DB using a hash as a key.
		"""
		if self.dbc is not None:
			if type == 0:
				cpickle_blobKey = self.__pickle_key(blobKey)
				res_tuple = self.dbc.selectone (""" select object from `%s`
								where objectKey='%s'""" %
								(self.tablename, cpickle_blobKey)
								)
				if res_tuple:
					return self.__unpickle_key(res_tuple[0])
				else:
					raise KeyError(blobKey)	

			elif type == 1:
				hash = md5.new(blobKey).hexdigest()
				res_tuple=self.dbc.selectone(""" select object from `%s`
								where hash='%s'""" %
								(self.tablename, hash)
								)
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
			blobKey_str="""%s""" % (blobKey)
			blob_str="""%s""" % (blob)
			blobKey_str=self.__addSlashes(blobKey_str)
			blob_str=self.__addSlashes(blob_str)

			q = ("""replace into `%s` (hash, objectKey, object, objectKeyString, objectString)
							values ('%s', '%s', '%s', %s, %s) """ %
						 	(self.tablename, hash, cpickle_blobKey, cpickle_blob, blobKey_str, blob_str)
						)
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

	def keys(self):
		'dump a list of keys from an object table'
		self.__open_db()
		t_pkeys = self.__keys()
		self.__close_db()
		keys=[]
		for k in t_pkeys:
			keys.append(self.__unpickle_key(k[0]))
		return keys

