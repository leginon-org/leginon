# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/version.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-26 20:46:29 $
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

if __name__ == '__main__':
	print getVersion()
