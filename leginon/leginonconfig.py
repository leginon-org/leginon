"""
config: Configuration file
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
#	Database	#
#########################
DB_HOST		= 'cronus2'
DB_NAME		= 'dbemdata'
DB_USER		= 'usr_object'
DB_PASS		= ''

#########################
#        Paths          #
#########################

## where to store images
## use os.getcwd() for current directory
LEGINON_PATH	= os.getcwd()
IMAGE_PATH	= os.path.join(LEGINON_PATH, 'images')
mkdirs(IMAGE_PATH)

