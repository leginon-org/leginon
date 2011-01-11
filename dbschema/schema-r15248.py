#!/usr/bin/env python
import schemabase
import leginon.leginondata
import leginon.projectdata
from appionlib import apParticle
from appionlib import appiondata

class SchemaUpdate15248(schemabase.SchemaUpdate):
	'''
	This will update ApContourData to give ApSelectionRunData reference
	'''
	def upgradeAppionDB(self):
		if self.appion_dbupgrade.columnExists('ApContourData', 'runname'):
			if not self.appion_dbupgrade.columnExists('ApContourData', 'REF|ApSelectionRunData|selectionrun'):
				self.appion_dbupgrade.addColumn('ApContourData', 'REF|ApSelectionRunData|selectionrun', self.appion_dbupgrade.link, index=True)
			contourq = appiondata.ApContourData()
			contours = contourq.query()
			for contourdata in contours:
				if not contourdata['runname']:
					continue
				selectionrundata = apParticle.getSelectionRunDataFromName(contourdata['image'], contourdata['runname'])
				contourid = contourdata.dbid
				selectionid = selectionrundata.dbid
				if contourid and selectionid:
					updateq = ("UPDATE ApContourData AS contour "
						+" SET "
						+"   contour.`REF|ApSelectionRunData|selectionrun` =  "
						+" %d " % selectionid
						+" WHERE contour.`DEF_id` = %d " % contourid
					)
					self.appion_dbupgrade.executeCustomSQL(updateq)

if __name__ == "__main__":
	update = SchemaUpdate15248()
	# update only leginon database
	update.setRequiredUpgrade('appion')
	update.run()

