#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import uidata
import uiserver
import uiclient
import threading

def add():
	for i in range(1):
		container = uidata.LargeContainer('Container ' + str(i))
		for i in range(32):
			container.addObject(uidata.Image('Image Viewer ' + str(i), None))
		server.addObject(container)

server = uiserver.Server()
server.addObject(uidata.Method('Add', add))
client = uiclient.UIApp({'instance': server}, 'UI Test')

