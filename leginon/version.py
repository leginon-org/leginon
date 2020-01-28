#!/usr/bin/env python

# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#
# $Source: /ami/sw/cvsroot/pyleginon/version.py,v $
# $Revision: 1.3 $
# $Name: not supported by cvs2svn $
# $Date: 2006-12-05 22:27:14 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import subprocess
import os.path
import inspect
from pyami import gitlib

def OLDgetVersion():
	name = cvsname[7:-2]
	if not name:
		return None
	tokens = name.split('-')
	version = ''

	# parse revision
	count = 0
	while tokens:
		token = tokens[0]
		if token.isdigit():
			if version:
				version += '.'
			version += token
			count += 1
		elif count > 1:
			break
		if count > 2:
			break
		del tokens[0]
	if count < 2:
		return None

	while tokens:
		token = tokens[0]
		if token in ['a', 'b']:
			version += token
			break
		del tokens[0]

	while tokens:
		token = tokens[0]
		if token.isdigit():
			version += token
			break
		del tokens[0]

	return version

def getShellResult(cmd):
	svninfo = ''
	svnerror = ''
	try:
		p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		svninfo,svnerror = p.communicate()
	except Exception,e: 
		print str(e)
	return svninfo,svnerror

def changeToModulePath(module_path=''):
	if not module_path:
		module_path = getInstalledLocation()
	module_path = os.path.abspath(module_path)
	currentpath = os.getcwd()
	os.chdir(module_path)
	return currentpath

def getGITBranch(module_path=''):
	revertpath = changeToModulePath(module_path)
	return gitlib.getCurrentBranch()
	#branch = getTextVersion()
		
def getGITHash(module_path=''):
	revertpath = changeToModulePath(module_path)
	return gitlib.getMostRecentCommitID()

def getVersion(module_path=''):
	# myami svn frozen before revision 20000
	return gitlib.getCurrentCommitCount()

def getGITInfo(module_path):
	info = {}
	info['Branch'] = getGITBranch(module_path)
	info['Hash'] = getGITHash(module_path)
	info['Revision'] = getVersion(module_path)

def getSVNInfo(module_path=''):
	revertpath = changeToModulePath(module_path='')
	svninfo, svnerror = getShellResult('svn info')
	os.chdir(revertpath)
	# releases have no svn info
	if svnerror:
		return {}
	infolist = svninfo.split('\n')
	infodict = {}
	for line in infolist:
		parts = line.split(': ')
		infodict[parts[0]] = ': '.join(parts[1:])
	return infodict

def getTextVersion():
	return 'trunk'

def getSVNVersion(module_path=''):
	svninfo = getSVNInfo(module_path)
	if 'Revision' in svninfo.keys():
		version = svninfo['Revision']
	else:
		version = getTextVersion()
	return version

def getSVNBranch(module_path=''):
	svninfo = getSVNInfo(module_path)
	if 'URL' in svninfo.keys():
		url = svninfo['URL']
		root = svninfo['Repository Root']
		parts = url.split(root)
		pieces = parts[-1].split('/')
		if pieces[1] =='trunk':
			return 'trunk'
		if 'branches' == pieces[1]:
			branch = pieces[2]
		return branch
	else:
		release_branch = getTextVersion()
		return 'myami-'+release_branch

def getInstalledLocation():
	'''where is this module located'''
	# full path of this module
	this_file = inspect.currentframe().f_code.co_filename
	fullmod = os.path.abspath(this_file)
	# just the directory
	dirname = os.path.dirname(fullmod)
	return dirname

if __name__ == '__main__':
	print getVersion()
	print getGITBranch()
	print getInstalledLocation()
