#!/usr/bin/env python
import schemabase
from leginon import leginondata, ddinfo

class SchemaUpdate17797(schemabase.SchemaUpdate):
	'''
	This schema adds trash status to ViewerImageStatus.  This is supposed to be for r17797 but wasn't made 
	until r17812 was made.  So we will call the module 17813
	'''

	def upgradeLeginonDB(self):
		if not self.leginon_dbupgrade.tableExists('ViewerImageStatus'):
			return
		q = "ALTER TABLE `ViewerImageStatus` CHANGE `status` `status` ENUM( 'hidden', 'visible', 'exemplar', 'trash' ) DEFAULT NULL "
		self.leginon_dbupgrade.executeCustomSQL(q)

		
if __name__ == "__main__":
	update = SchemaUpdate17797()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()
