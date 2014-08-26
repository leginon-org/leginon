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
				if value.lower() == path[:len(value)].lower():
					path = key + path[len(value):]
					break

			return os.path.normpath(path)

	def unmapPath(path):
			if not pathmapping:
				return path
			for key, value in pathmapping.items():
				if key.lower() == path[:len(key)].lower():
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
		## makedirs sometimes raises permission exception before exists exception
		## check for exists first
		if os.path.exists(newdir):
			return
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
if configparser.has_section('Drive Mapping'):
	drives = configparser.options('Drive Mapping')
	for drive in drives:
		drivepath = drive.upper() + ':'
		pathmapping[drivepath] = configparser.get('Drive Mapping', drive)

# image path
if configparser.has_section('Images'):
	IMAGE_PATH = configparser.get('Images', 'path')
else:
	sys.stderr.write('Warning:  You have not configured Images path in leginon.cfg!  Using current directory.\n')
	IMAGE_PATH = os.path.abspath(os.curdir)


if sys.platform == 'win32':
	mapped_path = mapPath(IMAGE_PATH)
else:
	mapped_path = IMAGE_PATH
if not os.access(mapped_path, os.W_OK):
	sys.stderr.write('Error:  image path is not writable: %s\n' % (IMAGE_PATH,))

# project
try:
	default_project = configparser.get('Project', 'default')
except:
	default_project = None

# user
try:
	USERNAME = configparser.get('User', 'fullname')
except:
	USERNAME = ''

try:
	emailhost = configparser.get('Email', 'host')
	emailuser = configparser.get('Email', 'user')
	emailfrom = configparser.get('Email', 'from')
	emailto = configparser.get('Email', 'to')
except:
	emailhost = emailuser = emailfrom = emailto = None
