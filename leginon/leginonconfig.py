#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#

import errno
import os
import ConfigParser

logevents = False

pathmapping = {}
def mapPath(path):
		if not pathmapping:
			return path

		for key, value in pathmapping.items():
			if value == path[:len(value)]:
				path = key + path[len(value):]
				break

		return os.path.normpath(path)

def unmapPath(path):
		if not pathmapping:
			return path

		for key, value in pathmapping.items():
			if key == path[:len(key)]:
				path = value + path[len(key):]
				break

		return os.path.normpath(path)

# Here is a replacement for os.mkdirs that won't complain if dir
# already exists (from Python Cookbook, Recipe 4.17)
def mkdirs(newdir, mode=0777):
	try:
		os.makedirs(newdir, mode)
	except OSError, err:
		if err.errno != errno.EEXIST or not os.path.isdir(newdir) and os.path.splitdrive(newdir)[1]:
			raise
### raise this if something is wrong in this config file
class LeginonConfigError(Exception):
	pass

HOME = os.path.expanduser('~')
CURRENT = os.getcwd()
MODULE = os.path.dirname(__file__)

configparser = ConfigParser.SafeConfigParser()
# look in the same directory as this module
defaultfilename = os.path.join(MODULE, 'config', 'default.cfg')
try:
	configparser.readfp(open(defaultfilename), defaultfilename)
except IOError:
	raise LeginonConfigError('cannot find configuration file default.cfg')
## process configs in this order (later ones overwrite earlier ones)
config_locations = [
	'leginon.cfg',
	os.path.join(MODULE, 'config', 'leginon.cfg'),
	os.path.join(HOME, 'leginon.cfg'),
]
print 'Possible config locations:', config_locations
configfiles = configparser.read(config_locations)
print 'Actually read: ', configfiles

# Database sections
dbsections = []
allsections = configparser.sections()
for section in allsections:
	if 'Database' in section:
		dbsections.append(section)
databases = {}
for section in dbsections:
	print 'SECTION', section
	dbconfig = {}
	options = configparser.options(section)
	for key in options:
		dbconfig[key] = configparser.get(section, key)
	databases[section] = dbconfig

# Main leginon database
DB_HOST = databases['Database']['hostname']
DB_NAME = databases['Database']['name']
DB_USER = databases['Database']['username']
DB_PASS = databases['Database']['password']

# This is a check to see if DB is configured above (DB_PASS can be '')
if '' in (DB_HOST, DB_NAME, DB_USER):
	print DB_HOST, DB_NAME, DB_USER
	raise LeginonConfigError('need database info in leginonconfig.py')

# This is optional.  If not using a project database, leave these
# set to None
DB_PROJECT_HOST = databases['Project Database']['hostname']
DB_PROJECT_NAME = databases['Project Database']['name']
DB_PROJECT_USER = databases['Project Database']['username']
DB_PROJECT_PASS = databases['Project Database']['password']

# drive mapping
drives = configparser.options('Drive Mapping')
for drive in drives:
	drivepath = drive.upper() + ':'
	pathmapping[drivepath] = configparser.get('Drive Mapping', drive)

# image path
IMAGE_PATH = configparser.get('Images', 'path')

# check to see if image path has been set, then create it
if not IMAGE_PATH:
	raise LeginonConfigError('set IMAGE_PATH in leginonconfig.py')
try:
	mkdirs(mapPath(IMAGE_PATH))
except:
	print 'Error accessing image path: %s' % (IMAGE_PATH,)

# user
USERNAME = configparser.get('User', 'fullname')

