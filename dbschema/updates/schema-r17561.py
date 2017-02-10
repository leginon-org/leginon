#!/usr/bin/env python
import schemabase
from leginon import leginondata

class SchemaUpdate17561(schemabase.SchemaUpdate):
	'''
	This schema update converts frame rate to frame time if present
	'''

	def upgradeLeginonDB(self):
		if not self.leginon_dbupgrade.columnExists('CameraEMData', 'frame rate'):
			return
		if not self.leginon_dbupgrade.columnExists('CameraEMData', 'frame time'):
			self.leginon_dbupgrade.addColumn('CameraEMData', 'frame time', self.leginon_dbupgrade.float)

		query = "SELECT `DEF_id` as dbid, `frame rate` FROM `CameraEMData` WHERE `frame rate` IS NOT NULL"
		results = self.leginon_dbupgrade.returnCustomSQL(query)
		for r in results:
			if r[1] > 0:
				seconds = 1.0 / r[1]
				ms = seconds * 1000
				status = self.leginon_dbupgrade.updateColumn('CameraEMData','frame time','%e' % ms,'`DEF_id`=%d' % r[0],True)
				if not status:
					print 'break_from_failed_update'
		
if __name__ == "__main__":
	update = SchemaUpdate17561()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()
