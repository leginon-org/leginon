"MySQL module for pyLeginon"
import MySQLdb

class sqlDB:
	"""
	This class is a SQL interface to connect a MySQL DB server.
	Default: host="localhost", user="usr_object", db="dbemdata"
	"""
	def __init__(self, hostname='localhost', username='usr_object', databasename='dbemdata'):
		self.hostname=hostname
		self.username=username
		self.databasename=databasename
		self.dbConnection = self.connect()

	def connect(self):
		'Open a DB connection'
		return MySQLdb.connect(host=self.hostname,user=self.username,db=self.databasename) 
		
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

