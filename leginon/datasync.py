#!/usr/bin/env python
"""
datasync.py:
	- update all table fields with NULL
	- update FocusSettingData
	- generate SQL queries to update the current database state 
		with Data Classes defined in data.py

"""
import data
import dbdatakeeper
import sqldb
import leginonconfig
import sys
		
### use a user with alter/drop/update privileges
dbparams = {
	'host':leginonconfig.DB_HOST,
	'user':leginonconfig.DB_USER,
	'db':leginonconfig.DB_NAME,
	'passwd':leginonconfig.DB_PASS
}

## modify you db params here
## dbparams['host']='stratocaster'
## dbparams['db']='dbemdata'

db = dbdatakeeper.DBDataKeeper(**dbparams)

dataclasses = {}


tables = []
tableclass = []
notableclass = []
dataclasses={}

## get tables
## dbc = sqldb.sqlDB(host='stratocaster')
dbc = sqldb.sqlDB(**dbparams)
r = dbc.selectall('show tables')
dbc.close()

for d in r:
	for key,value in d.items():
		tables.append(value)

## set default NULL
dbc = sqldb.sqlDB(**dbparams)

for table in tables:
	q = "SHOW FIELDS FROM `%s`" % (table)
	r = dbc.selectall(q)
	qalter = "ALTER TABLE `%s` " % (table)
	changes = []
	for d in r:
		if d['Field'] in ('DEF_id', 'DEF_timestamp',):
			continue
		if d['Null'] != 'YES':
			changes.append( "CHANGE `%s` `%s` %s NULL " % (d['Field'], d['Field'], d['Type'],))

	if changes:
		qalter += ", ".join(changes)
		dbc.execute(qalter)

## update FocusSettingData 
table = 'FocusSettingData'
q = "ALTER TABLE `FocusSettingData` CHANGE `beam tilt` `tilt` DOUBLE NULL" 
try:
	r = dbc.execute(q)
except:
	pass

## stig defocus max >0 AND stig defocus min >0
q = "UPDATE `FocusSettingData` SET `stig defocus max`=ABS(`stig defocus max`), `stig defocus min`=ABS(`stig defocus min`)"
try:
	r = dbc.execute(q)
except:
	pass

dbc.close()

## check if table is a Data class
for table in tables:
	try:
		cls = getattr(data, table)
		dataclasses[table] = cls
		tableclass.append(table)
	except:
		print "-- Not a class: ",table
		notableclass.append(table)
		pass


## check Class definition
for table,value in dataclasses.items():
	instance = db.dbd.sqlColumns2Data(table)
	print "--" 
	print "-- Table: ",table
	addcolumns, dropcolumns, queries = db.diffData(instance)
	for s in addcolumns:
		print "--  UPDATE `%s`" % (s['Field'],)
	for s in dropcolumns:
		print "--  DROP `%s`" % (s['Field'],)
	print "--" 
	for s in queries :
		print s
	print "\n"
