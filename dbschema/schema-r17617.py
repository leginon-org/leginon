#!/usr/bin/env python
import schemabase
from leginon import leginondata, ddinfo

class SchemaUpdate17617(schemabase.SchemaUpdate):
	'''
	This schema update frame path
	'''

	def upgradeLeginonDB(self):
		if not self.leginon_dbupgrade.columnExists('SessionData', 'frame path'):
			return
		sessions = leginondata.SessionData().query()
		for sessiondata in sessions:
			if sessiondata['frame path']:
				continue
			imagepath = sessiondata['image path']
			if not imagepath:
				continue
			framepath = ddinfo.getRawFrameSessionPathFromImagePath(imagepath)
			self.leginon_dbupgrade.updateColumn('SessionData', 'frame path',"'"+framepath+"'",'`DEF_id`=%d' % sessiondata.dbid,True)
		
if __name__ == "__main__":
	update = SchemaUpdate17617()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()
