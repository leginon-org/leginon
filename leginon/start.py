#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import gui.wx.Manager

def start():
	try:
		m = gui.wx.Manager.App(None)
	except RuntimeError, e:
		print 'Unable to start Leginon:', str(e)
	else:
		m.MainLoop()

if __name__ == '__main__':
	start()
	data.datamanager.exit()

