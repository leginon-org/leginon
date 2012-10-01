#!/usr/bin/env python
import schemabase

class SchemaUpdate17035(schemabase.SchemaUpdate):
	'''
	This will add fields to appion.ApCtfData to allow myamiweb query on old estimation 
	'''
	def upgradeAppionDB(self):
		if self.appion_dbupgrade.tableExists('ApCtfData'):
			strings = ['graph3','graph4']
			for colname in strings:
				if (not self.appion_dbupgrade.columnExists('ApCtfData',colname)):
					self.appion_dbupgrade.addColumn('ApCtfData', colname, self.appion_dbupgrade.str)
			floats = ['confidence_30_10', 'confidence_5_peak', 'resolution_80_percent','resolution_50_percent']
			for colname in floats:
				if (not self.appion_dbupgrade.columnExists('ApCtfData',colname)):
					self.appion_dbupgrade.addColumn('ApCtfData', colname, self.appion_dbupgrade.float)

if __name__ == "__main__":
	update = SchemaUpdate17035()
	# update only leginon database
	update.setRequiredUpgrade('appion')
	update.run()
