#!/usr/bin/env python

import os
import re
import subprocess


def getInstalledLocation():
	'''where is this module located'''
	# full path of this module
	fullmod = os.path.abspath(__file__)
	# just the directory
	dirname = os.path.dirname(fullmod)
	return dirname


def getSubverionRevision(filename=None):
	if filename is None:
		dirname = getInstalledLocation()
	else:
		dirname = os.path.dirname(os.path.abspath(filename))
	svndir = os.path.join(dirname, ".svn")
	if not os.path.isdir(svndir):
		return None
	cmd = "svn info"
	if filename is not None:
		cmd += " "+filename
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	proc.wait()
	for line in proc.stdout:
		line = line.strip()
		if not line.startswith('Revision:'):
			continue
		rev = re.sub('Revision:', '', line).strip()
		return rev
	return None

if __name__ == "__main__":
	rev = getSubverionRevision()
	print "Revision: %s"%(rev)
