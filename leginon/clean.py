#!/usr/bin/env python

import os

files = os.listdir(os.curdir)

for file in files:
	if file[:5] == 'pipe.':
		print 'removing %s' % file
		os.remove(file)
	if file[:6] == 'shelf.':
		print 'removing %s' % file
		os.remove(file)
	if file[:-3] == '.pyc':
		print 'removing %s' % file
		os.remove(file)
