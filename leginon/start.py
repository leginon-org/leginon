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

m = manager.Manager(('manager',), None)
managerlocation = m.location()
launcher = launcher.Launcher((socket.gethostname(),),
															{'manager': managerlocation})
client = uiclient.UIApp(managerlocation['hostname'],
													managerlocation['UI port'])
