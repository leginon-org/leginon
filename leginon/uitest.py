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

value = uidata.Integer('Test Value', 1, 'rw')
def Test(s):
	v = value.get()
	value.set(s + 1)
	return s

server = uiserver.Server()
server.addObject(value)
server.addObject(uidata.SingleSelectFromList('Test', ['foo', 'bar'], 1, callback=Test))

client = uiclient.UIApp({'instance': server}, 'UI Test')

