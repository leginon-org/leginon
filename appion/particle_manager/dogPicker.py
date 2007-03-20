#!/usr/bin/python -O

import sys
import data
import particleData
#import selexonFunctions  as sf1
#import selexonFunctions2 as sf2
#from selexonFunctions  import *
#from selexonFunctions2 import *
import apLoop
import apParam
import apDog
import apDatabase

data.holdImages(False)

if __name__ == '__main__':
	if len(sys.argv) < 2:
		apDog.dogHelp()
		sys.exit(1)

	(images,params,stats,donedict) = apLoop.startNewAppionFunction(sys.argv)

	#params = apDog.modifyDefaultParams(params)

	notdone = True
	while notdone:
		for img in images:
			
			imagename = img['filename']

			stats['imagesleft'] = stats['imagecount'] - stats['count']
			#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
			if( apLoop.startLoop(img, donedict, stats, params)==False ):
				continue

			peaks = apDog.runDogDetector(imagename, params)

			if peaks is None:
				continue
			
			numpeaks = (peaks.shape)[0]
			stats['lastpeaks'] = numpeaks
			stats['peaksum']   = stats['peaksum'] + numpeaks
			stats['peaksumsq'] = stats['peaksumsq'] + numpeaks**2



			if params['commit']:
				insertDogPicksIntoDB(img,params)
				
			apLoop.printSummary(stats, params)

			apLoop.writeDoneDict(donedict,params,imagename)
		notdone = apLoop.waitForMoreImages(stats, params)
	apLoop.completeLoop(stats)
