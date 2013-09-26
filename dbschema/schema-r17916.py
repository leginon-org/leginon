#!/usr/bin/env python
import schemabase
from leginon import leginondata, ddinfo

class SchemaUpdate17916(schemabase.SchemaUpdate):
	'''
	This schema adds probe as a field in related calibration so that we can add nanoprobe, too. 
	'''

	def upgradeLeginonDB(self):
		if not self.leginon_dbupgrade.tableExists('EucentricFocusData'):
			return
		
		# EucentricFocusData
		# initialize column by inserting the most recent data
		last_data = leginondata.EucentricFocusData().query(results=1)[0]
		q = leginondata.EucentricFocusData(initializer=last_data,probe='micro')
		q.insert()
		# update as 'micro' as default
		r = leginondata.EucentricFocusData().query()
		r.reverse()
		for data in r:
			q = "UPDATE `EucentricFocusData` SET `probe` = 'micro' WHERE `DEF_id` =%d" % data.dbid
			self.leginon_dbupgrade.executeCustomSQL(q)

		# RotationCenterData
		# initialize column by inserting the most recent data
		last_data = leginondata.RotationCenterData().query(results=1)[0]
		q = leginondata.RotationCenterData(initializer=last_data,probe='micro')
		q.insert()
		# update as 'micro' as default
		r = leginondata.RotationCenterData().query()
		r.reverse()
		for data in r:
			q = "UPDATE `RotationCenterData` SET `probe` = 'micro' WHERE `DEF_id` =%d" % data.dbid
			self.leginon_dbupgrade.executeCustomSQL(q)

		# MatrixCalibrationData
		# initialize column by inserting the most recent data
		last_data = leginondata.MatrixCalibrationData().query(results=1)[0]
		q = leginondata.MatrixCalibrationData(initializer=last_data,probe='micro')
		q.insert()
		r = leginondata.MatrixCalibrationData().query()
		r.reverse()
		for data in r:
				# update as 'micro' as default only on 'defocus' and 'stigx','stigy'
				if data['type'] in ('defocus','stigx','stigy'):
					q = "UPDATE `MatrixCalibrationData` SET `probe` = 'micro' WHERE `DEF_id` =%d" % data.dbid
					self.leginon_dbupgrade.executeCustomSQL(q)

		
if __name__ == "__main__":
	update = SchemaUpdate17916()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()
