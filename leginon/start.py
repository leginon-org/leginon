#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import manager
import time
import launcher
import uiclient
import socket
import os
import sys
import data
import threading

#import psyco
#psyco.log()
#psyco.profile()
#psyco.full()

#import gc
#gc.enable()
#gc.set_debug(gc.DEBUG_LEAK)

try:
	session = sys.argv[1]
except IndexError:
	session = time.strftime('%Y-%m-%d-%H-%M')

def startManager(location, event):
	location.update(manager.Manager(('manager',), None).location())
	event.set()

def startLauncher(location, event):
	launcher.Launcher((socket.gethostname(),), {'manager': location})
	event.set()

location = {}
event = threading.Event()
threading.Thread(target=startManager, args=(location, event)).start()
event.wait()
threading.Thread(target=startLauncher, args=(location, event)).start()
event.wait()

instance = location['UI']['instance']
client = uiclient.UIApp(uiclient.wxLocalClient, (instance,), 'Leginon II')

