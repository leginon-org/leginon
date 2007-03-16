#Part of the new pyappion

import sys
import data
import dbdatakeeper
import selexonFunctions  as sf1

data.holdImages(False)
db=dbdatakeeper.DBDataKeeper()
partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
projdb=dbdatakeeper.DBDataKeeper(db='project')

def getAllImages(params,stats):
	if params['dbimages']==True:
		images=_getImagesFromDB(params['sessionname'],params['preset'])
		params['session']=images[0]['session']
	elif params['alldbimages']==True:
		images=_getAllImagesFromDB(params['sessionname'])
		params['session']=images[0]['session']
	else:
		images = _getSpecificImagesFromDB(params)
		params['session']=images[0]['session']
		params['sessionname']=images[0]['session']['name']
	stats['imagecount']=len(images)
	return images

def _getSpecificImagesFromDB(params):
	if not params['mrcfileroot']:
		print "\nERROR: no files specified\n"
		sys.exit(1)
	sys.stderr.write("Querying database for specific images ... ")
	imglist=params["mrcfileroot"]
	images=[]
	for img in imglist:
		imageq      = data.AcquisitionImageData(filename=img)
		imageresult = db.query(imageq, readimages=False)
		images      = images+imageresult
	print "found",len(images)
	return images

def _getImagesFromDB(session,preset):
	# returns list of image names from DB
	sys.stderr.write("Querying database for images from session, "+session+"... ")
	sessionq = data.SessionData(name=session)
	presetq=data.PresetData(name=preset)
	imageq=data.AcquisitionImageData()
	imageq['preset'] = presetq
	imageq['session'] = sessionq
	# readimages=False to keep db from returning actual image
	# readimages=True could be used for doing processing w/i this script
	imagelist=db.query(imageq, readimages=False)
	#loop through images and make data.holdimages false 	 
	#this makes it so that data.py doesn't hold images in memory 	 
	#solves a bug where selexon quits after a dozen or so images 	 
	#for img in imagelist: 	 
		#img.holdimages=False
	print "found",len(imagelist)
	return imagelist

def _getAllImagesFromDB(session):
	# returns list of image data based on session name
	sys.stderr.write("Querying database for images ... ")
	sessionq= data.SessionData(name=session)
	imageq=data.AcquisitionImageData()
	imageq['session']=sessionq
	imagelist=db.query(imageq, readimages=False)
	print "found",len(imagelist)
	return imagelist


