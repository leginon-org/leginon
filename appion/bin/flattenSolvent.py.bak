#!/usr/bin/env python

import os
import sys
import numpy
from pyami import mrc

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "flattenSolvent.py filename.mrc"
		sys.exit(1)
	filename = sys.argv[1]
	if not os.path.isfile(filename):
		print "flattenSolvent.py filename.mrc"
		sys.exit(1)

	a = mrc.read(filename)
	b = numpy.where(a < 0, 0, a)
	mrc.write(b, filename)
	print "done"
