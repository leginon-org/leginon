#!/usr/bin/env python

#
# COPYRIGHT:
#	The Leginon software is Copyright 2003
#	The Scripps Research Institute, La Jolla, CA
#	For terms of the license agreement
#	see  http://ami.scripps.edu/software/leginon-license
#

import pyami.quietscipy
import sinedon.data as data
import leginon.gui.wx.Manager
import leginon.version
import leginon.project
print 'Leginon version:  ', leginon.version.getVersion()

def checkRequirements():

	try:
		projectdata = leginon.project.ProjectData()
		projects = projectdata.getProjects()
	except:
		projects = None
	if not projects:
		raise RuntimeError('Must create at least one project before starting Leginon')

def start(options=None):
	checkRequirements()
	m = leginon.gui.wx.Manager.App(None, options=options)
	if not m.abort:
		m.MainLoop()
	data.datamanager.exit()

if __name__ == '__main__':
	import leginon.legoptparse
	start(leginon.legoptparse.options)
