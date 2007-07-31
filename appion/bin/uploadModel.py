#!/usr/bin/python -O
# Upload pik or box files to the database

import os
import sys
import time
import apUpload
import apParam
import apDisplay
import apDatabase
import apRecon

if __name__ == '__main__':
	# record command line
	apParam.writeFunctionLog(sys.argv)

	# create params dictionary & set defaults
	params = apUpload.createDefaults()

	# parse command line input
	apUpload.parseModelUploadInput(sys.argv,params)

	# check to make sure that incompatible parameters are not set
	if params['apix'] is None:
		apDisplay.printError("enter the pixel size of the model")
	if params['session'] is None:
		apDisplay.printError("enter a session ID")
	if params['sym'] is None:
		apDisplay.printError("enter a symmetry ID")
	if params['description'] is None:
		apDisplay.printError("enter a description of the initial model")
	modelname = params['path']+'/'+params['name']
	# get dimensions of model, set box size
	params['box']=apUpload.getModelDimensions(modelname)
	
	# upload Initial Model
	apUpload.getProjectId(params)
	apUpload.insertModel(params)

	# render images of initial model
	initmodel={}
	initmodel['pixelsize']=params['apix']
	initmodel['boxsize']=params['box']
	initmodel['symmetry']=params['syminfo']
	apRecon.renderSnapshots(modelname,params['res'],initmodel,params['contour'],params['zoom'])
