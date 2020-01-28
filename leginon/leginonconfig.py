#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#

import errno
import os
import leginonconfigparser
import sys
import inspect

logevents = False
# Set to None if it is an optional configuration
REF_PATH = None

def replaceEnvironmentVariables(path):
	'''
	replace ${VAR_NAME} with the value of
	the environment variable named VAR_NAME.
	this restricts the path name not to include
	'${' nor '}'.
	'''
	if path is None:
		# new object has no path #8406
		return path
	while '}' in path:
		front = path.split('}')[0]
		back = '}'.join(path.split('}')[1:])
		if '${' in front:
			var_name = front.split('${')[1]
			front = front.split('${')[0]
			new_bit = os.getenv(var_name)
			if new_bit is None:
				new_bit = ''
			path = front+new_bit+back
		else:
			raise ValueError('input contains "}" but not "${" to do variable replacement')
	return path

pathmapping = {}
if sys.platform == 'win32':
	def mapPath(path):
			path = replaceEnvironmentVariables(path)
			if not pathmapping or path is None:
				return path
			for key, value in pathmapping.items():
				if value.lower() == path[:len(value)].lower():
					path = key + path[len(value):]
					break

			return os.path.normpath(path)

	def unmapPath(path):
			path = replaceEnvironmentVariables(path)
			if not pathmapping or path is None:
				return path
			for key, value in pathmapping.items():
				if key.lower() == path[:len(key)].lower():
					path = value + path[len(key):]
					break
			return os.path.normpath(path)
else:
	def mapPath(path):
		path = replaceEnvironmentVariables(path)
		return path

	def unmapPath(path):
		path = replaceEnvironmentVariables(path)
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

lconfigparser = leginonconfigparser.leginonconfigparser

# drive mapping
if lconfigparser.has_section('Drive Mapping'):
	drives = lconfigparser.options('Drive Mapping')
	for drive in drives:
		drivepath = drive.upper() + ':'
		pathmapping[drivepath] = lconfigparser.get('Drive Mapping', drive)

# image path
if lconfigparser.has_section('Images'):
	IMAGE_PATH = lconfigparser.get('Images', 'path')
else:
	sys.stderr.write('Warning:  You have not configured Images path in leginon.cfg!  Using current directory.\n')
	IMAGE_PATH = os.path.abspath(os.curdir)

	validatePath(IMAGE_PATH)

# optional reference path.  Will restrict research and create of
# reference sessions to these is specified
if lconfigparser.has_section('References'):
	REF_PATH = lconfigparser.get('References', 'path')

# project
try:
	default_project = lconfigparser.get('Project', 'default')
except:
	default_project = None

# user
try:
	USERNAME = lconfigparser.get('User', 'fullname')
except:
	USERNAME = ''

try:
	emailhost = lconfigparser.get('Email', 'host')
	emailuser = lconfigparser.get('Email', 'user')
	emailfrom = lconfigparser.get('Email', 'from')
	emailto = lconfigparser.get('Email', 'to')
except:
	emailhost = emailuser = emailfrom = emailto = None
