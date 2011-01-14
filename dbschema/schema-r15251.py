#!/usr/bin/env python
import schemabase
import leginon.leginondata
import leginon.projectdata
from appionlib import apParticle
from appionlib import appiondata

class SchemaUpdate15251(schemabase.SchemaUpdate):
	'''
	This will update ApManualParamsData to give trace field
	'''
	def upgradeAppionDB(self):
		if self.appion_dbupgrade.columnExists('ApContourData', 'runname'):
			if not self.appion_dbupgrade.columnExists('ApManualParamsData', 'trace'):
				self.appion_dbupgrade.addColumn('ApManualParamsData', 'trace', self.appion_dbupgrade.bool)
			contourq = appiondata.ApContourData()
			contours = contourq.query()
			for contourdata in contours:
				paramid = contourdata['selectionrun']['manparams'].dbid
				if paramid:
					updateq = ("UPDATE ApManualParamsData AS mp "
						+" SET "
						+"  mp.`trace` = 1 "
						+" WHERE mp.`DEF_id` = %d " % paramid
					)
					self.appion_dbupgrade.executeCustomSQL(updateq)

if __name__ == "__main__":
	update = SchemaUpdate15251()
	# update only leginon database
	update.setRequiredUpgrade('appion')
	update.run()

