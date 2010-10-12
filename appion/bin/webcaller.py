#!/usr/bin/env python

import os
import sys
import time
import subprocess

## this is a wrapper for all appion scripts
## use this function to launch from the web so that
## stdout & sterr will be saved to a file
if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Usage: webcaller.py '<command>' <outfile>"
		sys.exit(1)
	cmd = sys.argv[1]
	outf = sys.argv[2]

	## check if directory exists
	time.sleep(0.5)
	dirname = os.path.dirname(outf)
	if not os.path.isdir(dirname):
		subprocess.Popen("mkdir -p %s"%dirname,shell=True).wait()

	## run command and write to log file
	f = open(outf, "w")
	proc = subprocess.Popen(cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
	proc.wait()

	f.close()
