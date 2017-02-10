#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import os

files = os.listdir(os.curdir)

for file in files:
	if file[:5] == 'pipe.':
		print 'removing %s' % file
		os.remove(file)
	if file[:6] == 'shelf.':
		print 'removing %s' % file
		os.remove(file)
	if file[-4:] == '.pyc':
		print 'removing %s' % file
		os.remove(file)
