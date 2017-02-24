#!/usr/bin/env python

import os
import sys
import updatelib
from sinedon import dbupgrade
from leginon import projectdata

project_dbupgrade = dbupgrade.DBUpgradeTools('projectdata', drop=True)
dbupgrade.messaging['custom'] = False

if __name__ == "__main__":
	updatelib_inst = updatelib.UpdateLib(project_dbupgrade)
	updatelib_inst.checkSchemaInDatabase()
	schema_tag_list = updatelib_inst.getAvailableTagsForBranch()
	print "\n\nlist of schema tags to check:"
	print schema_tag_list

	schema_to_run_list = []
	# getnerate list of needed schema updates
	print ""
	for schema_tag in schema_tag_list:
		sys.stderr.write("... checking schema tag '%s' ... "%(str(schema_tag)))
		need_update = updatelib_inst.needUpdate(schema_tag)
		if need_update is True:
			print "set to run"
		elif need_update is False:
			print "completed"
		else:
			print "????"
		schema_pythonfile = "updates/schema-r%s.py"%(str(schema_tag))
		if not os.path.isfile(schema_pythonfile):
			print "schema file not found: %s"%(schema_pythonfile)
			if len(schema_to_run_list) > 0:
				# stop and update what we have so far
				del schema_tag_list
				break
			else:
				# error missing schema files
				raise IOError("schema update not found.")
		if need_update:
			schema_to_run_list.append("python %s" % (schema_pythonfile))

	if len(schema_to_run_list) > 0:
		schema_to_run_list.append("python log_package_revision.py")

	# print out the results
	if len(schema_to_run_list) > 0:
		outputstring = "\n".join(schema_to_run_list)
		print ""
		print "\033[36m------Copy the following lines to command terminal to run -------\033[0m"
		print outputstring
		print ""
	else:
		print "\033[35mNo database schema updates are needed \033[0m"