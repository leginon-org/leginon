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
import apVolume

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
		apUpload.printSymmetries()
		apDisplay.printError("enter a symmetry ID")
	if params['description'] is None:
		apDisplay.printError("enter a description of the initial model")
	if params['res'] is None:
		apDisplay.printError("enter the resolution of the initial model")
	if params['newbox'] and params['rescale'] is not True:
		apDisplay.printError("you must provide a reference model to resize the box")
	if params['outdir'] is None:
		#auto set the output directory
		sessiondata = apDatabase.getSessionDataFromSessionName(params['session'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		params['outdir'] = os.path.join(path,"models")

	#create the output directory, if needed
	apParam.createDirectory(params['outdir'])

	os.chdir(params['outdir'])
	apParam.writeFunctionLog(sys.argv)

	apUpload.checkSymInfo(params)

	new = os.path.join(params['outdir'], params['name'])

	if os.path.isfile(new):
		apDisplay.printError("model \'"+new+"\' already exists!\n")

	# if rescaling an old template:
	if params['rescale'] is True:
		# get model to be rescaled
		oldmod = apVolume.getModelFromId(params['origmodel'])
		old = os.path.join(oldmod['path']['path'],oldmod['name'])
		apVolume.rescaleModel(old,new,float(oldmod['pixelsize']),params['newapix'],params['newbox'])
		# set new ang/pix of the rescaled model
		params['apix']=params['newapix']

	# otherwise, copy templates to final location
	else:
		old = os.path.join(params['path'], params['name'])
		shutil.copy(old, new)

	# only allow user read access just so they don't get deleted
	os.chmod(new, 0666)

	modelname = os.path.join(params['outdir'], params['name'])

	params['box'] = apVolume.getModelDimensions(modelname)
	
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



