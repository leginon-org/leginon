#!/usr/bin/env python

#### right now I am assuming that presetlist is a sequence of ColumnSpecs
#### but may be more useful to simplify to only {'Field':..., 'Type':...}
#### for more consistency between all presetss

import re
import sqltable
import sqlstr

class Error(Exception):
	def __init__(self, value = None):
		if value:
			self.value = value
		else:
			self.value = ''
	def __str__(self):
		return `self.value`

class PresetTypeError(Error):
	def __init__(self, value=None):
		Error.__init__(self,value)
		self.value = 'illegal preset type'

class PresetNameError(Error):
	def __init__(self, value=None):
		Error.__init__(self,value)
		self.value = 'illegal preset name'

class NoPresetError(Error):
	def __init__(self, value=None):
		Error.__init__(self,value)
		self.value = 'query returned no presets'

def mtype2ptype(mysqltype):
	mtype = mysqltype
	mtype2 = mysqltype.upper()

	if mtype2.find('INT') == 0:
		ptype = int
	if mtype2.find('FLOAT') == 0:
		ptype = float
	if mtype2.find('VARCHAR') == 0:
		ptype = str
	if mtype2.find('TINYINT(1)') == 0:
		ptype = (0,1)
	if mtype2.find('ENUM') == 0:
		tupstr = re.search('enum(.*)', mtype, re.IGNORECASE).group(1)
		ptype = eval(tupstr)

	return ptype

def ptype2mtype(presettype):
	if type(presettype) == type:
		if presettype == int:
			mysqltype = 'INT'
		if presettype == float:
			mysqltype = 'FLOAT'
		if presettype == str:
			mysqltype = 'VARCHAR(255)'
	elif type(presettype) == tuple or type(presettype) == list:
		pt = tuple(presettype)
		if pt == (0,1):
			mysqltype = 'TINYINT(1)'
		else:
			mysqltype = 'ENUM' + `pt`
	else:
		raise PresetTypeError

	return mysqltype


class PresetTable(sqltable.SqlTable):
	def __init__(self, db, name, presetlist=()):
		sqltable.SqlTable.__init__(self, db, name)

		if not presetlist:
			self._verify(updateself=1)
			return

		### every presettable will have the following three columns:
		cd1 = sqltable.ColumnSpec()
		cd1.update({'Field':'id', 'Type':'int', 'Key':'PRI', 'Extra':'auto_increment'})
		self._add_col(cd1)

		cd2 = sqltable.ColumnSpec()
		cd2.update({'Field':'timestamp', 'Type':'timestamp'})
		self._add_col(cd2)

		cd3 = sqltable.ColumnSpec()
		cd3.update({'Field':'leginonid', 'Type':'tinyblob'})
		self._add_col(cd3)

		### one column for every preset
		for preset in presetlist:
			self._add_col(preset)

		self._create()

	def query(self, leginonid, keys=None):
		"""
		query(keys)
		get the most recent row from preset table
		if the sequence keys is provide, only those will be returned
		otherwise all keys will be returned
		"""

		if keys:
			presetkeys = keys
		else:
			presetkeys = self.presetnames()

		sql_str,sql_args = sqlstr.select(tablename=self.name, 
			fields=presetkeys, orderby=('id',),
			wheredict = {'leginonid': ('=',leginonid)},
			orderdesc=1, limit=(1,))

		c = self.db.cursor()
		c.execute(sql_str, sql_args)
		rows = c.fetchall()
		desc = c.description

		if len(rows) != 1:
			raise NoPresetError
		else:
			vals = rows[0]

		presetdict = {}
		for i in range(len(vals)):
			val = vals[i]
			key = desc[i][0]
			presetdict[key] = val

		return presetdict

	def update(self, newpresets):
		## validate the keys in newpresets
		mypresetnames = self.presetnames()
		for key in newpresets:
			if key not in mypresetnames:
				raise PresetNameError

		legid = newpresets['leginonid']
		## get current presets for update
		try:
			curpresets = self.query(legid)
			curpresets.update(newpresets)
		except NoPresetError:
			curpresets = newpresets

		sql_str, sql_args = sqlstr.insert(self.name, curpresets)
		c = self.db.cursor()
		c.execute(sql_str, sql_args)

	def presetcols(self):
		dlist = self._describe()
		plist = []
		for d in dlist:
			if d['Field'] not in ('id', 'timestamp'):
				plist.append(d)
		return plist

	def presetnames(self):
		"""return a sequence of preset names"""
		names = []
		for presetcol in self.presetcols():
			names.append(presetcol['Field'])
		return tuple(names)

class Presets(object):
	"""
	Presets(db, presetspec)
	   db - an open database object
	   presetspec - sequence of (name, type) pairs
	a Presets instance behaves like a dictionary in that is has the
	__getitem__, __setitem__, keys, and update methods

	To get the dict representation of this instance, use the dict() method
	"""
	def __init__(self, db, tablename, presetspec=()):
		presetcols = ()
		for presetname,presettype in presetspec:
			mysqltype = ptype2mtype(presettype)
			c = sqltable.ColumnSpec({'Field':presetname, 'Type':mysqltype})
			presetcols = presetcols + (c,)
		
		self.presettable = PresetTable(db, tablename, presetcols)

	def __getitem__(self, leginonid):
		return self.presettable.query(leginonid)

	def __setitem__(self, leginonid, presetdict):
		d = dict(presetdict)
		d['leginonid'] = leginonid
		self.presettable.update(d)

	def update(self, newdict):
		self.presettable.update(newdict)

	def keys(self):
		return self.presettable.presetnames()

	def dict(self):
		try:
			d = self.presettable.query()
		except NoPresetError:
			d = None
		return d

	def presetspec(self):
		presetcols = self.presettable.presetcols()
		ps = []
		for presetcol in presetcols:
			name = presetcol['Field']
			mtype = presetcol['Type']
			ptype = mtype2ptype(mtype)
			ps.append( (name,ptype) )
		return tuple(ps)

#if 0:
if __name__ == '__main__':
	import MySQLdb
	from sqltable import ColumnSpec
	db = MySQLdb.connect(db='jimtest', user='pulokas', passwd='jimbo5')
	
	presetspec = (('x',int), ('y',int), ('z',int))
	mypresets1 = Presets(db, 'mypresets2', presetspec)

	mypresets1.update({'leginonid':'asdfasdf','x':1, 'y':2, 'z':3})

	print 'query', mypresets1['asdfasdf']

if 0:
#if __name__ == '__main__':
	import MySQLdb
	from sqltable import ColumnSpec
	db = MySQLdb.connect(db='jimtest', user='pulokas', passwd='jimbo5')
	
	preset1 = ColumnSpec()
	preset1.update({'Field':'x', 'Type':'int'})
	preset2 = ColumnSpec()
	preset2.update({'Field':'y', 'Type':'int'})
	preset3 = ColumnSpec()
	preset3.update({'Field':'z', 'Type':'int'})

	mypresets1 = PresetTable(db, 'mypresets1', (preset1,preset2,preset3))

	mypresets1.update({'leginonid':'asdfasdf','x':1, 'y':2, 'z':3})

	print 'query', mypresets1.query('asdfasdf')



