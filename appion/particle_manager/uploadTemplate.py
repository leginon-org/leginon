#! /usr/bin/env python
# Python script to upload a template to the database, and prepare images for import

import os, re, sys
import time
from selexonFunctions import *

if __name__ == '__main__':
	# create params dictionary & set defaults
	params=createDefaults()

	# parse command line input
	parseUploadInput(sys.argv,params)

	# make sure the necessary parameters are set
	if not params['apix']:
		print "\nERROR: enter a pixel size\n";
		sys.exit()
	if not params['diam']:
		print "\nERROR: enter the particle diameter in Angstroms\n";
		sys.exit()
	if not params['template']:
		print "\nERROR: enter a template root name\n";
		sys.exit()
	if not params['session']:
		print "\nERROR: enter a session ID\n";
		sys.exit()
	if not params['description']:
		print "\nERROR: enter a template description\n";
		sys.exit()

	# find the number of template files
	checkTemplates(params,"upload")

	# insert templates to database
	getProjectId(params)
	insertTemplateImage(params)

	
	
