#!/usr/bin/env python
import datetime
import schemabase
from appionlib import appiondata
from leginon import projectdata

class SchemaUpdate17982(schemabase.SchemaUpdate):
	'''
	This change the sign of angle_astigmatism to +x to +y as positive
	'''
	def __init__(self,backup=False):
		super(SchemaUpdate17982, self).__init__()
		self.deltadays = 0
		self.checktime = datetime.datetime.now() + datetime.timedelta(days=self.deltadays)

	def hasRecentEntry(self):
		if self.appion_dbupgrade.tableExists('ApCtfData'):
			results = appiondata.ApCtfData().query(results=1)
			if results:
				ctfdata = results[0]
				if ctfdata.timestamp > self.checktime:
					return True
		if self.appion_dbupgrade.tableExists('ApStackRunData'):
			results = appiondata.ApStackRunData().query(results=1)
			if results:
				stackrundata = results[0]
				if stackrundata.timestamp > self.checktime and stackrundata['stackParams']['phaseFlipped']:
					return True
		return False

	def upgradeAppionDB(self):
		if not self.appion_dbupgrade.tableExists('ApCtfData'):
			return

		# CtfData
		r = appiondata.ApCtfData().query()
		r.reverse()
		for data in r:
			if data['angle_astigmatism']:
				# Only change non-zero or non- None results
				q = "UPDATE `ApCtfData` SET `angle_astigmatism` = %e WHERE `DEF_id` =%d" % (-data['angle_astigmatism'], data.dbid)
				self.appion_dbupgrade.executeCustomSQL(q)

if __name__ == "__main__":
	update = SchemaUpdate17982()
	# update only appion database
	update.setRequiredUpgrade('appion')
	# You may exclude a processing database that is currently been used
	#update.appendToExcluded_AppionDBs('ap1')
	update.run()
