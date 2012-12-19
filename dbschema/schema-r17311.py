#!/usr/bin/env python
import schemabase
from appionlib import appiondata, apDisplay

class SchemaUpdate17311(schemabase.SchemaUpdate):
	'''
	This will add a 'phaseflipped' field to appion.ApRefineStackData to allow querys on old refine stacks
	In general, eman and xmipp stacks are phaseflipped and Frealign stacks are not. 
	'''
	def upgradeAppionDB(self):
		if self.appion_dbupgrade.tableExists('ApRefineStackData'):
			colname = 'phaseflipped'
			if (not self.appion_dbupgrade.columnExists('ApRefineStackData',colname)):
				self.appion_dbupgrade.addColumn('ApRefineStackData', colname, self.appion_dbupgrade.bool)
				
				# get any existing entries in this table
				q = appiondata.ApRefineStackData()
				results = q.query()
				
				# Update the phaseflipped field for each row
				# based on what format the stack is.
				for row in results:
					defid = row.dbid
					if row['format'] == 'frealign':
						phaseflipped = 0  
					else:
						phaseflipped = 1
					self.appion_dbupgrade.updateColumn('ApRefineStackData', colname, phaseflipped,'`DEF_id`=%d' % defid, timestamp=False)

if __name__ == "__main__":
	update = SchemaUpdate17311()
	# update only appion database
	update.setRequiredUpgrade('appion')
	update.run()
