#!/usr/bin/env python

from . import baseSchemaClass
from sinedon import directq
from leginon import leginondata

class SchemaUpdate(baseSchemaClass.SchemaUpdate):
	'''
	This schema change add hidden field to existing GridHolderData
	Issue #5477
	'''

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
		self.schemaNumber = 20369
		# minimum update required (set to previous schema update number)
		self.minSchemaNumberRequired = 19470
		# minimum myami version
		self.minimumMyamiVersion = 3.3
		#what is the git tag name
		self.schemaTagName = 'schema20369'
		#git tag <tag name> <commit id>
		#git tag schema1 9fceb02
		#flags for what databases are updated and which ones are not
		self.modifyAppionDB = False
		self.modifyLeginonDB = True
		self.modifyProjectDB = False

	def upgradeLeginonDB(self):
		self.addBooleanColumn('leginondata', 'GridHolderData', 'hidden')

	#######################################################################
	#
	# Custom functions
	#
	#######################################################################

if __name__ == "__main__":
	update = SchemaUpdate()
	update.run()
