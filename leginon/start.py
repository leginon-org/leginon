#!/usr/bin/env python
import manager
import time
import launcher
import uiclient
import socket
import os
import sys

try:
	session = sys.argv[1]
except IndexError:
	session = time.strftime('%Y-%m-%d-%H-%M')

manager = manager.Manager(('manager',), session)
managerlocation = manager.location()
launcher = launcher.Launcher((socket.gethostname(),),
															{'manager': managerlocation})
client = uiclient.UIApp(managerlocation['hostname'],
													managerlocation['UI port'])
