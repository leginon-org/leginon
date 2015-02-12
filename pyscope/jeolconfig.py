#!/usr/bin/env python

import sys
import ConfigParser
import imp
import os
import inspect
import pyscope
import pyami.fileutil

configured = {}
configfiles = None

def parse():
	global configured, configfiles

	configparser = ConfigParser.SafeConfigParser()

	# use the path of this module
	modpath = pyscope.__path__

	# read instruments.cfg
	confdirs = pyami.fileutil.get_config_dirs()
	filenames = [os.path.join(confdir, 'jeol.cfg') for confdir in confdirs]
	one_exists = False
	for filename in filenames:
		if os.path.exists(filename):
			one_exists = True
	if not one_exists:
		print 'please configure at least one of these:  %s' % (filenames,)
		sys.exit()
	try:
		configfiles = configparser.read(filenames)
	except:
		print 'error reading %s' % (filenames,)
		sys.exit()

	# parse
	names = configparser.sections()

	for name in names:
		configured[name] = {}
		keys = configparser.options(name)
		for key in keys:
			try:
				configured[name][key] = int(configparser.get(name, key))
			except:
				try:
					configured[name][key] = float(configparser.get(name, key))
				except:
					try:
						configured[name][key] = configparser.getboolen(name,key)
					except:
						valuestring = configparser.get(name,key)
						if valuestring.lower() == 'true':
							configured[name][key] = True
						elif valuestring.lower() == 'false':
							configured[name][key] = False
						else:
							print name,key, configparser.get(name,key)
							pass
	return configured

def getConfigured():
	global configured
	if not configured:
		parse()
	return configured

print getConfigured()
