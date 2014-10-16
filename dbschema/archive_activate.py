#!/usr/bin/env python

import sys
from sinedon import dbupgrade, dbconfig
from leginon import projectdata, leginondata

# This will update databases that were archived with auto_increment off.

def activateAutoIncrement(database):
	q = 'Show Tables;'
	r = database.returnCustomSQL(q)
	print r
	for tablenametuple in r:
		tablename = tablenametuple[0]
		if database.columnExists(tablename, 'DEF_id'):
			q = 'ALTER TABLE `%s` CHANGE `DEF_id` `DEF_id` INT(16) NOT NULL AUTO_INCREMENT;' % (tablename,)
			database.executeCustomSQL(q)

if __name__ == "__main__":
	projectdb = dbupgrade.DBUpgradeTools('projectdata')
	activateAutoIncrement(projectdb)
	leginondb = dbupgrade.DBUpgradeTools('leginondata')
	activateAutoIncrement(leginondb)
