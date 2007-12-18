#!/usr/bin/python -O
# Upload pik or box files to the database

import sys
import os
import apParam
import apDisplay
import apUpload

if __name__ == '__main__':
	# record command line
	apParam.writeFunctionLog(sys.argv)

	# create params dictionary & set defaults
	params = apUpload.createDefaults()

	# parse command line input
	apUpload.parseMiscUploadInput(sys.argv, params)

	# check to make sure that necessary parameters are set
	if params['reconid'] is None and params['session'] is None:
		apDisplay.printError("enter a reconstruction id and/or session name")
	if params['description'] is None:
		apDisplay.printError("enter a description")

	# make sure that the stack & model IDs exist in database
	if params['reconid'] is not None:
		apUpload.checkReconId(params)

	if params['session'] is not None:
		apUpload.getProjectId(params)
	# insert the info
	apUpload.insertMisc(params)

