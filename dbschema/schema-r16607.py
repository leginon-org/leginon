#!/usr/bin/env python
import schemabase
import leginon.leginondata
import sys,os

class SchemaUpdate16607(schemabase.SchemaUpdate):
	'''
	This will copy first preset order in focuser settings to manual focus preset
	'''

	def upgradeLeginonDB(self):
		if self.leginon_dbupgrade.tableExists('FocuserSettingsData'):
			if (not self.leginon_dbupgrade.columnExists('FocuserSettingsData','manual focus preset')):
				self.leginon_dbupgrade.addColumn('FocuserSettingsData', 'manual focus preset', self.leginon_dbupgrade.str)
			q = leginon.leginondata.FocuserSettingsData()
			print 'Querying All Focuser Settings....'
			results = q.query()
			for qdata in results:
				presets = qdata['preset order']
				if not presets:
					continue
				first_preset = presets[0]
				old_manual_focus_preset = qdata['manual focus preset']
				if old_manual_focus_preset is None and first_preset:
				# only do the schema upgrade if FocuserSettingsData has no value in manual focus preset'
					query = "Update FocuserSettingsData set `manual focus preset`='%s' WHERE FocuserSettingsData.`DEF_id`=%d;" % (first_preset,qdata.dbid)
					self.leginon_dbupgrade.executeCustomSQL(query)

if __name__ == "__main__":
	update = SchemaUpdate16607()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()

