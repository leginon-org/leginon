#!/usr/bin/env python

#
# COPYRIGHT:
#	The Leginon software is Copyright 2003
#	The Scripps Research Institute, La Jolla, CA
#	For terms of the license agreement
#	see  http://ami.scripps.edu/software/leginon-license
#

import sinedon.data as data
import leginon.gui.wx.Manager
import leginon.version
print 'Leginon version:  ', leginon.version.getVersion()

def start(options=None):
	m = leginon.gui.wx.Manager.App(None, options=options)
	if not m.abort:
		m.MainLoop()
	data.datamanager.exit()

if __name__ == '__main__':
	import legoptparse
	start(legoptparse.options)

