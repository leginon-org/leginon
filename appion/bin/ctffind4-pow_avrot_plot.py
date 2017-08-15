#!/usr/bin/env python

import os
import sys
from appionlib.apCtf import ctffind4AvgRotPlot

#====================
#====================
def printUsage():
	print "Usage: %s xxxx_pow_avgrot.txt"%(os.path.basename(__file__))
	sys.exit(0)

#====================
#====================
if __name__ == '__main__':
	if len(sys.argv) < 2:
		printUsage()
	avgrotfile = sys.argv[1]
	if not os.path.exists(avgrotfile):
		printUsage()
	
	ctffind4AvgRotPlot.createPlot(avgrotfile)
