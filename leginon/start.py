#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import gui.wx.Manager
#import launcher
#import socket
import uiclient
#import profile
#import pstats

#import gc
#gc.enable()
#gc.set_debug(gc.DEBUG_LEAK)

#m = manager.Manager(None)
#location = m.location()
#launcher.Launcher((socket.gethostname().lower(),),
#									nodelocations={'manager': location})

'''
profiler = profile.Profile()
profiler.run("uiclient.UIApp(location['UI'], 'Leginon II')")
profiler.dump_stats('start.profile')
stats = pstats.Stats('start.profile')
stats.sort_stats('time', 'cumulative')
stats.print_stats(30)
stats.print_callers(30)
'''
#uiclient.UIApp(location['UI'], 'Leginon II')
#m.exit()

try:
	m = gui.wx.Manager.App(None)
except RuntimeError, e:
	print 'Unable to start Leginon:', str(e)
else:
	m.MainLoop()
