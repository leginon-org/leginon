#!/usr/bin/env python

import baseSchemaClass
from sinedon import directq
from leginon import leginondata

class SchemaUpdate(baseSchemaClass.SchemaUpdate):
	'''
	This schema change fixes coordinates for template saved as list, not tuple bug
	in json settings data import. Issue #3893
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
		self.schemaNumber = 19470
		# minimum update required (set to previous schema update number)
		self.minSchemaNumberRequired = 18034
		# minimum myami version
		self.minimumMyamiVersion = 3.2
		#what is the git tag name
		self.schemaTagName = 'schema19470'
		#git tag <tag name> <commit id>
		#git tag schema1 9fceb02
		#flags for what databases are updated and which ones are not
		self.modifyAppionDB = False
		self.modifyLeginonDB = True
		self.modifyProjectDB = False

	def upgradeLeginonDB(self):
		self.searchmap = {
			'JAHCFinderSettingsData':('acquisition template', 'focus template'),
		}
		for class_name in self.searchmap.keys():
			if not self.leginon_dbupgrade.tableExists(class_name):
				continue
		
			alldbids = set([])
			for field_key in self.searchmap.get(class_name, []):
				pattern_dbids = self.getPatternDBIDs(class_name, field_key)
				alldbids = alldbids.union(pattern_dbids)
			alldbids = list(alldbids)
			alldbids.sort()
			self. correctData(class_name, alldbids)

	#######################################################################
	#
	# Custom functions
	#
	#######################################################################

	def getPatternDBIDs(self, class_name, key):
		if not self.leginon_dbupgrade.columnExists(class_name, 'SEQ|%s' % key):
			return []
		pattern = '%[[%'
		query = "Select `DEF_id` from %s where `SEQ|%s` like '%s' group by `SEQ|%s`" % (class_name, key, pattern, key)
		results = directq.complexMysqlQuery('leginondata',query)
		return map((lambda x: x['DEF_id']), results)

	def correctData(self, class_name, alldbids):
		if alldbids:
			print 'fixing %s at dbids %s' % (class_name, alldbids)
		for dbid in alldbids:
			c1 = getattr(leginondata,class_name)()
			class_data = c1.direct_query(dbid)
			c2 = getattr(leginondata,class_name)(initializer=class_data)
			for field_name in self.searchmap[class_name]:
				c2[field_name] = map((lambda x: tuple(x)),c2[field_name])
			c2.insert(force=True)

if __name__ == "__main__":
	update = SchemaUpdate()
	update.run()
