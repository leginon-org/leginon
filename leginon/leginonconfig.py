#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#

import errno
import os
from leginon import leginonconfigparser
import sys
import inspect

logevents = False
# Set to None if it is an optional configuration
REF_PATH = None

pathmapping = {}
if sys.platform == 'win32':
	def mapPath(path):
			if not pathmapping or path is None:
				return path
			for key, value in pathmapping.items():
				if value.lower() == path[:len(value)].lower():
					path = key + path[len(value):]
					break

			return os.path.normpath(path)

	def unmapPath(path):
			if not pathmapping or path is None:
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

def validatePath(path):
	if not path:
		return None
	if sys.platform == 'win32':
		mapped_path = mapPath(path)
	else:
		mapped_path = path
	if not os.access(mapped_path, os.W_OK):
		sys.stderr.write('Error:  image path is not writable: %s\n' % (path,))
	return mapped_path

# Here is a replacement for os.mkdirs that won't complain if dir
# already exists (from Python Cookbook, Recipe 4.17)
def mkdirs(newdir):
	# python 2.7 02 is octa but python 3 need to say 0o2
	originalumask = os.umask(0o2)
	try:
		## makedirs sometimes raises permission exception before exists exception
		## check for exists first
		if os.path.exists(newdir):
			return
		os.makedirs(newdir)
	except OSError as err:
		os.umask(originalumask)
		if err.errno != errno.EEXIST or not os.path.isdir(newdir) and os.path.splitdrive(newdir)[1]:
			raise
	os.umask(originalumask)

### raise this if something is wrong in this config file
class LeginonConfigError(Exception):
	pass

leginonconfigparser = leginonconfigparser.leginonconfigparser

# drive mapping
if leginonconfigparser.has_section('Drive Mapping'):
	drives = leginonconfigparser.options('Drive Mapping')
	for drive in drives:
		drivepath = drive.upper() + ':'
		pathmapping[drivepath] = leginonconfigparser.get('Drive Mapping', drive)

# image path
if leginonconfigparser.has_section('Images'):
	IMAGE_PATH = leginonconfigparser.get('Images', 'path')
else:
	sys.stderr.write('Warning:  You have not configured Images path in leginon.cfg!  Using current directory.\n')
	IMAGE_PATH = os.path.abspath(os.curdir)

	validatePath(IMAGE_PATH)

# optional reference path.  Will restrict research and create of
# reference sessions to these is specified
if leginonconfigparser.has_section('References'):
	REF_PATH = leginonconfigparser.get('References', 'path')

# project
try:
	default_project = leginonconfigparser.get('Project', 'default')
except:
	default_project = None

# user
try:
	USERNAME = leginonconfigparser.get('User', 'fullname')
except:
	USERNAME = ''

try:
	emailhost = leginonconfigparser.get('Email', 'host')
	emailuser = leginonconfigparser.get('Email', 'user')
	emailfrom = leginonconfigparser.get('Email', 'from')
	emailto = leginonconfigparser.get('Email', 'to')
except:
	emailhost = emailuser = emailfrom = emailto = None
