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

import os.path
import inspect

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

def getVersion():
	return '2.0'

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
	print getInstalledLocation()
