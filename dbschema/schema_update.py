#!/usr/bin/env python

import os
import sys
import updatelib
from sinedon import dbupgrade
from leginon import projectdata

project_dbupgrade = dbupgrade.DBUpgradeTools('projectdata', drop=True)

if __name__ == "__main__":
	sq = projectdata.schemaupdates()
	sdata = sq.query(results=1)
	print sdata[0]
	sys.exit(1)
	updatelib_inst = updatelib.UpdateLib(project_dbupgrade)
	commit_count = updatelib_inst.getCommitCount()
	schema_number_list = updatelib_inst.getBranchUpdateSequence()
	revision_in_database = updatelib_inst.getDatabaseRevision(True)
	update_list = []
	# get a list of needed schema update
	for schema_number in schema_number_list:
		need_update = updatelib_inst.needUpdate(commit_count,schema_number)
		schema_pythonfile = "schema-r%d.py" % (schema_number)
		if need_update and os.path.exists(schema_pythonfile):
			update_list.append("python %s" % (schema_pythonfile))
	# log the package revision at the end of successful updates
	# revision 1000000000 is a dummy for unknown head revision
	if revision_in_database < 1000000000 and commit_count > revision_in_database:
		update_list.append("python log_package_revision.py")

	# print out the results
	if len(update_list):
		outputstring = "\n".join(update_list)
		print ""
		print "\033[36m------Copy the following lines to command terminal to run -------\033[0m"
		print outputstring
		print ""
	else:
		print "\033[35mNo database schema update script need or can be run \033[0m" 
