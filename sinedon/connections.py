import sinedon.dbconfig
from dbdatakeeper import DBDataKeeper as DB
import threading

lock = threading.Lock()

## connections dict holds all the unique database connections (DBDataKeeper objects)
connections = {}

def tail(modulename):
	return modulename.split('.')[-1]

def config_key(module_name, config_dict):
	key = (module_name, config_dict['host'], config_dict['db'])
	return key

def getConnection(modulename, config_dict=None):
	'''
	if config_dict is given, return the corresponding DBDataKeeper object
	otherwise, get the default config for the given module name, then  return that DBDataKeeper
	'''
	lock.acquire()
	try:
		if not isinstance(modulename, str):
			modulename = modulename.__name__
		modulename = tail(modulename)
		if config_dict is None:
			config_dict = sinedon.dbconfig.getConfig(modulename)
		key = config_key(modulename, config_dict)
		if key in connections:
			db = connections[key]
		else:
			db = DB(**config_dict)
			connections[key] = db
	finally:
		lock.release()
	return db
