#!/usr/bin/env python
from sinedon import dbupgrade, dbconfig
import updatelib

project_dbupgrade = dbupgrade.DBUpgradeTools('projectdata', drop=True)

if __name__ == "__main__":
	updatelib_inst = updatelib.UpdateLib(project_dbupgrade)
	checkout_version = updatelib_inst.getPackageVersion()
	checkout_revision = updatelib_inst.getCheckOutRevision()
	revision_in_database = updatelib_inst.getDatabaseRevision()
	if checkout_revision < 1000000000:
		updatelib_inst.updateDatabaseVersion(checkout_version)
		if updatelib_inst.allowVersionLog(checkout_revision):
			updatelib_inst.updateDatabaseRevision(checkout_revision)
			updatelib_inst.deleteDatabaseReset()
			print "\033[35mRevision Updated in the database\033[0m"
	else:
		print "\033[35mUnknown Revision, nothing to do\033[0m"
