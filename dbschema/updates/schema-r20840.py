#!/usr/bin/env python

from . import baseSchemaClass
from sinedon import directq
from leginon import leginondata

class SchemaUpdate(baseSchemaClass.SchemaUpdate):
	'''
	This schema add and set intended defocus field to existing ScopeEMData
	Issue #6538
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
		self.schemaNumber = 20840
		# minimum update required (set to previous schema update number)
		self.minSchemaNumberRequired = 20369
		# minimum myami version
		self.minimumMyamiVersion = 3.5
		#what is the git tag name
		self.schemaTagName = 'schema20840'
		#git tag <tag name> <commit id>
		#git tag schema1 9fceb02
		#flags for what databases are updated and which ones are not
		self.modifyAppionDB = False
		self.modifyLeginonDB = True
		self.modifyProjectDB = False

	def upgradeLeginonDB(self):
		# Make DEF_timestamp not to update values
		query = '''ALTER TABLE ScopeEMData Change `DEF_timestamp` `DEF_timestamp` 
							TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
						'''	
		results = directq.complexMysqlQuery('leginondata',query)
		# add column
		self.addFloatColumn('leginondata', 'ScopeEMData', 'intended defocus')
		# This update would take very long if it is a big database.
		# It is not practical to do on past data.  Data size is so
		# bit now that we can have 10000 record in less than a day.
		if False:
			self.setIntendedDefocus()
		else:
			print('Skipping setting values on old data because it would have taken too long')

	#######################################################################
	#
	# Custom functions
	#
	#######################################################################
	def setIntendedDefocus(self):
		# Set default values
		query = '''UPDATE ScopeEMData SET `intended defocus` = `defocus` WHERE
							`intended defocus` IS NULL;'''
		print('Updating ScopeEMData intended defocus....')
		results = directq.complexMysqlQuery('leginondata',query)

		# Substract delta z correction
		query = '''SELECT image.`REF|ScopeEMData|scope` as scope_id, 
							emtarget.`delta z` as delta_z FROM
							AcquisitionImageData image LEFT JOIN EMTargetData emtarget
							on image.`REF|EMTargetData|emtarget`=emtarget.`DEF_id`
							WHERE emtarget.`delta z` > 1e-9 or emtarget.`delta z` < -1e-9;'''
		results = directq.complexMysqlQuery('leginondata',query)
		print(('Updating %d stage tilt image shift correction....' % (len(results),)))
		for r in results:
			delta_z = r['delta_z']
			scope_id = r['scope_id']
			query = '''UPDATE ScopeEMData SET	`intended defocus` = `intended defocus`- %.12f where DEF_id=%d''' % (delta_z, scope_id)
			results = directq.complexMysqlQuery('leginondata',query)

if __name__ == "__main__":
	update = SchemaUpdate()
	update.run()
