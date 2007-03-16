#!/usr/bin/env python

import os, sys
import cPickle
import pymat
import time
import aceFunctions as ace
import apParam
import apLoop
#from aceFunctions import *

			
if __name__ == '__main__':
	apParam.writeFunctionLog(sys.argv,".pyacelog")

	#parse input and set up output dirs and params dictionary
	params = apParam.createDefaultParams(function=sys.argv[0])
	params = apParam.parseCommandLineInput(sys.argv,params)
	apParam.createOutputDirs(params)
	stats  = apParam.createDefaultStats()

	params=ace.getOutTextFile(params)
	ace.mkTempDir(params['tempdir'])

	#start connection to matlab	
	print "Connecting to matlab ... "
	matlab=pymat.open()
	
	#write ace config file to temp directory
	ace.setAceConfig(matlab,params)
	
	#get dictionary of completed images
	donedict = apLoop.readDoneDict(params)
	
	#get image data objects from Leg. database
#	if params['dbimages'] == True and not params['reprocess']:
	if params['dbimages'] == True:
		images=ace.getImagesFromDB(params['sessionname'],params['preset'])
	elif params['alldbimages']:
		images=ace.getAllImagesFromDB(params['sessionname'])
#	else:
#		images=ace.getImagesToReprocess(params)
	stats['imagecount']=len(images)

	notdone=True
	while notdone:
		for img in images:
			imagename = img['filename']

			stats['imagesleft'] = stats['imagecount'] - stats['count']
			#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
			if( apLoop.startLoop(img, donedict, stats, params)==False ):
				continue
			
			
			#if reprocess option is specified, skip over images with confidence better than specified
			if params['reprocess']:
				ctfparams=ace.getCTFParamsForImage(img)
				reprocess=True
				if ctfparams:
					for ctfvalue in ctfparams:
						if(ctfvalue['confidence'] > params['reprocess'] or \
							ctfvalue['confidence_d'] > params['reprocess']):
							reprocess=False
					if reprocess:
						print "Reprocessing", img['filename']
					else:
						print "Skipping", img['filename']
						#write results to donedict
						ace.donedict[img['filename']]=True
						ace.writeDoneDict(donedict,params)
						continue
				else:
					print img['filename'],'not processed yet. Will process with current ACE parameters.'
					
			#set up and write scopeparams.mat file to temp directory
			#do this for every image because pixel size can be different
			scopeparams={}
			scopeparams['kv']=img['scope']['high tension']/1000
			scopeparams['apix']=ace.getPixelSize(img)
			scopeparams['cs']=params['cs']
			scopeparams['tempdir']=params['tempdir']
			ace.setScopeParams(matlab,scopeparams)
			
			#run ace
			ace.runAce(matlab,img,params)
			
			#write results to donedict
			#donedict[img['filename']]=True
			#ace.writeDoneDict(donedict,params)
			
			apLoop.printSummary(stats, params)

			apLoop.writeDoneDict(donedict,params,imagename)
		notdone = apLoop.waitForMoreImages(stats, params)
	pymat.close(matlab)
	apLoop.completeLoop(stats)		
			
	print "Done!"
