#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
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
