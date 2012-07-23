import os
import sys
import inspect

#=================
def getAppionDir():
	### convoluted way to get location of this file
	appiondir = None
	this_file = inspect.currentframe().f_code.co_filename
	libdir = os.path.dirname(this_file)  #result: appion/bin
	libdir = os.path.abspath(libdir)	 #result: /path/to/appion/bin
	trypath = os.path.dirname(libdir)	#result: /path/to/appion
	if os.path.isdir(trypath):
		appiondir = trypath
	return appiondir

#=================
def getAppionConfigFile():
	homedir = os.path.expanduser('~')	
	configfile = os.path.join(homedir, ".appion.cfg")
	
	if not os.path.isfile(configfile):	
		appiondir = getAppionDir()
		configfile = os.path.join(appiondir, ".appion.cfg")

	if not os.path.isfile(configfile):
		sys.stderr.write("Appion config file : " + configfile 
				+ " doesn't exist.  Can't setup processing host\n")
		sys.exit(1)

	return configfile

#=================
