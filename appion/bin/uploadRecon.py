#!/usr/bin/python -O
# Upload pik or box files to the database

import sys
import os
import apParam
import apDisplay
import apRecon

if __name__ == '__main__':
	# record command line
	apParam.writeFunctionLog(sys.argv)

	# create params dictionary & set defaults
	params = apRecon.createDefaults()

	# parse command line input
	apRecon.parseInput(sys.argv, params)

	# check to make sure that necessary parameters are set
	if params['stackid'] is None:
		apDisplay.printError("enter a stack id")
	if params['modelid'] is None:
		apDisplay.printError("enter a starting model id")
	if not os.path.exists(params['path']):
		apDisplay.printError("directory does not exist")
	if not os.path.exists(os.path.join(params['path'],'.emanlog')):
		apDisplay.printError("directory does not contain EMAN log file")

	# make sure that the stack & model IDs exist in database
	apRecon.checkStackId(params)
	apRecon.checkModelId(params)

	# create directory for extracting data
	apParam.createDirectory(params['tmpdir'], warning=True)
	
	# parse out the refinement parameters from the log file
	apRecon.parseLogFile(params)

	# get a list of the files in the directory
	apRecon.listFiles(params)
	
	# create a refinementRun entry in the database
	apRecon.insertRefinementRun(params)

	# insert the Iteration info
	apRecon.insertIteration(params)
	

