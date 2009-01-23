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
import sys

logevents = False

pathmapping = {}
if sys.platform == 'win32':
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
else:
	def mapPath(path):
		return path
	def unmapPath(path):
		return path

# Here is a replacement for os.mkdirs that won't complain if dir
# already exists (from Python Cookbook, Recipe 4.17)
def mkdirs(newdir):
	originalumask = os.umask(02)
	try:
		os.makedirs(newdir)
	except OSError, err:
		os.umask(originalumask)
		if err.errno != errno.EEXIST or not os.path.isdir(newdir) and os.path.splitdrive(newdir)[1]:
			raise
	os.umask(originalumask)

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
configfiles = configparser.read(config_locations)

#sys.stderr.write("Leginon config files used: ")
#for configfile in configfiles:
	#sys.stderr.write(str(configfile)+" ")
#sys.stderr.write("\n")

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
	if not os.path.isdir(IMAGE_PATH):
		print 'Error accessing image path: %s' % (IMAGE_PATH,)

# user
USERNAME = configparser.get('User', 'fullname')

