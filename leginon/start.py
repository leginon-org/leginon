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

m = manager.Manager(('manager',), None)
managerlocation = m.location()
launcher = launcher.Launcher((socket.gethostname(),),
															{'manager': managerlocation})
#client = uiclient.UIApp(managerlocation['hostname'],
#												managerlocation['UI port'],

client = uiclient.UIApp(uiclient.wxLocalClient, (m.uiserver,),
												'Leginon II')

