#!/usr/bin/python -O

import sys
sys.stderr.write("loading modules...")
import os, re
import data
import time
import random
import apLoop
import apTilt
sys.stderr.write("done\n")

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
	#print (imagepairs.items())[0]
	notdone=True
	while notdone:
		for key,pair in imagepairs.items():
			if len(pair) == 1 or len(pair) > 2:
				print "\nERROR:",pair[0]['filename'],"is not a pair of images"
				stats['notpair']+=1
			if len(pair) == 2:
				img1,img2 = pair
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
		notdone,images = apLoop.waitForMoreImages(stats, params)
		#END NOTDONE LOOP	
	apLoop.completeLoop(stats)
