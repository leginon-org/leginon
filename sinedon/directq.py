"""
	pass a mysql query to a sinedon database
	output is simply a list of dictionary
	with field names as keys

  This allows more complex query such those
	require in, group by etc.
"""
import time
import sinedon
import sqldb
import _mysql_exceptions

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
		pymysql can reconnect when pinged.
		'''
		global connections
		db_obj = connections[modulename]
		# pymysql can reconnect when pinged
		db_obj.dbConnection.ping(reconnect=True)

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
