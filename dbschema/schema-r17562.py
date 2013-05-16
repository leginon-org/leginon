#!/usr/bin/env python
import schemabase
from leginon import leginondata

class SchemaUpdate17562(schemabase.SchemaUpdate):
	'''
	This schema update converts frame rate to frame time if present
	'''

	def upgradeLeginonDB(self):
		if not self.leginon_dbupgrade.columnExists('CameraEMData', 'nframes'):
			return
		if not self.leginon_dbupgrade.columnExists('CameraEMData', 'frame time'):
			self.leginon_dbupgrade.addColumn('CameraEMData', 'frame time', self.leginon_dbupgrade.float)

		query = "SELECT `DEF_id` as dbid, `nframes`, `frame time`, `exposure time` FROM `CameraEMData` WHERE `nframes` IS NOT NULL"
		results = self.leginon_dbupgrade.returnCustomSQL(query)
		for r in results:
			if r[1] and r[2] is None:
				ms = r[3] / r[1]
				status = self.leginon_dbupgrade.updateColumn('CameraEMData','frame time','%e' % ms,'`DEF_id`=%d' % r[0],True)
				if not status:
					print 'break_from_failed_update'
		
if __name__ == "__main__":
	update = SchemaUpdate17562()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()
