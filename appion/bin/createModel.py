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
import apEMAN
import apDisplay
import apDatabase
import appionData
import glob

appiondb = apDB.apdb

def parseCommandLine():
	usage = ( "Usage: %prog --template=<name> --apix=<pixel> --session=<session> --diam=<int> "
		+"--description='<text>' [options]")
	parser = OptionParser(usage=usage)

	parser.add_option("--description", dest="description",
		help="Description of the model (must be in quotes)", metavar="TEXT")
	parser.add_option("--session", dest="session",
		help="Session name associated with model (e.g. 06mar12a)", metavar="TEXT")
	parser.add_option("--outdir", dest="outdir",
		help="Location to copy the model to", metavar="PATH")
	parser.add_option("--noref", dest="noref", type="int",
		help="ID for reference-free alignment", metavar="INT")
	parser.add_option("--norefClass", dest="norefclass", type="int",
		help="ID for the classes of the reference-free alignment", metavar="INT")
	parser.add_option("--exclude", dest="exclude",
		help="Class indices to be excluded e.g. 1,0,10", metavar="TEXT")
	parser.add_option("--symm", dest="symm",
		help="Cn symmetry if any, e.g. c1", metavar="TEXT")
	parser.add_option("--mask", dest="mask",
		help="Mask radius", metavar="INT")
	parser.add_option("--lp", dest="lp",
		help="Lowpass filter radius in Fourier pixels", metavar="INT")
	parser.add_option("--rounds", dest="rounds",
		help="Rounds of Euler angle determination to use", metavar="INT")
	parser.add_option("--apix", dest="apix", type=float,
		help="Angstrom per pixel of the images in the class average file", metavar="FLOAT")
	parser.add_option("--commit", dest="commit", default=True,
		action="store_true", help="Commit model to database")
	parser.add_option("--no-commit", dest="commit", default=True,
		action="store_false", help="Do not commit model to database")

	params = apParam.convertParserToParams(parser)
	return params

def checkConflicts(params):
	# make sure the necessary parameters are set
	if params['session'] is None:
		apDisplay.printError("enter a session ID")
	if params['description'] is None:
		apDisplay.printError("enter a template description")
	if params['norefclass'] is None:
		apDisplay.printError("enter the ID for the classes of the reference-free alignment")
	if params['apix'] is None:
		apDisplay.printError("enter the apix for the images of the class average file")
	if params['lp'] is None:
		apDisplay.printError("enter the low pass filter value for the model")
	if params['mask'] is None:
		params['mask']=170

	# split params['symm'] into its id and name
	p= re.compile(r'\W+')
	list = p.split(params['symm'])
	params['symm_id']=list[0];
	params['symm_name']=list[1];

def cleanup(norefpath):
	clean = "rm CCL.hed CCL.img"
	move = "mv threed.0a.mrc %s/startAny.mrc" %(norefpath) 
	print "\nRemoving CCL.hed and CCL.img...\n"+clean+""
	print "\nMoving threed.0a.mrc to "+norefpath+" and renaming it startAny.mrc...\n"+move+""
	f=os.popen(clean)
	f=os.popen(move)
	f.close()
	return norefpath+"/startAny.mrc"

def changeapix(mrcpath, apix):
	cmd = "proc3d "+mrcpath+" "+mrcpath+" apix="+str(apix)
	print "\nChanging the apix value of "+mrcpath+"...\n"+cmd
	apEMAN.executeEmanCmd(cmd, verbose=True)


if __name__ == '__main__':
	# create params dictionary & set defaults
	params = parseCommandLine()
	apParam.writeFunctionLog(sys.argv)
	
	checkConflicts(params)
	
	if params['outdir'] is None:
		#auto set the output directory
		sessiondata = apDatabase.getSessionDataFromSessionName(params['session'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("lenorefpathginon","appion",path)
		path = re.sub("/rawdata","",path)
		params['outdir'] = os.path.join(path,"models")

	#create the output directory, if needed
	apDisplay.printMsg("Out directory: "+params['outdir'])
	apParam.createDirectory(params['outdir'])			

 	norefClassdata=appiondb.direct_query(appionData.ApNoRefClassRunData, params['norefclass'])

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

	#create the list of the indexes to be excluded
	if params['exclude'] is not None and params['exclude'] != "":
		p= re.compile(r'\W+')
		list = p.split(params['exclude'])
		 
		print "Creating exclude.list in "+norefpath+"..."

		if os.path.isfile(norefpath+"/exclude.list"): 
			print "\nThe file exclude.list exist in "+norefpath+"..."
			print "\nRemoving the file exclude.list exist in "+norefpath+"...\n"
			remove = "rm "+norefpath+"/exclude.list"
			f=os.popen(remove)
			f.close()
		
		for index in list:
			cmd = "echo %s >> %s/exclude.list" %(index, norefpath)
			print cmd
			f=os.popen(cmd)
			f.close()
		
		newclass = norefClassdata['classFile']+"-new.img"
		
		print "\nCreating new class averages "+newclass+" in "+norefpath+"..."
		cmd = "proc2d %s %s exclude=%s/exclude.list" %(absnorefpath, norefpath+"/"+newclass+"", norefpath)
		apEMAN.executeEmanCmd(cmd, verbose=True)
		print cmd
		
		#run startAny to create the model
		startAny = "startAny %s proc=1" %(norefpath+"/"+newclass+"")
		if params['symm_name'] is not None: 
			startAny+=" sym="+params['symm_name']

		if params['mask'] is not None: 
			startAny+=" mask="+params['mask']

		if params['lp'] is not None: 
			startAny+=" lp="+params['lp']
		
		if params['rounds'] is not None: 
			startAny+=" rounds="+params['rounds']
		
		print "\nCreating 3D model using class averages with EMAN function of startAny..."
		apEMAN.executeEmanCmd(startAny, verbose=True)
		print startAny
		
	#if there is no class to be excluded
	else:
		startAny = "startAny %s proc=1" %(absnorefpath)
		if params['symm_name'] is not None: 
			startAny+=" sym="+params['symm_name']

		if params['mask'] is not None: 
			startAny+=" mask="+params['mask']

		if params['lp'] is not None: 
			startAny+=" lp="+params['lp']
		
		if params['rounds'] is not None: 
			startAny+=" rounds="+params['rounds']

		apEMAN.executeEmanCmd(startAny, verbose=True)
		print startAny

	
	#cleanup the extra files, move the created model to the same folder as the class average and rename it as startAny.mrc
	modelpath = cleanup(norefpath)
	#change its apix back to be the same as the class average file
	changeapix(modelpath, params['apix'])

	
	#call uploadModel
	upload = "uploadModel.py %s session=%s apix=%.3f res=%i symmetry=%i contour=1.5 zoom=1.5 description=\"%s\"" %(modelpath, params['session'], params['apix'], int(params['lp']), int(params['symm_id']), params['description']) 	

	print "\n############################################"
	print "\nReady to upload model "+modelpath+" into the database...\n"
	print upload
	apEMAN.executeEmanCmd(upload, verbose=True)


