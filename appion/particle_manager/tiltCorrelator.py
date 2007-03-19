#!/usr/bin/python -O

import os, re, sys
import data
import time
import apLoop,apParam,apDatabase
import apTilt
import selexonFunctions  as sf1

data.holdImages(False)

if __name__ == '__main__':
	(images,params,stats,donedict) = apLoop.startNewAppionFunction(sys.argv)

	#TAKE ALL IMAGES AND SORT THEM INTO PAIRS
	imagepairs = {}
	for image in images:
		grandparent = image['target']['image']['target']
		grandid = grandparent.dbid
		targetnumber = image['target']['number']
		key = (grandid, targetnumber)
		if key in imagepairs:
			imagepairs[key].append(image)
		else:
			imagepairs[key] = [image]
	del images

	for key,pair in imagepairs.items():
		if len(pair) == 1:
			print 'One image: %s' % (pair[0]['filename'],)
		elif len(pair) > 2:
			print 'Too many:'
			for im in pair:
				print '  ', im['filename']
		else:
			print 'Pair:'
			for im in pair:
				print '  ', im['filename']

	notdone=True
	while notdone:
		while imagepairs:
			img = images.pop(0)
			imgname=img['filename']
			stats['imagesleft'] = len(images)

			#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
			if apLoop.startLoop(img, donedict, stats, params) == False:
				continue

			apCrud.findCrud(params,imgname)

			apLoop.writeDoneDict(donedict,params,imgname)
			apLoop.printSummary(stats, params)
			#END LOOP OVER IMAGES
		notdone = apLoop.waitForMoreImages(stats, params)
		#END NOTDONE LOOP	
	apLoop.completeLoop(stats)
