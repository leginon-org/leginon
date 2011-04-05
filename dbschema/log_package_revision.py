#!/usr/bin/env python
from sinedon import dbupgrade, dbconfig
import updatelib

project_dbupgrade = dbupgrade.DBUpgradeTools('projectdata', drop=True)

if __name__ == "__main__":
	checkout_version = updatelib.getPackageVersion()
	checkout_revision = updatelib.getCheckOutRevision()
	revision_in_database = updatelib.getDatabaseRevision(project_dbupgrade)
	if checkout_revision < 1000000000:
		updatelib.updateDatabaseVersion(project_dbupgrade,checkout_version)
		if updatelib.allowVerisionLog(project_dbupgrade,checkout_revision):
			updatelib.updateDatabaseRevision(project_dbupgrade,checkout_revision)
			print "\033[35mRevision Updated in the database\033[0m"
	else:
		print "\033[35mUnknown Revision, nothing to do\033[0m"
