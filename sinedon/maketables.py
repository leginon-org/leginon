#!/usr/bin/env python


import sys
import sqldict
import dbdatakeeper
import inspect
import _mysql_exceptions
import sinedon
import imp

Data = sinedon.data.Data

#=================
class DatabaseError(Exception):
	pass

#=================
columns_created = {}
dbd = None

#=================
#=================
#=================
if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "Usage:   maketables.py modulename <dbname>"
		print "Example: maketables.py appionData ap218"
		sys.exit(1)

	# clean up name
	modulename = sys.argv[1].strip()
	if modulename[-3:] == ".py":
		modulename = modulename[:-3]
	print "Using module name: "+modulename

	# use alternate db name if desired
	if len(sys.argv) > 2:
		newdbname = sys.argv[2].strip()
		print "Using alternate DB name for module: "+newdbname
		try:
			sinedon.setConfig(modulename, db=newdbname)
			dbconf = sinedon.getConfig(modulename)
			print dbconf
			dbd = sqldict.SQLDict(**dbconf)
		except _mysql_exceptions.OperationalError, e:
			raise DatabaseError(e.args[-1])
	else:
		dbconf = sinedon.getConfig(modulename)
		print dbconf
		dbd = sqldict.SQLDict(**dbconf)

	# import desire module
	(file, pathname, description) = imp.find_module(modulename)
	tableData = imp.load_module(modulename, file, pathname, description)
	
	# get module members
	funcs = inspect.getmembers(tableData, inspect.isclass)
	dbkeeper = dbdatakeeper.DBDataKeeper(**dbconf)

	# parse members
	for func in funcs:
		# check if member is a class

		if issubclass(func[1], Data):
			a = func[1]()
			#print "=============\n", a, "\n"
			#print func
			if not a:
				print "Did not do "+str(func)
			else:
				dbkeeper.flatInsert(a, skipinsert=True, fail=False)



