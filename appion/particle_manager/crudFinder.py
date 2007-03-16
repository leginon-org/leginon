#!/usr/bin/python -O
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

import os, re, sys
import data
import time
import apLoop,apParam,apDatabase
import apCrud
import selexonFunctions  as sf1

data.holdImages(False)

if __name__ == '__main__':
	(images,params,stats,donedict) = apLoop.startNewAppionFunction(sys.argv)
	
	#IS THIS STILL NECESSARY???
	#sf1.createImageLinks(images)

	# create directory to contain the 'crud' files
	if not (os.path.exists("crudfiles")):
		os.mkdir("crudfiles")
	# create directory to contain the 'pik' files
	#if not (os.path.exists("pikfiles")):
	#	os.mkdir("pikfiles")

	notdone=True
	while notdone:
		while images:
			img = images.pop(0)
			imgname=img['filename']
			stats['imagesleft'] = len(images)

			#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
			if( apLoop.startLoop(img, donedict, stats, params)==False ):
				continue

			apCrud.findCrud(params,imgname)
			#NEED TO DO SOMETHING ELSE IF particles ARE ALREADY IN DATABASE
			apLoop.writeDoneDict(donedict,params,imgname)
			apLoop.printSummary(stats, params)
			#END LOOP OVER IMAGES
		notdone = apLoop.waitForMoreImages(stats, params)
		#END NOTDONE LOOP	
	apLoop.completeLoop(stats)
