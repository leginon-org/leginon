#!/usr/bin/env python

import updatelib
from sinedon import dbupgrade

project_dbupgrade = dbupgrade.DBUpgradeTools('projectdata', drop=True)

if __name__ == "__main__":
	updatelib_inst = updatelib.UpdateLib(project_dbupgrade)
	checkout_version = updatelib_inst.getPackageVersion()
	commit_count = updatelib_inst.getCommitCount()
	revision_in_database = updatelib_inst.getDatabaseRevision()
	if commit_count < 1000000000:
		updatelib_inst.updateDatabaseVersion(checkout_version)
		if updatelib_inst.allowVersionLog(commit_count):
			updatelib_inst.updateDatabaseRevision(commit_count)
			updatelib_inst.deleteDatabaseReset()
			print "\033[35mRevision Updated in the database\033[0m"
	else:
		print "\033[35mUnknown Revision, nothing to do\033[0m"
