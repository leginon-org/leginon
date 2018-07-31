#!/usr/bin/env python

#
# COPYRIGHT:
#	The Leginon software is Copyright under
#	Apache License, Version 2.0
#	For terms of the license agreement
#	see  http://leginon.org
#

# testing before start
import configcheck
configcheck.testBeforeStart()

import pyami.quietscipy
import sinedon.data as data
import leginon.gui.wx.Manager
import leginon.version
import leginon.project

# An TSRI local database split configuration matching
try:
	# This is a local file
	import leginon.configmatch
	matchconfigs=True
except:
	matchconfigs=False

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
	if matchconfigs:
		leginon.configmatch.matchConfigs()
	checkRequirements()
	m = leginon.gui.wx.Manager.App(None, options=options)
	if not m.abort:
		m.MainLoop()
	data.datamanager.exit()

if __name__ == '__main__':
	import leginon.legoptparse
	start(leginon.legoptparse.options)
