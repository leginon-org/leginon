#!/usr/bin/python -O

import pdb
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
	pyacepath = os.path.join(os.getcwd(),"pyaceCorrect.py")
	if(not os.path.exists(pyacepath)):
		print "\nERROR: 'pyacecorrects.py' needs to be run in the same directory as"+\
			"all of its matlab files\n"
		sys.exit(1)
	
	(images,params,stats,donedict) = apLoop.startNewAppionFunction(sys.argv)

	ace.mkTempDir(params['tempdir'])
	
	#~ os.mkdir(params['matdir'])
	#~ os.mkdir(params['opimagedir'])


	#start connection to matlab	
	sys.stderr.write("Connecting to matlab ... ")
	matlab=pymat.open()
	sys.stderr.write("done\n")

	notdone=True
	while notdone:
		for img in images:
			imagename = img['filename']

			stats['imagesleft'] = stats['imagecount'] - stats['count']
			#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
			if( apLoop.startLoop(img, donedict, stats, params)==False ):
				continue
			
			#set up and write scopeparams.mat file to temp directory
			#do this for every image because pixel size can be different
			#~ scopeparams={}
			#~ scopeparams['kv']=img['scope']['high tension']/1000
			#~ scopeparams['apix']=ace.getPixelSize(img)
			#~ scopeparams['cs']=params['cs']
			#~ scopeparams['tempdir']=params['tempdir']
			#~ ace.setScopeParams(matlab,scopeparams)
			
### RUN ACE Correction
			apCtf.runAceCorrect(matlab,img,params)
### END RUN ACE Correction

			apLoop.printSummary(stats, params)

			apLoop.writeDoneDict(donedict,params,imagename)
		notdone = apLoop.waitForMoreImages(stats, params)
		images = apDatabase.getAllImages(params,stats)
	pymat.close(matlab)
	apLoop.completeLoop(stats)		
			
	print "Done!"
