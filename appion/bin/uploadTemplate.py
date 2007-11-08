#!/usr/bin/python -O
# Python script to upload a template to the database, and prepare images for import

import os
import apDB
import sys
import re
import shutil
from optparse import OptionParser
import apUpload
import apParam
import apTemplate
import apStack
import apDisplay
import apDatabase
import appionData
import glob

appiondb = apDB.apdb

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
	parser.add_option("--avgstack", dest="avgstack", default=False,
		action="store_true", help="Average all particles in stack for template")

	params = apParam.convertParserToParams(parser)
	return params

def checkConflicts(params):
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
	if params['stackid'] is not None and params['norefid'] is not None:
		apDisplay.printError("only one of either stackid or norefid can be used, NOT both")

if __name__ == '__main__':
	# create params dictionary & set defaults
	params = parseCommandLine()
	apParam.writeFunctionLog(sys.argv)

	checkConflicts(params)

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

	if params['stackid'] is not None:
		apDisplay.printMsg("Using stack to make template")
		#get stack data (path, file)
		stackdata = apStack.getOnlyStackData(params['stackid'])
		stackpath = (stackdata['path'])['path']
		stackname = stackdata['name']
		absstackpath = os.path.join(stackpath,stackname)
		abstemplatepath = None

		#check to see if stackimagenum is within the boundary of the stack
		stacksize = len(apStack.getStackParticlesFromId(params['stackid']))

		#make sure that params['stackimgnum'] is less than the num of particles in the stack,
		# or averaging all files together
		if params['stackimgnum'] < stacksize and params['stackimgnum'] >= 0:
			apDisplay.printMsg("Extracting image %i from stack" %params['stackimgnum'])
			templatename = "template"+str(params['stackimgnum'])+".mrc"
			abstemplatepath= os.path.join(stackpath,templatename)
			
			#run proc2d with params['stackimgnum']
			cmd = "proc2d %s %s first=%i last=%i" %(absstackpath, abstemplatepath, params['stackimgnum'], params['stackimgnum'])
		elif params['avgstack'] is True:
			apDisplay.printMsg("Averaging all images in stack")
			templatename = "template"+str(params['stackid'])+"avg.mrc"
			abstemplatepath = os.path.join(stackpath,templatename)
			#average all images using proc2d
			cmd = "proc2d %s %s average" %(absstackpath, abstemplatepath)
			
		# create template
		if abstemplatepath is not None:
			print "creating "+templatename+" in "+stackpath+"...\n"
			f=os.popen(cmd)
			f.close()
		        #Add file names to params['templatelist']
			params['templatelist'] = []
			params['templatelist'].append(abstemplatepath)

	elif params['norefid'] is not None:
		apDisplay.printMsg("Using reference-free class to make template")
		norefClassdata=appiondb.direct_query(appionData.ApNoRefClassRunData, params['norefid'])
		
		#Get class average file path through ApNoRefRunData
		norefRun=norefClassdata['norefRun']
		norefpath = (norefRun['path'])['path']
		norefname = norefRun['name']
		norefpath = os.path.join(norefpath,norefname)
				
		#Get class average file name
		norefClassFile = norefClassdata['classFile']
		norefClassFile+=".img"

		#complete path of the class average file
		absnorefpath = os.path.join(norefpath,norefClassFile)
		print absnorefpath

		#get the num of classes
		classnum = norefClassdata['num_classes']
		
		#make sure that params['stackimgnum'] is less than the num of classes
		if params['stackimgnum'] < classnum and params['stackimgnum'] >= 0:
			templatename = "template"+str(params['stackimgnum'])+".mrc"
			abstemplatepath= os.path.join(norefpath,templatename)

			#run proc2d with params['stackimgnum']
			print "creating "+templatename+" in "+norefpath+"...\n"
			cmd = "proc2d %s %s first=%i last=%i" %(absnorefpath, abstemplatepath, params['stackimgnum'], params['stackimgnum'])
			print cmd
			f=os.popen(cmd)
			f.close() 
		
		#Add file names to params['templatelist']
		params['templatelist'] = []
		params['templatelist'].append(abstemplatepath)
	else:
		apDisplay.printMsg("Using file to upload template")
		#find the number of template files
		apTemplate.findTemplates(params)
		

	print params['templatelist']
	# copy templates to final location
	apTemplate.copyTemplatesToOutdir(params)

	apUpload.getProjectId(params)

	# insert templates to database
	apTemplate.insertTemplateImage(params)

	
	
