#!/usr/bin/env python
import os
import ConfigParser
import pyami.fileutil

configfilename = 'redux.cfg'

confdirs = pyami.fileutil.get_config_dirs()
config_locations = [os.path.join(confdir, configfilename) for confdir in confdirs]

configparser = ConfigParser.SafeConfigParser()
configfiles = configparser.read(config_locations)

def printConfigFiles():
	'''
	print config files loaded for debugging purposes
	'''
	print "Config files used: "
	for configfile in configfiles:
		print '\t%s' % (configfile,)

# default config
config = {'server host':'localhost', 'server port':55123, 'cache on': False}

# from config file
config['server host'] = configparser.get('server','host')
config['server port'] = configparser.getint('server','port')
cache_on = configparser.get('cache','enable')
if cache_on.strip().lower() in ('yes','on','true'):
	config['cache on'] = True
	config['cache path'] = configparser.get('cache','path')
	config['cache disk size'] = configparser.getint('cache','disksize')
	config['cache mem size'] = configparser.getint('cache','memsize')
config['log file'] = configparser.get('log', 'file')

def printConfig():
	'''
	print all configs for debugging purposes
	'''
	print 'Redux Config:'
	for key,value in config.items():
		print '\t%s: %s' % (key,value)

if __name__ == '__main__':
	printConfigFiles()
	printConfig()
