#!/usr/bin/env python

import subprocess

"""
library for working with git
"""

def getCurrentCommitCount():
	cmd = "git rev-list --count HEAD"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	number = int(result)
	return number

def getCurrentBranch():
	cmd = "git branch | grep '\*' | cut -d' ' -f2-"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	return result

def getVersion():
	cmd = "git --version | cut -d' ' -f3-"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	return result

def getCurrentTags():
	cmd = "git tag --merged"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	return result.split()

def getMostRecentCommitID():
	cmd = "git log --pretty=oneline -n 1 | cut -d' ' -f1"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	return result

def getMostRecentCommitTime():
	cmd = "git log --format='%cd' -n 1"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	return result

if __name__ == '__main__':
	print "getCurrentCommitCount()", getCurrentCommitCount()
	print "getCurrentBranch()", getCurrentBranch()
	print "getVersion()", getVersion()
	print "getCurrentTags()", getCurrentTags()
	print "getMostRecentCommitID()", getMostRecentCommitID()
	print "getMostRecentCommitTime()", getMostRecentCommitTime()
