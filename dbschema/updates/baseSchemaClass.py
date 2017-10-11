#!/usr/bin/env python
import time
import string

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import updatelib

from pyami import gitlib
from sinedon import dbupgrade
dbupgrade.messaging['custom'] = False

from leginon import projectdata

class SchemaUpdate(object):
	#######################################################################
	#
	# Functions to include in every schema update sub-class
	#
	#######################################################################

	def setFlags(self):
		"""
		set important flags
		"""
		raise NotImplementedError ## remove this line
		# can this schema update be run more than once and not break anything
		self.isRepeatable = False
		# should this schema update be run again whenever the branch is upgraded, i.e., 3.1 -> 3.2
		self.reRunOnBranchUpgrade = False
		# minimum myami version
		self.minimumMyamiVersion = -1
		# what is the number associated with this update, use 'git rev-list --count HEAD'
		self.schemaNumber = -1
		# minimum update required (set to previous schema update number)
		self.minSchemaNumberRequired = 1e10
		#what is the git tag name
		self.schemaTagName = 'schema1'
		#git tag <tag name> <commit id>
		#git tag schema1 9fceb02
		#flags for what databases are updated and which ones are not
		self.modifyAppionDB = False
		self.modifyLeginonDB = False
		self.modifyProjectDB = False

	def upgradeAppionDB(self):
		"""
		define AppionDB upgrade in this function
		"""
		raise NotImplementedError

	def upgradeLeginonDB(self):
		"""
		define LeginonDB upgrade in this function
		"""
		raise NotImplementedError

	def upgradeProjectDB(self):
		"""
		define ProjectDB upgrade in this function
		"""
		raise NotImplementedError

	#######################################################################
	#
	# Functions exclusive to the base class
	#
	#######################################################################

	def __init__(self, backup=False):
		self.setFlags()
		self.schemaCommitId = gitlib.getCommitIDfromTag(self.schemaTagName)
		self.project_dbupgrade = dbupgrade.DBUpgradeTools('projectdata', drop=True)
		self.leginon_dbupgrade = dbupgrade.DBUpgradeTools('leginondata', drop=True)
		self.updatelib = updatelib.UpdateLib(self.project_dbupgrade)
		self.backup = backup
		self.schema_pythonfile = "schema-r%s.py"%(str(self.schemaNumber))
		subclassfile = os.path.basename(sys.modules[self.__module__].__file__)
		# pyc file is o.k.
		if subclassfile.endswith('pyc'):
			subclassfile = subclassfile[:-1]
		if subclassfile != self.schema_pythonfile:
			raise IOError("filename of schema tag '%s' must be '%s' NOT '%s'"
				%(self.schemaNumber, self.schema_pythonfile, subclassfile))
		self.excluded_appiondbs = []
		self.setForceUpdate(False)

	def appendToExcluded_AppionDBs(self,dbname):
		self.excluded_appiondbs.append(dbname)

	def inExcluded_AppionDBList(self,appiondbname):
		if appiondbname in self.excluded_appiondbs:
			return True
		return False

	def getSchemaNumber(self):
		if self.schemaNumber > 0:
			return self.schemaNumber
		raise ValueError("script schema number is invalid")

	def getAppionDatabases(self,project_dbupgrade):
		"""
		Get list of appion databases to upgrade
		"""
		if project_dbupgrade.columnExists('processingdb', 'appiondb'):
			colname = 'appiondb'
		elif project_dbupgrade.columnExists('processingdb', 'db'):
			colname = 'db'
		else:
			print "could not find appion tables"
			return []

		selectq = "SELECT DISTINCT "+colname+" FROM processingdb ORDER BY `REF|projects|project` ASC"
		results = project_dbupgrade.returnCustomSQL(selectq)
		appiondblist = []
		for result in results:
			appiondblist.append(result[0])
		#random.shuffle(appiondblist)
		return appiondblist

	#=====================
	def makeTimestamp(self):
		datestamp = time.strftime("%y%b%d").lower()
		hourstamp = string.lowercase[(time.localtime()[3])%26]
		if hourstamp == "x":
			### SPIDER does not like x's
			hourstamp = "z"
		#mins = time.localtime()[3]*12 + time.localtime()[4]
		#minstamp = string.lowercase[mins%26]
		minstamp = "%02d"%(time.localtime()[4])
		timestamp = datestamp+hourstamp+minstamp
		return timestamp

	def appionbackup(self,appiondblist):
		appiondb_unique_list = list(set(appiondblist))
		for appiondbname in appiondb_unique_list:
			if not self.project_dbupgrade.databaseExists(appiondbname):
				print "\033[31merror database %s does not exist\033[0m"%(appiondbname)
				time.sleep(1)
				continue
			appion_dbupgrade = dbupgrade.DBUpgradeTools('appiondata', appiondbname, drop=True)
			backupfile = "%s-%s.sql" % (appiondbname, self.makeTimestamp())
			appion_dbupgrade.backupDatabase(backupfile, data=True)

	def commitUpdate(self):
		"""
		Log that this update has been completed and therefore can not be repeated.
		"""
		self.addUpdateToSchemaTable()
		if not self.force:
			self.updatelib.updateDatabaseReset(self.updatelib.db_revision)
			self.updatelib.updateDatabaseRevision(self.schemaNumber)
			print "\033[35mUpdated install table reset and schema number\033[0m"
		else:
			print "\033[35mForced Update does not update install table reset and schema number\033[0m"

	def addUpdateToSchemaTable(self):
		updateq = projectdata.schemaupdates()
		updateq['schematag'] = self.schemaTagName
		updateq['schemaid'] = self.getSchemaNumber()
		updateq['schemacommitid'] = self.schemaCommitId
		updateq['branch'] = gitlib.getCurrentBranch()
		updateq['commitcount'] = gitlib.getCurrentCommitCount()
		updateq['gitversion'] = gitlib.getVersion()
		updateq['recentcommitid'] = gitlib.getMostRecentCommitID()
		updateq['modifyappiondb'] = self.modifyAppionDB
		updateq['modifyleginondb'] = self.modifyLeginonDB
		updateq['modifyprojectdb'] = self.modifyProjectDB
		updateq.insert(force=True)

	def setForceUpdate(self,is_force):
		self.force = is_force

	def runUpdates(self):
		divider = "-------------------------------------------"
		if self.modifyLeginonDB is True:
			# leginon part
			print divider
			if self.backup:
				self.leginon_dbupgrade.backupDatabase("leginondb"+self.makeTimestamp()+".sql", data=True)
			print "\033[35mUpgrading %s\033[0m" % (self.leginon_dbupgrade.getDatabaseName())
			self.upgradeLeginonDB()
		if self.modifyProjectDB is True:
			# project part
			print divider
			if self.backup:
				self.leginon_dbupgrade.backupDatabase("projectdb"+self.makeTimestamp()+".sql", data=True)
			print "\033[35mUpgrading %s\033[0m" % (self.project_dbupgrade.getDatabaseName())
			self.upgradeProjectDB()
		if self.modifyAppionDB is True:
			# appion part
			print divider
			appiondblist = self.getAppionDatabases(self.project_dbupgrade)
			if self.backup:
				self.appionbackup(appiondblist)
			for appiondbname in appiondblist:
				if self.inExcluded_AppionDBList(appiondbname):
					print "\033[31mSkipping database %s\033[0m"%(appiondbname)
					time.sleep(1)
					continue
				if not self.project_dbupgrade.databaseExists(appiondbname):
					print "\033[31merror database %s does not exist\033[0m"%(appiondbname)
					time.sleep(1)
					continue
				self.appion_dbupgrade = dbupgrade.DBUpgradeTools('appiondata', appiondbname, drop=True)
				print "\033[35mUpgrading %s\033[0m" % (self.appion_dbupgrade.getDatabaseName())
				self.upgradeAppionDB()
		print divider
		return

	def run(self):
		commit_count = self.updatelib.getCommitCount()
		#check if other updates should be run first
		if self.updatelib.getDatabaseRevision() < self.minSchemaNumberRequired:
			raise RuntimeError("\033[31mPlease run other prior updates first\033[0m")
		if self.updatelib.needUpdate(self.schemaNumber, self.force) is False:
			print ("\033[31mUpdate not needed\033[0m")
			sys.exit(0)
		self.runUpdates()
		print "\033[35mSuccessful Update\033[0m"
		self.commitUpdate()

if __name__ == "__main__":
	update = SchemaUpdate(backup=False)
	update.run()
