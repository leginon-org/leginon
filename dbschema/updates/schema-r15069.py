#!/usr/bin/env python
import schemabase
import leginon.leginondata
import leginon.projectdata

class SchemaUpdate15069(schemabase.SchemaUpdate):
	'''
	This will update project database to create privilege level of banned user
	and add such a group in leginon database
	refer to redmine issue #1053 and #1059 and in sync with 
	revision r15069 which add these database entry to new installation
	'''
	def upgradeLeginonDB(self):
		qp = leginon.projectdata.privileges()
		qp['description'] = 'No privilege for anything'
		qp['groups'] = 0
		qp['users'] = 0
		qp['projects'] = 0
		qp['projectowners'] = 0
		qp['shareexperiments'] = 0
		qp['data'] = 0
		qp['gridboxes'] = 0
		q = leginon.leginondata.GroupData()
		q['privilege'] =qp
		q['name'] = 'disabled'
		q['description'] = 'Disabled Group - locked users'
		q.insert()

if __name__ == "__main__":
	update = SchemaUpdate15069()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()

