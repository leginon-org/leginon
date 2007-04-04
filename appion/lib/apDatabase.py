#Part of the new pyappion

import sys
import data
import dbdatakeeper
import apLoop,apDisplay
import time,math
#import selexonFunctions  as sf1

data.holdImages(False)
db     = dbdatakeeper.DBDataKeeper()
#partdb = dbdatakeeper.DBDataKeeper(db='dbparticledata')
#acedb  = dbdatakeeper.DBDataKeeper(db='dbctfdata')
#projdb = dbdatakeeper.DBDataKeeper(db='project')

def getAllImages(stats,params):
	startt = time.time()
	if 'dbimages' in params and params['dbimages']==True:
		images = _getImagesFromDB(params['sessionname'],params['preset'])
	elif 'alldbimages' in params and  params['alldbimages']==True:
		images = _getAllImagesFromDB(params['sessionname'])
	elif 'mrcfileroot' in params and len(params['mrcfileroot']) > 0:
		images = _getSpecificImagesFromDB(params)
		params['sessionname']=images[0]['session']['name']
	else:
		print len(params['mrcfileroot']),params['alldbimages'],params['dbimages'],params['mrcfileroot']
		apDisplay.printError("no files specified")
	params['session']=images[0]['session']
	stats['imagecount']=len(images)
	print " ... found",len(images),"in",apDisplay.timeString(time.time()-startt)
	return images

def _getSpecificImagesFromDB(params):
	imglist=params["mrcfileroot"]
	print "Querying database for "+str(len(imglist))+" specific images ... "
	images=[]
	for img in imglist:
		imageq      = data.AcquisitionImageData(filename=img)
		imageresult = db.query(imageq, readimages=False)
		images      = images+imageresult

	return images

def _getImagesFromDB(session,preset):
	# returns list of image names from DB
	apDisplay.printMsg("Querying database for preset '"+preset+"' images from session '"+session+"' ... ")
	sessionq = data.SessionData(name=session)
	presetq=data.PresetData(name=preset)
	imageq=data.AcquisitionImageData()
	imageq['preset'] = presetq
	imageq['session'] = sessionq
	imagelist=db.query(imageq, readimages=False)
	"""
	loop through images and make data.holdimages false 	 
	this makes it so that data.py doesn't hold images in memory 	 
	solves a bug where processing quits after a dozen or so images
	"""
	#for img in imagelist: 	 
		#img.holdimages=False
	return imagelist

def _getAllImagesFromDB(session):
	# returns list of image data based on session name
	apDisplay.printMsg("Querying database for all images from session '"+session+"' ... ")
	sessionq= data.SessionData(name=session)
	imageq=data.AcquisitionImageData()
	imageq['session']=sessionq
	imagelist=db.query(imageq, readimages=False)
	return imagelist

def getImageData(imagename):
	# get image data object from database
	imagedataq = data.AcquisitionImageData(filename=imagename)
	imagedata  = db.query(imagedataq, results=1, readimages=False)
	#imagedata[0].holdimages=False
	if imagedata:
		return imagedata[0]
	else:
		apDisplay.printError("Image "+imagename+" not found in database\n")

def getTiltAngle(img,params):
	return img['scope']['stage position']['a']*180.0/math.pi

def getPixelSize(img):
	# use image data object to get pixel size
	# multiplies by binning and also by 1e10 to return image pixel size in angstroms
	# shouldn't have to lookup db already should exist in imgdict
	pixelsizeq=data.PixelSizeCalibrationData()
	pixelsizeq['magnification']=img['scope']['magnification']
	pixelsizeq['tem']=img['scope']['tem']
	pixelsizeq['ccdcamera'] = img['camera']['ccdcamera']
	pixelsizedata=db.query(pixelsizeq, results=1)
	
	binning=img['camera']['binning']['x']
	pixelsize=pixelsizedata[0]['pixelsize'] * binning
	
	return(pixelsize*1e10)

def getImgSize(img):
	if 'image' in img:
		return (img['image'].shape)[1]
	fname = img['filename']
	# get image size (in pixels) of the given mrc file
	imageq=data.AcquisitionImageData(filename=fname)
	imagedata=db.query(imageq, results=1, readimages=False)
	if imagedata:
		size=int(imagedata[0]['camera']['dimension']['y'])
		return(size)
	else:
		apDisplay.printError("Image "+fname+" not found in database\n")
	return(size)
