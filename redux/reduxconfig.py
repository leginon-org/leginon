#!/usr/bin/env python
import os
import configparser
import pyami.fileutil

configfilename = 'redux.cfg'

confdirs = pyami.fileutil.get_config_dirs()
config_locations = [os.path.join(confdir, configfilename) for confdir in confdirs]
pyami.fileutil.check_exist_one_file(config_locations)

cparser = configparser.ConfigParser()
configfiles = cparser.read(config_locations)

# default config
config = {
	'server host' :'localhost', 
	'server port' :55123, 
	'cache on'    : False,
	'files'	      : configfiles,
}

# from config file
config['server host'] = cparser.get('server','host')
config['server port'] = cparser.getint('server','port')
cache_on = cparser.get('cache','enable')
if cache_on.strip().lower() in ('yes','on','true'):
	config['cache on'] = True
	config['cache path'] = cparser.get('cache','path')
	config['cache disk size'] = cparser.getint('cache','disksize')
	config['cache mem size'] = cparser.getint('cache','memsize')
config['log file'] = cparser.get('log', 'file')

def printConfig():
	'''
	print all configs for debugging purposes
	'''
	print('Redux Config:')
	for key,value in list(config.items()):
		print('\t%s: %s' % (key,value))

if __name__ == '__main__':
	printConfig()
