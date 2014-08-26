#!/usr/bin/env python
import time
from sinedon import dbupgrade, dbconfig
from leginon import leginondata
from appionlib import appiondata

class ScanDB(object):
	'''
		Base Class for database query over Project,Leginon, and all Appion database.
	'''

	def __init__(self):
		self.project_dbtools = dbupgrade.DBUpgradeTools('projectdata')
		self.leginon_dbtools = dbupgrade.DBUpgradeTools('leginondata')

	def getAppionDatabases(self,project_dbtools):
		"""
		Get list of appion databases to upgrade
		"""
		if project_dbtools.columnExists('processingdb', 'appiondb'):
			colname = 'appiondb'
		elif project_dbtools.columnExists('processingdb', 'db'):
			colname = 'db'
		else:
			print "could not find appion tables"
			return []

		selectq = "SELECT DISTINCT "+colname+" FROM processingdb ORDER BY `REF|projects|project` ASC"
		results = project_dbtools.returnCustomSQL(selectq)
		appiondblist = []
		for result in results:
			appiondblist.append(result[0])
		#random.shuffle(appiondblist)
		return appiondblist

	def scanLeginonDB(self):
		'''
			define LeginonDB search in this function
		'''
		pass

	def scanProjectDB(self):
		'''
			define ProjectDB search in this function
		'''
		pass

	def scanAppionDB(self):
		'''
			define AppionDB search in this function
		'''
		pass

	def run(self):
		divider = "-------------------------------------------"
		try:
			print divider
			self.scanLeginonDB()
			print divider
			self.scanProjectDB()
			# appion part
			print divider
			appiondblist = self.getAppionDatabases(self.project_dbtools)
			for appiondbname in appiondblist:
				if not self.project_dbtools.databaseExists(appiondbname):
					print "\033[31merror database %s does not exist\033[0m"%(appiondbname)
					time.sleep(1)
					continue
				self.appion_dbtools = dbupgrade.DBUpgradeTools('appiondata', appiondbname, drop=True)
				self.scanAppionDB()
		except:
			print "\033[31mUpdate failed\033[0m"
			raise

class SearchPath(ScanDB):
	def __init__(self,searchdrive):
		super(SearchPath,self).__init__()
		self.searchdrive = searchdrive

	def scanLeginonDB(self):
		'''
		Use sinedon data object to query
		'''
		# get all session data objects
		allsessiondata = leginondata.SessionData().query()
		for sessiondata in allsessiondata:
			# when the selected field is not filled, it gives None, not empty string
			if not sessiondata['image path']:
				continue
			# text search
			if self.searchdrive in sessiondata['image path']:
				self.leginon_sessions.append(sessiondata['name'])

	def scanAppionDB(self):
		'''
		Alternatively, use mysql query directly.  
		The proper database is connected in self.appion_dbtools
		'''
		q = "select path from ApPathData where path like '%"+self.searchdrive+"%';"
		print q
		paths = self.appion_dbtools.returnCustomSQL(q)
		if paths:
			self.appion_paths.append(paths)

	def run(self):
		self.leginon_sessions = []
		self.appion_paths = []
		super(SearchPath,self).run()
		for sessionname in self.leginon_sessions:
			print sessionname
		print ''
		for aprundirs in self.appion_paths:
			# multiple records may be found by the query in one database
			for rundirs in aprundirs:
				# first item in the tuple is the first item in the mysql 'select' list
				rundir = rundirs[0]
				halves = rundir.split('appion')
				bits = halves[-1].split('/')
				# sessionname is always after the last 'appion/'
				sessionname = bits[1]
				# runname is typically the last part of the rundir
				runname = bits[-1]
				print sessionname,runname

if __name__ == "__main__":
	update = SearchPath('/archive/17/')
	update.run()
