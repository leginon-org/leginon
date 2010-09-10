#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#

import errno
import os
import configparser
import sys
import inspect

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

configparser = configparser.configparser

# drive mapping
drives = configparser.options('Drive Mapping')
for drive in drives:
	drivepath = drive.upper() + ':'
	pathmapping[drivepath] = configparser.get('Drive Mapping', drive)

# image path
IMAGE_PATH = configparser.get('Images', 'path')

# project
try:
	default_project = configparser.get('Project', 'default')
except:
	default_project = None

# check to see if image path has been set, then create it
if not IMAGE_PATH:
	raise LeginonConfigError('set IMAGE_PATH in leginonconfig.py')
try:
	mkdirs(mapPath(IMAGE_PATH))
except:
	if not os.path.isdir(IMAGE_PATH):
		sys.stderr.write('Error accessing image path: %s\n' % (IMAGE_PATH,))

# user
USERNAME = configparser.get('User', 'fullname')

try:
	emailhost = configparser.get('Email', 'host')
	emailuser = configparser.get('Email', 'user')
	emailfrom = configparser.get('Email', 'from')
	emailto = configparser.get('Email', 'to')
except:
	emailhost = emailuser = emailfrom = emailto = None
