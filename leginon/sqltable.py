#!/usr/bin/env python

# description:
# (name, type_code, display_size, internal_size, precision, scale, null_ok)

#  MySQL field types,  MySQLdb.FIELD_TYPE.:
#  BLOB, CHAR, DATE, DATETIME, DECIMAL, DOUBLE, ENUM, FLOAT, 
#  INT24, INTERVAL, LONG, LONGLONG, LONG_BLOB, MEDIUM_BLOB,
#  NEWDATE, NULL, SET, SHORT, STRING, TIME, TIMESTAMP, TINY, 
#  TINY_BLOB, VAR_STRING, YEAR

import sqlstr

class ColumnSpec(dict):
	"""
	ColumnSpec is a dictionary describing one column of a table.
	The keys of this dictionary match the result columns of 
	a 'describe table' query.
	"""
	def __init__(self, initdict=None):
		dict.__init__(self)

		self.update({'Field':None, 'Type':None, 'Null':None, 
			'Key':None, 'Default':None, 'Extra':None})
		if initdict:
			self.update(initdict)

	def create_definition(self):
		kwargs = {}
		kwargs['name'] = self['Field']
		kwargs['type'] = self['Type']

		if self['Null'] == 'YES':
			kwargs['null'] = 1
		else:
			kwargs['null'] = 0

		if self['Key'] == 'PRI':
			kwargs['primary'] = 1

		kwargs['default'] = self['Default']

		if self['Extra'] == 'auto_increment':
			kwargs['auto'] = 1
		else:
			kwargs['auto'] = 0

		return sqlstr.create_definition(**kwargs)
		

class SqlTable(object):
	def __init__(self, db, tablename):
		self.db = db
		self.name = tablename
		self.columns = []

	def _add_col(self, columnspec):
		self.columns.append(columnspec)

	def _del_col(self, delcol):
		coltype = type(delcol)
		if coltype == int:
			del(self.columns[delcol])
		if coltype == ColumnSpec:
			self.columns.remove(delcol)
		if coltype == str:
			for col in self.columns:
				if col['Field'] == delcol:
					self.columns.remove(col)

	def _create(self):
		"""create the table from my description"""
		# make list of create_definitions
		cdefs = []
		for col in self.columns:
			cdefs.append(col.create_definition())
		create_str = sqlstr.create_table(self.name, cdefs)
		c = self.db.cursor()
		c.execute(create_str[0], create_str[1])

		self._verify()

	def _describe(self):
		desc,args = sqlstr.describe(self.name)
		c = self.db.cursor()
		c.execute(desc)
		rows = c.fetchall()
		info = c.description
		
		dictlist = []
		for row in rows:
			d = {}
			for i in range(len(info)):
				key = info[i][0]
				value = row[i]
				d[key] = value
			dictlist.append(d)
		return dictlist

	def _verify(self, updateself=None):
		"""verify self.columns matches table description"""

		dlist = self._describe()

		if updateself:
			self.columns = []
			for d in dlist:
				c = ColumnSpec(d)
				self.columns.append(c)

		if len(self.columns) != len(dlist):
			raise RuntimeError, 'verify error'
		for i in range(len(dlist)):
			mycol = self.columns[i]
			dbcol = dlist[i]
			if mycol['Field'] != dbcol['Field']:
				raise RuntimeError, 'verify error'
			### add more comparisons here


if __name__ == '__main__':
	import MySQLdb
	db = MySQLdb.connect(db = 'jimtest', passwd='jimbo5')

	cd1 = ColumnSpec()
	cd1.update({'Field': 'id', 'Type': 'int'})
	cd2 = ColumnSpec()
	cd2.update({'Field': 'junk2', 'Type': 'varchar(20)'})

	s = SqlTable(db,'first')
	s._add_col(cd1)
	s._add_col(cd2)
	s._create()
	#s._verify(updateself=1)

	print 'columns', s.columns
