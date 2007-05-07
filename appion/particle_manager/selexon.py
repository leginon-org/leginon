#!/usr/bin/python -O
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

#pythonlib
import os, sys
#leginon
import data
#appion-old
#import selexonFunctions  as sf1
#import selexonFunctions2 as sf2
#appion
import apLoop
import apCrud
import apDatabase
import apDefocalPairs
import apFindEM
import apViewIt
import apDisplay
import apTemplate
import apParticle
import apPeaks

if __name__ == '__main__':
	apDisplay.printWarning("Please use 'pyappion/bin/templateCorrelator.py' to use selexon")

	(imgtree, stats, params, donedict) = apLoop.startNewAppionFunction(sys.argv)

	# if shiftonly is specified, make defocpair true
	if 'shiftonly' in params and params['shiftonly'] == True:
		print "PLEASE: Write me a different program for 'shiftonly'"
		params['defocpair']=True

	# if templateIds specified, create temporary template files in this directory & rescale
	apTemplate.getTemplates(params)

	if params['method'] == "classic":
		apViewIt.createImageLinks(imgtree)
	
	# check to see if user only wants to run the crud finder
	if params["crudonly"] is True:
		apDisplay.printError("'crudonly' no longer supported please run 'makeMask.py'")
        
	# check to see if user only wants to find shifts
	if params['shiftonly'] is True:
		apDisplay.printWarning("please make a new shiftonly script")
		for img in imgtree:
			sibling=apDefocalPairs.getDefocusPair(img)
			if sibling:
				peak=apDefocalPairs.getShift(img,sibling)
				apDefocalPairs.recordShift(params,img,sibling,peak)
				if params['commit']:
					apDefocalPairs.insertShift(img,sibling,peak)
		sys.exit(1)

	# unpickle dictionary of previously processed images
	donedict = apLoop.readDoneDict(params)

	# run selexon
	notdone=True
	while notdone is True:
		for imgdict in imgtree:
			imgname = imgdict['filename']

			#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
			if( apLoop.startLoop(imgdict, donedict, stats, params)==False ):
				continue

			if params['templateIds']:
				apTemplate.rescaleTemplates(params)
				#SHOULD ONLY DO ABOVE IF APIX CHANGES

			# run FindEM
			ccmaplist = apFindEM.runFindEM(imgdict, params)

			#FIND PEAKS
			if params['method'] == "classic":
				apViewIt.findPeaks(params, imgdict)
				numpeaks = 0
			else:
				#numpeaks = sf2.findPeaks2(params,imgname)
				peaktree  = apPeaks.findPeaks(imgdict, ccmaplist, params)
				numpeaks = len(peaktree)
				stats['lastpeaks'] = numpeaks
				stats['peaksum']   = stats['peaksum'] + numpeaks
				stats['peaksumsq'] = stats['peaksumsq'] + numpeaks**2

			# if no particles were found, skip rest and go to next image
			if numpeaks == 0 and not os.path.isfile("pikfiles/"+imgname+".a.pik"):
				print "no particles found in \'"+imgname+".mrc\'"
				# write results to dictionary
				apLoop.writeDoneDict(donedict,params,imgname)
				continue

			#CREATE JPG of selected particles
			if params['method'] == "classic":
				apViewIt.createJPG(params,imgdict)
			else:
				apPeaks.createPeakJpeg(imgdict, peaktree, params)
				#sf2.createJPG2(params,imgname)

			# convert resulting pik file to eman box file
			if (params["box"]>0):
				apParticle.pik2Box(params,imgname)
		
			# find defocus pair if defocpair is specified
			if params['defocpair'] == True:
				apDisplay.printWarning("please make a new defocpair script")
				sibling=apDefocalPairs.getDefocusPair(imgdict)
				if sibling:
					peak=apDefocalPairs.getShift(imgdict,sibling)
					apDefocalPairs.recordShift(params,imgdict,sibling,peak)
					if params['commit']:
						apDefocalPairs.insertShift(imgdict,sibling,peak)
			
			if params['commit'] is True:
				expid=int(imgdict['session'].dbid)
				#SELEXON MUST COME FIRST
				apParticle.insertSelexonParams(params,expid)
				if params['method'] == "classic":
					apParticle.insertParticlePicks(params,imgdict,expid)
				else:
					apParticle.insertParticlePeaks(peaktree, imgdict, expid, params)

			# write results to dictionary
			apLoop.writeDoneDict(donedict,params,imgname)
			apLoop.printSummary(stats, params)
			#END LOOP OVER IMAGES

		notdone,imgtree = apLoop.waitForMoreImages(stats, params)
		#END NOTDONE LOOP

	# remove temporary templates if getting images from db
	if params['templateIds']:
		i=1
		for tmplt in params['ogTmpltInfo']:
			ogname="originalTemporaryTemplate"+str(i)+".mrc"
			scname="scaledTemporaryTemplate"+str(i)+".mrc"
			scdwnname="scaledTemporaryTemplate"+str(i)+".dwn.mrc"
			os.remove(ogname)
			os.remove(scname)
			os.remove(scdwnname)
			i=i+1
			
	apLoop.completeLoop(stats)
