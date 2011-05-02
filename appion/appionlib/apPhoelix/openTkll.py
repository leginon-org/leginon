#!/usr/bin/env python
#
import os
import subprocess
from appionlib import appionScript
from appionlib import appionLoop2

#=====================
#=====================

def openTkll(filename, dekfile, msg=True):

	if not os.path.isfile(filename):
		apDisplay.printError("Layer line file does not exist")
	if not os.path.isfile(filename):
		apDisplay.printError("Dek file does not exist")
	if msg is True:
		apDisplay.printMsg("tkll -f %s -d %s -cut"%(filename, dekfile))
	cmd = "tkll -f", filename, " -d ", dekfile, " -cut"
	proc = subprocess.Popen(cmd)
	proc.wait()

#=====================
if __name__ == "__main__":
	run = openTkll()
	run.start()
