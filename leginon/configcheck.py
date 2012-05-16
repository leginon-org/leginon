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
def printError(str):
	print "\033[33mError: %s\033[0m"%(str)
	sys.exit(1)

def printResult(configname,allconfigfiles):
	if len(allconfigfiles) > 0:
		print '%s.cfg loaded is from %s' % (configname,allconfigfiles[-1])
		return allconfigfiles[-1]
	else:
		printError('ERROR: No %s.cfg defined' % (configname))

def checkSinedonConfig():
	from sinedon import dbconfig
	allconfigfiles = dbconfig.configfiles
	configfile = printResult('sinedon',allconfigfiles)
	if configfile:
		for module in ['leginondata','projectdata']:
			try:
				value = dbconfig.getConfig(module)
			except:
				printError('%s required' % (module))
			if not value:
				printError('%s required' % (module))

def checkLeginonConfig():
	from leginon import configparser
	allconfigfiles = configparser.configfiles
	configfile = printResult('leginon',allconfigfiles)
	if configfile:
		try:
			image_path = configparser.configparser.get('Images','path')
		except:
			path
			printError('Default image path required')
		if not image_path:
			printError('Default image path required')

def checkInstrumentConfig():
	from pyscope import config
	config.parse()
	allconfigfiles = config.configfiles
	printResult('instruments',allconfigfiles)

if __name__ == '__main__':
	checkSinedonConfig()
	checkLeginonConfig()
	checkInstrumentConfig()	
