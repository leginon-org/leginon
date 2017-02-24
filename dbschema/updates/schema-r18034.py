#!/usr/bin/env python

import baseSchemaClass

class SchemaUpdate(baseSchemaClass.SchemaUpdate):
	"""
	This schema change hidden column in SessionData to allow null
	because sinedon requires it.
	"""

	#######################################################################
	#
	# Functions to include in every schema update sub-class 
	#
	#######################################################################

	def setFlags(self):
		# can this schema update be run more than once and not break anything
		self.isRepeatable = False 
		# should this schema update be run again whenever the branch is upgraded, i.e., 3.1 -> 3.2
		self.reRunOnBranchUpgrade = False
		# what is the number associated with this update, use 'git rev-list --count HEAD'
		self.schemaNumber = 18034
		# minimum update required (set to previous schema update number)
		self.minSchemaNumberRequired = 18000
		# minimum myami version
		self.minimumMyamiVersion = 3.2
		#what is the git tag name
		self.schemaTagName = 'schema18034'
		#git tag <tag name> <commit id>
		#git tag schema1 9fceb02
		#flags for what databases are updated and which ones are not
		self.modifyAppionDB = False
		self.modifyLeginonDB = True
		self.modifyProjectDB = False
	
	def upgradeLeginonDB(self):
		if not self.leginon_dbupgrade.tableExists('SessionData'):
			return
		if not self.leginon_dbupgrade.columnExists('SessionData', 'hidden'):
			self.leginon_dbupgrade.addColumn('ApplicationData', 'hidden', self.leginon_dbupgrade.bool)
		else:
			q = "DESCRIBE `SessionData` hidden"
			results = self.leginon_dbupgrade.returnCustomSQL(q)
			if results[0][2].lower() == 'no':
				q = "ALTER TABLE `SessionData` modify `hidden` tinyint NULL default 0"
				self.leginon_dbupgrade.executeCustomSQL(q)

if __name__ == "__main__":
	update = SchemaUpdate()
	update.run()
