#Part of the new pyappion
import os
import sys
import re
import time
import sinedon.data as data
import apDB
import apVersion
import apDisplay
import apDatabase
try:
	import pyami.mem as mem
except:
	apDisplay.printError("Please load 'usepythoncvs' for CVS leginon code, which includes 'mem.py'")
#import selexonFunctions  as sf1

#db=dbdatakeeper.DBDataKeeper()
db=apDB.db
data.holdImages(False)

def getAppionDirectory():
	"""
	Used by appionLoop
	"""
	appiondir = None

	trypath = os.environ.get('APPIONDIR')
	if os.path.isdir(trypath):
		appiondir = trypath
		return appiondir

	user = os.environ.get('USER')
	trypath = "/home/"+user+"/pyappion"
 	if os.path.isdir(trypath):
		appiondir = trypath
		return appiondir

	trypath = "/ami/sw/packages/pyappion"
 	if os.path.isdir(trypath):
		appiondir = trypath
		return appiondir

	apDisplay.printError("environmental variable, APPIONDIR, is not defined.\n"+
		"Did you source useappion.sh?")

def writeFunctionLog(commandline, params=None, logfile=None):
	"""
	Used by appionLoop
	"""
	if logfile is not None:
		pass
	elif params is not None and params['functionLog'] is not None:
		logfile = params['functionLog']
	else:
		logfile = "function.log"
	apDisplay.printMsg("writing function log to: "+logfile)
	#WRITE INFO
	timestamp = "["+time.asctime()+"]\n"
	out=""
	for arg in commandline:
		out += arg+" "
	f=open(logfile,'a')
	f.write(timestamp)
	f.write(out+"\n")
	f.close()

def createDirectory(path, mode=0777, warning=True, remove=False):
	"""
	Used by appionLoop
	"""
	if os.path.isdir(path):
		if warning is True:
			apDisplay.printWarning("directory \'"+path+"\' already exists.")
		# if necessary, remove the directory
		if remove is True:
			if warning is True:
				apDisplay.printWarning("removing \'"+path+"\'.")
			try:
				os.system('rm -rf '+path)
			except: 
				apDisplay.printError("Could not remove directory, '"+path+"'\nCheck the folder write permissions")
		else:
			return False
	try:
		os.makedirs(path, mode=mode)
		#makedirs(path, mode=mode)
	except:
		apDisplay.printError("Could not create directory, '"+path+"'\nCheck the folder write permissions")
	return True

def makedirs(name, mode=0777):
	"""
	Works like mkdir, except that any intermediate path segment (not
	just the rightmost) will be created if it does not exist.  This is
	recursive.
	"""
	head, tail = os.path.split(name)
	if not tail:
		head, tail = os.path.split(head)
	if head and tail and not os.path.exists(head):
		makedirs(head, mode)
		if tail == curdir:
			return
	if not os.path.isdir(name):
		os.mkdir(name, mode)
		os.chmod(name, mode)
	return

def removefiles(path,patterns):
	allfiles = os.listdir(path)
	files = allfiles[:]
	for pattern in patterns:
		files = filter((lambda x: x.find(pattern)>=0),files)
	patterns_line = ('","'.join(patterns))
	apDisplay.printWarning('%d files with the patterns ("%s") will be removed in %s' % (len(files),patterns_line,path))
	for file in files:
		fullpath = os.path.join(path,file)
		try:
			os.remove(fullpath)
		except:
			apDisplay.printError('%s can not be removed' % fullpath)
