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
	if params['reconid'] is None:
		apDisplay.printError("enter a reconstruction id")
	if params['description'] is None:
		apDisplay.printError("enter a description")

	# make sure that the stack & model IDs exist in database
	apUpload.checkReconId(params)

	# insert the info
	apUpload.insertMisc(params)

