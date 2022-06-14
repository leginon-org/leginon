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

def printWarning(str):
	msg = "Non-Fatal Failure: %s"%(str)
	if sys.platform == 'win32':
		print msg
	else:
		print "\033[1;33m"+msg+"\033[0m"

def printSearch(filename):
	msg = "Looking for %s in:" %(filename)
	if sys.platform == 'win32':
		print msg
	else:
		print "\033[35m"+msg+"\033[0m"

def printResult(configname,allconfigfiles):
	try:
			print '%s.cfg loaded is from %s' % (configname,allconfigfiles[-1])
			return allconfigfiles[-1]
	except Exception, e:
		if len(allconfigfiles) > 0:
			printError(e)
		else:
			printError('No %s.cfg defined' % (configname))

def checkSinedonConfig():
	print '---------------------------'
	printSearch('sinedon.cfg')
	confdirs = pyami.fileutil.get_config_dirs(package_name='sinedon')
	print "\t",confdirs
	try:
		from sinedon import dbconfig
	except Exception, e:
		printError(e)
		return
	allconfigfiles = dbconfig.configfiles
	configfile = printResult('sinedon',allconfigfiles)
	if configfile:
		for module in ['leginondata','projectdata']:
			try:
				value = dbconfig.getConfig(module)
				if not value:
					printError('%s required' % (module))
			except:
				printError('%s required' % (module))

def checkLeginonConfig():
	print '---------------------------'
	confdirs = pyami.fileutil.get_config_dirs(package_name='leginon')
	printSearch('leginon.cfg')
	print "\t",confdirs
	try:
		from leginon import leginonconfigparser
	except Exception, e:
		printError(e)
		return
	allconfigfiles = leginonconfigparser.configfiles
	configfile = printResult('leginon',allconfigfiles)
	if configfile:
		try:
			image_path = leginonconfigparser.leginonconfigparser.get('Images','path')
		except:
			printError('Default image path required')
			return
		if not image_path:
			printError('Default image path required')

def checkInstrumentConfig():
	print '---------------------------'
	confdirs = pyami.fileutil.get_config_dirs(package_name='pyscope')
	printSearch('instruments.cfg')
	print "\t",confdirs
	try:
		from pyscope import config
		config.parse()
	except Exception as e:
		printWarning('No instrument.cfg configured.  Fatal only if an instrument is needed on this host.')
		return
	allconfigfiles = config.configfiles
	printResult('instruments',allconfigfiles)

def testBeforeStart():
	try:
		import myami_test.pyami_test.test_mysocket
		myami_test.pyami_test.test_mysocket.runTestCases()
		import myami_test.test_configs
		myami_test.test_configs.runTestCases()
		import myami_test.test_db
		myami_test.test_db.runTestCases()
	except Exception, e:
		print 'Error:', e
		if sys.platform == 'win32':
			raw_input('Hit Enter key to quit')
		sys.exit(1)

if __name__ == '__main__':
	try:
		checkSinedonConfig()
		checkLeginonConfig()
		checkInstrumentConfig()
	finally:
		print
		if sys.platform == 'win32':
			raw_input('hit ENTER after reviewing the result to exit ....')
