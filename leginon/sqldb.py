"MySQL module for pyLeginon"
import MySQLdb
import config

def connect(**kwargs):
	defaults = {
		'host':config.DB_HOST,
		'user':config.DB_USER,
		'db':config.DB_NAME,
		'passwd':config.DB_PASS
	}
	defaults.update(kwargs)
	c = MySQLdb.connect(**defaults)
	return c

class sqlDB:
	"""
	This class is a SQL interface to connect a MySQL DB server.
	Default: host="localhost", user="usr_object", db="dbemdata"
	"""
	def __init__(self, **kwargs):
		self.dbConnection = connect(**kwargs)
		
	def selectone(self, strSQL, param=None):
		'Execute a query and return the first row.'
		c=self.dbConnection.cursor()	
		c.execute(strSQL, param)
		result = c.fetchone()
		return result

	def selectall(self, strSQL, param=None):
		'Execute a query and return all rows.'
		c=self.dbConnection.cursor()	
		c.execute(strSQL, param)
		result = c.fetchall()
		return result

	def insert(self, strSQL, param=None):
		'Execute a query to insert data. It returns the last inserted Id.'
		c=self.dbConnection.cursor()	
		c.execute(strSQL, param)
		return c.insert_id()

	def execute(self, strSQL, param=None):
		'Execute a query'
		c=self.dbConnection.cursor()	
		return c.execute(strSQL, param)

	def close(self):
		'Close a DB connection'
		self.dbConnection.close()
