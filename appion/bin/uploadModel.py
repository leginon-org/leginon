#!/usr/bin/python -O
# Upload pik or box files to the database

import os
import sys
import time
import re
import shutil
import apUpload
import apParam
import apDisplay
import apDatabase
import apRecon

if __name__ == '__main__':
	# record command line
	#apParam.writeFunctionLog(sys.argv)

	# create params dictionary & set defaults
	params = apUpload.createDefaults()

	# parse command line input
	apUpload.parseModelUploadInput(sys.argv, params)

	# check to make sure that incompatible parameters are not set
	if params['apix'] is None:
		apDisplay.printError("enter the pixel size of the model")
	if params['session'] is None:
		apDisplay.printError("enter a session ID")
	if params['sym'] is None:
		apDisplay.printError("enter a symmetry ID")
	if params['description'] is None:
		apDisplay.printError("enter a description of the initial model")
	if params['outdir'] is None:
		#auto set the output directory
		sessiondata = apDatabase.getSessionDataFromSessionName(params['session'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		params['outdir'] = os.path.join(path,"models")

	os.chdir(params['outdir'])
	apParam.writeFunctionLog(sys.argv)

	apUpload.checkSymInfo(params)

	#create the output directory, if needed
	apParam.createDirectory(params['outdir'])		

	# copy templates to final location
	old = os.path.join(params['path'], params['name'])
	new = os.path.join(params['outdir'], params['name'])
	if os.path.isfile(new):
		apDisplay.printError("model \'"+new+"\' already exists!\n")
	shutil.copy(old, new)
	#and only allow user read access just so they don't get deleted
	os.chmod(new, 0666)



	modelname = os.path.join(params['outdir'], params['name'])
	# get dimensions of model, set box size
	params['box'] = apUpload.getModelDimensions(modelname)
	
	# upload Initial Model
	apUpload.getProjectId(params)
	if params['commit'] is True:
		apUpload.insertModel(params)

	# render images of initial model
	initmodel={}
	initmodel['pixelsize']=params['apix']
	initmodel['boxsize']=params['box']
	initmodel['symmetry']=params['syminfo']
	apRecon.renderSnapshots(modelname,params['res'],initmodel,params['contour'],params['zoom'])



