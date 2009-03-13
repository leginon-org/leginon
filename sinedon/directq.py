"""
	pass a mysql query to a sinedon database
	output is simply a list of dictionary
	with field names as keys

  This allows more complex query such those
	require in, group by etc.
"""

import sinedon
import sqldb

connections = {}

def getConnection(modulename='leginondata'):
	if not connections:
		if not connections.has_key(modulename):
			print 'connecting'
			param = sinedon.getConfig(modulename)
			connections[modulename] = sqldb.sqlDB(**param)
	return connections[modulename]

def complexMysqlQuery(basedbmodule,query):
	cur = getConnection(basedbmodule)
	results = cur.selectall(query)

	return results
