#! /usr/bin/env python
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

import os, re, sys
import data
import time
from selexonFunctions import *
from selexonFunctions2 import *

selexondonename='.selexondone.py'

if __name__ == '__main__':
	# record command line
	writeSelexLog(sys.argv)

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
		sys.exit()
	if params['templateIds'] and params['template']:
		print "\nERROR: Both template database IDs and mrc file templates are specified,\nChoose one\n"
		sys.exit(1)
	if params['crudonly']=='TRUE' and params['shiftonly']=='TRUE':
		print 'ERROR: crudonly and shiftonly can not be specified at the same time'
		sys.exit()
	if (params["thresh"]==0 and params["autopik"]==0):
		print "\nERROR: neither manual threshold or autopik parameters are set, please set one.\n"
		sys.exit(1)
	if (params["diam"]==0):
		print "\nERROR: please input the diameter of your particle\n\n"
		sys.exit(1)
	if len(params["mrcfileroot"]) > 0 and params["dbimages"]=='TRUE':
		print len(images)
		print "\nERROR: dbimages can not be specified if particular images have been specified\n"
		sys.exit(1)
	if params['alldbimages'] and params['dbimages']=='TRUE':
		print "ERROR: dbimages and alldbimages can not be specified at the same time\n"
		sys.exit()
	if len(params['mrcfileroot']) > 0 and params['alldbimages']:
		print "ERROR: alldbimages can not be specified if particular images have been specified\n"
		sys.exit()
	
	# get list of input images, since wildcards are supported
	if params['dbimages']=='TRUE':
		images=getImagesFromDB(params['sessionname'],params['preset'])
		params['session']=images[0]['session']
	elif params['alldbimages']:
		images=getAllImagesFromDB(params['sessionname'])
		params['session']=images[0]['session']
	else:
		if not params['mrcfileroot']:
			print "\nERROR: no files specified\n"
			sys.exit()
		imglist=params["mrcfileroot"]
		images=[]
		for img in imglist:
			print img
			imageq=data.AcquisitionImageData(filename=img)
			imageresult=db.query(imageq, readimages=False)
			images=images+imageresult
		params['session']=images[0]['session']

	getOutDirs(params)

	# if templateIds specified, create temporary template files in this directory & rescale
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
	if params["crudonly"]=='FALSE':
		checkTemplates(params)
		# go through the template mrc files and downsize & filter them
		for tmplt in params['templatelist']:
			dwnsizeTemplate(params,tmplt)
		print "\ndownsize & filtered "+str(len(params['templatelist']))+ \
			" file(s) with root \""+params["template"]+"\"\n"
			
	# unpickle dictionary of previously processed images
	donedict=getDoneDict(selexondonename)

	createImageLinks(images)
	
	# check to see if user only wants to run the crud finder
	if (params["crudonly"]=='TRUE'):
		if (params["crud"]=='TRUE' and params["cdiam"]==0):
			print "\nError: both \"crud\" and \"crudonly\" are set, choose one or the other.\n"
			sys.exit(1)
		if (params["diam"]==0): # diameter must be set
			print "\nError: please input the diameter of your particle\n\n"
			sys.exit(1)
		# create directory to contain the 'crud' files
		if not (os.path.exists("crudfiles")):
			os.mkdir("crudfiles")
		for img in images:
			imgname=img['filename']
			findCrud(params,imgname)
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

	# run selexon
	notdone=True
	while notdone:
		while images:
			img = images.pop(0)

			# get the image's pixel size:
			params['apix']=getPixelSize(img)

			# skip if image doesn't exist:
			if not os.path.isfile(params['imgdir']+img['filename']+'.mrc'):
				print img['filename']+".mrc not found, skipping"
				continue

			# if continue option is true, check to see if image has already been processed
			imgname=img['filename']
			doneCheck(donedict,imgname)
			if (params["continue"]=='TRUE'):
				if donedict[imgname]:
					print imgname,'already processed. To process again, remove "continue" option.'
					continue

			# insert selexon params into dbparticledata.selectionParams table
			expid=int(img['session'].dbid)
			if params['commit']==True:
				insertSelexonParams(params,expid)

			# match the original template pixel size to the img pixel size
			if params['templateIds']:
				rescaleTemplates(img,params)
			
			# run FindEM
			t1=time.time()
			dwnsizeImg(params,imgname)
			tdwnsize= "%.2f" % float(time.time()-t1)

			t1=time.time()
			runFindEM(params,imgname)
			tfindem= "%.2f" % float(time.time()-t1)

			t1=time.time()
			findPeaks(params,imgname)
			tfindPeaks= "%.2f" % float(time.time()-t1)

			t1=time.time()
			findPeaks2(params,imgname)
			tfindPeaks2= "%.2f" % float(time.time()-t1)

			# if no particles were found, skip rest and go to next image
			if not (os.path.exists("pikfiles/"+imgname+".a.pik")):
				print "no particles found in \""+imgname+".mrc\"\n"
				# write results to dictionary
				donedict[imgname]=True
				writeDoneDict(donedict,selexondonename)
				continue

			# run the crud finder on selected particles if specified
			if (params["crud"]=='TRUE'):
				if not (os.path.exists("crudfiles")):
					os.mkdir("crudfiles")
					findCrud(params,imgname)
				# if crudfinder removes all the particles, go to next image
				if not (os.path.exists("pikfiles/"+imgname+".a.pik.nocrud")):
					print "no particles left after crudfinder in \""+imgname+".mrc\"\n"
 					# write results to dictionary
					donedict[imgname]=True
					writeDoneDict(donedict)
					continue

			# create jpg of selected particles if not created by crudfinder
			if (params["crud"]=='FALSE'):
				t1=time.time()
				createJPG(params,imgname)
				tcreateJPG= "%.2f" % float(time.time()-t1)

				t1=time.time()
				createJPG2(params,imgname)
				tcreateJPG2= "%.2f" % float(time.time()-t1)

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
	    
			print "TIME SUMMARY:"
			print "	dwnsizeImg:\t",tdwnsize,"seconds"
			print "	runFindEM: \t",tfindem,"seconds"
			print "	findPeaks: \t",tfindPeaks,"seconds"
			print "	findPeaks2:\t",tfindPeaks2,"seconds"
			print "	createJPG: \t",tcreateJPG,"seconds"
			print "	createJPG2:\t",tcreateJPG2,"seconds"



		if params["dbimages"]=='TRUE':
			notdone=True
			print "Waiting ten minutes for new images"
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
			


