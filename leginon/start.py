#!/usr/bin/env python
import manager
import time
import launcher
import uiclient
import socket
import os
import sys

manager = manager.Manager(('manager',), time.strftime('%Y-%m-%d-%H-%M'))
managerlocation = manager.location()
launcher = launcher.Launcher((socket.gethostname(),),
															{'manager': managerlocation})
client = uiclient.UIApp(managerlocation['hostname'],
													managerlocation['UI port'])
