#!/usr/bin/env python
import manager
import time
import launcher
import uiclient
import socket
import os
import sys
import data

try:
	session = sys.argv[1]
except IndexError:
	session = time.strftime('%Y-%m-%d-%H-%M')

initializer = {'name': session}
sessiondata = data.SessionData(initializer=initializer)
m = manager.Manager(('manager',), sessiondata)
managerlocation = m.location()
launcher = launcher.Launcher((socket.gethostname(),),
															{'manager': managerlocation})
client = uiclient.UIApp(managerlocation['hostname'],
													managerlocation['UI port'])
