#!/usr/bin/python -O

import os, sys
import cPickle
import pymat
import time
import aceFunctions as ace
import apParam
import apLoop
import apDatabase
import apCtf
import data
#from aceFunctions import *

data.holdImages(False)
			
if __name__ == '__main__':
	(images,params,stats,donedict) = apLoop.startNewAppionFunction(sys.argv)

	ace.mkTempDir(params['tempdir'])

	#start connection to matlab	
	sys.stderr.write("Connecting to matlab ... ")
	matlab=pymat.open()
	sys.stderr.write("done\n")

	#write ace config file to temp directory
	ace.setAceConfig(matlab,params)

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
						apLoop.writeDoneDict(donedict,params,imagename)
						continue
				#else:
					#print img['filename'],'not processed yet. Will process with current ACE parameters.'
					
			#set up and write scopeparams.mat file to temp directory
			#do this for every image because pixel size can be different
			scopeparams={}
			scopeparams['kv']=img['scope']['high tension']/1000
			scopeparams['apix']=ace.getPixelSize(img)
			scopeparams['cs']=params['cs']
			scopeparams['tempdir']=params['tempdir']
			ace.setScopeParams(matlab,scopeparams)
			
### RUN ACE
			apCtf.runAce(matlab,img,params)
### END RUN ACE

			apLoop.printSummary(stats, params)

			apLoop.writeDoneDict(donedict,params,imagename)
		notdone = apLoop.waitForMoreImages(stats, params)
	pymat.close(matlab)
	apLoop.completeLoop(stats)		
			
	print "Done!"
