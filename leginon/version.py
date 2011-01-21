#!/usr/bin/env python

# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
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

def getSVNInfo():
	modulepath = getInstalledLocation()
	currentpath = os.getcwd()
	os.chdir(modulepath)
	try:
		p = subprocess.Popen('svn info', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		svninfo,svnerror = p.communicate()
		os.chdir(currentpath)
	except:
		raise
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
	return '2.0'

def getVersion():
	svninfo = getSVNInfo()
	if 'Revision' in svninfo.keys():
		version = svninfo['Revision']
	else:
		version = getTextVersion()
	return version

def getSVNBranch():
	svninfo = getSVNInfo()
	if 'URL' in svninfo.keys():
		url = svninfo['URL']
		root = svninfo['Repository Root']
		parts = url.split(root)
		branch = parts[-1].rstrip('/leginon')
		branch = branch.strip('/branches')
		branch = branch.strip('/')
		return branch
	else:
		release_branch = getTextVersion()
		return 'myami-'+release_branch

def getInstalledLocation():
	'''where is this module located'''
	# full path of this module
	fullmod = os.path.abspath(__file__)
	# just the directory
	dirname = os.path.dirname(fullmod)
	return dirname

if __name__ == '__main__':
	print getVersion()
	print getSVNBranch()
	print getInstalledLocation()
