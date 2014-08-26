#!/usr/bin/env python
import schemabase

class SchemaUpdate15497(schemabase.SchemaUpdate):
	'''
	This will add boolean 'advanced' field to leginon.UserData to indicate if a user is an advanced user 
	'''
	def __init__(self):
		super(SchemaUpdate15497,self).__init__()

	def upgradeLeginonDB(self):
		if not self.leginon_dbupgrade.columnExists('UserData', 'noleginon'):
			self.leginon_dbupgrade.addColumn('UserData', 'noleginon', self.leginon_dbupgrade.bool)

if __name__ == "__main__":
	update = SchemaUpdate15497()
	update.setForceUpdate(True)
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()
