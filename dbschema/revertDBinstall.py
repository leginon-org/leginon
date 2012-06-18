#!/usr/bin/env python
from sinedon import dbupgrade, dbconfig
import updatelib

project_dbupgrade = dbupgrade.DBUpgradeTools('projectdata', drop=True)

if __name__ == "__main__":
	updatelib_inst = updatelib.UpdateLib(project_dbupgrade)
	checkout_version = raw_input('Revert to checkout version, for example, 2.1 -->')
	if checkout_version != 'trunk':
		try:
			map((lambda x:int(x)),checkout_version.split('.')[:2])
		except:
			print "valid versions are 'trunk', '2.1', or '2.1.2' etc"
			raise
	checkout_revision = int(raw_input('Revert to checkout revision, for example, 16500 -->'))
	updatelib_inst.updateDatabaseVersion(checkout_version)
	print "\033[35mVersion Updated in the database %s\033[0m" % checkout_version
	updatelib_inst.updateDatabaseRevision(checkout_revision)
	print "\033[35mRevision Updated in the database as %d\033[0m" % checkout_revision
