#!/usr/bin/python -O

import sys,os
import apLoop
import apDog
import apPeaks
import apDisplay

if __name__ == '__main__':

	apDisplay.printWarning("Please use 'pyappion/bin/basicDogPicker.py' to use dogpicker")

	if not os.path.isfile("pcavects.txt"):
		apDisplay.printError("dogPicker.py requires the file 'pcavects.txt'\n"+
			"\tto be in the directory where you run the script")

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

			peakdict = apDog.convertDogPeaks(peaks, params)
			apPeaks.createPeakJpeg(img, peakdict, params)

			if params['commit']:
				apDog.insertDogPicksIntoDB(img, peaks, params)
				
			apLoop.printSummary(stats, params)

			apLoop.writeDoneDict(donedict,params,imagename)
		notdone,images = apLoop.waitForMoreImages(stats, params)
	apLoop.completeLoop(stats)
