"MySQL module for pyLeginon"
import MySQLdb
import config

class sqlDB:
	"""
	This class is a SQL interface to connect a MySQL DB server.
	Default: host="localhost", user="usr_object", db="dbemdata"
	"""
	def __init__(self, host=config.DB_HOST, user=config.DB_USER, db=config.DB_NAME, passwd=config.DB_PASS):
		self.host=host
		self.user=user
		self.db=db
		self.passwd=passwd
		self.dbConnection = self.connect()

	def connect(self):
		'Open a DB connection'
		return MySQLdb.connect(host=self.host,user=self.user,db=self.db,passwd=self.passwd) 
		
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

