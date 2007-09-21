#!/usr/bin/python -O
# Python script to upload a template to the database, and prepare images for import

import os
import sys
import shutil
import apUpload
import apParam
import apTemplate
import apDisplay

if __name__ == '__main__':
	# create params dictionary & set defaults
	params = apUpload.createDefaults()

	# parse command line input
	apUpload.parseTmpltUploadInput(sys.argv, params)
	apParam.writeFunctionLog(sys.argv)

	# make sure the necessary parameters are set
	if params['apix'] is None:
		apDisplay.printError("enter a pixel size")
	if params['diam'] is None:
		apDisplay.printError("enter the particle diameter in Angstroms")
	if params['template'] is None:
		apDisplay.printError("enter a template root name")
	if params['session'] is None:
		apDisplay.printError("enter a session ID")
	if params['description'] is None:
		apDisplay.printError("enter a template description")

	# find the number of template files
	apTemplate.checkTemplates(params, "upload")

	#we should copy the templates to, etc:
	#/ami/data00/appion/session/templates/groEl1.mrc
	#/ami/data00/appion/session/templates/groEl2.mrc
	#and only allow user read access just so they don't get deleted

	# insert templates to database
	apUpload.getProjectId(params)
	apTemplate.insertTemplateImage(params)

	
	
