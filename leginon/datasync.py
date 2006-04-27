#!/usr/bin/env python
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
dbparams['host']='stratocaster'
dbparams['db']='dbemtest'

db = dbdatakeeper.DBDataKeeper(**dbparams)

dataclasses = {}
"""

FocusSettingData
	stig defocus max >0
	stig defocus min >0
	rename `beam tilt` `tilt`
"""

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
	for d in r:
		if d['Field'] in ('DEF_id', 'DEF_timestamp',):
			continue
		if d['Null'] is not 'YES':
			qalter = "ALTER TABLE `%s` CHANGE `%s` `%s` %s NULL " % (table, d['Field'], d['Field'], d['Type'],)
			dbc.execute(qalter)

## update FocusSettingData 
table = 'FocusSettingData'
q = "ALTER TABLE `%s` CHANGE `beam tilt` `tilt` DOUBLE NULL" % (table,)
try:
	r = dbc.execute(q)
except:
	pass

## stig defocus max >0 AND stig defocus min >0
q = "UPDATE `%s` SET `stig defocus max`=ABS(`stig defocus max`), `stig defocus min`=ABS(`stig defocus min`)"
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
		print "Not a class: ",table
		notableclass.append(table)
		pass


## check Class definition
for key,value in dataclasses.items():
	instance = value()
	print "-- Table: ",key
	addcolumns, dropcolumns, queries = db.diffData(instance)
	for s in addcolumns:
		print "-- ADD ",s['Field']
	for s in dropcolumns:
		print "-- DROP ",s['Field']
	print "\n"
	for s in queries :
		print s
	print "\n\n"


sys.exit()
## check if Data class has a table in DB
tables = []
notables = []
for key,value in dataclasses.items():
	instance = value()
	results = db.query(instance, results=1, readimages=False)
	if results:
		print 'TABLE:', key
		tables.append(key)
	else:
		print 'NO TABLE:', key
		notables.append(key)
		
