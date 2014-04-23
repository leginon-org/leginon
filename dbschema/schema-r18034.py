#!/usr/bin/env python
import schemabase
from leginon import leginondata

class SchemaUpdate18034(schemabase.SchemaUpdate):
	'''
	This schema change hidden column in SessionData to allow null
  because sinedon requires it.
	'''

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
	update = SchemaUpdate18034()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()
