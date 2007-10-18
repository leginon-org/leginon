#!/usr/bin/python -O
# Python script to upload a template to the database, and prepare images for import

import os
import sys
import re
import shutil
from optparse import OptionParser
import apUpload
import apParam
import apTemplate
import apDisplay
import apDatabase
import glob


def parseCommandLine():
	usage = ( "Usage: %prog --template=<name> --apix=<pixel> --session=<session> --diam=<int> "
		+"--description='<text>' [options]")
	parser = OptionParser(usage=usage)
	parser.add_option("--apix", dest="apix", type="float",
		help="Template pixel size in Angstroms per pixel", metavar="FLOAT")
	parser.add_option("-d", "--diam", dest="diam", type="int",
		help="Approximate diameter of particle (in Angstroms)", metavar="INT")
	parser.add_option("-t", "--template", dest="template",
		help="Filename of the template (wild cards accepted)", metavar="FILE")
	parser.add_option("--description", dest="description",
		help="Description of the template (must be in quotes)", metavar="TEXT")
	parser.add_option("-s", "--session", dest="session",
		help="Session name associated with template (e.g. 06mar12a)", metavar="INT")
	parser.add_option("-o", "--outdir", dest="outdir",
		help="Location to copy the templates to", metavar="PATH")
	parser.add_option("--commit", dest="commit", default=True,
		action="store_true", help="Commit template to database")
	parser.add_option("--no-commit", dest="commit", default=True,
		action="store_false", help="Do not commit template to database")
	parser.add_option("--norefid", dest="norefid", type="int",
		help="ID for reference-free alignment (optional)", metavar="INT")
	parser.add_option("--stackid", dest="stackid", type="int",
		help="ID for particle stack (optional)", metavar="INT")
	parser.add_option("--stackimgnum", dest="stackimgnum", type="int",
		help="Particle number in stack", metavar="INT")
	parser.disable_interspersed_args()
	(options, args) = parser.parse_args()
	if len(args) > 0:
		apDisplay.printError("Unknown commandline options: "+str(args))
	if len(sys.argv) < 2:
		parser.print_help()
		parser.error("no options defined")

	params = {}
	for i in parser.option_list:
		if isinstance(i.dest, str):
			params[i.dest] = getattr(options, i.dest)
	return params

if __name__ == '__main__':
	# create params dictionary & set defaults
	#params = apUpload.createDefaults()

	# parse command line input
	#apUpload.parseTmpltUploadInput(sys.argv, params)
	params = parseCommandLine()
	apParam.writeFunctionLog(sys.argv)

	# make sure the necessary parameters are set
	if params['apix'] is None:
		apDisplay.printError("enter a pixel size")
	if params['diam'] is None:
		apDisplay.printError("enter the particle diameter in Angstroms")
	if params['template'] is None:
		apDisplay.printError("enter a template root name (wild cards are valid)")
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
	apDisplay.printMsg("Out directory: "+params['outdir'])
	apParam.createDirectory(params['outdir'])			

	# find the number of template files
	apTemplate.findTemplates(params)

	# copy templates to final location
	apTemplate.copyTemplatesToOutdir(params)

	apUpload.getProjectId(params)

	# insert templates to database
	apTemplate.insertTemplateImage(params)

	
	
