import os
import sys
import inspect
import re

#=================
def getAppionDir():
	### convoluted way to get location of this file
	appiondir = None
	this_file = __file__
	libdir = os.path.dirname(this_file)  #result: appion/lib/appionlib
	libdir = os.path.abspath(libdir)	 #result: /path/to/appion/lib/appionlib
	trypath = os.path.dirname(os.path.split(libdir)[0])	#result: /path/to/appion
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
def parseConfigFile (configFile):
	confDict ={}
	try:
		cFile= file(configFile, 'r')
	except IOError, e:
		raise IOError ("Couldn't read configuration file " + configFile + ": " + str(e))
	
	#for line in cFile.readlines():		  
	line = cFile.readline()
	while line:
		#get rid of an leading and trailing white space
		#line = line.strip()
		#Only process lines of the correct format, quietly ignore all others"
		matchedLine=re.match(r'\s*([A-Za-z]+)\s*=\s*(\S.*)\s*',line)
		if  matchedLine:
			#split the two parts of the line
			(key, value) = matchedLine.groups()
			#value strings can be spread across multiple lines if \n is escaped (\)
			#process these lines.			  
			while '\\' == value[-1]:	  
				value = value[:-1]
				line= cFile.readline()
				value += line.rstrip('\n')
			#split comma separated values into a list
			if ',' in value:   
				value = re.split(r'\s*,\s*', value)
			#put the key/value pair in the configuration dictionary	
			confDict[key]=value
		line = cFile.readline()
			
	return confDict

if __name__ == '__main__':
	print "getAppionDir()=",getAppionDir()
	print "getAppionConfigFile=",getAppionConfigFile()
