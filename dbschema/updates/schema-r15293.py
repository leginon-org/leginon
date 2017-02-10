#!/usr/bin/env python
import schemabase
import leginon.leginondata
import leginon.projectdata
from appionlib import apParticle
from appionlib import appiondata

class SchemaUpdate15293(schemabase.SchemaUpdate):
	'''
	This will update several appionTables
	'''
	def upgradeAppionDB(self):
		for tablename in ('ApAppionJobData','ApInitialModelData','ApPathData','ApSymmetryData','ApTemplateImageData'):
			if self.appion_dbupgrade.tableExists(tablename):
				updateq = ("ALTER TABLE "+tablename+" "
					+" MODIFY `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP "
					)
				self.appion_dbupgrade.executeCustomSQL(updateq)

if __name__ == "__main__":
	update = SchemaUpdate15293()
	# update only leginon database
	update.setRequiredUpgrade('appion')
	update.run()

