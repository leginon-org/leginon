#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import gui.wx.Manager

try:
	m = gui.wx.Manager.App(None)
except RuntimeError, e:
	print 'Unable to start Leginon:', str(e)
else:
	m.MainLoop()
