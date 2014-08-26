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
import pyami.fileutil

def printError(str):
	msg = "Failed: %s"%(str)
	if sys.platform == 'win32':
		print msg
	else:
		print "\033[1;31m"+msg+"\033[0m"

def printSearch(filename):
	msg = "Looking for %s in:" %(filename)
	if sys.platform == 'win32':
		print msg
	else:
		print "\033[35m"+msg+"\033[0m"

def printResult(configname,allconfigfiles):
	if len(allconfigfiles) > 0:
		print '%s.cfg loaded is from %s' % (configname,allconfigfiles[-1])
		print '---------------------------'
		return allconfigfiles[-1]
	else:
		printError('No %s.cfg defined' % (configname))
		print '---------------------------'

def checkSinedonConfig():
	from sinedon import dbconfig
	confdirs = pyami.fileutil.get_config_dirs(dbconfig)
	printSearch('sinedon.cfg')
	print "\t",confdirs
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
	confdirs = pyami.fileutil.get_config_dirs(configparser)
	printSearch('leginon.cfg')
	print "\t",confdirs
	allconfigfiles = configparser.configfiles
	configfile = printResult('leginon',allconfigfiles)
	if configfile:
		try:
			image_path = configparser.configparser.get('Images','path')
		except:
			printError('Default image path required')
			return
		if not image_path:
			printError('Default image path required')

def checkInstrumentConfig():
	from pyscope import config
	confdirs = pyami.fileutil.get_config_dirs(config)
	printSearch('instruments.cfg')
	print "\t",confdirs
	config.parse()
	allconfigfiles = config.configfiles
	printResult('instruments',allconfigfiles)

if __name__ == '__main__':
	try:
		checkSinedonConfig()
		checkLeginonConfig()
		checkInstrumentConfig()
	finally:
		print
		raw_input('hit ENTER after reviewing the result to exit ....')
