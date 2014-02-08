#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
"MySQL module for pyLeginon"
import MySQLdb

def connect(**kwargs):
	c = MySQLdb.connect(**kwargs)
	c.autocommit(True)
	c.kwargs = dict(kwargs)
	return c

def escape(anystring):
	'addslashes to any quotes if necessary'
	return MySQLdb.escape_string(anystring)

def addbackquotes(anystring):
	return "`%s`" % (anystring,)


class sqlDB(object):
	"""
	This class is a SQL interface to connect a MySQL DB server.
	Default: host="localhost", user="usr_object", db="dbemdata"
	"""
	def __init__(self, **kwargs):
		self.dbConnection = connect(**kwargs)
		self.c = self.dbConnection.cursor(cursorclass=MySQLdb.cursors.DictCursor)

	def selectone(self, strSQL, param=None):
		'Execute a query and return the first row.'
		self.c.execute(strSQL, param)
		result = self.c.fetchone()
		return result

	def selectall(self, strSQL, param=None):
		'Execute a query and return all rows.'
		self.c.execute(strSQL, param)
		result = self.c.fetchall()
		return result

	def insert(self, strSQL, param=None):
		'Execute a query to insert data. It returns the last inserted Id.'
		self.c.execute(strSQL, param)
		## try the new lastrowid attribute first,
		## then try the old insert_id() method
		try:
			insert_id = self.c.lastrowid
		except Exception, e:
			insert_id = self.c.insert_id()
		return insert_id

	def execute(self, strSQL, param=None):
		'Execute a query'
		return self.c.execute(strSQL, param)

	def close(self):
		'Close a DB connection'
		self.dbConnection.close()

