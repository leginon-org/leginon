#!/usr/bin/env python
# The line above will attempt to interpret this script in python.
# It uses the current environment, which must define a path to the python
# executable.

########################################################################
#  Leginon Dependency Checker
#  This script will check Python and the Python modules installed
#  on this system to see if all requirements are met.
########################################################################

import sys
from leginon import leginondata

def printError(str):
	print "\033[1;31mError: %s\033[0m"%(str)

def printWarning(str):
	print "\033[35m %s\033[0m"%(str)

def printResult(configname,allconfigfiles):
	if len(allconfigfiles) > 0:
		print '%s.cfg loaded is from %s' % (configname,allconfigfiles[-1])
		print '---------------------------'
		return allconfigfiles[-1]
	else:
		printError('No %s.cfg defined' % (configname))
		print '---------------------------'

def getCsFromLeginonSessions():
	sessions = leginondata.SessionData().query()
	if len(sessions) == 0:
		printError('No sessions found. New installation does not need to run this')
	tems = []
	realtems = []
	for sessiondata in sessions:
		images = leginondata.AcquisitionImageData(session=sessiondata).query(results=1)
		if not images:
			continue
		temdata = images[0]['scope']['tem']
		if temdata is not None and temdata.dbid not in map((lambda x:x.dbid),tems):
			tems.append(temdata)
			# Only consider non-appion tem
			if temdata['hostname'] != 'appion':
				realtems.append(temdata)
				print 'TEM %s.%s used in session %s has Cs value of %.3e m' % (temdata['hostname'],temdata['name'],sessiondata['name'],temdata['cs'])
				print
	if len(tems) == 0:
		printWarning('No images acquired with any TEM. Do not worry about it')
	if len(realtems) == 0:
		printWarning('No images acquired with a real TEM. Do not worry about it')

if __name__ == '__main__':
	getCsFromLeginonSessions()
	raw_input('hit ENTER after reviewing the result to exit ....')
