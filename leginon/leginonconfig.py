"""
leginonconfig.py: Configuration file for leginon defaults and such
We could also do this using the ConfigParser module and have this
be a more standard .ini file thing.
"""
import os, errno

#########################
#   utility functions   #
#########################

## replacement for os.mkdirs that won't complain if dir already exists
##    (from Python Cookbook, Recipe 4.17)
def mkdirs(newdir, mode=0777):
	try: os.makedirs(newdir, mode)
	except OSError, err:
		if err.errno != errno.EEXIST or not os.path.isdir(newdir):
			raise

#########################
#       Launchers       #
#########################
LAUNCHERS = [
	'tecnai2',
	'defcon1',
	'amilab2',
	'defcon3',
]

#########################
#	Database	#
#########################
DB_HOST		= 'cronus2'
DB_NAME		= 'dbemdata'
DB_USER		= 'usr_object'
DB_PASS		= ''

#########################
#        Paths          #
#########################
## use os.getcwd() for current directory
LEGINON_PATH	= os.getcwd()

IMAGE_PATH	= os.path.join(LEGINON_PATH, 'images')
PREFS_PATH	= os.path.join(LEGINON_PATH, 'prefs')

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
CAMERA_CONFIG = {}
CAMERA_CONFIG['auto square'] = 1
CAMERA_CONFIG['auto offset'] = 1
CAMERA_CONFIG['correct'] = 1
CAMERA_CONFIG['offset'] = {'x': 0, 'y': 0}
CAMERA_CONFIG['dimension'] = {'x': 1024, 'y': 1024}
CAMERA_CONFIG['binning'] = {'x': 4, 'y': 4}
CAMERA_CONFIG['exposure time'] = 500
