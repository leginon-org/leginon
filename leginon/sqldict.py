"""
sqldict: 

This creates a database interface which works pretty much like a
Python dictionary. 

>>> from sqldict import *
>>> dbc = MySQLdb.connect(host='localhost', db='test', user='anonymous', passwd='')
>>> db = SQLDict(dbc)

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
...     indices = [ ('Name', ['Name']), ('NameMag', ['Name', 'Mag']) ]
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
import MySQLdb

import string
from types import *

class SQLDict:

    """SQLDict: An object class which implements something resembling
    a Python dictionary on top of an SQL DB-API database."""

    def __init__(self, db):

	"""Create a new SQLDict object.
	db: an SQL DB-API database connection object"""
	self.db = db

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

	def __init__(self, db, table, columns):

	    """Construct a new table definition. Don't invoke this
	    directly. Use Table method of SQLDict instead."""

	    self.db = db
	    self.table = table
	    self.columns = tuple(map(lambda col: sqlexpr.Field(self.table,col), columns))

	def select(self, WHERE=''):

	    """Execute a SELECT command based on this Table and Index. The
	    required argument i is a tuple containing the values to match
	    against the index columns. A string containing a WHERE clause
	    should be passed along, but this is technically optional. The
	    WHERE clause must have the same number of value placeholders
	    (?) as there are values in i. Returns a _Cursor object for the
	    matched rows.

	    Usually you don't need to call select() directly; this is done
	    by the indexing operations (Index.__getitem__)."""

	    c = self.cursor()
	    q = sqlexpr.Select(items=self.columns, table=self.table, where=WHERE).sqlRepr()
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

	    def __init__(self, table, indices, WHERE):
		self.table = table
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
		return self.table.select(WHERE=w)

	    def __delitem__(self, i):
		"""Delete items in the database matching i."""
		if type(i) == ListType: i = tuple(i)
		elif type(i) != TupleType: i = (i,)
		w = sqlexpr.AND_EQUAL(zip(self.fields,i))
		return self.table.delete(i, WHERE=w)


	def Index(self, indices=[], WHERE=''):

	    """Create an index definition for this table.

	    Usage: db.table.Index(indices)
	    Where: indices   = tuple or list of column names to key on
		   WHERE     = optional WHERE clause.
		   WHERE not implemented YET...

	    """

	    return self._Index(self, indices, WHERE)

	class _Cursor:

	    """A subclass (shadow class?) of a cursor object which knows how to
	    load the tuples returned from the database into a more interesting
	    object."""

	    def __init__(self, db, load):
		self.cursor = db.cursor()
		self.load = load

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


	def cursor(self):
	    """Returns a new _Cursor object which is load-aware and
	    otherwise behaves normally."""
	    return self._Cursor(self.db, self.load)


    def Table(self, table, columns):

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
	loader = lambda t, s=self.__class__: apply(s, t)
	setattr(t, 'load', loader)
	for indexname, columns in self.indices:
	    setattr(t, indexname, t.Index(columns))
	return t

