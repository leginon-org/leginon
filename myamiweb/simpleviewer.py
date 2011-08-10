#!/usr/bin/env python

import os
import leginondata
import projectdata

def getProjectList():
	projectlist = projectdata.projects()


def writeProjectDropList():
	projectlist = getProjectList()
	print "<select>"
	for project in projectlist:
		print ("<option value='%s'>%s</option>"
			%(value, name))
	print "</select>"


if __name__ == "__main__":
	writeProjectDropList()
