import dbconfig
from dbdatakeeper import DBDataKeeper as DB
import threading

lock = threading.Lock()
connections = {}

def tail(modulename):
	return modulename.split('.')[-1]

def getConnection(modulename):
	lock.acquire()
	try:
		if not isinstance(modulename, str):
			modulename = modulename.__name__
		modulename = tail(modulename)
		if modulename not in connections:
			connectedconf = None
		else:
			connectedconf = connections[modulename]['config']
		dbconf = dbconfig.getConfig(modulename)
	
		if dbconf != connectedconf:
			#print 'MAKING CONNECTION', modulename, dbconf
			connections[modulename] = {'config': dbconf, 'connection': DB(**dbconf)}
		connection = connections[modulename]['connection']
	finally:
		lock.release()
	return connection
