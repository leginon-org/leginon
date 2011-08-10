#!/usr/bin/env python

import os
import time
from leginon import leginondata
from leginon import projectdata

def getProjectList():
	projectsdata = projectdata.projects()
	projectlist = projectsdata.query()
	return projectlist

def getLatestSession(projectdata):
	sessionq = leginondata.SessionData()
	sessionq['project'] = projectdata
	sessiondatas = sessionq.query(results=1)
	return sessiondatas[0]

def writeProjectDropList():
	projectlist = getProjectList()
	print "<select name='projectid' onChange='select_project()'>"
	currentyear = time.localtime()[0]
	for project in projectlist:
		sessiondata = getLatestSession(project)
		year = int(str(sessiondata.timestamp)[:4])
		if year > currentyear-1:
			print ("  <option value='%d'>%s (%d)</option>"
				%( project.dbid, project['name'].strip(), project.dbid ))
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
