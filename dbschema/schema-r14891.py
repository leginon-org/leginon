#!/usr/bin/env python
import schemabase

class SchemaUpdate14891(schemabase.SchemaUpdate):

# This will update leginon databases that were installed prior to r14897.
# This script is going to fix the timestamp problem on LaunchedApplicationData table.
# Originally default timestamp set to null which cause leginon session not remember
# last launched application since a query for recent time fails.
# see issue number 942 in redmine.
	def upgradeLeginonDB(self):
		if self.leginon_dbupgrade.tableExists('LaunchedApplicationData'):
			alterSQL = (" Alter Table LaunchedApplicationData " + 
					" Modify `DEF_timestamp` timestamp not null " + 
					" default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP")

			result = self.leginon_dbupgrade.executeCustomSQL(alterSQL)

if __name__ == "__main__":
	update = SchemaUpdate14891()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()

