#!/usr/bin/env python

import os
#import leginondata
from leginon import projectdata

def getProjectList():
	projectsdata = projectdata.projects()
	projectlist = projectsdata.query()
	return projectlist

def writeProjectDropList():
	projectlist = getProjectList()
	print "<select name='projectid' onChange='select_project()'>"
	for project in projectlist:
		print ("  <option value='%d'>%s</option>"
			%( project.dbid, project['name'].strip() ))
	print "</select>"

if __name__ == "__main__":
	print "<html>"
	print "<head>"
	print "  <title>Simple Viewer</title>"
	print "</head>"
	print "<body>"

	### Project Drop Down List
	writeProjectDropList()

	print "</body>"
	print "</html>"
