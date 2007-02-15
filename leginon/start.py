#!/usr/bin/env python

#
# COPYRIGHT:
#	The Leginon software is Copyright 2003
#	The Scripps Research Institute, La Jolla, CA
#	For terms of the license agreement
#	see  http://ami.scripps.edu/software/leginon-license
#

import data
import gui.wx.Manager

# TODO: handle better
import warnings
warnings.filterwarnings('ignore', module='sqldb')
warnings.filterwarnings('ignore', module='sqldict')
warnings.filterwarnings('ignore', module='sqlexpr')

def start():
	m = gui.wx.Manager.App(None)
	if not m.abort:
		m.MainLoop()
	data.datamanager.exit()

if __name__ == '__main__':
	start()

