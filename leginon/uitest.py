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

client = uiclient.UIApp({'instance': server}, 'UI Test')

