#!/usr/bin/env python
import time
from sinedon import dbupgrade, dbconfig
from leginon import version

def getUpdateRevisionSequence():
	if version.getSVNBranch() == 'trunk':
		schema_revisions = [12857,13713,14077,14891,15069,15248,15251]
	if version.getSVNBranch() == 'myami-2.1':
		schema_revisions = [12857,13713,14077,14891]
	return schema_revisions

def getCheckOutRevision():
	try:
		return int(version.getVersion())
	except:
		print 'failed to get an integer revision'
	return False

def getDatabaseRevision(projectdb):
	### get revision from database
	selectq = " SELECT value FROM `install` WHERE `key`='revision'"
	values = projectdb.returnCustomSQL(selectq)
	if values:
		return int(values[0][0])
	else:
		# myami-2.0 database has no revision record
		return 14077
	
def needUpdate(projectdb,checkout_revision,selected_revision):
	''' 
		database update of the schema at selected_revision is 
		performed only if the checkout_revision
		is newer than the selected_revision and that previous
		update was made successfully as recorded in the database
	'''
	revision_in_database = getDatabaseRevision(projectdb)
	schema_revisions = getUpdateRevisionSequence()
	try:
		index = schema_revisions.index(selected_revision)
	except:
		return False
	if index > 0:
		minimal_revision_in_database = schema_revisions[index-1]
	else:
		minimal_revision_in_database = 0
	if checkout_revision >= selected_revision:
		if revision_in_database < selected_revision:
			if minimal_revision_in_database == 0 or revision_in_database >= minimal_revision_in_database:
				return 'now'
			else:
				print '\033[35mYou must successfully run schema-r%d.py first\033[0m' % (minimal_revision_in_database)
				return 'later'
		else:
			print "\033[35mAlready Up to Date for schema r%d\033[0m" % (selected_revision)
	else:
		print "\033[35mCode not yet at r%d\033[0m" % (selected_revision)
	return False

def updateDatabaseRevision(projectdb,current_revision):
	### set version of database
	selectq = " SELECT * FROM `install` WHERE `key`='revision'"
	values = projectdb.returnCustomSQL(selectq)
	if values:
		projectdb.updateColumn("install", "value", "'%d'" % (current_revision), 
			"install.key = 'revision'",timestamp=False)
	else:
		insertq = "INSERT INTO `install` (`key`, `value`) VALUES ('revision', %d)"% (current_revision)
		projectdb.executeCustomSQL(insertq)
