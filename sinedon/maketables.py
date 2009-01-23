#!/usr/bin/env python

import appionData
import sys
import apDisplay
#import dbconfig
import sqldict
import inspect
import _mysql_exceptions
import sinedon




Data = sinedon.data.Data

#=================
class DatabaseError(Exception):
	pass

#=================
columns_created = {}

#=================
try:
	newdbname = "ap"+str(0)
	sinedon.setConfig('appionData', db=newdbname)
	dbconf = sinedon.getConfig('appionData')
	print dbconf
	dbd = sqldict.SQLDict(**dbconf)
except _mysql_exceptions.OperationalError, e:
	raise DatabaseError(e.args[-1])

#=================
#=================
#=================

#=================
def flatInsert(newdata, force=False):
	dbname = sinedon.getConfig(newdata.__module__)['db']
	#dbname = dbconfig.getConfig(newdata.__module__)['db']
	tablename = newdata.__class__.__name__
	table = (dbname, tablename)
	definition, formatedData = sqldict.dataSQLColumns(newdata)
	## check for any new columns that have not been created
	if table not in columns_created:
		columns_created[table] = {}
	fields = [d['Field'] for d in definition]
	create_table = False
	for field in fields:
		if field not in columns_created[table]:
			columns_created[table][field] = None
			create_table = True
	if create_table:
		dbd.createSQLTable(table, definition)
	myTable = dbd.Table(table)
	#newid = myTable.insert([formatedData], force=force)
	return

#=================
#=================
#=================
if __name__ == "__main__":
	funcs = inspect.getmembers(appionData, inspect.isclass)
	for func in funcs:
		if issubclass(func[1], Data):
			a = func[1]()
			print "=============\n", a, "\n"
			if not a:
				apDisplay.printWarning("Did not do "+str(func))
			else:
				flatInsert(a)
				flatInsert(a)



