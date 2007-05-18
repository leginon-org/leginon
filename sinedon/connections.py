import dbconfig
from dbdatakeeper import DBDataKeeper as DB

connections = {}

def tail(modulename):
	return modulename.split('.')[-1]

def getConnection(modulename):
	if not isinstance(modulename, str):
		modulename = modulename.__name__
	modulename = tail(modulename)
	if modulename not in connections:
		connectedconf = None
	else:
		connectedconf = connections[modulename]['config']
	dbconf = dbconfig.getConfig(modulename)

	if dbconf != connectedconf:
		print 'MAKING CONNECTION', modulename, dbconf
		connections[modulename] = {'config': dbconf, 'connection': DB(**dbconf)}

	return connections[modulename]['connection']
