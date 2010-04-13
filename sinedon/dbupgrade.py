#!/usr/bin/env python

import sys
import MySQLdb
import dbconfig

class DBUpgradeTools(object):
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
		db     = MySQLdb.connect(**dbconf)

		### create cursor
		self.cursor = db.cursor()

	#==============
	def checkTableName(self, table):
		"""
		check name of table for security reasons
		"""
		if "." in table:
			print "error . in table name"
			sys.exit(1)
		if ";" in table:
			print "error ; in table name"
			sys.exit(1)
		return

	#==============
	def checkColumnName(self, column):
		"""
		check name of column for security reasons
		"""
		if "." in column:
			print "error . in column name"
			sys.exit(1)
		if ";" in column:
			print "error ; in column name"
			sys.exit(1)
		return

	#==============
	def customSQL(self, sql):
		#use sinedon.directq.complexMysqlQuery?
		return

	#==============
	def renameTable(self, table1, table2):
		"""
		rename table1 to table2
		"""
		self.checkTableName(table1)
		self.checkTableName(table2)

		query = "RENAME TABLE %s TO %s;"%(table1, table2)
		self.cursor.execute(query)
		return

	#==============
	def getColumnDefinition(self, table, column):
		"""
		get column definition (e.g., TINYINT(1))
		"""
		query = "DESCRIBE %s %s;"%(table, column)
		self.cursor.execute(query)
		result = self.cursor.fetchone()
		if not result:
			print "column definition not found %s.%s"%(table, column)
			return None
		return result[1]

	#==============
	def renameColumn(self, table, column1, column2):
		"""
		rename column1 to column2 in table
		"""
		self.checkTableName(table)
		self.checkColumnName(column1)
		self.checkColumnName(column2)

		columndefine = self.getColumnDefinition(table, column1)
		if not columndefine:
			return
		query = "ALTER TABLE %s CHANGE %s %s %s;"%(table1, column1, column2, columndefine)
		self.cursor.execute(query)
		return

	#==============
	def moveColumnChild(self, table1, table2, column):
		"""
		rename column from table1 to child table2
		"""
		return

		self.getColumnDefinition(table1, column)
		query = "INSERT INTO %s (SELECT %s FROM %s); "%(table2, column, table1)
		#self.cursor.execute(query)
		#results = self.cursor.fetchall()
		return

	#==============
	def moveColumnParent(self, table1, table2, column):
		"""
		rename column from table1 to parent table2
		"""
		return

		self.getColumnDefinition(table1, column)
		query = "INSERT INTO %s (SELECT %s FROM %s LEFT JOIN); "%(table2, column, table1)
		#self.cursor.execute(query)
		#results = self.cursor.fetchall()
		return

	#==============
	def moveAndRenameColumn(self, table1, table2, column1, column2):
		"""
		move column1 in table1 to column2 in table2
		"""
		query = "ALTER TABLE %s CHANGE %s %s;"%(table1, table2)
		#self.cursor.execute(query)
		return

	#==============
	def createTable(self, table):
		"""
		create table
		"""
		print "incomplete"
		return
		self.checkTableName(table)
		query = "CREATE TABLE "%(table) ### cannot create table without columns
		#self.cursor.execute(query)
		return


if __name__ == "__main__":
	#basic test
	a = DBUpgradeTools('ap212', 'appiondata')
	print a.getColumnDefinition('ApPathData', 'DEF_id')
	print a.getColumnDefinition('ApPathData', 'path')






