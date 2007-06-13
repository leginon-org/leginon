#!/usr/bin/python -O

import sys
sys.stderr.write("loading modules...")
import os
import re
import time
import random
import apLoop
import apTilt
import apDisplay
import apParticle
sys.stderr.write("done\n")

def shuffleTree(tree):
	oldtree = tree
	newtree = []
	while len(oldtree) > 0:
		j = int(len(oldtree)*random.random())
		newtree.append(oldtree[j])
		del oldtree[j]
	return newtree

if __name__ == '__main__':
	(images,stats,params,donedict) = apLoop.startNewAppionFunction(sys.argv)
	images = shuffleTree(images)

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

	#print random.shuffle(imagepairs)
	#print (imagepairs.items())[0]
	if params['selexonId'] is None:
		params['selexonId'] = apParticle.guessParticlesForSession(images[0]['session'].dbid)
	del images
	notdone=True
	while notdone:
		for key,pair in imagepairs.items():
			if len(pair) == 1 or len(pair) > 2:
				apDisplay.printWarning(apDisplay.short(pair[0]['filename'])+" is not a pair of images")
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
				print "PROCESSING\n\t",apDisplay.short(imgname1),"\n\t",apDisplay.short(imgname2)
				apTilt.process(img1,img2,params)

				apLoop.writeDoneDict(donedict,params,imgname1)
				apLoop.writeDoneDict(donedict,params,imgname2)
				apLoop.printSummary(stats, params)
				#END LOOP OVER IMAGES
		notdone,images = apLoop.waitForMoreImages(stats, params)
		#END NOTDONE LOOP	
	apLoop.completeLoop(stats)
