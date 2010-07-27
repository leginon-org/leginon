import inspect
import os

def getInstalledLocation():
	'''where is this module located'''
	# full path of this module
	this_file = inspect.currentframe().f_code.co_filename
	fullmod = os.path.abspath(this_file)
	# just the directory
	dirname = os.path.dirname(fullmod)
	return dirname

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
