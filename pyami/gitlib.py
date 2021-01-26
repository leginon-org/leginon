#!/usr/bin/env python
import sys
import subprocess

"""
library for working with git
"""

def getCurrentCommitCount():
	if sys.platform == 'win32':
		# fake return.  No easy way to get git version
		return 100000
	cmd = "git rev-list --count HEAD"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	try:
		number = int(result)
	except:
		return getCurrentCommitCountOLDGit()
	return number

def getCurrentCommitCountOLDGit():
	if sys.platform == 'win32':
		# fake return.  No easy way to get git version
		return 100000
	cmd = "git rev-list HEAD | wc -l"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	number = int(result)
	return number

def getCurrentBranch():
	if sys.platform == 'win32':
		# fake return.
		return 'non-sense on win32'
	cmd = "git branch | grep '\*' | cut -d' ' -f2-"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	return result

def getVersion():
	if sys.platform == 'win32':
		# fake return.  No easy way to get git version
		return '100000'
	cmd = "git --version | cut -d' ' -f3-"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	return result

def getAvailableTagsForBranch():
	cmd = "git tag --merged"
	return _getAvailableTags(cmd)

def getAvailableTagsForAll():
	cmd = "git tag"
	return _getAvailableTags(cmd)

def _getAvailableTags(cmd):
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	if len(stderr) > 0:
		print("Warning: git version is possibly too old for tag option --merged. Trying getAvailableTagsForBranchOLDGit()")
		return getAvailableTagsForBranchOLDGit()
	result = stdout.strip()
	return result.split()

def getAvailableTagsForBranchOLDGit():
	availabletags = []
	taglist = getAllTags()
	for tagname in taglist:
		commitid = getCommitIDfromTag(tagname)
		result = isCommitInCurrentBranch(commitid)
		if result is True:
			availabletags.append(tagname)
	return availabletags

def getAllTags():
	cmd = "git tag"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	return result.split()

def isCommitInCurrentBranch(commitid):
	"""
	gets the most recent commit and checks
	to see if commitid is an ascestor of it
	"""
	currentcommitid = getMostRecentCommitID()
	cmd = "git merge-base %s %s"%(commitid, currentcommitid)
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	if result[:len(commitid)] == commitid:
		return True
	return False

def getCommitIDfromTag(tagname):
	cmd = "git rev-list -n 1 '%s'"%(tagname)
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	if len(result) != 40:
		return None
	return result

def getMostRecentCommitID():
	#cmd = "git log --pretty=oneline -n 1 | cut -d' ' -f1"
	cmd = "git rev-parse HEAD"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	return result

def getMostRecentCommitTime():
	cmd = "git log --format='%cd' -n 1"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = proc.communicate()
	result = stdout.strip()
	return result

if __name__ == '__main__':
	print(("getCurrentCommitCount()", getCurrentCommitCount()))
	print(("getCurrentBranch()", getCurrentBranch()))
	print(("getVersion()", getVersion()))
	try:
		print(("getAvailableTagsForBranch()", getAvailableTagsForBranch()))
	except NotImplementedError:
		print("FAIL")
		print(("getAvailableTagsForBranchOLDGit()", getAvailableTagsForBranchOLDGit()))
	print(("getMostRecentCommitID()", getMostRecentCommitID()))
	print(("getMostRecentCommitTime()", getMostRecentCommitTime()))
	print(("isCommitInCurrentBranch('5a14f0b7')", isCommitInCurrentBranch('5a14f0b7')))
	taglist = getAllTags()
	for tagname in taglist:
		commitid = getCommitIDfromTag(tagname)
		result = isCommitInCurrentBranch(commitid)
		print((tagname, result))
