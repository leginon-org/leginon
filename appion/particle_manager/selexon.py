#!/usr/bin/python -O
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

import os, re, sys
import data
import time
from selexonFunctions import *
from selexonFunctions2 import *
from crudFinderFunctions2 import *

selexondonename='.selexondone.py'
imagesskipped=False

if __name__ == '__main__':
	# record command line
	writeSelexLog(sys.argv)

	print " ... checking parameters"
	# create params dictionary & set defaults
	params=createDefaults()

	# parse command line input
	parseSelexonInput(sys.argv,params)

	# if shiftonly is specified, make defocpair true
	if params['shiftonly']:
		params['defocpair']=True

	# check to make sure that incompatible parameters are not set
	if not params['templateIds'] and not params['apix']:
		print "\nERROR: if not using templateIds, you must enter a template pixel size\n"
		sys.exit(1)
	if params['templateIds'] and params['template']:
		print "\nERROR: Both template database IDs and mrc file templates are specified,\nChoose only one\n"
		sys.exit(1)
	if params['crudonly']==True and params['shiftonly']==True:
		print "\nERROR: crudonly and shiftonly can not be specified at the same time\n"
		sys.exit(1)
	if (params["thresh"]==0 and params["autopik"]==0):
		print "\nERROR: neither manual threshold or autopik parameters are set, please set one.\n"
		sys.exit(1)
	if (params["diam"]==0):
		print "\nERROR: please input the diameter of your particle\n"
		sys.exit(1)
	if len(params["mrcfileroot"]) > 0 and params["dbimages"]==True:
		print len(images)
		print "\nERROR: dbimages can not be specified if particular images have been specified\n"
		sys.exit(1)
	if params['alldbimages'] and params['dbimages']==True:
		print "\nERROR: dbimages and alldbimages can not be specified at the same time\n"
		sys.exit(1)
	if len(params['mrcfileroot']) > 0 and params['alldbimages']:
		print "\nERROR: alldbimages can not be specified if particular images have been specified\n"
		sys.exit(1)
	
	# get list of input images, since wildcards are supported
	print " ... getting images"
	if params['dbimages']==True:
		images=getImagesFromDB(params['sessionname'],params['preset'])
		params['session']=images[0]['session']
	elif params['alldbimages']:
		images=getAllImagesFromDB(params['sessionname'])
		params['session']=images[0]['session']
	else:
		if not params['mrcfileroot']:
			print "\nERROR: no files specified\n"
			sys.exit(1)
		imglist=params["mrcfileroot"]
		images=[]
		for img in imglist:
			imageq=data.AcquisitionImageData(filename=img)
			imageresult=db.query(imageq, readimages=False)
			images=images+imageresult
		params['session']=images[0]['session']

	getOutDirs(params)

	# if templateIds specified, create temporary template files in this directory & rescale
	print " ... getting templates"
	if params['templateIds']:
		# get the first image's pixel size:
		params['apix']=getPixelSize(images[0])
		params['template']='originalTemporaryTemplate'
		# move to run directory
		os.chdir(params['rundir'])
		# get the templates from the database
		getDBTemplates(params)
		# scale them to the appropriate pixel size
		rescaleTemplates(images[0],params)
		# set the template name to the copied file names
		params['template']='scaledTemporaryTemplate'
		
	# find the number of template files
	if params["crudonly"]==False:
		checkTemplates(params)
		# go through the template mrc files and downsize & filter them
		for tmplt in params['templatelist']:
			dwnsizeTemplate(params,tmplt)
		print " ... downsize & filtered "+str(len(params['templatelist']))+ \
			" file(s) with root \""+params["template"]+"\""
			
	# unpickle dictionary of previously processed images
	donedict=getDoneDict(selexondonename)

	createImageLinks(images)
	
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
			tstart=time.time()
			#findCrud(params,imgname)
			findCrud2(params,imgname)
			tend=time.time()
			print "CRUD FINDING TIME",tend-tstart
		sys.exit(1)
        
	# check to see if user only wants to find shifts
	if params['shiftonly']:
		for img in images:
			sibling=getDefocusPair(img)
			if sibling:
				peak=getShift(img,sibling)
				recordShift(params,img,sibling,peak)
				if params['commit']:
					insertShift(img,sibling,peak)
		sys.exit()	
	
	# create directory to contain the 'pik' files
	if not (os.path.exists("pikfiles")):
		os.mkdir("pikfiles")

	#Write log to rundir
	writeSelexLog(sys.argv,file="selexon.log")

	# run selexon
	notdone=True
	twhole=time.time()
	count  = 1
	lastcount = 0
	peaksum = 0
	peaksumsq = 0
	timesum = 0
	timesumsq = 0
	while notdone:
		while images:
			if(lastcount != count):
				print "\nStarting image",count,"..."
				lastcount = count
			tbegin=time.time()
			img = images.pop(0)

			# get the image's pixel size:
			params['apix']=getPixelSize(img)

			# skip if image doesn't exist:
			if not os.path.isfile(params['imgdir']+img['filename']+'.mrc'):
				print " !!! "+img['filename']+".mrc not found, skipping"
				continue

			# if continue option is true, check to see if image has already been processed
			imgname=img['filename']
			doneCheck(donedict,imgname)
			if (params["continue"]==True):
				if donedict[imgname]:
					imagesskipped=True
					#print imgname,'already processed. To process again, remove "continue" option.'
					continue

			# insert selexon params into dbparticledata.selectionParams table
			expid=int(img['session'].dbid)
			if params['commit']==True:
				insertSelexonParams(params,expid)

			# match the original template pixel size to the img pixel size
			if params['templateIds']:
				rescaleTemplates(img,params)
			
			# run FindEM
			if params['method'] == "experimental":
				#Finds peaks as well:
				numpeaks = runCrossCorr(params,imgname)
				peaksum = peaksum + numpeaks
				peaksumsq = peaksumsq + numpeaks**2
			else:
#				tmpRemoveCrud(params,imgname)
#				sys.exit()
				dwnsizeImg(params,imgname)
				runFindEM(params,imgname)

			if params['method'] == "classic":
				findPeaks(params,imgname)
				numpeaks = 0
			elif params['method'] == "experimental":
				print "skipping findpeaks..."
			else:
				numpeaks = findPeaks2(params,imgname)
				peaksum = peaksum + numpeaks
				peaksumsq = peaksumsq + numpeaks**2

			# if no particles were found, skip rest and go to next image
			if not (os.path.exists("pikfiles/"+imgname+".a.pik")):
				print "no particles found in \'"+imgname+".mrc\'"
				# write results to dictionary
				donedict[imgname]=True
				writeDoneDict(donedict,selexondonename)
				continue

			# run the crud finder on selected particles if specified
			if (params["crud"]==True):
				if not (os.path.exists("crudfiles")):
					os.mkdir("crudfiles")
					t1=time.time()
					findCrud(params,imgname)
					tfindCrud= "%.2f" % float(time.time()-t1)
				# if crudfinder removes all the particles, go to next image
				if not (os.path.exists("pikfiles/"+imgname+".a.pik.nocrud")):
					print "no particles left after crudfinder in \'"+imgname+".mrc\'"
 					# write results to dictionary
					donedict[imgname]=True
					writeDoneDict(donedict)
					continue

			# create jpg of selected particles if not created by crudfinder
			if (params["crud"]==False):
				if params['method'] == "classic":
					createJPG(params,imgname)
				else:
					createJPG2(params,imgname)

			# convert resulting pik file to eman box file
			if (params["box"]>0):
				pik2Box(params,imgname)
		
			# find defocus pair if defocpair is specified
			if params['defocpair']:
				sibling=getDefocusPair(img)
				if sibling:
					peak=getShift(img,sibling)
					recordShift(params,img,sibling,peak)
					if params['commit']:
						insertShift(img,sibling,peak)
			
			if params['commit']:
				insertParticlePicks(params,img,expid)

			# write results to dictionary
 			donedict[imgname]=True
			writeDoneDict(donedict,selexondonename)

			#SUMMARIZE INFO
			tdiff = time.time()-tbegin
			ttotal = "%.2f" % float(tdiff)
			if(params["continue"]==False or tdiff > 0.3):


				print "\n\t\tSUMMARY:"
				print "\t-----------------------------"
				print "\t...using the",params['method'],"method"
				if (params["crud"]==True):
					print "\tFindCrud:  \t",tfindCrud,"seconds"

				print "\tPEAKS:    \t",numpeaks,"peaks"
				if(count > 1):
					peakstdev = math.sqrt(float(count*peaksumsq - peaksum**2) / float(count*(count-1)))
					print "\tAVG PEAKS:\t",round(float(peaksum)/float(count),1),"+/-",\
						round(peakstdev,1),"peaks"
					print "\t(- TOTAL:",peaksum,"peaks for",count,"images -)"

				print "\tTIME:     \t",ttotal,"sec"
				timesum = timesum + tdiff
				timesumsq = timesumsq + (tdiff**2)
				if(count > 1):
					timestdev = math.sqrt(float(count*timesumsq - timesum**2) / float(count*(count-1)))
					print "\tAVG TIME: \t",round(float(timesum)/float(count),1),"+/-",\
						round(timestdev,1),"sec"
					print "\t(- TOTAL:",round(timesum/60.0,2),"min -)"

				count = count + 1
				print "\t-----------------------------"

		if params["dbimages"]==True:
			notdone=True
			if(imagesskipped == True):
				print " !!! Images already processed and were therefore skipped."
				print " !!! to them process again, remove \'continue\' option and run selexon again."
				imagesskipped=False
			print "\nAll images processed. Waiting ten minutes for new images."
			time.sleep(600)
			images=getImagesFromDB(params['session']['name'],params['preset'])
			createImageLinks(images)
		else:
			notdone=False

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
			
	ttotal= "%.2f" % float(time.time()-twhole)
	print "COMPLETE LOOP:\t",ttotal,"seconds for",count-1,"images"
	print "end run"
	print "====================================================="
	print "====================================================="
	print "====================================================="
	print "====================================================="
	print ""

