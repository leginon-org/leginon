#Part of the new pyappion

#pythonlib
import sys
import os
import time
import math
import shutil
#sinedon
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

def getTemplateFromId(templateid):
	# find templateImage row
	tmpltinfo = appiondb.direct_query(appionData.ApTemplateImageData, templateid)
	if not (tmpltinfo):
		apDisplay.printError("TemplateId "+str(templateid)+" not found in database. Use 'uploadTemplate.py'\n")
	return tmpltinfo
	
def getDBTemplates(params):
	tmptmplt=params['template']
	i=1
	for tid in params['templateIds']:
		tmpltinfo = getTemplateFromId(tid)
		apix = tmpltinfo['apix']
		# store row data in params dictionary
		params['ogTmpltInfo'].append(tmpltinfo)

		# copy file to current directory
		origtmplpath = os.path.join(tmpltinfo['path']['path'], tmpltinfo['templatename'])
		if os.path.isfile(origtmplpath):
			print "getting image:", origtmplpath
			newtmplpath = os.path.join(params['rundir'],tmptmplt+str(i)+".mrc")
			shutil.copy(origtmplpath, newtmplpath)
		else:
			apDisplay.printError("Template file not found: "+origtmplpath)
		params['scaledapix'][i] = 0
		i+=1
	return

	tmptmplt=params['template']
	i=1
	for tid in params['templateIds']:
		# find templateImage row
		tmpltinfo=appiondb.direct_query(appionData.ApTemplateImageData, tid)
		if not (tmpltinfo):
			apDisplay.printError("TemplateId "+str(tid)+" not found in database.  Use 'uploadTemplate.py'\n")
		fname=os.path.join(tmpltinfo['path']['path'],tmpltinfo['templatename'])
		apix=tmpltinfo['apix']
		# store row data in params dictionary
		params['ogTmpltInfo'].append(tmpltinfo)
		# copy file to current directory
		print "getting image:",fname
		os.system("cp "+fname+" "+tmptmplt+str(i)+".mrc")
		params['scaledapix'][i]=0
		i+=1
	return

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
	pixelsizeq['magnification']=imgdict['scope']['magnification']
	pixelsizeq['tem']=imgdict['scope']['tem']
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
	assessrun['dbemdata|SessionData|session'] = imgdata['session'].dbid
	#override to ALWAYS be 'run1'
	#assessrun['name'] = runname
	assessrun['name'] = "run1"
	assessrundata = appiondb.query(assessrun)

	assessquery = appionData.ApAssessmentData()
	assessquery['dbemdata|AcquisitionImageData|image'] = imgdata.dbid
	assessquery['assessmentrun'] = assessrundata[0]
	assessquery['selectionkeep'] = assessment

	appiondb.insert(assessquery)

	return None


def getImgAssessmentStatus(imgdata):
	"""
	gets the assessment status (keep/reject) from the last assessment run
		keep = True
		reject = False 
		unassessed = None
	"""
	### this function should be modified in the future to allow for a particular assessment run
	assessquery = appionData.ApAssessmentData()
	assessquery['dbemdata|AcquisitionImageData|image'] = imgdata.dbid
	assessdata = appiondb.query(assessquery)

	if assessdata:
		#check results of only most recent run
		if assessdata[0]['selectionkeep'] == 1:
			return True
		elif assessdata[0]['selectionkeep'] == 0:
			return False
	return None

def getImgAssessmentStatusREFLEGINON(imgdata):
	"""
	gets the assessment status (keep/reject) from the last assessment run
		keep = True
		reject = False 
		unassessed = None
	"""
	### this function should be modified in the future to allow for a particular assessment run
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
