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
		apDisplay.printError("upload directory does not exist: "+params['path'])
	os.chdir(params['path'])

	# make sure that the stack & model IDs exist in database
	apRecon.findEmanLogFile(params)
	apRecon.checkStackId(params)
	apRecon.checkModelId(params)

	# create directory for extracting data
	if params['tmpdir'] is None:
		params['tmpdir'] = os.path.join(params['path'],"temp")
	apParam.createDirectory(params['tmpdir'], warning=True)
	
	# parse out the refinement parameters from the log file
	apRecon.parseLogFile(params)

	# parse out the massage passing subclassification parameters from the log file
	if params['package'] == 'EMAN/MsgP':
		apRecon.parseMsgPassingLogFile(params)

	# get a list of the files in the directory
	apRecon.listFiles(params)
	
	# create a refinementRun entry in the database
	apRecon.insertRefinementRun(params)

	# insert the Iteration info
	for iteration in params['iterations']:
		# if only uploading one iteration, skip to that one
		if params['oneiteration']:
			if int(iteration['num'])!=params['oneiteration']:
				continue
		apRecon.insertIteration(iteration,params)

