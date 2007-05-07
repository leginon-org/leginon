

#/makestack.py/1.29/Tue Mar 20 21:04:13 2007//
#/tiltCorrelator.py/1.5/Thu Mar 29 18:45:55 2007//
#/crudFinder.py/1.3/Sat Mar 31 20:22:01 2007//
#/dogPicker.py/1.3/Mon Apr  2 21:28:18 2007//
#/selexon.py/1.95/Mon Apr  2 21:34:56 2007//

import os

def getVersion(arg):
	"""
	gets the version of arg (assuming CVS)
	"""
	functionname = os.path.basename(arg)
	functpath    = getInstalledLocation(arg)
	entriesfile  = os.path.join(functpath,"CVS/Entries")
	if os.path.isfile(entriesfile):
		f = open(entriesfile,"r")
		for line in f:
			chunks = line.split('/')
			if chunks[1] == functionname:
				return chunks[2],chunks[3]
	return ""

def getInstalledLocation(arg):
	"""
	gets the installed location of arg
	"""
	# full path of this module
	fullmod = os.path.abspath(arg)
	# just the directory
	dirname = os.path.dirname(fullmod)
	return dirname
