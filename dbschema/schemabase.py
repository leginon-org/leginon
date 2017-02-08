#!/usr/bin/env python
import time
import string
import updatelib
from sinedon import dbupgrade, dbconfig

class SchemaUpdate(object):
	#######################################################################
	#
	# Functions to include in every schema update sub-class 
	#
	#######################################################################

	def setFlags(self):
		"""
		define LeginonDB upgrade in this function
		"""
		raise NotImplementedError
		# can this schema update be run more than once and not break anything
		self.isRepeatable = False 
		# what is the number associated with this update, use 'git rev-list --count HEAD'
		self.revisionNumber = -1
		#what is the git tag name
		self.gitTagName = 'schema1'
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
		self.project_dbupgrade = dbupgrade.DBUpgradeTools('projectdata', drop=True)
		self.leginon_dbupgrade = dbupgrade.DBUpgradeTools('leginondata', drop=True)
		self.updatelib = updatelib.UpdateLib(self.project_dbupgrade)
		self.selected_revision = self.getSchemaRevision()
		self.backup = backup
		self.excluded_appiondbs = []
		self.setForceUpdate(False)

	def appendToExcluded_AppionDBs(self,dbname):
		self.excluded_appiondbs.append(dbname)

	def inExcluded_AppionDBList(self,appiondbname):
		if appiondbname in self.excluded_appiondbs:
			return True
		return False

	def getSchemaRevision(self):
		if self.revisionNumber > 0:
			return self.revisionNumber
		raise ValueError("script revision number is invalid")

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
		if not self.force:
			self.updatelib.updateDatabaseReset(self.updatelib.db_revision)
			self.updatelib.updateDatabaseRevision(self.selected_revision)
			print "\033[35mUpdated install table reset and revision\033[0m"
		else:
			print "\033[35mForced Update does not update install table reset and revision\033[0m"

	def setForceUpdate(self,is_force):
		self.force = is_force

	def run(self):
		if not self.required_upgrade:
			print "\033[31mNothing to do\033[0m"
			return
		divider = "-------------------------------------------"
		checkout_revision = self.updatelib.getCheckOutRevision()
		revision_in_database = self.updatelib.getDatabaseRevision()
		if self.updatelib.needUpdate(checkout_revision,self.selected_revision,self.force) == 'now':
			try:
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
			except:
				print "\033[31mUpdate failed\033[0m"
				raise
			print divider
			print "\033[35mSuccessful Update\033[0m"
			self.commitUpdate()

if __name__ == "__main__":
	update = SchemaUpdate(backup=False)
	update.run()
