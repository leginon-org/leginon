#!/usr/bin/env python

import sys
import MySQLdb
import dbconfig

class DBUpgradeTools(object):
	#============================
	#== PRIVATE FUNCTIONS
	#============================
	def __init__(self, dbname, dbconfname=None):
		if dbconfname is None:
			print "setting db conf name to db name"
			dbconfname = dbname
		### get database config from sinedon.cfg
		dbconf = dbconfig.getConfig(dbconfname)
		### if database name is not config name, e.g., ap212 and appiondata
		if dbname != dbconfname:
			dbconfig.setConfig(dbconfname, db=dbname)
		### connect to db
		db = MySQLdb.connect(**dbconf)
		### create cursor
		self.cursor = db.cursor()

	#==============
	def _validTableName(self, table):
		"""
		check name of table for security reasons
		"""
		if "." in table:
			print "\033[31merror . in table name\033[0m"
			return False
		if ";" in table:
			print "\033[31merror ; in table name\033[0m"
			return False
		return True

	#==============
	def _tableExists(self, table):
		"""
		check if table exists
		"""
		query = "SHOW TABLES LIKE `%s`;"%(table)
		numrows = int(self.cursor.rowcount)
		if numrows > 0
			return True
		return False

	#==============
	def _validColumnName(self, column):
		"""
		check name of column for security reasons
		"""
		if "." in column:
			print "\033[31merror . in column name\033[0m"
			return False
		if ";" in column:
			print "\033[31merror ; in column name\033[0m"
			return False
		if " " in column:
			print "\033[31merror ' ' in column name\033[0m"
			return False
		return True

	#==============
	def _columnExists(self, table, column):
		"""
		check if column exists
		"""
		query = "SHOW COLUMNS FROM `%s` LIKE '%s';"%(table, column)
		numrows = int(self.cursor.rowcount)
		if numrows > 0
			return True
		return False

	#==============
	def _getColumnDefinition(self, table, column):
		"""
		get column definition (e.g., TINYINT(1))
		"""
		query = "DESCRIBE %s %s;"%(table, column)
		self.cursor.execute(query)
		result = self.cursor.fetchone()
		if not result:
			print "\033[31mcolumn definition not found %s.%s\033[0m"%(table, column)
			return None
		return result[1]

	#============================
	#== PUBLIC FUNCTIONS
	#============================

	#==============
	def executeCustomSQL(self, query):
		"""
		execute custom query
		"""
		self.cursor.execute(query)
		return True

	#==============
	def returnCustomSQL(self, query):
		"""
		execute custom query
		"""
		self.cursor.execute(query)
		return self.cursor.fetchall()

	#==============
	def renameTable(self, table1, table2):
		"""
		rename table1 to table2
		"""
		if self._validTableName(table1) is False:
			return False
		if self._validTableName(table2) is False:
			return False

		if self._tableExists(self, table2):
			print "\033[31mcannot rename %s to %s, table exists\033[0m"%(table1, table2)
			return

		query = "RENAME TABLE `%s` TO `%s`;"%(table1, table2)
		self.cursor.execute(query)
		return True

	#==============
	def renameColumn(self, table, column1, column2):
		"""
		rename column1 to column2 in table
		"""
		if self._validTableName(table) is False:
			return False
		if self._validColumnName(column1) is False:
			return False
		if self._validColumnName(column2) is False:
			return False

		if self._columnExists(self, table, column2):
			print "\033[31mcannot rename %s to %s, column exists\033[0m"%(column1, column2)
			return False

		columndefine = self._getColumnDefinition(table, column1)
		if not columndefine:
			return False
		query = "ALTER TABLE `%s` CHANGE `%s` `%s` %s;"%(table1, column1, column2, columndefine)
		self.cursor.execute(query)
		return True

	#==============
	def createTable(self, table):
		"""
		create table with DEF_id and DEF_timestamp
		"""
		if self._validTableName(table) is False:
			return False
		if self._tableExists(table) is True:
			print "\033[31mcannot create table %s, table exists\033[0m"%(table)
			return False

		query = "CREATE TABLE `%s` \n"%(table)
		query += "( \n"
		### add DEF_id and DEF_timestamp
		query += "`DEF_id` int(20) NOT NULL auto_increment, \n"
		query += "`DEF_timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP, \n"
		### set keys
		query += "PRIMARY KEY (`DEF_id`), \n"
		query += "KEY `DEF_timestamp` (`DEF_timestamp`) \n"
		### set defaults
		query += ") ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;\n"
		self.cursor.execute(query)
		return True

	#============================
	#== END CLASS
	#============================

if __name__ == "__main__":
	#basic test
	a = DBUpgradeTools('ap212', 'appiondata')
	print a.getColumnDefinition('ApPathData', 'DEF_id')
	print a.getColumnDefinition('ApPathData', 'path')






