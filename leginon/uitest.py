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
container = uidata.LargeContainer('Large Container')
messages = [uidata.Message('0', 'error', 'Testing error message'),
						uidata.Message('1', 'info', 'Testing info message'),
						uidata.Message('2', 'warning', 'Testing warning message'),
						uidata.Message('3', 'info', 'Testing info message' + ' foo'*50),
						uidata.Message('4', 'error', 'Testing error message')]
messagelog = uidata.MessageLog('Message log name')
parentcontainer = uidata.LargeContainer('Parent Container')
parentcontainer.addObject(container)
container.addObject(messagelog)
container.addObject(uidata.LargeContainer('Sub Container 0'))
container.addObject(uidata.LargeContainer('Sub Container 1'))
container.addObject(uidata.LargeContainer('Sub Container 2'))
server.addObject(parentcontainer)
messagelog.addObjects(messages)
client = uiclient.UIApp({'instance': server}, 'UI Test')

