#!/usr/bin/env python
import inspect
import os
import sys
import errno

def getMyFilename(up=1):
	'''
	return the filename of the caller or the caller's caller, etc depending
	on the "up" argument.  up=1 (default) means the caller.  up=2 means the
	caller's caller, etc.
	'''
	frame_record = inspect.stack()[up]
	calling_filename = frame_record[1]  # second item of tuple is filename
	fullname = os.path.abspath(calling_filename)
	return fullname

def getMyDir(up=1):
	'''
	similar to getMyfilename, but get the directory containing the calling file
	'''
	myfile = getMyFilename(up=up+1)
	dirname = os.path.dirname(myfile)
	return dirname

def getMyLineno(up=1):
	'''
	similar to getMyfilename, but get the line number the calling file
	'''
	frame_record = inspect.stack()[up]
	calling_lineno = frame_record[2]  # third item of tuple is lineno
	return calling_lineno

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

def get_config_dirs(module=None):
	'''
	Determine a list of directories where config files may be located.
	One of the directories will be the installed module directory, but
	this only works automatically if this function is called from that
	module.  If you want to force a certain module, pass it to this
	function in the optional argument.
	'''
	# system config location is /etc/myami on unix like systems or
	# under PROGRAMFILES on windows
	if sys.platform == 'win32':
		system_dir = os.path.join(os.environ['PROGRAMFILES'], 'myami')
	else:
		system_dir = '/etc/myami'

	# installed module directory, specified by argument, or auto detected
	if module is None:
		# not this function, but the caller of this function, so up=2
		installed_dir = getMyDir(up=2)
	else:
		installed_dir = os.path.dirname(os.path.abspath(module.__file__))

	# user home dir
	user_dir = os.path.expanduser('~')

	return [system_dir, installed_dir, user_dir]

if __name__ == '__main__':
	print getMyFilename()
