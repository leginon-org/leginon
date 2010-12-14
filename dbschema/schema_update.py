#!/usr/bin/env python
import time
from sinedon import dbupgrade, dbconfig
from leginon import projectdata, leginondata
from leginon import version
import updatelib
import os

projectdb = dbupgrade.DBUpgradeTools('projectdata', drop=True)

if __name__ == "__main__":
	check_out_revision = updatelib.getCheckOutRevision()
	schema_revisions = updatelib.getUpdateRevisionSequence()
	update_list = []
	for selected_revision in schema_revisions:
		need_update = updatelib.needUpdate(projectdb,check_out_revision,selected_revision)
		schema_pythonfile = "schema-r%d.py" % (selected_revision)
		if need_update and os.path.exists(schema_pythonfile):
			update_list.append("python %s" % (schema_pythonfile))
	if len(update_list):
		outputstring = "\n".join(update_list)
		print "------Copy the following lines to command terminal to run -------"
		print outputstring
	else:
		print "\033[35mNo database schema update script need or can be run \033[0m" 
