# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/version.py,v $
# $Revision: 1.1 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-26 20:21:53 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

cvsname = '$Name: not supported by cvs2svn $'

def getVersion():
	name = cvsname[7:-2]
	if not name:
		return None
	tokens = name.split('-')
	version = ''
	for token in tokens:
		if token.isdigit():
			if version:
				version += '.'
			version += token
	if not version:
		return None
	return version

