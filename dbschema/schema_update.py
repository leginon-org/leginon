#!/usr/bin/env python
import time
from sinedon import dbupgrade, dbconfig
from leginon import projectdata, leginondata
import updatelib
import os

project_dbupgrade = dbupgrade.DBUpgradeTools('projectdata', drop=True)

if __name__ == "__main__":
	updatelib_inst = updatelib.UpdateLib(project_dbupgrade)
	checkout_revision = updatelib_inst.getCheckOutRevision()
	schema_revisions = updatelib_inst.getBranchUpdateRevisionSequence()
	revision_in_database = updatelib_inst.getDatabaseRevision(True)
	update_list = []
	# get a list of needed schema update
	for selected_revision in schema_revisions:
		need_update = updatelib_inst.needUpdate(checkout_revision,selected_revision)
		schema_pythonfile = "schema-r%d.py" % (selected_revision)
		if need_update and os.path.exists(schema_pythonfile):
			update_list.append("python %s" % (schema_pythonfile))
	# log the package revision at the end of successful updates
	# revision 1000000000 is a dummy for unknown head revision
	if revision_in_database < 1000000000 and checkout_revision > revision_in_database:
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
