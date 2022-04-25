#!/usr/bin/env python

import sys
import os
from pyami import mrc
from appionlib import apDisplay

if len(sys.argv) != 2:
	print 'Usage: fixMrcMachineStamp.py filename'
	sys.exit()
else:
	filename = sys.argv[1]

if not os.path.isfile(filename):
	print 'Failed: file does not exist'
	sys.exit()

mrc.fix_file_machine_stamp(filename)
print 'Machine Stamp Fixed!!!'
