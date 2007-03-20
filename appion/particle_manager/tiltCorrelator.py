#!/usr/bin/python -O

import os, re, sys
import data
import time
import random
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

	#print random.shuffle(imagepairs)
	notdone=True
	while notdone:
		for key,pair in imagepairs.items():
			if len(pair) == 1 or len(pair) > 2:
				print "\nERROR:",pair[0]['filename'],"is not a pair of images"
				stats['notpair']+=1
			if len(pair) == 2:
				img1,img2 = pair
				print dir(img1)
				print dir(img1['image'])
				image = sf1.getImageData(img1)['image']
				sys.exit(1)
				imgname1=img1['filename']
				imgname2=img2['filename']
				stats['imagesleft'] = len(imagepairs)-stats['count']-stats['notpair']

				#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
				if apLoop.startLoop(img1, donedict, stats, params) == False:
					continue

				#PROCESS PAIR
				print "PROCESSING\n\t",imgname1,"\n\t",imgname2
				apTilt.process(img1,img2,params)

				apLoop.writeDoneDict(donedict,params,imgname1)
				apLoop.writeDoneDict(donedict,params,imgname2)
				apLoop.printSummary(stats, params)
				#END LOOP OVER IMAGES
		notdone = apLoop.waitForMoreImages(stats, params)
		#END NOTDONE LOOP	
	apLoop.completeLoop(stats)
