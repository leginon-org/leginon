#!/usr/bin/env python

import sys
from sinedon import dbupgrade, dbconfig
from leginon import projectdata, leginondata

# This will update databases that were archived with auto_increment off.
excluding_tablenames = ['ImportMappingData','ImportDBConfigData']

def activateAutoIncrement(database):
	q = 'Show Tables;'
	r = database.returnCustomSQL(q)
	if not r:
		print "No archive to be deactivate"
		return
	if r[0] == 'AcquisitionFFTData':
		print "Acting on original data. STOP!!!!!"
		raw_input('kill this!!!!')
		return
	for tablenametuple in r:
		tablename = tablenametuple[0]
		if tablename in excluding_tablenames:
			continue
		if database.columnExists(tablename, 'DEF_id'):
			q = 'ALTER TABLE `%s` CHANGE `DEF_id` `DEF_id` INT(16) NOT NULL;' % (tablename,)
			database.executeCustomSQL(q)

if __name__ == "__main__":
	projectdb = dbupgrade.DBUpgradeTools('projectdata')
	activateAutoIncrement(projectdb)
	leginondb = dbupgrade.DBUpgradeTools('leginondata')
	activateAutoIncrement(leginondb)
