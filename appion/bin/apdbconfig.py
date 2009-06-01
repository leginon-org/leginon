#!/usr/bin/env python
import os
import ConfigParser

debug = True

HOME = os.path.expanduser('~')
modulepath = os.path.dirname(__file__)

configfilename = 'sinedon.cfg'

config_locations = [
	configfilename,
	os.path.join(HOME, configfilename),
	os.path.join(modulepath, configfilename),
]

configparser = ConfigParser.SafeConfigParser()
configfiles = configparser.read(config_locations)

def tail(modulename):
	return modulename.split('.')[-1]

def printConfigFiles():
	'''
	print config files loaded for debugging purposes
	'''
	print "Config files used: "
	for configfile in configfiles:
		print '\t%s' % (configfile,)

allsections = configparser.sections()
configs = {}
globals = {}
windowsdrives = {}
for section in allsections:
	options = configparser.options(section)
	if section == 'global':
		for key in options:
			globals[key] = configparser.get(section, key)
	elif section == 'Windows Drives':
		for key in options:
			drivepath = key.upper() + ':'
			windowsdrives[drivepath] = configparser.get(section, key)
	else:
		configs[section] = {}
		for key in options:
			configs[section][key] = configparser.get(section, key)

## combine globals with specifics
for section in configs:
	config = dict(globals)
	config.update(configs[section])
	configs[section] = config

def getConfig(modulename):
	'''
	return a copy of the named configuration dict
	'''
	modulename = tail(modulename)
	return dict(configs[modulename])

def setConfig(modulename, **kwargs):
	'''
	Configure connection params for a db module.
	If config already exists, this will overwrite any parameters specified.
	If config does not exist, it will be initialized to the global params,
	then any specified parameters will be overwritten.
	'''
	modulename = tail(modulename)
	if modulename not in configs:
		configs[modulename] = dict(globals)
	configs[modulename].update(kwargs)
	return configs[modulename]

def mapPath(path):
		if not windowsdrives:
			return path
		for key, value in windowsdrives.items():
			if value == path[:len(value)]:
				path = key + path[len(value):]
				break
		return os.path.normpath(path)

def unmapPath(path):
		if not windowsdrives:
			return path
		for key, value in windowsdrives.items():
			if key == path[:len(key)]:
				path = value + path[len(key):]
				break
		return os.path.normpath(path)

def printConfigs():
	'''
	print all configs for debugging purposes
	'''
	print 'Configs:'
	for name,config in configs.items():
		print '\t%s' % (name,)
		print '\t\t%s' % (config,)

if __name__ == '__main__':
	printConfigFiles()
	setConfig('test123', fakeparam=8)
	printConfigs()
