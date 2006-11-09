#! /usr/bin/env python
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

import os, re, sys
import data
import time
from selexonFunctions import *

selexondonename='.selexondone.py'

if __name__ == '__main__':
	# record command line
	writeSelexLog(sys.argv)

	# create params dictionary & set defaults
	params=createDefaults()

	# parse command line input
	parseInput(sys.argv,params)

	# if shiftonly is specified, make defocpair true
	if params['shiftonly']:
		params['defocpair']=True

	# check to make sure that incompatible parameters are not set
	if params['templateIds'] and params['template']:
		print "\nBoth template database IDs and mrc file templates are specified,\nChoose one\n";
		sys.exit(1)
	if params['crudonly']=='TRUE' and params['shiftonly']=='TRUE':
		print 'crudonly and shiftonly can not be specified at the same time'
		sys.exit()
	if params['preptmplt']=='TRUE' and params['crudonly']=='TRUE':
		print 'preptemplate and crudonly can not be specified at the same time'
		sys.exit()
	if params['preptmplt']=='TRUE' and params['shiftonly']=='TRUE':
		print 'preptemplate and shiftonly can not be specified at the same time'
		sys.exit()

	# check for wrong or missing inputs
	if (params["apix"]==0 and not params["templateIds"]):
		print "\nError: no pixel size has been entered\n\n"
		sys.exit(1)

	# get list of input images, since wildcards are supported
	if params['dbimages']=='TRUE':
		images=getImagesFromDB(params['session']['name'],params['preset'])
	elif params['preptmplt']=='FALSE':
		imglist=params["mrcfileroot"]
		images=[]
		for img in imglist:
			imageq=data.AcquisitionImageData(filename=img)
			imageresult=db.query(imageq, readimages=False)
			images=images+imageresult
		params['session']=images[0]['session']

	getOutDirs(params)

	# move to run directory
	os.chdir(params['rundir'])

	# if templateIds specified, create temporary template files in this directory
	if params['templateIds']:
		getDBTemplates(params)
		# set the template name to the copied file names
		params['template']='originalTemporaryTemplate'
	
	# find the number of template files
	if (params["crudonly"]=='FALSE'):
		params=checkTemplates(params)
		# set the template name to scaled file name if getting from database
		if params['templateIds']:
			params['template']='scaledTemporaryTemplate'

	# check to see if user only wants to downsize & filter template files
	if (params["preptmplt"]=='TRUE' and not params["templateIds"]):
		prepTemplate(params)

	if (params["thresh"]==0 and params["autopik"]==0):
		print "\nError: neither manual threshold or autopik parameters are set, please set one.\n"
		sys.exit(1)
	if (params["diam"]==0):
		print "\nError: please input the diameter of your particle\n\n"
		sys.exit(1)
	if len(params["mrcfileroot"]) > 0 and params["dbimages"]=='TRUE':
		print len(images)
		print "\nError: dbimages can not be specified if particular images have been specified"
		sys.exit(1)
	
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

			print params['imgdir']
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

			# insert selexon params into dbparticledata.selexonParams table
			expid=int(img['session'].dbid)
			if params['commit']==True:
				insertSelexonParams(params,expid)

			# match the original template pixel size to the img pixel size
			if params['templateIds']:
				rescaleTemplates(img,params)
			
			# run FindEM
			dwnsizeImg(params,imgname)
			runFindEM(params,imgname)
			findPeaks(params,imgname)

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
				createJPG(params,imgname)

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
	    

		if params["dbimages"]=='TRUE':
			notdone=True
			print "Waiting one minute for new images"
			time.sleep(60)
			images=getImagesFromDB(params['session']['name'],params['preset'])
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
			

