#!/usr/bin/env python
'''
This module is used to check if the image path in leginon.cfg and sinedon.cfg
used are matched properly.  It is useful in a multi-database and multi-storage server
situation to prevent cross file saving.

TO use; 1. add unique part of the image path and database server in matchpairs below
				2. move or copy this file to the installed leginon folder
'''
matchpairs = [('data1','dbserver1'),('data2','dbserver2')]

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
	returnvalue = None
	if configfile:
		for module in ['leginondata','projectdata']:
			try:
				value = dbconfig.getConfig(module)
				if module == 'leginondata':
					returnvalue = value
			except:
				printError('%s required' % (module))
			if not value:
				printError('%s required' % (module))
	return returnvalue

def checkLeginonConfig():
	from leginon import configparser
	confdirs = pyami.fileutil.get_config_dirs(configparser)
	allconfigfiles = configparser.configfiles
	configfile = printResult('leginon',allconfigfiles)
	if configfile:
		try:
			image_path = configparser.configparser.get('Images','path')
			return image_path
		except:
			printError('Default image path required')
			return
		if not image_path:
			printError('Default image path required')

def validateMatch(image_path,dbhost):
	global matchpairs
	for pair in matchpairs:
		if pair[0] in image_path and pair[1] in dbhost:
			return True
	return False

def matchConfigs():
	leginon_image_path = checkLeginonConfig()
	leginondata_config = checkSinedonConfig()
	dbhost = leginondata_config['host']
	result = validateMatch(leginon_image_path,dbhost)
	if not result:
		printError('sinedon.cfg and leginon.cfg not matched')

if __name__ == '__main__':
	try:
		matchConfigs()
	finally:
		print
		raw_input('hit ENTER after reviewing the result to exit ....')
