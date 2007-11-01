#!/usr/bin/env python

import subprocess
import sys
import os

## this is a wrapper for all appion scripts
## use this function to launch from the web so that
## stdout & sterr will be saved to a file
if __name__ == '__main__':
	cmd = sys.argv[1]
	outf = sys.argv[2]
	PIPE = subprocess.PIPE
	f=open(outf,"w")
	sub = subprocess.Popen(cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
	out = sub.wait()
	f.close()
