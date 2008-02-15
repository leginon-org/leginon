#!/usr/bin/python -O
# Upload pik or box files to the database

import sys
import os
import time
import apParam
import apDisplay
import apRecon

if __name__ == '__main__':
	t0 = time.time()
	# create params dictionary & set defaults
	params = apRecon.createDefaults()

	# parse command line input
	apRecon.parseInput(sys.argv, params)

	# msgPassing requires a jobId in order to get the jobfile & the paramters
	if params['package'] == 'EMAN/MsgP' and params['jobid'] is None:
		apDisplay.printError("EMAN/MsgP package requires a jobId to be processed. Please enter a jobId.")

	# if jobid is supplied, get the job info from the database
	if params['jobid']:
		params['jobinfo']=apRecon.getClusterJobDataFromID(params['jobid'])
		if params['jobinfo'] is None:
			apDisplay.printError("jobid supplied does not exist: "+str(params['jobid']))
		params['path'] = params['jobinfo']['path']['path']
			
	# check to make sure that necessary parameters are set
	if params['stackid'] is None:
		apDisplay.printError("enter a stack id")
	if params['modelid'] is None:
		apDisplay.printError("enter a starting model id")
	if not os.path.exists(params['path']):
		apDisplay.printError("upload directory does not exist: "+params['path'])
	os.chdir(params['path'])

	# record command line
	logfile = apParam.writeFunctionLog(sys.argv)

	# make sure that the stack & model IDs exist in database
	emanJobFile = apRecon.findEmanJobFile(params)
	apRecon.checkStackId(params)
	apRecon.checkModelId(params)

	# create directory for extracting data
	if params['tmpdir'] is None:
		params['tmpdir'] = os.path.join(params['path'],"temp")
	apParam.createDirectory(params['tmpdir'], warning=True)
	
	# parse out the refinement parameters from the log file
	apRecon.parseLogFile(params)

	# parse out the massage passing subclassification parameters from the job/log file
	if params['package'] == 'EMAN/MsgP':
		apRecon.parseMsgPassingParams(params)
		#apRecon.parseMsgPassingLogFile(params)

	# get a list of the files in the directory
	apRecon.listFiles(params)
	
	# create a refinementRun entry in the database
	apRecon.insertRefinementRun(params)

	# insert the Iteration info
	for iteration in params['iterations']:
		# if only uploading one iteration, skip to that one
		if params['oneiteration'] and int(iteration['num'])!=params['oneiteration']:
			continue

		apDisplay.printColor("\nUploading iteration "+str(iteration['num'])+" of "+str(len(params['iterations']))+"\n", "green")
		for i in range(75): 
			sys.stderr.write("#")
		sys.stderr.write("\n")
		apRecon.insertIteration(iteration,params)

	#finish up
	apParam.closeFunctionLog(params=params, logfile=logfile)
	apDisplay.printColor("COMPLETE UPLOAD:\t"+apDisplay.timeString(time.time()-t0),"green")
