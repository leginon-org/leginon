#!/usr/bin/env python
import schemabase
from sinedon import directq
from leginon import leginondata

class SchemaUpdate19470(schemabase.SchemaUpdate):
	'''
	This schema change fixes coordinates for template saved as list, not tuple bug
	in json settings data import. Issue #3893
	'''

	def upgradeLeginonDB(self):
		self.searchmap = {
				'JAHCFinderSettingsData':('acquisition template', 'focus template'),
		}

		for class_name in self.searchmap.keys():
			if not self.leginon_dbupgrade.tableExists(class_name):
				continue
		
			alldbids = set([])
			for field_key in ('acquisition template', 'focus template'):
				pattern_dbids = self.getPatternDBIDs(class_name, field_key)
				alldbids = alldbids.union(pattern_dbids)
			alldbids = list(alldbids)
			alldbids.sort()
			self. correctData(class_name, alldbids)

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
	update = SchemaUpdate19470()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()
