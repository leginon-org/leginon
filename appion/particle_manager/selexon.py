#!/usr/bin/python -O
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

#pythonlib
import os, sys
#leginon
import data
#appion-old
import selexonFunctions  as sf1
import selexonFunctions2 as sf2
#appion
import apLoop
import apCrud
import apDatabase
import apDefocalPairs
import apFindEM
import apViewIt
import apDisplay
import apTemplate

data.holdImages(False)

if __name__ == '__main__':
	(images,stats,params,donedict) = apLoop.startNewAppionFunction(sys.argv)

	# if shiftonly is specified, make defocpair true
	if 'shiftonly' in params and params['shiftonly'] == True:
		print "PLEASE: Write me a different program for 'shiftonly'"
		params['defocpair']=True

	# if templateIds specified, create temporary template files in this directory & rescale
	print " ... getting templates"
	if params['templateIds']:
		# get the first image's pixel size:
		params['apix'] = apDatabase.getPixelSize(images[0])
		params['template']='originalTemporaryTemplate'
		# move to run directory
		os.chdir(params['rundir'])
		# get the templates from the database
		apDatabase.getDBTemplates(params)
		# scale them to the appropriate pixel size
		apTemplate.rescaleTemplates(params)
		# set the template name to the copied file names
		params['template']='scaledTemporaryTemplate'
		
	# find the number of template files
	if params["crudonly"]==False:
		apTemplate.checkTemplates(params)
		# go through the template mrc files and downsize & filter them
		for tmplt in params['templatelist']:
			apTemplate.downSizeTemplate(tmplt, params)
		print " ... downsize & filtered "+str(len(params['templatelist']))+ \
			" file(s) with root \""+params["template"]+"\""

	if (params["crud"]==True or params['method'] == "classic"):
		apViewIt.createImageLinks(images)
	
	# check to see if user only wants to run the crud finder
	if (params["crudonly"]==True):
		apDisplay.printError("'crudonly' no longer supported please run 'crudFinder.py'")
		#if (params["crud"]==True and params["cdiam"]==0):
		#	apDisplay.printError("both \"crud\" and \"crudonly\" are set, choose one or the other.\n")
		#if (params["diam"]==0): # diameter must be set
		#	apDisplay.printError("please input the diameter of your particle")
		# create directory to contain the 'crud' files
		#if not (os.path.exists("crudfiles")):
		#	os.mkdir("crudfiles")
		#for img in images:
		#	imgname=img['filename']
		#	#findCrud(params,imgname)
		#	apCrud.findCrud(params,imgname)
		#sys.exit(1)
        
	# check to see if user only wants to find shifts
	if params['shiftonly']:
		apDisplay.printWarning("please make a new shiftonly script")
		for img in images:
			sibling=apDefocalPairs.getDefocusPair(img)
			if sibling:
				peak=apDefocalPairs.getShift(img,sibling)
				apDefocalPairs.recordShift(params,img,sibling,peak)
				if params['commit']:
					apDefocalPairs.insertShift(img,sibling,peak)
		sys.exit(1)	
	
	# create directory to contain the 'pik' files
	if not (os.path.exists("pikfiles")):
		os.mkdir("pikfiles")

	# unpickle dictionary of previously processed images
	donedict = apLoop.readDoneDict(params)

	# run selexon
	notdone=True
	while notdone:
		#while images:
		for imgdict in images:
			#img = images.pop(0)
			imgname = imgdict['filename']
			#stats['imagesleft'] = len(images)

			#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
			if( apLoop.startLoop(imgdict, donedict, stats, params)==False ):
				continue
			if params['function'] == "selexon" and params['templateIds']:
				apTemplate.rescaleTemplates(params)
				#SHOULD ONLY DO ABOVE IF APIX CHANGES

			# run FindEM
			if params['method'] == "experimental":
				#Finds peaks as well:
				numpeaks = sf2.runCrossCorr(params,imgname)
				stats['lastpeaks'] = numpeaks
				stats['peaksum']   = stats['peaksum'] + numpeaks
				stats['peaksumsq'] = stats['peaksumsq'] + numpeaks**2
			else:
#				sf2.tmpRemoveCrud(params,imgname)
				sf1.dwnsizeImg(params, imgname)
				apFindEM.runFindEM(imgname, params)

			#FIND PEAKS
			if params['method'] == "classic":
				apViewIt.findPeaks(params, imgdict)
				numpeaks = 0
			elif params['method'] == "experimental":
				print "skipping findpeaks..."
			else:
				numpeaks = sf2.findPeaks2(params,imgname)
				stats['lastpeaks'] = numpeaks
				stats['peaksum']   = stats['peaksum'] + numpeaks
				stats['peaksumsq'] = stats['peaksumsq'] + numpeaks**2

			# if no particles were found, skip rest and go to next image
			#if not (os.path.exists("pikfiles/"+imgname+".a.pik")):
			if numpeaks == 0 and not os.path.exists("pikfiles/"+imgname+".a.pik"):
				print "no particles found in \'"+imgname+".mrc\'"
				# write results to dictionary
				apLoop.writeDoneDict(donedict,params,imgname)
				continue

			# run the crud finder on selected particles if specified
			if (params["crud"]==True):
				if not (os.path.exists("crudfiles")):
					os.mkdir("crudfiles")
				apCrud.removCrudPiks(params,imgname)
				# if crudfinder removes all the particles, go to next image
				if not (os.path.exists("pikfiles/"+imgname+".a.pik.nocrud")):
					print "no particles left after crudfinder in \'"+imgname+".mrc\'"
 					# write results to dictionary
					apLoop.writeDoneDict(donedict,params,imgname)
					continue

			#CREATE JPG of selected particles if not created by crudfinder
			if (params["crud"]==False):
				if params['method'] == "classic":
					apViewIt.createJPG(params,imgdict)
				else:
					sf2.createJPG2(params,imgname)

			# convert resulting pik file to eman box file
			if (params["box"]>0):
				sf1.pik2Box(params,imgname)
		
			# find defocus pair if defocpair is specified
			if params['defocpair'] == True:
				apDisplay.printWarning("please make a new defocpair script")
				sibling=apDefocalPairs.getDefocusPair(imgdict)
				if sibling:
					peak=apDefocalPairs.getShift(imgdict,sibling)
					apDefocalPairs.recordShift(params,imgdict,sibling,peak)
					if params['commit']:
						apDefocalPairs.insertShift(imgdict,sibling,peak)
			
			if params['commit'] == True:
				expid=int(imgdict['session'].dbid)
				#SELEXON MUST COME FIRST
				sf1.insertSelexonParams(params,expid)
				sf1.insertParticlePicks(params,imgdict,expid)

			# write results to dictionary
			apLoop.writeDoneDict(donedict,params,imgname)

			apLoop.printSummary(stats, params)
			#END LOOP OVER IMAGES

		notdone,images = apLoop.waitForMoreImages(stats, params)
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

