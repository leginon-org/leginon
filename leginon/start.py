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

location = manager.Manager(('manager',), None).location()
launcher.Launcher((socket.gethostname().lower(),),
									nodelocations={'manager': location})
client = uiclient.UIApp(location['UI'], 'Leginon II')

