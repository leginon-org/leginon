#!/usr/bin/env python
import schemabase
from appionlib import appiondata
import sys,os

class SchemaUpdate16412(schemabase.SchemaUpdate):
	'''
	This will scale contour point coordinates to original image size
	'''

	def upgradeAppionDB(self):
		if self.appion_dbupgrade.tableExists('ApContourPointData'):
			q = appiondata.ApContourPointData()
			results = q.query()
			for pointdata in results:
				bin = pointdata['contour']['selectionrun']['manparams']['bin']
				pointid = pointdata.dbid
				new_x = pointdata['x']*bin
				new_y = pointdata['y']*bin
				self.appion_dbupgrade.updateColumn('ApContourPointData','x',new_x,'`DEF_id`=%d' % pointid, timestamp=False)
				self.appion_dbupgrade.updateColumn('ApContourPointData','y',new_y,'`DEF_id`=%d' % pointid, timestamp=False)

if __name__ == "__main__":
	update = SchemaUpdate16412()
	# update only appion database
	update.setRequiredUpgrade('appion')
	update.run()

