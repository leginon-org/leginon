"""
	pass a mysql query to a sinedon database
	output is simply a list of dictionary
	with field names as keys

  This allows more complex query such those
	require in, group by etc.
"""

import sinedon
import MySQLdb
import sqldb

connections = {}

def getConnection(modulename='leginondata'):
	global connections
	param = sinedon.getConfig(modulename)
	if not connections.has_key(modulename):
		connections[modulename] = sqldb.sqlDB(**param)
	ping(modulename,param)
	return connections[modulename]

def ping(modulename,param):
		'''
		Check connection stat and reconnect if needed.
		'''
		global connections
		db_obj = connections[modulename]
		db=db_obj.dbConnection
		try:
			if db.stat() == 'MySQL server has gone away':
				connections[modulename] = sqldb.sqlDB(**param)
		except MySQLdb.InterfaceError as e:
			errno = e.args[0]
			if errno == 0:
				# connection closed
				# print  "reconnecting after connection is closed"
				connections[modulename] = sqldb.sqlDB(**param)
			else:
				raise
		except (MySQLdb.ProgrammingError, MySQLdb.OperationalError) as e:
			# db.stat function gives error when connection is not available.
			errno = e.args[0]
			## some version of mysqlpython parses the exception differently
			if not isinstance(errno, int):
				errno = errno.args[0]
			## 2006:  MySQL server has gone away
			if errno in (2006,):
				ctime = time.strftime("%H:%M:%S")
				print "reconnecting at %s after MySQL server has gone away error" % (ctime,)
				connections[modulename] = sqldb.sqlDB(**param)
			else:
				raise

def complexMysqlQuery(basedbmodule,query):
	if len(query) > 10000:
		print "Long MySQL query of %d characters"%(len(query))
	cur = getConnection(basedbmodule)
	results = cur.selectall(query)

	return results

def datakeyToSqlColumnName(sinedondata,key):
	'''
	Returns sql column name in sinedon format based on the referenced class if needed
	The input sinedondata has to contain dbid, i.e., is the result of
	a query or another reference.
	'''
	if hasattr(sinedondata[key],'dbid'):
		refdata = sinedondata[key]
		module_name = ''
		if refdata.__module__ != sinedondata.__module__:
			module_name = refdata.__module__.split('.')[-1]+'|'
		return 'REF|%s%s|%s' % (module_name,refdata.__class__.__name__,key)
	return key
