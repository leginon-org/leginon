#Part of the new pyappion

#pythonlib
import sys
import os
import time
import math
import shutil
#sinedon
import sinedon
import sinedon.data as data
#leginon
import leginondata
#appion
import apDB
import apDisplay
import appionData
import apDefocalPairs

data.holdImages(False)
leginondb = apDB.db
appiondb = apDB.apdb

def getAllImages(stats, params):
	startt = time.time()
	if 'dbimages' in params and params['dbimages']==True:
		imgtree = getImagesFromDB(params['sessionname'],params['preset'])
	elif 'alldbimages' in params and  params['alldbimages']==True:
		imgtree = getAllImagesFromDB(params['sessionname'])
	elif 'mrcfileroot' in params and len(params['mrcfileroot']) > 0:
		imgtree = getSpecificImagesFromDB(params["mrcfileroot"])
		params['sessionname']=imgtree[0]['session']['name']
	else:
		print len(params['mrcfileroot']),params['alldbimages'],params['dbimages'],params['mrcfileroot']
		apDisplay.printError("no files specified")
	if imgtree is None or len(imgtree) < 1:
		apDisplay.printError("did not find any images") 
	params['session'] = imgtree[0]['session']
	params['apix'] = getPixelSize(imgtree[0])
	stats['imagecount']=len(imgtree)
	print " ... found",stats['imagecount'],"in",apDisplay.timeString(time.time()-startt)
	return imgtree

def getSpecificImagesFromDB(imglist):
	print "Querying database for "+str(len(imglist))+" specific images ... "
	imgtree=[]
	for imgname in imglist:
		imgquery = leginondata.AcquisitionImageData(filename=imgname)
		imgres   = leginondb.query(imgquery, readimages=False, results=1)
		imgtree.append(imgres[0])
	return imgtree

def getImagesFromDB(session, preset):
	"""
	returns list of image names from DB
	"""
	apDisplay.printMsg("Querying database for preset '"+preset+"' images from session '"+session+"' ... ")
	sessionq = leginondata.SessionData(name=session)
	presetq=leginondata.PresetData(name=preset)
	imgquery = leginondata.AcquisitionImageData()
	imgquery['preset']  = presetq
	imgquery['session'] = sessionq
	imgtree = leginondb.query(imgquery, readimages=False)
	"""
	loop through images and make data.holdimages false 	 
	this makes it so that data.py doesn't hold images in memory 	 
	solves a bug where processing quits after a dozen or so images
	"""
	#for img in imgtree: 	 
		#img.holdimages=False
	return imgtree

def getAllImagesFromDB(session):
	"""
	returns list of image data based on session name
	"""
	apDisplay.printMsg("Querying database for all images from session '"+session+"' ... ")
	sessionq= leginondata.SessionData(name=session)
	imgquery = leginondata.AcquisitionImageData()
	imgquery['session'] = sessionq
	imgtree = leginondb.query(imgquery, readimages=False)
	return imgtree

def getExpIdFromSessionName(sessionname):
	apDisplay.printMsg("looking up session, "+sessionname)
	sessionq = leginondata.SessionData(name=sessionname)
	sessioninfo = leginondb.query(sessionq, readimages=False, results=1)
	if sessioninfo:
		return sessioninfo[0].dbid
	else:
		apDisplay.printError("could not find session, "+sessionname)

def getSessionDataFromSessionName(sessionname):
	apDisplay.printMsg("looking up session, "+sessionname)
	sessionq = leginondata.SessionData(name=sessionname)
	sessioninfo = leginondb.query(sessionq, readimages=False, results=1)
	if sessioninfo:
		return sessioninfo[0]
	else:
		apDisplay.printError("could not find session, "+sessionname)

def getImageData(imgname):
	"""
	get image data object from database
	"""
	imgquery = leginondata.AcquisitionImageData(filename=imgname)
	imgtree  = leginondb.query(imgquery, results=1, readimages=False)
	if imgtree:
		#imgtree[0].holdimages=False
		return imgtree[0]
	else:
		apDisplay.printError("Image "+imgname+" not found in database\n")

def getImgDir(sessionname):
	sessionq = leginondata.SessionData(name=sessionname)
	sessiondata = leginondb.query(sessionq)
	imgdir = os.path.abspath(sessiondata[0]['image path'])
	return imgdir

def getSessionName(imgname):
	"""
	get session name from database
	"""
	imgquery = leginondata.AcquisitionImageData(filename=imgname)
	imgtree  = leginondb.query(imgquery, results=1, readimages=False)
	if 'session' in imgtree[0]:
		return imgtree[0]['session']['name']
	else:
		apDisplay.printError("Image "+imgname+" not found in database\n")

def getTiltAngleDeg(imgdata):
	return imgdata['scope']['stage position']['a']*180.0/math.pi

def getTiltAngleRad(imgdata):
	return imgdata['scope']['stage position']['a']

def getPixelSize(imgdict):
	"""
	use image data object to get pixel size
	multiplies by binning and also by 1e10 to return image pixel size in angstroms
	shouldn't have to lookup db already should exist in imgdict
	"""
	pixelsizeq=leginondata.PixelSizeCalibrationData()
	pixelsizeq['magnification'] = imgdict['scope']['magnification']
	pixelsizeq['tem'] = imgdict['scope']['tem']
	pixelsizeq['ccdcamera'] = imgdict['camera']['ccdcamera']
	pixelsizedata=leginondb.query(pixelsizeq, results=1)
	binning=imgdict['camera']['binning']['x']
	pixelsize=pixelsizedata[0]['pixelsize'] * binning
	return(pixelsize*1e10)

def getImgSize(imgdict):
	### SHOULD BE A DIRECT QUERY
	if 'image' in imgdict:
		return (imgdict['image'].shape)[1]
	fname = imgdict['filename']
	# get image size (in pixels) of the given mrc file
	imageq=leginondata.AcquisitionImageData(filename=fname)
	imagedata=leginondb.query(imageq, results=1, readimages=False)
	if imagedata:
		size=int(imagedata[0]['camera']['dimension']['y'])
		return(size)
	else:
		apDisplay.printError("Image "+fname+" not found in database\n")
	return(size)

def getApixFromStackData(stackdata):
	# pixel size is obtained from the first image in the stack
	stkptclq=appionData.ApStackParticlesData()
	stkptclq['stack'] = stackdata
	stkptclresults=appiondb.query(stkptclq, results=1)
	if not stkptclresults:
		apDisplay.printError("Stack not found")
	stackbin = stkptclresults[0]['stackRun']['stackParams']['bin']
	if stackbin is None:
		stackbin = 1

	imageref = stkptclresults[0]['particle'].special_getitem('image',dereference = False)
	imagedata = leginondb.direct_query(leginondata.AcquisitionImageData,imageref.dbid, readimages = False)

	if 'defocpair' in stkptclresults[0]['stackRun']['stackParams']:
		defocpair = stkptclresults[0]['stackRun']['stackParams']['defocpair']
	else:
		defocpair = None
	if defocpair != 0:
		imagedata = apDefocalPairs.getTransformedDefocPair(imagedata,1)
	
#	imagedata=leginondb.direct_query(leginondata.AcquisitionImageData,imageid)
		
	apix = getPixelSize(imagedata)
	stackapix = apix*stackbin

	return stackapix	

def getImgSizeFromName(imgname):
	# get image size (in pixels) of the given mrc file
	imageq=leginondata.AcquisitionImageData(filename=imgname)
	imagedata=leginondb.query(imageq, results=1, readimages=False)
	if imagedata:
		size=int(imagedata[0]['camera']['dimension']['y'])
		return(size)
	else:
		apDisplay.printError("Image "+imgname+" not found in database\n")
	return(size)

def getSiblingImgAssessmentStatus(imgdata):
	status = getImgAssessmentStatus(imgdata)
	if status is not None:
		return status
	siblingimgdata = apDefocalPairs.getDefocusPair(imgdata)
	if siblingimgdata:
		status = getImgAssessmentStatus(siblingimgdata)

	return status
	
def insertImgAssessmentStatus(imgdata, runname="pyapp1", assessment=None):
	"""
	Insert the assessment status 
		keep = True
		reject = False 
		unassessed = None
	"""
	if assessment is not True and assessment is not False:
		return False

	assessrun = appionData.ApAssessmentRunData()
	assessrun['session'] = imgdata['session']
	#override to ALWAYS be 'run1'
	#assessrun['name'] = runname
	assessrun['name'] = "run1"
	#assessrundata = appiondb.query(assessrun)

	assessquery = appionData.ApAssessmentData()
	assessquery['image'] = imgdata
	assessquery['assessmentrun'] = assessrun
	assessquery['selectionkeep'] = assessment

	appiondb.insert(assessquery)

	return True


def getImgCompleteStatus(imgdata):
	assess = getImgAssessmentStatus(imgdata)
	hidden = getImageViewerStatus(imgdata)
	if hidden is None:
		return assess
	elif assess is None:
		return hidden
	#False overrides True
	elif assess is False or hidden is False:
		return False
	return True

def getImgAssessmentStatus(imgdata):
	"""
	gets the assessment status (keep/reject) from the last assessment run
		keep = True
		reject = False 
		unassessed = None
	"""
	### this function should be modified in the future to allow for a particular assessment run
	if imgdata is None:
		return None
	assessquery = appionData.ApAssessmentData()
	assessquery['image'] = imgdata
	assessdata = appiondb.query(assessquery)

	if assessdata:
		#check results of only most recent run
		if assessdata[0]['selectionkeep'] == 1:
			return True
		elif assessdata[0]['selectionkeep'] == 0:
			return False
	return None


### flatfield correction functions

cache = {}
def camkey(camstate):
	return camstate['dimension']['x'], camstate['binning']['x'], camstate['offset']['x']

def getDarkNorm(sessionname, cameraconfig):
	"""
	return the most recent dark and norm image from the given session
	"""
	camquery = leginondata.CorrectorCamstateData()
	for i in ('dimension', 'binning', 'offset'):
		try:
			camquery[i] = cameraconfig[i]
		except:
			pass
	#print 'CAMQUERY', camquery
	key = camkey(camquery) 
	if key in cache:
		print 'using cache'
		return cache[key]
	
	print 'querying dark,norm'
	sessionquery = leginondata.SessionData(name=sessionname)
	darkquery = leginondata.DarkImageData(session=sessionquery, camstate=camquery)
	#print 'DARKQUERY', darkquery
	normquery = leginondata.NormImageData(session=sessionquery, camstate=camquery)
	darkdata = leginondb.query(darkquery, results=1)
	dark = darkdata[0]['image']
	#print darkdata[0]
	normdata = leginondb.query(normquery, results=1)
	norm = normdata[0]['image']
	result = dark,norm
	cache[key] = result

	return result

def getImageViewerStatus(imgdata):
	"""
	Function that returns whether or not the image was hidden in the viewer
	False: Image was hidden
	True: Image is an exemplar
	None: Image is visible

	see 'ImageStatusData' table in dbemdata
	or 'viewer_pref_image' table in dbemdata
	"""
	statusq = leginondata.ImageStatusData()
	statusq['image'] = imgdata
	statusdata = statusq.query(results=1)

	### quick fix to get status from viewer_pref_image
	dbconf=sinedon.getConfig('leginondata')
	db=sinedon.sqldb.sqlDB(**dbconf)
	imageId=imgdata.dbid
	q="select `status` from dbemdata.`viewer_pref_image` where imageId=%i" % (imageId,)
	### to add: something like if statusdata has a higher priority than
	### viewer hidden status
	### if statusdata is not None: return statusdata ...

	result=db.selectone(q)
	if result is None:
		return None
	if result['status']=='hidden':
		return False
	if result['status']=='examplar':
		return True
	return None


def checkInspectDB(imgdata):
	status = getImageViewerStatus(imgdata)
	if status is False:
		return False
	else:
		if status is True:
			return True
		else:
			keep = getImgAssessmentStatus(imgdata)
			return keep

def isModelInDB(md5sum):
	modelq = appionData.ApInitialModelData()
	modelq['md5sum'] = md5sum
	modeld = modelq.query(results=1)
	if modeld:
		return True
	return False
	
def isTemplateInDB(md5sum):
	templq = appionData.ApTemplateImageData()
	templq['md5sum'] = md5sum
	templd = templq.query(results=1)
	if templd:
		return True
	return False


if __name__ == '__main__':
	id = 442
	stackdata = appiondb.direct_query(appionData.ApStackData,id)
	stackapix = getApixFromStackData(stackdata)
	print stackapix


