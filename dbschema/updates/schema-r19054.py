#!/usr/bin/env python

import baseSchemaClass
from sinedon import directq
from leginon import leginondata

class SchemaUpdate(baseSchemaClass.SchemaUpdate):
	"""
	This schema adds hidden column in InstrumentData and default to 0
	refs #4176 and refs #4655
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
		self.schemaNumber = 19054
		# minimum update required (set to previous schema update number)
		self.minSchemaNumberRequired = 18034
		# minimum myami version
		self.minimumMyamiVersion = 3.2
		#what is the git tag name
		self.schemaTagName = 'schema19054'
		#git tag <tag name> <commit id>
		#git tag schema1 9fceb02
		#flags for what databases are updated and which ones are not
		self.modifyAppionDB = False
		self.modifyLeginonDB = True
		self.modifyProjectDB = False

	def upgradeLeginonDB(self):
		self.searchmap = {
			'InstrumentData':('hidden'),
		}
		if not self.leginon_dbupgrade.tableExists('InstrumentData'):
			return
		if not self.leginon_dbupgrade.columnExists('Instrument', 'hidden'):
			# Insert fake data to add the column
			q = leginondata.InstrumentData(name='fake',hostname='localhost',hidden=True)
			q.insert()

		self.defaultBooleanToZero('InstrumentData','hidden')

	#######################################################################
	#
	# Custom functions
	#
	#######################################################################

	def defaultBooleanToZero(self, class_name, key):
		where_cause = "`%s` is Null" % (key)
		self.leginon_dbupgrade.updateColumn(class_name, key, 0, where_cause, timestamp=True)

if __name__ == "__main__":
	update = SchemaUpdate()
	update.run()
