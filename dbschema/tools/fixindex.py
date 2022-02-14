#!/usr/bin/env python
'''
a but intruduced in myami-pymysql causes projectexperiments to
add new index to reference columns.  This fixes that.
It is not clear that why it is not a problem in some installation
but is so in another.
'''

from sinedon import directq

def getBadIndexName(dbmodule, table):
	# The '%s' % (variable) syntex is in conflict with mysql wildcard
	# append str works.
	query = "SHOW INDEX FROM "
	query += table
	query +=" where key_name like 'REF%\_%'"
	results = directq.complexMysqlQuery(dbmodule,query)
	names = map((lambda x: x['Key_name']),results)
	for name in names:
		# Only if the last bits are numeric
		bits = name.split('_')
		try: 
			int(bits[-1])
		except ValueError:
			names.remove(name)
	return names

def dropIndex(dbmodule, table, index_name):
	query = "DROP INDEX `%s` ON %s" % (index_name, table)
	print query
	results = directq.complexMysqlQuery(dbmodule,query)

def getAllTables(dbmodule):
	query = "SHOW TABLES"
	results = directq.complexMysqlQuery(dbmodule,query)
	if results:
		key = results[0].keys()[0]
	tables = map((lambda x: x[key]),results)
	return tables

for dbmodule in ('projectdata','leginondata'):
	tables =  getAllTables(dbmodule)
	for table in tables:
		bads = getBadIndexName(dbmodule,table)
		if bads:
			print('Have %d duplicated index in %s table %s' % (len(bads), dbmodule, table) )
		for index_name in bads:
			dropIndex(dbmodule,table, index_name)
