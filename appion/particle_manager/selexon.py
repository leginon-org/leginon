#!/usr/bin/python -O
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

import os, re, sys
import data
#import mem
import apLoop
import apParam
import apDatabase
import selexonFunctions  as sf1
import selexonFunctions2 as sf2
import apCrud

data.holdImages(False)

if __name__ == '__main__':
	(images,params,stats,donedict) = apLoop.startNewAppionFunction(sys.argv)

	# if shiftonly is specified, make defocpair true
	if params['shiftonly']:
		print "write me a different program for shiftonly"
		params['defocpair']=True

	# if templateIds specified, create temporary template files in this directory & rescale
	print " ... getting templates"
	if params['templateIds']:
		# get the first image's pixel size:
		params['apix'] = sf1.getPixelSize(images[0])
		params['template']='originalTemporaryTemplate'
		# move to run directory
		os.chdir(params['rundir'])
		# get the templates from the database
		sf1.getDBTemplates(params)
		# scale them to the appropriate pixel size
		sf1.rescaleTemplates(images[0],params)
		# set the template name to the copied file names
		params['template']='scaledTemporaryTemplate'
		
	# find the number of template files
	if params["crudonly"]==False:
		sf1.checkTemplates(params)
		# go through the template mrc files and downsize & filter them
		for tmplt in params['templatelist']:
			sf1.dwnsizeTemplate(params,tmplt)
		print " ... downsize & filtered "+str(len(params['templatelist']))+ \
			" file(s) with root \""+params["template"]+"\""

	if (params["crud"]==True or params['method'] == "classic"):
		sf1.createImageLinks(images)
	
	# check to see if user only wants to run the crud finder
	if (params["crudonly"]==True):
		if (params["crud"]==True and params["cdiam"]==0):
			print "\nERROR: both \"crud\" and \"crudonly\" are set, choose one or the other.\n"
			sys.exit(1)
		if (params["diam"]==0): # diameter must be set
			print "\nERROR: please input the diameter of your particle\n\n"
			sys.exit(1)
		# create directory to contain the 'crud' files
		if not (os.path.exists("crudfiles")):
			os.mkdir("crudfiles")
		for img in images:
			imgname=img['filename']
			#findCrud(params,imgname)
			apCrud.findCrud(params,imgname)
		sys.exit(1)
        
	# check to see if user only wants to find shifts
	if params['shiftonly']:
		for img in images:
			sibling=sf1.getDefocusPair(img)
			if sibling:
				peak=sf1.getShift(img,sibling)
				sf1.recordShift(params,img,sibling,peak)
				if params['commit']:
					sf1.insertShift(img,sibling,peak)
		sys.exit(1)	
	
	# create directory to contain the 'pik' files
	if not (os.path.exists("pikfiles")):
		os.mkdir("pikfiles")

	# unpickle dictionary of previously processed images
	donedict = apLoop.readDoneDict(params)

	# run selexon
	notdone=True
	while notdone:
		while images:
			img = images.pop(0)
			imgname=img['filename']
			stats['imagesleft'] = len(images)

			#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
			if( apLoop.startLoop(img, donedict, stats, params)==False ):
				continue

			# run FindEM
			if params['method'] == "experimental":
				#Finds peaks as well:
				numpeaks = sf2.runCrossCorr(params,imgname)
				stats['lastpeaks'] = numpeaks
				stats['peaksum']   = stats['peaksum'] + numpeaks
				stats['peaksumsq'] = stats['peaksumsq'] + numpeaks**2
			else:
#				sf2.tmpRemoveCrud(params,imgname)
				sf1.dwnsizeImg(params,imgname)
				if(os.getloadavg() > 3.1):
					sf1.runFindEM(params,imgname)
				else:
					sf2.threadFindEM(params,imgname)

			#FIND PEAKS
			if params['method'] == "classic":
				sf1.findPeaks(params,imgname)
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
					sf1.createJPG(params,imgname)
				else:
					sf2.createJPG2(params,imgname)

			# convert resulting pik file to eman box file
			if (params["box"]>0):
				sf1.pik2Box(params,imgname)
		
			# find defocus pair if defocpair is specified
			if params['defocpair'] == True:
				sibling=sf1.getDefocusPair(img)
				if sibling:
					peak=sf1.getShift(img,sibling)
					sf1.recordShift(params,img,sibling,peak)
					if params['commit']:
						sf1.insertShift(img,sibling,peak)
			
			if params['commit'] == True:
				expid=int(img['session'].dbid)
				sf1.insertParticlePicks(params,img,expid)
				sf1.insertSelexonParams(params,expid)

			# write results to dictionary
			apLoop.writeDoneDict(donedict,params,imgname)

			apLoop.printSummary(stats, params)
			#END LOOP OVER IMAGES

		notdone = apLoop.waitForMoreImages(stats, params)
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

