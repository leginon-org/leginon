#!/usr/bin/env python

import subprocess
import sys
import os

## this is a wrapper for all appion scripts
## use this function to launch from the web so that
## stdout & sterr will be saved to a file
if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Usage: webcaller.py '<command>' <outfile>"
		sys.exit(1)
	cmd = sys.argv[1]
	outf = sys.argv[2]

	f = open(outf, "w")
	proc = subprocess.Popen(cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
	proc.wait()

	f.close()
