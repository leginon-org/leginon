#!/usr/bin/env python

import os, sys
import cPickle
import pymat
import time
from aceFunctions import *

			
if __name__ == '__main__':

	writePyAceLog(sys.argv)
	#parse input and set up output dirs and params dictionary
	params=parseInput(sys.argv)
	params=getOutDirs(params)
	params=getOutTextFile(params)
	mkTempDir(params['tempdir'])

	#start connection to matlab	
	print "Connecting to matlab"
	matlab=pymat.open()
	
	#write ace config file to temp directory
	setAceConfig(matlab,params)
	
	#get dictionary of completed images
	(params, donedict)=getDoneDict(params)
	
	#get image data objects from Leg. database
#	if params['dbimages'] == 'TRUE' and not params['reprocess']:
	if params['dbimages'] == 'TRUE':
		images=getImagesFromDB(params['session'],params['preset'])
	elif params['alldbimages']:
		images=getAllImagesFromDB(params['session'])
#	else:
#		images=getImagesToReprocess(params)
	
	notdone=True
	while notdone:
		for img in images:
			# skip if image doesn't exist:
			if not os.path.isfile(params['imgdir']+img['filename']+'.mrc'):
				print img['filename']+".mrc not found, skipping"
				continue
			
			#if continue option is true, check to see if image has already been processed
			doneCheck(donedict,img['filename'])
			if params['continue']=='TRUE':
				if donedict[img['filename']]:
					print img['filename'], 'already processed. To process again, remove "continue" option.'
					continue
			
			#if reprocess option is specified, skip over images with confidence better than specified
			if params['reprocess']:
				ctfparams=getCTFParamsForImage(img)
				reprocess=True
				if ctfparams:
					for ctfvalue in ctfparams:
						if ctfvalue['confidence'] > params['reprocess'] or ctfvalue['confidence_d'] > params['reprocess']:
							reprocess=False
					if reprocess:
						print "Reprocessing", img['filename']
					else:
						print "Skipping", img['filename']
						#write results to donedict
						donedict[img['filename']]=True
						writeDoneDict(donedict,params)
						continue
				else:
					print img['filename'],'not processed yet. Will process with current ACE parameters.'
					
			#set up and write scopeparams.mat file to temp directory
			#do this for every image because pixel size can be different
			scopeparams={}
			scopeparams['kv']=img['scope']['high tension']/1000
			scopeparams['apix']=getPixelSize(img)
			scopeparams['cs']=params['cs']
			scopeparams['tempdir']=params['tempdir']
			setScopeParams(matlab,scopeparams)
			
			#run ace
			runAce(matlab,img,params)
			
			#write results to donedict
			donedict[img['filename']]=True
			writeDoneDict(donedict,params)
			
		if params['dbimages']=='TRUE' and not params['reprocess']:
			notdone=True
			print "Waiting ten minutes for new images"
			time.sleep(600)
			images=getImagesFromDB(params['session'],params['preset'])
		else:
			notdone=False
				
			
	pymat.close(matlab)
	print "Done!"
