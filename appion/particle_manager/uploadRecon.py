#! /usr/bin/env python
# Upload pik or box files to the database

import sys
import os
import apParam
import apDisplay
#from reconFunctions import *
import reconFunctions as rf

if __name__ == '__main__':
	# record command line
	apParam.writeFunctionLog(sys.argv)

	# create params dictionary & set defaults
	params = rf.createDefaults()

	# parse command line input
	rf.parseInput(sys.argv, params)

	# check to make sure that necessary parameters are set
	if params['stackid'] is None:
		apDisplay.printError("enter a stack id")
	if params['modelid'] is None:
		apDisplay.printError("enter a starting model id")
	if not os.path.isdir(params['dir']):
		apDisplay.printError("directory does not exist")
	if not os.path.isfile(os.path.join(params['dir'],'.emanlog')):
		apDisplay.printError("directory does not contain EMAN log file")

	# make sure that the stack & model IDs exist in database
	rf.checkStackId(params)
	rf.checkModelId(params)

	# parse out the refinement parameters from the log file
	rf.parseLogFile(params)

	# get a list of the files in the directory
	rf.listFiles(params)
	
	# create a reconRun entry in the database
	rf.insertReconRun(params)

	# insert the Iteration info
	rf.insertIteration(params)
	

