#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

"""
leginonconfig.py: Configuration file for leginon defaults and such
We could also do this using the ConfigParser module and have this
be a more standard .ini file thing.
"""

import errno
import os

#############################################################
#   utility functions and exceptions used in this script    #
#     (do not change any of this, skip to next section)     #
#############################################################
# Here is a replacement for os.mkdirs that won't complain if dir
# already exists (from Python Cookbook, Recipe 4.17)
def mkdirs(newdir, mode=0777):
	try: os.makedirs(newdir, mode)
	except OSError, err:
		if err.errno != errno.EEXIST or not os.path.isdir(newdir):
			raise
### raise this if something is wrong in this config file
class LeginonConfigError(Exception):
	pass

#########################
#       Launchers       #
#########################
## This list is used by the Manager when launching nodes.
## Add host names where you could potentially be running a launcher.
## example:   LAUNCHERS = ['temhost', 'yourhost', 'myhost']
LAUNCHERS = []

# check if launchers configured
if not LAUNCHERS:
	raise LeginonConfigError('need launcher list in leginonconfig.py')

#########################
#	Database	#
#########################
## fill in your database and user info
DB_HOST = ''
DB_NAME = ''
DB_USER = ''
DB_PASS = ''

## check if DB is configured (DB_PASS can be '')
if '' in (DB_HOST, DB_NAME, DB_USER):
	raise LeginonConfigError('need database info in leginonconfig.py')

# This is optional.  If not using a project database, leave blank.
DB_PROJECT_HOST = ''
DB_PROJECT_NAME = ''
DB_PROJECT_USER = ''
DB_PROJECT_PASS = ''

#########################
#        Paths          #
#########################
## These are defaults, but can be changed per session configuration.
## use os.getcwd() for current directory
LEGINON_PATH	= os.getcwd()
IMAGE_PATH	= os.path.join(LEGINON_PATH, 'images')
HOME_PATH	= os.path.expanduser('~')
PREFS_PATH	= os.path.join(HOME_PATH, '.leginon', 'prefs')
ID_PATH		= os.path.join(HOME_PATH, '.leginon', 'ids')

## create those paths
try:
	mkdirs(IMAGE_PATH)
except:
	print 'error creating IMAGE_PATH %s' % (IMAGE_PATH,)
try:
	mkdirs(PREFS_PATH)
except:
	print 'error creating IMAGE_PATH %s' % (IMAGE_PATH,)

###################################
#       Default Camera Config     #
###################################
## this is likely to move in future versions, since it should be dependent
## on which camera you are using.
CAMERA_CONFIG = {}
CAMERA_CONFIG['auto square'] = 1
CAMERA_CONFIG['auto offset'] = 1
CAMERA_CONFIG['correct'] = 1
CAMERA_CONFIG['offset'] = {'x': 0, 'y': 0}
CAMERA_CONFIG['dimension'] = {'x': 1024, 'y': 1024}
CAMERA_CONFIG['binning'] = {'x': 2, 'y': 2}
CAMERA_CONFIG['exposure time'] = 500.0
