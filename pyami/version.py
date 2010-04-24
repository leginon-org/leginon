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
	#print "DIRNAME: ", dirname
	svndir = os.path.join(dirname, ".svn")
	if not os.path.isdir(svndir):
		return None
	cmd = "svn info"
	if dirname is not None:
		cmd += " "+dirname
	proc = subprocess.Popen(cmd, shell=True, 
		stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	proc.wait()
	for line in proc.stdout:
		line = line.strip()
		if not line.startswith('Revision:'):
			continue
		rev = re.sub('Revision:', '', line).strip()
		return rev
	#still no revision get fourth line from entries file
	entries = os.path.join(dirname, ".svn/entries")
	if os.path.isfile(entries):
		f = open(entries, "r")
		f.readline()
		f.readline()
		f.readline()
		line = f.readline()
		rev = line.strip()
		return rev
	return None

if __name__ == "__main__":
	rev = getSubverionRevision()
	print "Revision: %s"%(rev)
