#!/usr/bin/env python

import re
import sys
import sqldict
import inspect
import sinedon
import MySQLdb

from optparse import OptionParser

#=================
def getOptions():
	usage = "Usage: %prog --sinedon-name=appiondata --module-name=appionlib.appiondata --db-name=ap73"

	parser = OptionParser(usage=usage)
	parser.add_option("-s", "--sinedon-name", dest="sinedonname",
		help="Sinedon name of database, e.g., appiondata", metavar="X")
	parser.add_option("-m", "--module-name", dest="modulename",
		help="Module name of database, e.g., appionlib.appiondata", metavar="X")
	parser.add_option("-d", "--db-name", dest="dbname",
		help="Name of database, e.g., ap74", metavar="X")
	parser.add_option("-x", "--xml-file", dest="xmlfile",
		help="Write XML file do not modify database", metavar="X")

	if len(sys.argv) < 2:
		parser.print_help()
		parser.error("no options defined")

	(options, args) = parser.parse_args()

	if options.sinedonname is None:
		print "Please provide a sinedon name of database, e.g., appiondata"
	if options.modulename is None:
		print "Please provide a module name of database, e.g., appionlib.appiondata"

	print "Using sinedon name: "+options.sinedonname
	print "Using module name: "+options.modulename
	if options.dbname is not None:
		print "Using database name: "+options.dbname

	return options

def definitionToXml(xmlf, tablename, definition):
	tabledef = ("<sqltable name=\"%s\" >\n"%(tablename))

	### write column definitions
	for column in definition:
		tabledef += ("\t<field \n")
		tabledef += ("\t\tname=\"%s\" \n"%(column['Field']))
		tabledef += ("\t\ttype=\"%s\" \n"%(column['Type']))
		if not 'Null' in column or column['Null'] == 'NO':
			tabledef += ("\t\tnull=\"NOT NULL\" \n")
		else:
			tabledef += ("\t\tnull=\"NULL\" \n")
		if column['Field'] == 'DEF_timestamp':
			tabledef += ("\t\tdefault=\"DEFAULT 'CURRENT_TIMESTAMP' on update 'CURRENT_TIMESTAMP'\" \n")
		elif 'Default' in column:
			tabledef += ("\t\tdefault=\"%s\" \n"%(column['Default']))
		if 'Extra' in column:
			tabledef += ("\t\textra=\"%s\" \n"%(column['Extra']))

		tabledef += ("\t/> \n")

	### add column indexing
	for column in definition:
		if 'Key' in column:
			if column['Key'] == 'PRIMARY':
				tabledef += ("\t<key>PRIMARY KEY (`%s`)</key> \n"%(column['Field']))
			elif column['Key'] == 'INDEX':
				tabledef += ("\t<key>KEY `%s` (`%s`)</key> \n"%(column['Field'], column['Field']))

	tabledef += ("</sqltable>\n")
	xmlf.write(tabledef)

def makeTables(sinedonname,modulename,dbname=None,xmlfile=None,check_exist=False):
	### use alternate db name if desired
	if dbname is not None:
		print "setting alternate database name"
		sinedon.setConfig(sinedonname, db=dbname)

	### connect to DB
	dbconf = sinedon.getConfig(sinedonname)
	dbd = sqldict.SQLDict(**dbconf)

	### import desire module
	module = __import__(modulename)
	modbase = re.sub("^.*\.", "", modulename)
	tableData = getattr(module, modbase) ## hope this works
	
	### get module members
	funcs = inspect.getmembers(tableData, inspect.isclass)

	print "Found %d classes in module"%(len(funcs))
	#print funcs

	### parse members
	count = 0
	if xmlfile is not None:
		xmlf = open(xmlfile, 'w')
		xmlf.write("<defaulttables>\n <definition>\n")
	for func in funcs:
		### Check if member is valid len 2 tuple
		if len(func) != 2:
			continue
		### Check if member is a sinedon Data class
		if not issubclass(func[1], sinedon.data.Data) or func[0] == "Data":
			continue

		### Create table
		tablename = func[0]
		tableclass = func[1]()
		table = (dbname, tablename)
		definition, formatedData = sqldict.dataSQLColumns(tableclass, False)
		create_flag=False
		if check_exist:
			try:
				dbd.diffSQLTable(tablename,definition)
			except (MySQLdb.ProgrammingError, MySQLdb.OperationalError), e:
				errno = e.args[0]
				## some version of mysqlpython parses the exception differently
				if not isinstance(errno, int):
					errno = errno.args[0]
				## 1146:  table does not exist
				if errno in (1146,):
					print tablename,' does not yet exist, and will be created'
					create_flag=True
		else:
			create_flag=True
		if create_flag:
				if xmlfile is None:
					dbd.createSQLTable(table, definition)
				else:
					definitionToXml(xmlf, tablename, definition)
				count += 1

	if xmlfile is not None:
		xmlf.write(" </definition>\n</defaulttables>\n")
		xmlf.close()

	print "Created %d tables"%(count)

#=================
#=================
#=================
if __name__ == "__main__":
	options = getOptions()
	if options.xmlfile is not None:
		existcheck = True
	else:
		existcheck = False
	makeTables(options.sinedonname,options.modulename,
		options.dbname,options.xmlfile,check_exist=existcheck)
