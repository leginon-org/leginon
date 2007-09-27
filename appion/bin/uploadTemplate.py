#!/usr/bin/python -O
# Python script to upload a template to the database, and prepare images for import

import os
import sys
import re
import shutil
import apUpload
import apParam
import apTemplate
import apDisplay
import apDatabase

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

	if params['outdir'] is None:
		#auto set the output directory
		sessiondata = apDatabase.getSessionDataFromSessionName(params['session'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		params['outdir'] = os.path.join(path,"templates")

	#create the output directory, if needed
	apParam.createDirectory(params['outdir'])			

	# find the number of template files
	apTemplate.checkTemplates(params)

	# copy templates to final location
	apTemplate.copyTemplatesToOutdir(params)

	# insert templates to database
	if params['commit'] is True:
		apUpload.getProjectId(params)
		apTemplate.insertTemplateImage(params)

	
	
