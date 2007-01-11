#! /usr/bin/env python
# Upload pik or box files to the database

import os, re, sys
import data
from reconFunctions import *

if __name__ == '__main__':
	# record command line
	writeReconLog(sys.argv)

	# create params dictionary & set defaults
	params=createDefaults()

	# parse command line input
	parseInput(sys.argv,params)

	# check to make sure that necessary parameters are set
	if not params['stackid']:
		print "\nERROR: enter a stack id\n"
		sys.exit()
      	if not params['modelid']:
		print "\nERROR: enter a starting model id\n"
		sys.exit()
	if not(os.path.exists(params['dir'])):
		print "\nERROR: directory does not exist\n"
		sys.exit()	        
	if not(os.path.exists(params['dir']+'.emanlog')):
		print "\nERROR: directory does not contain EMAN log file\n"
		sys.exit()	        

	# make sure that the stack & model IDs exist in database
	checkStackId(params)
	checkModelId(params)

	# parse out the refinement parameters from the log file
	parseLogFile(params)

	# get a list of the files in the directory
	listFiles(params)
	
	# create a reconRun entry in the database
	insertReconRun(params)

	# insert the Iteration info
	insertIteration(params)
	

