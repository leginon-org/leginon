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
...     table = "PRESET"
...	columns = [ 'Name', 'Defocus', 'Dose', 'Mag' ]
...     indices = [ ('Name', ['Name'], {'orderBy':{'fields':('id',)}}),
...		    ('NameMag', ['Name', 'Mag']) ]
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


import sqlexpr
import copy
import sqldb
import string
import re
import Numeric
import MySQLdb.cursors
from types import *

class SQLDict:

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
	By default, this is in the config.py file
	"""
	self.db = sqldb.connect(**kwargs)

    def __del__(self):	self.close()

    def close(self):
	try: self.db.close()
	except: pass

    def __getattr__(self, attr):
	# Get any other interesting attributes from the base class.
	return getattr(self.db, attr)


    class _createSQLTable:

	def __init__(self, db, table, definition):
	    self.db = db
	    self.table = table
	    self.definition = definition
	    self.create(db)

	def create(self, db):
	    q = sqlexpr.CreateTable(self.table, self.definition).sqlRepr()
	    c = db.cursor()
	    c.execute(q)
	    return c

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

	def insert(self, v=[]):
	    c = self.cursor()
	    q = sqlexpr.Insert(self.table, v).sqlRepr()
	    c.execute(q)
	    return c.insert_id()

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

	class _Index:

	    """
		Index handler for a _Table object.
	    """

	    def __init__(self, table, indices, **kwargs):
		self.table = table
		self.kwargs= kwargs
		ind = map(lambda id: sqlexpr.Field(self.table.table, id), indices)
		self.fields = ind

	    def __setitem__(self, i=(), v=None):
		"""Update the item in the database matching i
		with the value v."""
		if type(i) == ListType: i = tuple(i)
		elif type(i) != TupleType: i = (i,)
		w = sqlexpr.AND_EQUAL(zip(self.fields,i))
		self.table.update(v, WHERE=w)

	    def __getitem__(self, i=()):
		"""Select items in the database matching i."""
		if type(i) == ListType: i = tuple(i)
		elif type(i) != TupleType: i = (i,)
		w = sqlexpr.AND_EQUAL(zip(self.fields,i))
		return self.table.select(where=w, **self.kwargs)

	    def __delitem__(self, i):
		"""Delete items in the database matching i."""
		if type(i) == ListType: i = tuple(i)
		elif type(i) != TupleType: i = (i,)
		w = sqlexpr.AND_EQUAL(zip(self.fields,i))
		return self.table.delete(i, WHERE=w)


	def Index(self, indices=[], **kwargs):

	    """Create an index definition for this table.

	    Usage: db.table.Index(indices)
	    Where: indices   = tuple or list of column names to key on
		   orderBy = optional ORDER BY clause.
		   WHERE     = optional WHERE clause.
		   WHERE not implemented YET...

	    """

	    return self._Index(self, indices, **kwargs)

	class _Cursor:

	    """A subclass (shadow class?) of a cursor object which knows how to
	    load the tuples returned from the database into a more interesting
	    object."""

	    def __init__(self, db, load, columns):
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


	def cursor(self):
	    """Returns a new _Cursor object which is load-aware and
	    otherwise behaves normally."""
	    return self._Cursor(self.db, self.load, self.columns)


    def Table(self, table, columns=[]):

	"""Add a new Table member.

	Usage: db.Table(tablename, columns)
	Where: tablename  = name of table in database
               columns    = tuple containing names of columns of interest

	       """
	return self._Table(self.db, table, columns)

    def createSQLTable(self, table, definition):
	"""
		>>> CreateTable('PEOPLE',
			[{'Field': 'id', 'Type': 'int(16)', 'Key': 'PRIMARY', 'Extra':'auto_increment'},
			 {'Field': 'Name', 'Type': 'VARCHAR(50)'}])
	"""
	return self._createSQLTable(self.db, table, definition)


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

###################################
# Database insert  tool functions #
###################################

# default separator is |
# Note: Check Regular Expression
# in unFlatDict function if changed
sep ='|'

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

def unflatDict(in_dict):
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
		a = re.findall('[^%s]+'%(sep,),key)
		if a[0] == 'SUBD':
			name = a[1]
			if not allsubdicts.has_key(name):
				allsubdicts[a[1]]=None
		
		elif a[0] != 'ARRAY':
			items.update(datatype({key:value}))

	for subdict in allsubdicts:
		dm={}
		for key,value in in_dict.items():
			l = re.findall('^SUBD\%s%s' %(sep,subdict,),key)
			if l:
				s = re.sub('^SUBD\%s%s\%s' %(sep,subdict,sep),'',key)
				dm.update({s:value})

		allsubdicts[subdict]=unflatDict(dm)

	allsubdicts.update(items)
	return allsubdicts

	
def dict2matrix(in_dict):
	"""
	This function returns a matrix from a dictionary.
	Each key from in_dict must have 2 numbers representing [row][colum].
	They can be separated by any characters.

	{'m|1_1': 1, 'm|1_2': 2, 'm|2_1': 3, 'm|2_2': 4, ..., 'm|i_j':n}
					 _         _
					|           |
					| 1   2   j |
					|           |
		=>			| 3   4   . |
					|       .   |
					| i   .   n |
					|_         _|

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
	matrix = Numeric.zeros(shape, Numeric.Float64)
	for m in in_dict:
		i=eval(re.findall('\d+',m)[0])-1
		j=eval(re.findall('\d+',m)[1])-1
		matrix[i][j]=in_dict[m]

	return matrix
		
def matrix2dict(matrix, name=None):
	"""
	This function returns a dictionary which represents a matrix.
	matrix must be at least 2x1 or 1x2 Numeric arrays.

	 _         _
	|           |
	| 1   2   j |
	|           |
	| 3   4   . |	=>
	|       .   |
	| i   .   n |
	|_         _|

	{'m|1_1': 1, 'm|1_2': 2, 'm|2_1': 3, 'm|2_2': 4, ..., 'm|i_j':n}

	"""

	if name is None:
		name='m'
		
	try:
		if not (matrix.shape >= (1, 1) and len(matrix.shape) > 1):
			raise ValueError("Wrong shape: must be at least 2x1 or 1x2")
	except AttributeError:
		raise TypeError("Must be Numeric array") 
	d={}
	i=0
	for row in matrix:
		i+=1
		j=1
		for col in row:
			# k = "ARRAY|%s|%s_%s" % (name,i,j)
			k = sep.join(['ARRAY',name,'%s_%s'%(i,j)])
			v = float(matrix[i-1,j-1])
			d[k]=v
			j+=1
	return d

def sqltype(object):
	"""
	Convert a python type to an SQL type
	"""
	t = type(object)
	if t is type(""):
		return "TEXT"
	elif t is float:
		return "DOUBLE"
	elif t is int:
		return "INT(20)"
	else:
		return None

def sqlColumnsDefinition(in_dict, noDefault=None):
	"""
	Format a table definition for any Data Class:

	[{'Field': 'magnification', 'Type': 'INT(20)'}, {'Field': 'SUBD|BShift|X', 'Type': 'DOUBLE'},
	 {'Field': 'SUBD|BShift|Y', 'Type': 'DOUBLE'},
	 {'Field': 'ARRAY|matrix|1_1', 'Type': 'DOUBLE'},
	 {'Field': 'ARRAY|matrix|1_2', 'Type': 'DOUBLE'},
	 {'Field': 'ARRAY|matrix|2_1', 'Type': 'DOUBLE'},
	 {'Field': 'ARRAY|matrix|2_2', 'Type': 'DOUBLE'},
	 {'Field': 'defocus', 'Type': 'DOUBLE'}, {'Field': 'float', 'Type': 'DOUBLE'},
	 {'Field': 'type', 'Type': 'TEXT'}]
	"""
	columns=[]
	# default columns are listed below
	if noDefault is None:
		defaults = [	{'Field': 'DEF_id', 'Type': 'int(16)',
				'Key': 'PRIMARY', 'Extra':'auto_increment'},
				{'Field':'DEF_timestamp','Type':'timestamp',
				'Null':'YES', 'Key':'INDEX'}
				]
		columns += defaults
	for key in in_dict:
		column={}
		value=in_dict[key]
		sqlt = sqltype(value)
		if sqlt is not None:
			column['Field']=key
			column['Type']=sqlt
			columns.append(column)
		elif type(value) is Numeric.ArrayType:
			if len(Numeric.ravel(value)) < 10:
				arraydict = matrix2dict(value,key)
				nd = sqlColumnsDefinition(arraydict, noDefault=[])
				nd.sort()
				columns += nd
			# Think about store the filename
				
		elif type(value) is dict:
			flatdict = flatDict({key:value})
			nd = sqlColumnsDefinition(flatdict, noDefault=[])
			nd.sort()
			columns += nd

		elif type(value) in [tuple, list]:
			nd = sqlColumnsDefinition({seq2sqlColumn(key):repr(value)}, noDefault=[])
			columns += nd
			
	return columns


def seq2sqlColumn(key):
	"""
	Add SEQ|if key is tuple or list
	"""
	return "SEQ%s%s"%(sep,key,)

def sqlColumnsSelect(in_dict):
	"""
	['magnification', 'SUBD|BShift|X', 'SUBD|BShift|Y',
	 'ARRAY|matrix|1_1', 'ARRAY|matrix|1_2', 'ARRAY|matrix|2_1',
	 'ARRAY|matrix|2_2', 'defocus', 'float', 'type']
	"""
	columns=[]
	for key in in_dict:
		value=in_dict[key]
		sqlt = sqltype(value)
		if sqlt is not None:
			columns.append(key)
		elif type(value) is type(Numeric.array([0])):
			arraydict = matrix2dict(value,key)
			nd = sqlColumnsSelect(arraydict)
			nd.sort()
			columns += nd
		elif type(value) is dict:
			flatdict = flatDict({key:value})
			nd = sqlColumnsSelect(flatdict)
			nd.sort()
			columns += nd
		elif type(value) in [tuple, list]:
			nd = sqlColumnsSelect({seq2sqlColumn(key):repr(value)})
			columns += nd
	return columns


def sqlColumnsFormat(in_dict):
	"""
	{'ARRAY|matrix|2_1': 3.0, 'magnification': 5, 'ARRAY|matrix|2_2': 4.0,
	 'SUBD|BShift|Y': 18.0, 'SUBD|BShift|X': 45.0, 'ARRAY|matrix|1_1': 1.0,
	 'defocus': -9.9999999999999998e-13, 'ARRAY|matrix|1_2': 2.0,
	 'float': 12.25, 'type': 'test'}
	"""
	columns={}
	for key in in_dict:
		value=in_dict[key]
		sqlt = sqltype(value)
		if sqlt is not None:
			columns[key]=value
		elif type(value) is type(Numeric.array([0])):
			arraydict = matrix2dict(value,key)
			columns.update(arraydict)
		elif type(value) is dict:
			flatdict = flatDict({key:value})
			columns.update(flatdict)
		elif type(value) in [tuple, list]:
			columns[seq2sqlColumn(key)] = repr(value)
	return columns



def sql2data(in_dict):
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

	# Convert ARRAY, SEQ, string, int, float
	content = datatype(in_dict)

	# build dictionaries
	allsubdicts=unflatDict(in_dict)

	content.update(allsubdicts)

	return content


def datatype(in_dict):
	"""
	This function converts a specific string or a SQL type to 
	a python type.
	"""
	content={}
	allarrays={}
	for key,value in in_dict.items():
		a = re.findall('[^%s]+'%(sep,),key)
		if a[0] == 'ARRAY':
			name = a[1]
			if not allarrays.has_key(name):
				allarrays[a[1]]=None
		elif a[0] == 'SEQ':
			content[a[1]] = eval(value)
		elif not a[0] in ['SUBD', ]:
			content[key]=value
	for matrix in allarrays:
		dm={}
		for key,value in in_dict.items():
			l = re.findall('ARRAY%s%s' %(sep,matrix,),key)
			if l:
				dm.update({key:value})
		allarrays[matrix]=dict2matrix(dm)

	content.update(allarrays)
	return content
