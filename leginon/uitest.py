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

server = uiserver.Server()
server.addObject(uidata.Container('Foo'))
server.addObject(uidata.ExternalContainer('Bar'))
threading.Thread(target=uiclient.UIApp,
									args=({'instance': server}, 'UI Test')).start()
#client = uiclient.UIApp({'instance': server}, 'UI Test')

