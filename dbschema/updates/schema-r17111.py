#!/usr/bin/env python
import baseSchemaClass

class SchemaUpdate17111(baseSchemaClass.SchemaUpdate):
	'''
	This will add boolean 'advanced' field to leginon.UserData to indicate if a user is an advanced user 
	'''

	def upgradeLeginonDB(self):
		if not self.leginon_dbupgrade.columnExists('UserData', 'advanced'):
			self.leginon_dbupgrade.addColumn('UserData', 'advanced', self.leginon_dbupgrade.bool)

if __name__ == "__main__":
	update = SchemaUpdate17111()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()
