"""
The functions in the module each return a tuple:  (sql_str, sql_args)
sql_str is a string that can be passed to a cursor's execute method and
sql_args in a list of arguments for replacement into sql_str
"""


import string

#	create_definition:
#	col_name type [NOT NULL | NULL] [DEFAULT default_value] [AUTO_INCREMENT]
#	[PRIMARY KEY] [reference_definition]
#	or    PRIMARY KEY (index_col_name,...)
#	or    KEY [index_name] (index_col_name,...)
#	or    INDEX [index_name] (index_col_name,...)
#	or    UNIQUE [INDEX] [index_name] (index_col_name,...)
#	or    FULLTEXT [INDEX] [index_name] (index_col_name,...)
#	or    [CONSTRAINT symbol] FOREIGN KEY [index_name] (index_col_name,...) [reference_definition]
#	or    CHECK (expr)


def backquote(inputstr):
	"""
	surround a string with backquotes
	"""
	return '`' + inputstr + '`'

def create_definition(name=None, type=None, null=1, default=None, auto=None, primary=None, index=None):
	"""
	returns the proper sql syntax given the following params:
		index:   sequence of column names to index
			OR
		name:  column name
		type:  data type
		null:  0 = NOT NULL, 1 = NULL
		default:  default value
		auto:  1 = AUTO_INCREMENT
		primary:  PRIMARY KEY
	"""

	if index:
		pieces = []
		sql_args = []
		for name in index:
			pieces.append('%s')
			sql_args.append(name)
		sql_str = string.join(pieces, ',')
		sql_str = 'INDEX (' + sql_str + ')'

	elif name and type: 
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
			pieces.append('%s')
			sql_args.append(default)
		if auto:
			pieces.append('AUTO_INCREMENT')
		if primary:
			pieces.append('PRIMARY KEY')
		sql_str = string.join(pieces)

	else:
		sql_str = ''
		sql_args = []

	return (sql_str, tuple(sql_args))

def create_table(tablename, create_defs):
	cd_pieces = []
	cd_args = []
	for cd in create_defs:
		cd_pieces.append(cd[0])
		cd_args +=  cd[1]
	create_defs_str = '(' + string.join(cd_pieces, ', ') + ')'

	pieces = []
	sql_args = []
	pieces.append('CREATE TABLE IF NOT EXISTS')
	pieces.append(backquote(tablename))
	pieces.append(create_defs_str)
	sql_args += cd_args
	sql_str = string.join(pieces)
	return (sql_str, tuple(sql_args))

def insert(tablename, setdict):
	sql_args = []
	sql_str = 'INSERT ' + backquote(tablename) + ' SET '
	pieces = []
	for key in setdict:
		pieces.append(backquote(key) + ' = %s')
		sql_args.append(setdict[key])
	sql_str += string.join(pieces, ', ')
	return (sql_str, tuple(sql_args))

def update(tablename, setdict, wheredict):
	sql_args = []
	pieces = []
	pieces.append('UPDATE')
	pieces.append(backquote(tablename))
	pieces.append('SET')

	setpieces = []
	for key in setdict:
		setpieces.append(backquote(key) + ' = %s')
		sql_args.append(setdict[key])
	pieces.append(string.join(setpieces,', '))

	if wheredict:
		pieces.append('WHERE')
		wherelist = []
		for key in wheredict:
			cond = wheredict[key][0]
			value = wheredict[key][1]
			wherelist.append(backquote(key) + cond + '%s')
			sql_args.append(value)
			print 'value', value
		wherestr = string.join(wherelist, ' AND ')
		pieces.append(wherestr)

	sql_str = string.join(pieces)

	return (sql_str, tuple(sql_args))

def select(tablename, fields=(), wheredict={}, orderby=(), orderdesc=None, limit=()):
	sql_args = []
	pieces = []
	pieces.append('SELECT')
	if fields:
		newfields = map(backquote, fields)
		fieldstr = string.join(newfields, ', ')
	else:
		fieldstr = '*'
	pieces.append(fieldstr)
	pieces.append('FROM')
	pieces.append(backquote(tablename))

	if wheredict:
		pieces.append('WHERE')
		wherelist = []
		for key in wheredict:
			cond = wheredict[key][0]
			value = wheredict[key][1]

			wherelist.append(backquote(key) + cond + '%s')
			sql_args.append(value)
		wherestr = string.join(wherelist, ' AND ')
		pieces.append(wherestr)

	if orderby:
		pieces.append('ORDER BY')
		neworderby = map(backquote, orderby)
		orderstr = string.join(neworderby, ', ')
		pieces.append(orderstr)
		if orderdesc:
			pieces.append('DESC')
			

	if limit:
		pieces.append('LIMIT')
		limlist = []
		for lim in limit:
			limlist.append('%s')
			sql_args.append(lim)
		pieces.append(string.join(limlist, ','))

	sql_str = string.join(pieces)

	return (sql_str, tuple(sql_args))

def describe(tablename):
	sql_str = 'DESCRIBE ' + backquote(tablename)
	return (sql_str,())
