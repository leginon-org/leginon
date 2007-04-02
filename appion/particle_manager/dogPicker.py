#!/usr/bin/python -O

import sys
import apLoop
import apDog
	
if __name__ == '__main__':
	(images,stats,params,donedict) = apLoop.startNewAppionFunction(sys.argv)

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
				apDog.insertDogPicksIntoDB(img, peaks, params)
				
			apLoop.printSummary(stats, params)

			apLoop.writeDoneDict(donedict,params,imagename)
		notdone,images = apLoop.waitForMoreImages(stats, params)
	apLoop.completeLoop(stats)
