#!/usr/bin/env python

#
# COPYRIGHT:
#	The Leginon software is Copyright 2003
#	The Scripps Research Institute, La Jolla, CA
#	For terms of the license agreement
#	see  http://ami.scripps.edu/software/leginon-license
#

import sinedon.data as data
import gui.wx.Manager
import version
print 'Leginon version:  ', version.getVersion()

def start(options=None):
	m = gui.wx.Manager.App(None, options=options)
	if not m.abort:
		m.MainLoop()
	data.datamanager.exit()

if __name__ == '__main__':
	import legoptparse
	start(legoptparse.options)

