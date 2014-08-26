#!/usr/bin/env python
import time
from sinedon import dbupgrade, dbconfig
import updatelib

class SchemaUpdate(object):
	'''
		Base Class for database schema upgrade.  Please name the supclass as
		SchemaUpdatexxxxx where xxxxx is the svn revision number.  See
		schema-r14891.py as an example
	'''

	def __init__(self,backup=False):
		self.project_dbupgrade = dbupgrade.DBUpgradeTools('projectdata', drop=True)
		self.leginon_dbupgrade = dbupgrade.DBUpgradeTools('leginondata', drop=True)
		self.updatelib = updatelib.UpdateLib(self.project_dbupgrade)
		self.selected_revision = self.getSchemaRevision()
		self.backup = backup
		self.valid_upgrade = ['leginon','project','appion']
		self.required_upgrade = self.valid_upgrade
		self.excluded_appiondbs = []
		self.setForceUpdate(False)

	def appendToExcluded_AppionDBs(self,dbname):
		self.excluded_appiondbs.append(dbname)

	def inExcluded_AppionDBList(self,appiondbname):
		if appiondbname in self.excluded_appiondbs:
			return True
		return False

	def setRequiredUpgrade(self,input):
		list = []
		if type(input) == type([]):
			list = input
		else:
			list.append(input)
		for item in list:
			try:
				self.valid_upgrade.index(item)
			except:
				raise
		self.required_upgrade = list

	def getSchemaRevision(self):
		name = self.__class__.__name__
		digits = name.strip('SchemaUpdate')
		if digits.isdigit():
			return int(digits)

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

	def upgradeLeginonDB(self):
		'''
			define LeginonDB upgrade in this function
		'''
		pass

	def upgradeProjectDB(self):
		'''
			define ProjectDB upgrade in this function
		'''
		pass

	def upgradeAppionDB(self):
		'''
			define ProjectDB upgrade in this function
		'''
		pass

	def appionbackup(self,appiondblist):
		appiondb_unique_list = list(set(appiondblist))
		for appiondbname in appiondb_unique_list:
			if not self.project_dbupgrade.databaseExists(appiondbname):
				print "\033[31merror database %s does not exist\033[0m"%(appiondbname)
				time.sleep(1)
				continue
			appion_dbupgrade = dbupgrade.DBUpgradeTools('appiondata', appiondbname, drop=True)
			appion_dbupgrade.backupDatabase("%s.sql" % (appiondbname), data=True)

	def commitUpdate(self):
		'''
		Log that this update has been completed and therefore can not be repeated.
		'''
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
				if 'leginon' in self.required_upgrade:
					# leginon part
					print divider
					if self.backup:
						self.leginon_dbupgrade.backupDatabase("leginondb.sql", data=True)
					print "\033[35mUpgrading %s\033[0m" % (self.leginon_dbupgrade.getDatabaseName())
					self.upgradeLeginonDB()
				if 'project' in self.required_upgrade:
					# project part
					print divider
					if self.backup:
						self.leginon_dbupgrade.backupDatabase("leginondb.sql", data=True)
					print "\033[35mUpgrading %s\033[0m" % (self.project_dbupgrade.getDatabaseName())
					self.upgradeProjectDB()
				if 'appion' in self.required_upgrade:
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
