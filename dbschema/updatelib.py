#!/usr/bin/env python
import time
import os
import xml.dom.minidom as dom
from leginon import version

def getPackageVersion():
	# getSVNBranch gives branch name from either svn or text
	svn_branch = version.getSVNBranch('.')
	if svn_branch == 'trunk':
		version_log = svn_branch
	elif 'myami-' in svn_branch:
		version_log = svn_branch.split('-')[-1]
	else:
		raise "Unknown svn branch"
	return version_log

def getUpdateRevisionSequence():
	svn_branch = version.getSVNBranch('.')
	if svn_branch == 'trunk':
		schema_revisions = [12857,13713,14077,14891,15069,15248,15251,15293]
	elif svn_branch == 'myami-2.1':
		schema_revisions = [12857,13713,14077,14891,15293]
	elif svn_branch == 'myami-2.0':
		schema_revisions = [12857,13713,14077,14380,15293]
	else:
		raise "Unknown svn branch"
	return schema_revisions

def getCheckOutRevision(module_path='.'):
	try:
		# Only svn checkout have integer revision number
		svn_revision = int(version.getVersion(module_path))
		print '\033[36mSVN checkout revision is %s\033[0m' % svn_revision
		return svn_revision
	except:
		release_revision = getReleaseRevisionFromXML(module_path)
		if release_revision:
			print '\033[36mRelease revision is %s\033[0m' % release_revision
			return release_revision
		else:
			# For unknown releases, assume head revision
			return 1000000000

def getDatabaseRevision(project_dbupgrade,printMsg=False):
	### get revision from database
	selectq = " SELECT value FROM `install` WHERE `key`='revision'"
	values = project_dbupgrade.returnCustomSQL(selectq)
	if values:
		revision = int(values[0][0])
	else:
		selectq = " SELECT value FROM `install` WHERE `key`='version'"
		versionvalues = project_dbupgrade.returnCustomSQL(selectq)
		if versionvalues:
			dbversion = versionvalues[0][0]
			if dbversion == '1.7':
				# pre myami-2.0 database need more updates
				revision = 12000
			else:
				# early myami-2.0 database has no revision record
				revision = 14077
		else:
			raise "Unknown version log in database. Can not proceed"
	if printMsg:
		print '\033[36mDatabase recorded revision is %s\033[0m' % revision
	return revision

def allowVerisionLog(project_dbupgrade,checkout_revision):
	'''
		Package version log is allowed only if the checkout_revision
		ahead of the current revision_in_database less than one
		required update ahead
	'''
	revision_in_database = getDatabaseRevision(project_dbupgrade)
	if checkout_revision <= revision_in_database:
		print '\033[35mDatabase revision log up to date, Nothing to do\033[0m'
		return False
	schema_revisions = getUpdateRevisionSequence()
	schema_revisions.sort()
	schema_revisions.reverse()
	for revision in schema_revisions:
		if revision < checkout_revision:
			minimal_revision_in_database = revision
			break
	if minimal_revision_in_database <= revision_in_database:
		return True
	else:
		print '\033[35mYou must successfully run schema-r%d.py first\033[0m' % (minimal_revision_in_database)
		return False

def needUpdate(project_dbupgrade,checkout_revision,selected_revision):
	''' 
		database update of the schema at selected_revision is 
		performed only if the checkout_revision
		is newer than the selected_revision and that previous
		update was made successfully as recorded in the database
	'''
	revision_in_database = getDatabaseRevision(project_dbupgrade)
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

def getReleaseRevisionFromXML(module_path='.'):
	if not module_path:
		module_path = version.getInstalledLocation()
	module_path = os.path.abspath(module_path)
	pieces = module_path.split('/')
	xmlpathpieces = pieces[:-1]
	xmlpathpieces.extend(['myamiweb','xml','projectDefaultValues.xml'])
	xmlfilepath = '/'.join(xmlpathpieces)
	print '\033[35mGetting release revision from %s\033[0m' % xmlfilepath
	curkey = None
	installdata = {}
	try:
		xmlapp = dom.parse(xmlfilepath)
	except:
		raise ValueError('unable to parse XML file "%s"' % xmlfilepath)
	defaulttables = xmlapp.getElementsByTagName('defaulttables')[0]
	data = defaulttables.getElementsByTagName('data')[0]
	sqltables = defaulttables.getElementsByTagName('sqltable')
	for node in sqltables:
		if node.attributes['name'].value == 'install':
			for n in node.childNodes:
				if n.nodeName == 'field':
					if n.attributes['name'].value == 'key':
						curkey = n.firstChild.data
					if n.attributes['name'].value == 'value':
						installdata[curkey] = n.firstChild.data
	if 'revision' in installdata:
		return int(installdata['revision'])

def updateDatabaseRevision(project_dbupgrade,current_revision):
	### set version of database
	selectq = " SELECT * FROM `install` WHERE `key`='revision'"
	values = project_dbupgrade.returnCustomSQL(selectq)
	if values:
		project_dbupgrade.updateColumn("install", "value", "'%d'" % (current_revision), 
			"install.key = 'revision'",timestamp=False)
	else:
		insertq = "INSERT INTO `install` (`key`, `value`) VALUES ('revision', %d)"% (current_revision)
		project_dbupgrade.executeCustomSQL(insertq)

def updateDatabaseVersion(project_dbupgrade,current_version):
	### set version of database
	selectq = " SELECT * FROM `install` WHERE `key`='version'"
	values = project_dbupgrade.returnCustomSQL(selectq)
	if values:
		project_dbupgrade.updateColumn("install", "value", "'%s'" % (current_version), 
			"install.key = 'version'",timestamp=False)
