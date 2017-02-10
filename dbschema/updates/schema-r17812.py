#!/usr/bin/env python
import schemabase
from leginon import leginondata, ddinfo

class SchemaUpdate17812(schemabase.SchemaUpdate):
	'''
	This schema correct adjust for transform from no to one in Centered Square
	'''

	def upgradeLeginonDB(self):
		if not self.leginon_dbupgrade.columnExists('AcquisitionSettingsData', 'adjust for transform'):
			return
		users = leginondata.UserData().query()
		for userdata in users:
			sessionq = leginondata.SessionData(user=userdata)
			asettingsq = leginondata.AcquisitionSettingsData(session=sessionq,name='Centered Square')
			# only need to change the most recent one
			asettings = asettingsq.query(results=1)
			if asettings:
				asettingsdata = asettings[0]
				if asettingsdata['adjust for transform'] == 'no':
					print asettingsdata.dbid,asettingsdata['session']['name'],asettingsdata['session']['user']['username']
					self.leginon_dbupgrade.updateColumn('AcquisitionSettingsData', 'adjust for transform',"'one'",'`DEF_id`=%d' % asettingsdata.dbid,True)
		
if __name__ == "__main__":
	update = SchemaUpdate17812()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()
