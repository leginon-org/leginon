#!/usr/bin/env python

#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#

"""
sqlexpr.py: Build SQL expressions

"""

########################################
## Constants
########################################

class VersionError(Exception):
	pass

True, False = (1==1), (0==1)

########################################
## Quoting
########################################

sqlStringReplace = [
	('\\', '\\\\'),
	('\'', '\\\''),
	('\000', '\\0'),
	('\b', '\\b'),
	('\n', '\\n'),
	('\r', '\\r'),
	('\t', '\\t'),
	]

try:
	try:
		import mx.DateTime.ISO
		origISOStr = mx.DateTime.ISO.strGMT
		from mx.DateTime import DateTimeType
	except ImportError:
		import DateTime.ISO
		origISOStr = DateTime.ISO.strGMT
		from DateTime import DateTimeType
except ImportError:
	origISOStr = None
	DateTimeType = None

import re
import string
import sqldict
import MySQLdb
import newdict
import cPickle
import dbconfig

def backquote(inputstr):
		"""
		surround a string with backquotes
		"""
		return '`' + inputstr + '`'

def isoStr(val):
	"""Gets rid of time zone information"""
	val = origISOStr(val)
	if val.find('+') == -1:
		return val
	else:
		return val[:val.find('+')]

def sqlRepr(obj):
	if isinstance(obj, SQLExpression):
		return obj.sqlRepr()
	elif isinstance(obj, basestring):
		for orig, repl in sqlStringReplace:
			obj = str(obj.replace(orig, repl))
		return "'%s'" % obj
	elif isinstance(obj, bool):
		return repr(int(obj))
	elif isinstance(obj, (int,long)):
		return repr(int(obj))
	elif isinstance(obj, float):
		return repr(obj)
	elif DateTimeType is not None and isinstance(obj, DateTimeType):
		return "'%s'" % isoStr(obj)
	elif obj is None:
		return "NULL"
	elif isinstance(obj, (tuple, list)):
		return "(%s)" % ", ".join(map(sqlRepr, obj))
	else:
		raise ValueError, "Unknown SQL builtin type: %s for %s" % \
			  (type(obj), obj)


########################################
## Expression generation
########################################

class SQLExpression:
	def __add__(self, other):
		return SQLOp("+", self, other)
	def __radd__(self, other):
		return SQLOp("+", other, self)
	def __sub__(self, other):
		return SQLOp("-", self, other)
	def __rsub__(self, other):
		return SQLOp("-", other, self)
	def __mul__(self, other):
		return SQLOp("*", self, other)
	def __rmul__(self, other):
		return SQLOp("*", other, self)
	def __div__(self, other):
		return SQLOp("/", self, other)
	def __rdiv__(self, other):
		return SQLOp("/", other, self)
	def __pos__(self):
		return SQLPrefix("+", self)
	def __neg__(self):
		return SQLPrefix("-", self)
	def __pow__(self, other):
		return SQLConstant("POW")(self, other)
	def __rpow__(self, other):
		return SQLConstant("POW")(other, self)
	def __abs__(self):
		return SQLConstant("ABS")(self)
	def __mod__(self, other):
		return SQLConstant("MOD")(self, other)
	def __rmod__(self, other):
		return SQLConstant("MOD")(other, self)

	def __lt__(self, other):
		return SQLOp("<", self, other)
	def __le__(self, other):
		return SQLOp("<=", self, other)
	def __gt__(self, other):
		return SQLOp(">", self, other)
	def __ge__(self, other):
		return SQLOp(">=", self, other)
	def __eq__(self, other):
		return SQLOp("=", self, other)
	def __ne__(self, other):
		return SQLOp("<>", self, other)

	def __and__(self, other):
		return SQLOp("AND", self, other)
	def __rand__(self, other):
		return SQLOp("AND", other, self)
	def __or__(self, other):
		return SQLOp("OR", self, other)
	def __ror__(self, other):
		return SQLOp("OR", other, self)
	def __invert__(self):
		return SQLPrefix("NOT", self)

	def __call__(self, *args):
		return SQLCall(self, args)

	def __repr__(self):
		return self.sqlRepr()
	def __str__(self):
		return self.sqlRepr()

	def __cmp__(self, other):
		raise VersionError, "Python 2.1+ required"
	def __rcmp__(self, other):
		raise VersionError, "Python 2.1+ required"

	def startswith(self, s):
		return STARTSWITH(self, s)
	def endswith(self, s):
		return ENDSWITH(self, s)

	def components(self):
		return []

	def tablesUsed(self):
		return self.tablesUsedDict().keys()
	def tablesUsedDict(self):
		tables = {}
		for table in self.tablesUsedImmediate():
			tables[table] = 1
		for component in self.components():
			tables.update(tablesUsedDict(component))
		return tables
	def tablesUsedImmediate(self):
		return []

def tablesUsedDict(obj):
	if hasattr(obj, "tablesUsedDict"):
		return obj.tablesUsedDict()
	else:
		return {}

class SQLOp(SQLExpression):
	def __init__(self, op, expr1, expr2):
		self.op = op
		self.expr1 = expr1
		self.expr2 = expr2
	def sqlRepr(self):
		return "(%s %s %s)" % (sqlRepr(self.expr1), self.op, sqlRepr(self.expr2))
	def components(self):
		return [self.expr1, self.expr2]

class SQLCall(SQLExpression):
	def __init__(self, expr, args):
		self.expr = expr
		self.args = args
	def sqlRepr(self):
		return "%s%s" % (sqlRepr(self.expr), sqlRepr(self.args))
	def components(self):
		return [self.expr] + list(self.args)

class SQLPrefix(SQLExpression):
	def __init__(self, prefix, expr):
		self.prefix = prefix
		self.expr = expr
	def sqlRepr(self):
		return "%s %s" % (self.prefix, sqlRepr(self.expr))
	def components(self):
		return [self.expr]

class SQLConstant(SQLExpression):
	def __init__(self, const):
		self.const = const
	def sqlRepr(self):
		return self.const


########################################
## Namespaces
########################################

class TableSpace:
	def __getattr__(self, attr):
		return Table(attr)

class Table(SQLExpression):
	def __init__(self, tableName):
		self.tableName = tableName
	def __getattr__(self, attr):
		return Field(self.tableName, attr)
	def sqlRepr(self):
		return str(self.tableName)

class SmartTable(Table):
	_capRE = re.compile(r'[A-Z]+')
	def __getattr__(self, attr):
		if self._capRE.search(attr):
			attr = attr[0] + self._capRE.sub(lambda m: '_%s' % m.group(0), attr[1:])
		return Table.__getattr__(self, attr)

class Field(SQLExpression):
	def __init__(self, tableName, fieldName):
		self.tableName = tableName
		self.fieldName = fieldName
	def sqlRepr(self):
		return tableStr(self.tableName) + "." + backquote(self.fieldName)
	def tablesUsedImmediate(self):
		return [self.tableName]

class ConstantSpace:
	def __getattr__(self, attr):
		return SQLConstant(attr)


########################################
## SQL Statements
########################################

class Show(SQLExpression):
	def __init__(self, items, table=None):
		self.table = table
		self.items = items

	def sqlRepr(self):
		show = "SHOW %s" % (self.items,)

		if self.table is not None:
			show += " FROM %s" % tableStr(self.table)

		return show

class Select(SQLExpression):
	def __init__(self, items, table=None, where=None, groupBy=None,
				 having=None, orderBy=None, limit=None):
		if type(items) is not type([]) and type(items) is not type(()):
			items = [items]
		self.items = items
		self.table = table
		self.whereClause = where
		self.groupBy = groupBy
		self.having = having
		self.orderBy = orderBy
		self.limit = limit

	def sqlRepr(self):
		select = "SELECT %s" % ", ".join(map(sqlRepr, self.items))

		tables = {}
		things = self.items

		for thing in things:
			if isinstance(thing, SQLExpression):
				tables.update(tablesUsedDict(thing))
		tables = tables.keys()
		if tables:
			select += " FROM %s" % ", ".join(tables)
		elif self.table:
			select += " FROM %s" % self.table
		
		if self.whereClause is not None:
			select += " WHERE %s" % sqlRepr(self.whereClause)
		if self.groupBy is not None:
			select += " GROUP BY %s" % sqlRepr(self.groupBy)
		if self.having is not None:
			select += " HAVING %s" % sqlRepr(self.having)
		if self.orderBy is not None:
			fields = self.orderBy['fields']
			sort = 'ASC'
			if self.orderBy.has_key('sort'):
				sort = self.orderBy['sort']
			fields = string.join(map(lambda id: sqlRepr(id), fields), ', ')
			select += " ORDER BY %s %s" % (fields, sort,)
		if self.limit is not None:
			select += " LIMIT %s" % sqlRepr(self.limit)
		return select

class SelectAll(SQLExpression):
	def __init__(self,table, where=None, groupBy=None,
		having=None, orderBy=None, limit=None):
		self.table = table
		self.whereClause = where
		self.groupBy = groupBy
		self.having = having
		self.orderBy = orderBy
		self.limit = limit

	def sqlRepr(self):
		select = "SELECT * " 

		select += " FROM %s" % (tableStr(self.table),)
		
		if self.whereClause is not None:
			select += " WHERE %s" % sqlRepr(self.whereClause)
		if self.groupBy is not None:
			select += " GROUP BY %s" % sqlRepr(self.groupBy)
		if self.having is not None:
			select += " HAVING %s" % sqlRepr(self.having)
		if self.orderBy is not None:
			fields = self.orderBy['fields']
			sort = 'ASC'
			if self.orderBy.has_key('sort'):
				sort = self.orderBy['sort']
			fields = string.join(map(lambda id: sqlRepr(id), fields), ', ')
			select += " ORDER BY %s %s" % (fields, sort,)
		if self.limit is not None:
			select += " LIMIT %s" % sqlRepr(self.limit)
		return select

class ColumnSpec(dict):
		"""
		ColumnSpec is a dictionary describing one column of a table.
		The keys of this dictionary match the result columns of 
		a 'describe table' query.
		"""
		def __init__(self, initdict=None):
				dict.__init__(self)

				self.update({'Field':None, 'Type':None, 'Null':None,
						'Key':None, 'Default':None, 'Extra':None, 'Index':None})
				if initdict:
						self.update(initdict)

		def create_key(self):
				keyargs = {}
				keyargs['index'] = self['Index']
				keyargs['name'] = self['Field']

				if self['Key'] in ('PRI', 'PRIMARY'):
						keyargs['primary'] = 1

				elif self['Key'] in ('UNI', 'UNIQUE'):
						keyargs['unique'] = 1

				elif self['Key'] in ('FULL', 'FULLTEXT'):
						keyargs['fulltext'] = 1

				return self.create_sql(**keyargs)

		def create_column(self):
				colargs = {}
				colargs['name'] = self['Field']
				colargs['type'] = self['Type']

				if self['Null'] == 'YES':
						colargs['null'] = 1
				else:
						colargs['null'] = 0

				colargs['default'] = self['Default']

				if self['Extra'] == 'auto_increment':
						colargs['auto'] = 1
				else:
						colargs['auto'] = 0

				return self.create_sql(**colargs)

		def create_sql(self, name=None, type=None, null=1, default=None, auto=None, primary=None, index=None, unique=None, fulltext=None):
			"""
			returns the proper sql syntax given the following params:
				index:   sequence of column names to index
					primary:  PRIMARY KEY
					index:  INDEX
					unique:  UNIQUE
					fulltext: FULLTEXT
				OR

				name:  column name
				type:  data type
				null:  0 = NOT NULL, 1 = NULL
				default:  default value
				auto:  1 = AUTO_INCREMENT
			"""

			sqlIndex_str = ''

			if name and type:
				pieces = []
				sql_args = []
				pieces.append(backquote(name))
				pieces.append(type)
				if null: 
					pieces.append('NULL')
				else:
					pieces.append('NOT NULL')
				if default:
					pieces.append('DEFAULT')
					pieces.append("%s" % default)
					sql_args.append(default)
				if auto:
					pieces.append('AUTO_INCREMENT')
				sql_str = string.join(pieces)
				return sql_str
			else:
				keys = []
				key_str = ''
				if unique:
					key_str += 'UNIQUE'
				if fulltext:
					key_str += 'FULLTEXT'

				key_str += ' KEY'

				if index:
					indexes = []
					for indexName in index:
						indexes.append(indexName)
					index_str = string.join(indexes, ',')
					keys.append(key_str+' '+backquote(name) +' (' + backquote(index_str) + ')')

				if primary:
					keys.append('PRIMARY KEY '+'('+ backquote(name) +')' )

				return string.join(keys)

class AlterTable(SQLExpression):
	''' ALTER TABLE `particle` ADD `fieldname` TEXT NOT NULL ;
	ALTER TABLE `particle` CHANGE `fieldname` `fieldname` TEXT NOT NULL 
	ALTER TABLE `particle` DROP `fieldname` 
	'''
	def __init__(self, table, column, operation):
		self.table = table
		self.column = column
		self.operation = operation

	def sqlRepr(self):
		str_null = "NOT NULL"
		if self.column.has_key('Null') and self.column['Null']=='YES':
			str_null = "NULL"
		default = ""
		if self.column.has_key('Default') and self.column['Default'] is not None:
			default = "DEFAULT '%s'" % (self.column['Default'])

		if not self.column:
			return ''
		elif self.operation=='DROP':
			alter = "ALTER TABLE %s %s %s" % (tableStr(self.table), self.operation, backquote(self.column['Field']))
		elif self.operation=='ADD':
			alter = "ALTER TABLE %s %s %s %s %s %s" % (tableStr(self.table), self.operation, backquote(self.column['Field']), self.column['Type'], default, str_null)
		elif self.operation=='CHANGE':
			alter = "ALTER TABLE %s %s %s %s %s %s %s" % (tableStr(self.table), self.operation, backquote(self.column['Field']), backquote(self.column['Field']), self.column['Type'], default, str_null)
		return alter

def tableStr(tableinfo):
	if isinstance(tableinfo, str):
		return backquote(tableinfo)
	else:
		return '.'.join(map(backquote, tableinfo))

class AlterTableIndex(SQLExpression):
	def __init__(self, table, column):
		self.table = table
		self.column = column

	def sqlRepr(self):
		if not self.column:
			return ''
		else:
			alter = "ALTER TABLE %s ADD INDEX (%s) " % (tableStr(self.table), backquote(self.column['Field']))
		return alter


class CreateTable(SQLExpression):
	def __init__(self, table, columns, type=None):
		self.table = table
		self.columns = columns
		self.type = type
	def sqlRepr(self):
		if not self.columns:
			return ''
		if self.type in ('BDB', 'HEAP', 'ISAM', 'InnoDB', 'MERGE', 'MRG_MyISAM', 'MyISAM'):
			type_str = " ENGINE=%s " % self.type
		else:
			type_str = " ENGINE=MyISAM" 

		create = "CREATE TABLE IF NOT EXISTS %s " % (tableStr(self.table),)
		keys = []
		fields = []

		for column in self.columns:
			fields.append(ColumnSpec(column).create_column())
			if ColumnSpec(column).create_key():
				keys.append(ColumnSpec(column).create_key())

		l = fields + keys
		create += '(' + string.join(l, ', ') + ')' + type_str
		return create

class Insert(SQLExpression):
	def __init__(self, table, valueList=None, values=None, template=None):
		self.template = template
		self.table = table
		if valueList:
			if values:
				raise TypeError, "You may only give valueList *or* values"
			self.valueList = valueList
		else:
			self.valueList = [values]
	def sqlRepr(self):
		if not self.valueList:
			return ''
		insert = "INSERT INTO %s" % (tableStr(self.table),)
		allowNonDict = True
		template = self.template
		if template is None and type(self.valueList[0]) is type({}):
			template = self.valueList[0].keys()
			allowNonDict = False
		if template is not None:
			f = map(backquote, template)
			insert += " (%s)" % ", ".join(f)
		first = True
		insert += " VALUES "
		for value in self.valueList:
			if first:
				first = False
			else:
				insert += ", "
			if type(value) is type({}):
				if template is None:
					raise TypeError, "You can't mix non-dictionaries with dictionaries in an INSERT if you don't provide a template (%s)" % repr(value)
				value = dictToList(template, value)
			elif not allowNonDict:
				raise TypeError, "You can't mix non-dictionaries with dictionaries in an INSERT if you don't provide a template (%s)" % repr(value)
			insert += "(%s)" % ", ".join(map(sqlRepr, value))
		return insert

def dictToList(template, dict):
	list = []
	for key in template:
		list.append(dict[key])
	if len(dict.keys()) > len(template):
		raise TypeError, "Extra entries in dictionary that aren't asked for in template (template=%s, dict=%s)" % (repr(template), repr(dict))
	return list

class Update(SQLExpression):
	def __init__(self, table, values, template=None, where=None):
		self.table = table
		self.values = values
		self.template = template
		self.whereClause = where
	def sqlRepr(self):
		update = "%s %s" % (self.sqlName(), self.table)
		update += " SET"
		first = True
		if self.template is not None:
			for i in range(len(self.template)):
				if first:
					first = False
				else:
					update += ","
				update += " %s=%s" % (self.template[i], sqlRepr(self.values[i]))
		else:
			for key, value in self.values.items():
				if first:
					first = False
				else:
					update += ","
				update += " %s=%s" % (key, sqlRepr(value))
		if self.whereClause is not None:
			update += " WHERE %s" % repr(self.whereClause)
		return update

	def sqlName(self):
		return "UPDATE"

class Delete(SQLExpression):
	"""To be safe, this will signal an error if there is no where clause,
	unless you pass in where=None to the constructor."""
	def __init__(self, table, where=None):
		self.table = table
		if where is None:
			raise TypeError, "You must give a where clause or pass in None to indicate no where clause"
		self.whereClause = where
	def sqlRepr(self):
		if self.whereClause is None:
			return "DELETE FROM %s" % self.table
		return "DELETE FROM %s WHERE %s" \
			   % (self.table, sqlRepr(self.whereClause))

class Replace(Update):
	def sqlName(self):
		return "REPLACE"

class DropTable(SQLExpression):
	def __init__(self, table):
		self.table = table

	def sqlRepr(self):
			return "DROP TABLE %s" % self.table

class Describe(SQLExpression):
	def __init__(self, table):
		self.table = table

	def sqlRepr(self):
			return "DESCRIBE %s" % tableStr(self.table,)

########################################
## SQL Builtins
########################################

def AND_LIKE(list_args):
	e = 'LIKE(arg[0], arg[1])'
	new_args = []
	for arg in list_args:
		new_args.append(eval(e))
	return AND(*new_args)

def AND_EQUAL(list_args):
	return AND_OP(list_args, '==')

def AND_IS(list_args):
	e = 'IS(arg[0], arg[1])'
	new_args = []
	for arg in list_args:
		new_args.append(eval(e))
	return AND(*new_args)

def AND_OP(list_args, op):
	e = 'arg[0] %s arg[1]' % op
	new_args = []
	for arg in list_args:
		new_args.append(eval(e))
	return AND(*new_args)

def AND(*ops):
	if len(ops) == 0:
		return ''
	elif len(ops) == 1:
		return ops[0]
	else:
		op1 = ops[0]
		ops = ops[1:]
		return SQLOp("AND", op1, AND(*ops))

def OR(*ops):
	op1 = ops[0]
	ops = ops[1:]
	if ops:
		return SQLOp("OR", op1, OR(*ops))
	else:
		return op1

def NOT(op):
	return SQLPrefix("NOT", op)

def IS(expr, string):
	return SQLOp("IS", expr, string)

def IN(item, list):
	return SQLOp("IN", item, list)

def LIKE(expr, string):
	return SQLOp("LIKE", expr, string)

def STARTSWITH(expr, string):
	return SQLOp("LIKE", expr, _likeQuote(string) + '%')

def ENDSWITH(expr, string):
	return SQLOp("LIKE", expr, '%' + _likeQuote(string))

def CONTAINSSTRING(expr, string):
	return SQLOp("LIKE", expr, '%' + _likeQuote(string) + '%')

def _likeQuote(s):
	return s.replace('%', '%%')

########################################
## Multiple Table Queries functions
########################################


def selectAllFormat(field):
	return "SELECT %s.* " % backquote(field)

def fromFormat(dataclass, alias=None):
	dbname = dbconfig.getConfig(dataclass.__module__)['db']
	tablename = dataclass.__name__
	sqlfrom = "FROM %s.%s " % (backquote(dbname), backquote(tablename))
	if alias is not None:
		sqlfrom += "AS %s " % backquote(alias)
	return sqlfrom

def joinFormat(field, joinTable):
	dataclass = joinTable['class']
	dbname = dbconfig.getConfig(dataclass.__module__)['db']
	dbname = backquote(dbname)
	tablename = backquote(joinTable['class'].__name__)
	alias = backquote(joinTable['alias'])
	sqljoin = " JOIN %s.%s AS %s ON (%s = %s.%s) " % (dbname, tablename, alias, field, alias, backquote('DEF_ID'))
	return sqljoin

def whereFormat(in_dict):
	first = True
	whereDict = sqldict.flatDict(in_dict['where'])
	alias = in_dict['alias']
	wherelist = []
	for key, value in whereDict.items():
		if type(value) in [tuple, list]:
			key = sqldict.seq2sqlColumn(key)
		elif type(value) is bool:
			value = int(value)
		elif isinstance(value,newdict.AnyObject):
			key = sqldict.object2sqlColumn(key)
			value = cPickle.dumps(value.o, cPickle.HIGHEST_PROTOCOL)
		evalue = str(value)
		if key=="DEF_timelimit":
		#	For MySQL 4.1.1 or greater
		#	sqlwhere = ''' %s.%s >= ADDTIME(NOW(), '%s') ''' % (backquote(alias), backquote('DEF_timestamp'), evalue)
			sqlwhere = ''' %s.%s >= DATE_ADD(now(), INTERVAL '%s' DAY_SECOND) ''' % (backquote(alias), backquote('DEF_timestamp'), evalue)
		else:
			sqlwhere = ''' %s.%s="%s" ''' % (backquote(alias), backquote(key), evalue)
		wherelist.append(sqlwhere)
	wherestr = ' AND '.join(wherelist)
	return wherestr

def whereFormatSimple(in_dict):
	first = True
	whereDict = sqldict.flatDict(in_dict)
	wherelist = []
	for key, value in whereDict.items():
		if type(value) in [tuple, list]:
			key = sqldict.seq2sqlColumn(key)
		elif isinstance(value,newdict.AnyObject):
			key = sqldict.object2sqlColumn(key)
		evalue = str(value)
		wherelist.append(''' %s="%s" ''' % (backquote(key), evalue))
	wherestr = ' AND '.join(wherelist)
	return wherestr

def orderFormat(alias):
	#sqlorder = "ORDER BY %s.DEF_timestamp DESC " % backquote(alias)
	sqlorder = "ORDER BY %s.DEF_id DESC " % backquote(alias)
	return sqlorder 

def limitFormat(limit):
	if limit is None:
		sqllimit = ""
	else:
		sqllimit = "LIMIT %d " % (limit,)
	return sqllimit

########################################
## Global initializations
########################################

table = TableSpace()
const = ConstantSpace()
func = const

########################################
## Testing
########################################

if __name__ == "__main__":
	tests = """
>>> AND(table.preset.Mag == 66000, table.preset.Defocus > -200)
>>> AND(LIKE(table.preset.name, "MyPreset"), IN(table.Mag.zip, [600, 1600, 6600]))
>>> Select([table.preset.name, table.preset.Defocus], where=LIKE(table.preset.name, "%square%"))
>>> Insert(table.preset, [{'Defocus': -20, 'Name': 'foc', 'Mag': 66000, 'Dose': 0.67542999999999997}, {'Defocus': -20, 'Name': 'hole', 'Mag': 6000, 'Dose': 0.67542999999999997}])
>>> Insert(table.preset, [("expo1", 66000, -200, 0.867543), ("expo2", 66000, -2000, 0.867543)], template=('Name', 'Mag', 'Defocus', 'Dose'))
>>> Delete(table.preset, where="expo"==table.preset.name)
>>> Update(table.preset, {"lastModified": const.NOW()})
>>> Replace(table.preset, ["expo1", 66000, -200, 0.867543], template=('name', 'Mag', 'Defocus', 'Dose'))
>>> CreateTable('myTable2', [{'Field': 'id', 'Type': 'int(16) ', 'Key': 'PRIMARY', 'Extra':'auto_increment'}, {'Field': 'filename', 'Type': 'VARCHAR(50)', 'Key': 'INDEX', 'Index': ['filename']}, {'Field': 'filenameFR', 'Type': 'VARCHAR(50)', 'Key': 'INDEX', 'Index': ['filename']}], 'ISAM')
>>> CreateTable('PEOPLE', [{'Field': 'id', 'Type': 'int(16)', 'Key': 'PRIMARY', 'Extra':'auto_increment'}, {'Field': 'Name', 'Type': 'VARCHAR(50)'}, {'Field': 'Address', 'Type': 'VARCHAR(50)'}, {'Field': 'City', 'Type': 'VARCHAR(50)'}, {'Field': 'State', 'Type': 'VARCHAR(50)'}])
>>> Replace("tablename", ["expo1", 66000, -200, 0.867543], template=('name', 'Mag', 'Defocus', 'Dose'))
>>> Select([table.preset.name, const.count(table.preset.Id)], where=LIKE(table.preset.name, "%square%"))
>>> DropTable(table.preset)
>>> CreateTable('OBJECT', [{'Field': 'Id', 'Type': 'int(20) unsigned', 'Key': 'PRIMARY', 'Extra':'auto_increment'}, {'Field': 'hash', 'Type': 'VARCHAR(64)', 'Key': 'UNIQUE', 'Index': ['hash']}, {'Field': 'objectKey', 'Type': 'varchar(50)', 'Key': 'UNIQUE', 'Index': ['objectKey(50)'], 'Null' : 'YES', 'Default': 'Denis'}, {'Field': 'object', 'Type': 'longblob'}, {'Field': 'objectKeyString', 'Type': 'text'}, {'Field': 'objectString', 'Type': 'text'},{'Field':'timestamp','Type':'timestamp','Null':'YES', 'Key':'INDEX'}])
>>> SelectAll(table.PRESET, where=LIKE(table.PRESET.name, "%square%"), orderBy=None)
>>> Select([table.preset.name, table.preset2.Defocus], where=AND(LIKE(table.preset.name, "%square%"), table.preset.id==table.preset2.id), orderBy={'fields':('id', 'name'), 'sort':'DESC'})
>>> Show('Index', table.PRESET)
"""
	for expr in tests.split('\n'):
		if not expr.strip(): continue
		print expr
		if expr.startswith('>>> '):
			expr = expr[4:]
			print repr(eval(expr))

