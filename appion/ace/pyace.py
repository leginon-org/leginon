#!/usr/bin/python -O

import os, sys
import cPickle
import time
#import aceFunctions as af
import apParam
import apLoop
import apDatabase,apDisplay
import apCtf
import data
try:
	import pymat
except:
	apDisplay.matlabError()
	apDisplay.printError("")

data.holdImages(False)

if __name__ == '__main__':

	#check directory location
	pyacepath = os.path.join(os.getcwd(),"pyace.py")
	if(not os.path.exists(pyacepath)):
		apDisplay.printWarning("'pyace.py' usually needs to be run in the same directory as "+\
			"all of its matlab files")

	#start connection to matlab	
	print "Connecting to matlab ... "
	try:
		matlab=pymat.open()
	except:
		apDisplay.matlabError()
		apDisplay.printError("")

	(images,stats,params,donedict) = apLoop.startNewAppionFunction(sys.argv)

	apCtf.mkTempDir(params['tempdir'])

	#write ace config file to temp directory
	apCtf.setAceConfig(matlab,params)

	notdone=True
	while notdone:
		for img in images:
			imagename = img['filename']

			stats['imagesleft'] = stats['imagecount'] - stats['count']
			#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
			if( apLoop.startLoop(img, donedict, stats, params)==False ):
				continue
			
			# NEED TO MAKE THIS MORE GENERAL
			#if reprocess option is specified, skip over images with confidence better than specified
			if params['reprocess']:
				ctfparams=apCtf.getCTFParamsForImage(img)
				reprocess=True
				if ctfparams:
					for ctfvalue in ctfparams:
						if(ctfvalue['confidence'] > params['reprocess'] or \
							ctfvalue['confidence_d'] > params['reprocess']):
							reprocess=False
					if reprocess != None:
						print " ... reprocessing", apDisplay.shortenImageName(imagename)
					else:
						print " ... skipping", apDisplay.shortenImageName(imagename)
						#write results to donedict
						apLoop.writeDoneDict(donedict,params,imagename)
						continue
				#else:
					#print img['filename'],'not processed yet. Will process with current ACE parameters.'
					
			#set up and write scopeparams.mat file to temp directory
			#do this for every image because pixel size can be different
			scopeparams={}
			scopeparams['kv']=img['scope']['high tension']/1000
			scopeparams['apix']=apDatabase.getPixelSize(img)
			scopeparams['cs']=params['cs']
			scopeparams['tempdir']=params['tempdir']
			apCtf.setScopeParams(matlab,scopeparams)
			
### RUN ACE
			if params['stig']==1:
				apCtf.runAceAstig(matlab,img,params)
			else:
				apCtf.runAce(matlab,img,params)
### END RUN ACE

			apLoop.printSummary(stats, params)

			apLoop.writeDoneDict(donedict,params,imagename)
		notdone,images = apLoop.waitForMoreImages(stats, params)
	pymat.close(matlab)
	apLoop.completeLoop(stats)		
			
	print "Done!"
