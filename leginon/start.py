#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import manager
import launcher
import socket
import threading
import uiclient

#import gc
#gc.enable()
#gc.set_debug(gc.DEBUG_LEAK)

def startManager(location, event):
	m = manager.Manager(('manager',), None)
	location.update(m.location())
	m.start()
	event.set()

def startLauncher(location, event):
	launcher.Launcher((socket.gethostname(),), nodelocations={'manager': location}).start()
	event.set()

location = {}
event = threading.Event()
thread = threading.Thread(target=startManager, args=(location, event))
thread.setDaemon(True)
thread.start()
event.wait()
thread = threading.Thread(target=startLauncher, args=(location, event))
thread.setDaemon(True)
thread.start()
event.wait()

'''
location = manager.Manager(('manager',), None).location()
launcher.Launcher((socket.gethostname(),), nodelocations={'manager': location})
'''

client = uiclient.UIApp(location['UI'], 'Leginon II')

