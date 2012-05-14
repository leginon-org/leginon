#!/usr/bin/env python

import inspect
import os

def getThisFileDir():
	this_file = inspect.currentframe().f_code.co_filename
	fullmod = os.path.abspath(this_file)
	# just the directory
	dirname = os.path.dirname(fullmod)
	return dirname

# check sinedon.cfg
from leginon import configcheck
configcheck.checkSinedonConfig()
configcheck.checkLeginonConfig()

print '----------------------------------------'
print 'appion bin is from %s' % (getThisFileDir())

from appionlib import appiondata
print 'appionlib python package is from %s' % (os.path.dirname(os.path.abspath(appiondata.__file__)))

from pyami import mrc
print 'pyami python package is from %s' % (os.path.dirname(os.path.abspath(mrc.__file__)))

