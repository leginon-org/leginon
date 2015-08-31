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
import leginon.leginondata
#appion
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apDefocalPairs

####
# This is a database connections file with no file functions
# Please keep it this way
####

splitdb = True

data.holdImages(False)

#================
def getSpecificImagesFromDB(imglist, sessiondata=None):
	print "Querying database for "+str(len(imglist))+" specific images ... "
	imgtree=[]
	for imgname in imglist:
		if imgname[-4:] == ".mrc" or imgname[-4:] == ".box" or imgname[-4:] == ".pos":
			imgname = imgname[:-4]
		if '/' in imgname:
			imgname = os.path.basename(imgname)
		if sessiondata is not None:
			### slightly faster query
			imgquery = leginon.leginondata.AcquisitionImageData(filename=imgname, session=sessiondata)
		else:
			imgquery = leginon.leginondata.AcquisitionImageData(filename=imgname)
		imgres   = imgquery.query(readimages=False, results=1)
		if len(imgres) >= 1:
			imgtree.append(imgres[0])
		else:
			print imgres
			apDisplay.printError("Could not find image: "+imgname)
	return imgtree

#================
def getSpecificImagesFromSession(imglist, sessionname):
	print "Querying database for "+str(len(imglist))+" specific images ... "
	sessiondata = getSessionDataFromSessionName(sessionname)
	imgtree=[]
	for imgname in imglist:
		if imgname[-4:] == ".mrc" or imgname[-4:] == ".box":
			imgname = imgname[:-4]
		if '/' in imgname:
			imgname = os.path.basename(imgname)
		imgquery = leginon.leginondata.AcquisitionImageData()
		imgquery['filename'] = imgname
		imgquery['session'] = sessiondata
		imgres   = imgquery.query(readimages=False, results=1)
		if len(imgres) >= 1:
			imgtree.append(imgres[0])
		else:
			print imgres
			apDisplay.printError("Could not find image: "+imgname)
	return imgtree

#================
def getImagesFromDB(session, preset):
	"""
	returns list of image names from DB
	"""
	apDisplay.printMsg("Querying database for preset '"+preset+"' images from session '"+session+"' ... ")
	if preset != 'manual':
		sessionq = leginon.leginondata.SessionData(name=session)
		presetq=leginon.leginondata.PresetData(name=preset)
		imgquery = leginon.leginondata.AcquisitionImageData()
		imgquery['preset']  = presetq
		imgquery['session'] = sessionq
		imgtree = imgquery.query(readimages=False)
	else:
		allimgtree = getAllImagesFromDB(session)
		imgtree = []
		for imagedata in allimgtree:
			if imagedata['preset'] is None:
				imgtree.append(imagedata)
	"""
	loop through images and make data.holdimages false
	this makes it so that data.py doesn't hold images in memory
	solves a bug where processing quits after a dozen or so images
	"""
	#for img in imgtree:
		#img.holdimages=False
	return imgtree

#================
def getAllImagesFromDB(session):
	"""
	returns list of image data based on session name
	"""
	apDisplay.printMsg("Querying database for all images from session '"+session+"' ... ")
	sessionq= leginon.leginondata.SessionData(name=session)
	imgquery = leginon.leginondata.AcquisitionImageData()
	imgquery['session'] = sessionq
	imgtree = imgquery.query(readimages=False)
	return imgtree

#================
def getImageDataFromSpecificImageId(imageid):
	imagedata = leginon.leginondata.AcquisitionImageData().direct_query(imageid)
	if imagedata:
		return imagedata
	else:
		apDisplay.printError('Image (id=%d) does not exist' % (imageid))

#================
def getRefImageDataFromSpecificImageId(reftype,imageid):
		q = leginon.leginondata.AcquisitionImageData()
		imagedata = q.direct_query(imageid)
		if imagedata:
			return imagedata[reftype]
		else:
			apDisplay.printError('Image (id=%d) to retrieve reference image does not exist' % (imageid))

#================
def getAllTiltSeriesFromSessionName(sessionname):
	"""
	returns list of image data based on session name
	"""
	apDisplay.printMsg("Querying database for all tilt series from session '"+sessionname+"' ... ")
	sessionq= leginon.leginondata.SessionData(name=sessionname)
	seriesquery = leginon.leginondata.TiltSeriesData()
	seriesquery['session'] = sessionq
	seriestree = seriesquery.query(readimages=False)
	return seriestree

#================
def getExpIdFromSessionName(sessionname):
	apDisplay.printMsg("Looking up session, "+sessionname)
	sessionq = leginon.leginondata.SessionData(name=sessionname)
	sessioninfo = sessionq.query(readimages=False, results=1)
	if sessioninfo:
		return sessioninfo[0].dbid
	else:
		apDisplay.printError("could not find session, "+sessionname)

#================
def getSessionDataFromSessionId(sessionid):
	sessionid = int(sessionid)
	apDisplay.printMsg("Looking up session, %d" % sessionid)
	sessionq = leginon.leginondata.SessionData()
	sessioninfo = sessionq.direct_query(sessionid)
	return sessioninfo

#================
def getSessionDataFromSessionName(sessionname):
	apDisplay.printMsg("Looking up session, "+sessionname)
	sessionq = leginon.leginondata.SessionData(name=sessionname)
	sessioninfo = sessionq.query(readimages=False, results=1)
	if sessioninfo:
		return sessioninfo[0]
	else:
		apDisplay.printWarning("could not find session, "+sessionname)
		return None

#================
def getTiltSeriesDataFromTiltNumAndSessionId(tiltseries,sessiondata):
	apDisplay.printMsg("Looking up session first, "+ str(sessiondata.dbid));
	tiltseriesq = leginon.leginondata.TiltSeriesData(session=sessiondata,number=tiltseries)
	tiltseriesdata = tiltseriesq.query(readimages=False,results=1)
	if tiltseriesdata:
		return tiltseriesdata[0]
	else:
		apDisplay.printError("could not find tilt series, "+str(tiltseries))


#================
def getPredictionDataForImage(imagedata):
	q=leginon.leginondata.TomographyPredictionData()
	q['image']=imagedata
	predictiondata=q.query()
	return predictiondata

#================
def getImagesFromTiltSeries(tiltseriesdata,printMsg=True):
	if printMsg:
		apDisplay.printMsg("Looking up images for tilt series %d" % tiltseriesdata['number']);
	q = leginon.leginondata.AcquisitionImageData()
	q['tilt series'] = tiltseriesdata
	results = q.query()
	realist = []
	for imagedata in results:
		if imagedata['label'] != 'projection':
			realist.append(imagedata)
	if printMsg:
		apDisplay.printMsg("found %d images" % len(realist))
	return realist

#================
def getImageData(imgname):
	"""
	get image data object from database
	"""
	imgquery = leginon.leginondata.AcquisitionImageData(filename=imgname)
	imgtree  = imgquery.query(results=1, readimages=False)
	if imgtree:
		#imgtree[0].holdimages=False
		return imgtree[0]
	else:
		apDisplay.printError("Image "+imgname+" not found in database\n")

#================
def getImgDir(sessionname):
	sessionq = leginon.leginondata.SessionData(name=sessionname)
	sessiondata = sessionq.query()
	imgdir = os.path.abspath(sessiondata[0]['image path'])
	return imgdir

#================
def getSessionName(imgname):
	"""
	get session name from database
	"""
	imgquery = leginon.leginondata.AcquisitionImageData(filename=imgname)
	imgtree  = imgquery.query(results=1, readimages=False)
	if 'session' in imgtree[0]:
		return imgtree[0]['session']['name']
	else:
		apDisplay.printError("Image "+imgname+" not found in database\n")

#================
def getFrameImageCamera(sessiondata):
	'''
	Use latest frame saved image to find digital camera data
	'''
	camq = leginon.leginondata.CameraEMData(session=sessiondata)
	camq['save frames'] = True
	camems = camq.query(results=1)
	if camems:
		return camems[0]['ccdcamera']
	
#================
def getTiltAngleDeg(imgdata):
	return imgdata['scope']['stage position']['a']*180.0/math.pi

#================
def getTiltAngleDegFromParticle(partdata):
	imageref = partdata.special_getitem('image', dereference=False)
	imgdata = leginon.leginondata.AcquisitionImageData.direct_query(imageref.dbid, readimages=False)
	degrees = imgdata['scope']['stage position']['a']*180.0/math.pi
	return degrees

#================
def getTiltAnglesDegFromTransform(transformdata):
	imageref1 = transformdata.special_getitem('image1', dereference=False)
	imgdata1 = leginon.leginondata.AcquisitionImageData.direct_query(imageref1.dbid, readimages=False)
	degrees1 = imgdata1['scope']['stage position']['a']*180.0/math.pi
	imageref2 = transformdata.special_getitem('image2', dereference=False)
	imgdata2 = leginon.leginondata.AcquisitionImageData.direct_query(imageref2.dbid, readimages=False)
	degrees2 = imgdata2['scope']['stage position']['a']*180.0/math.pi
	return degrees1, degrees2

#================
def getTiltAngleRad(imgdata):
	return imgdata['scope']['stage position']['a']

#================
def getPixelSize(imgdata):
	"""
	use image data object to get pixel size
	multiplies by binning and also by 1e10 to return image pixel size in angstroms
	shouldn't have to lookup db already should exist in imgdict

	return image pixel size in Angstroms
	"""
	pixelsizeq = leginon.leginondata.PixelSizeCalibrationData()
	pixelsizeq['magnification'] = imgdata['scope']['magnification']
	pixelsizeq['tem'] = imgdata['scope']['tem']
	pixelsizeq['ccdcamera'] = imgdata['camera']['ccdcamera']
	pixelsizedatas = pixelsizeq.query()

	if len(pixelsizedatas) == 0:
		apDisplay.printError("No pixelsize information was found image %s\n\twith mag %d, tem id %d, ccdcamera id %d"
			%(imgdata['filename'], imgdata['scope']['magnification'],
			imgdata['scope']['tem'].dbid, imgdata['camera']['ccdcamera'].dbid)
		)

	### check to get one before image was taken
	i = 0
	pixelsizedata = pixelsizedatas[i]
	oldestpixelsizedata = pixelsizedata
	while pixelsizedata.timestamp > imgdata.timestamp and i < len(pixelsizedatas):
		i += 1
		pixelsizedata = pixelsizedatas[i]
		if pixelsizedata.timestamp < oldestpixelsizedata.timestamp:
			oldestpixelsizedata = pixelsizedata
	if pixelsizedata.timestamp > imgdata.timestamp:
		apDisplay.printWarning("There is no pixel size calibration data for this image, using oldest value")
		pixelsizedata = oldestpixelsizedata
	binning = imgdata['camera']['binning']['x']
	pixelsize = pixelsizedata['pixelsize'] * binning
	return(pixelsize*1e10)

#================
def getImgSize(imgdict):
	### SHOULD BE A DIRECT QUERY
	if 'image' in imgdict:
		return (imgdict['image'].shape)[1]
	fname = imgdict['filename']
	# get image size (in pixels) of the given mrc file
	imageq=leginon.leginondata.AcquisitionImageData(filename=fname)
	imagedata=imageq.query(results=1, readimages=False)
	if imagedata:
		size=int(imagedata[0]['camera']['dimension']['y'])
		return(size)
	else:
		apDisplay.printError("Image "+fname+" not found in database\n")
	return(size)

#================
def getImgSizeFromName(imgname):
	# get image size (in pixels) of the given mrc file
	imageq=leginon.leginondata.AcquisitionImageData(filename=imgname)
	imagedata=imageq.query(results=1, readimages=False)
	if imagedata:
		size=int(imagedata[0]['camera']['dimension']['y'])
		return(size)
	else:
		apDisplay.printError("Image "+imgname+" not found in database\n")
	return(size)

#================
def insertImgAssessmentStatus(imgdata, runname="run1", assessment=None, msg=True):
	"""
	Insert the assessment status
		keep = True
		reject = False
		unassessed = None
	"""
	if assessment is True or assessment is False:
		assessrun = appiondata.ApAssessmentRunData()
		assessrun['session'] = imgdata['session']
		#override to ALWAYS be 'run1'
		#assessrun['name'] = runname
		assessrun['name'] = "run1"

		assessquery = appiondata.ApAssessmentData()
		assessquery['image'] = imgdata
		assessquery['assessmentrun'] = assessrun
		assessquery['selectionkeep'] = assessment
		assessquery.insert()
	else:
		apDisplay.printWarning("No image assessment made, invalid data: "+str(assessment))


	#check assessment
	if msg is True:
		finalassess = getImgAssessmentStatus(imgdata)
		imgname = apDisplay.short(imgdata['filename'])
		if finalassess is True:
			astr = apDisplay.colorString("keep", "green")
		elif finalassess is False:
			astr = apDisplay.colorString("reject", "red")
		elif finalassess is None:
			astr = apDisplay.colorString("none", "yellow")
		apDisplay.printMsg("Final image assessment: "+astr+" ("+imgname+")")

	return True

#================
def getImgCompleteStatus(imgdata):
	assess = getImgAssessmentStatus(imgdata)
	viewer_status = getImgViewerStatus(imgdata)
	if viewer_status is None:
		return assess
	elif assess is None:
		return viewer_status
	#False overrides True
	elif assess is False or viewer_status is False:
		return False
	elif assess is True or viewer_status is True:
		return True
	return None

#================
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
	assessquery = appiondata.ApAssessmentData()
	assessquery['image'] = imgdata
	assessdata = assessquery.query()

	if assessdata:
		#check results of only most recent run
		if assessdata[0]['selectionkeep'] == 1:
			return True
		elif assessdata[0]['selectionkeep'] == 0:
			return False
	return None

#================
def getSiblingImgAssessmentStatus(imgdata):
	status = getImgAssessmentStatus(imgdata)
	if status is not None:
		return status
	siblingimgdata = apDefocalPairs.getDefocusPair(imgdata)
	if siblingimgdata:
		status = getImgAssessmentStatus(siblingimgdata)

	return status

#================
def getSiblingImgCompleteStatus(imgdata):
	'''
	Get the assessment status for sibling. Uses getImgCompleteStatus method to include viewer_status assessment
	'''
	siblingimgdata = apDefocalPairs.getDefocusPair(imgdata)
	if siblingimgdata:
		status = getImgCompleteStatus(siblingimgdata)
	else:
		status = None

	return status

#================
def getTiltSeriesDoneStatus(tiltseriesdata):
		imgtree = getImagesFromTiltSeries(tiltseriesdata)
		if len(imgtree) == 0:
			return False
		target = imgtree[0]['target']
		if target['type'] == 'simulated':
			q = leginon.leginondata.AcquisitionImageTargetData(initializer=target)
			q['status'] = 'done'
		else:
			q = leginon.leginondata.AcquisitionImageTargetData(fromtarget=imgtree[0]['target'],status='done')
		results = q.query()
		if results:
			return True
		else:
			# If there is only one tilt group, target is never done 
			# only its fromtarget will be done
			if target['fromtarget']:
				q = leginon.leginondata.AcquisitionImageTargetData(fromtarget=target['fromtarget'],status='done')
				results = q.query()
		if results:
			return True
		return False

### flatfield correction functions

#================
cache = {}
def camkey(camstate):
	return camstate['dimension']['x'], camstate['binning']['x'], camstate['offset']['x']

#================
def getDarkNorm(sessionname, cameraconfig):
	"""
	return the most recent dark and norm image from the given session
	"""
	camquery = leginon.leginondata.CorrectorCamstateData()
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
	sessionquery = leginon.leginondata.SessionData(name=sessionname)
	darkquery = leginon.leginondata.DarkImageData(session=sessionquery, camstate=camquery)
	#print 'DARKQUERY', darkquery
	normquery = leginon.leginondata.NormImageData(session=sessionquery, camstate=camquery)
	darkdata = darkquery.query(results=1)
	dark = darkdata[0]['image']
	#print darkdata[0]
	normdata = normquery.query(results=1)
	norm = normdata[0]['image']
	result = dark,norm
	cache[key] = result

	return result

#================
def getImgViewerStatus(imgdata):
	"""
	Function that returns whether or not the image was hidden in the viewer
	False: Image was hidden or trash
	True: Image is an exemplar
	None: Image is visible

	see 'ViewerImageStatus' table in dbemdata
	"""
	statusq = leginon.leginondata.ViewerImageStatus()
	statusq['image'] = imgdata
	statusdatas = statusq.query(results=1)
	if not statusdatas:
		return None

	statusdata = statusdatas[0]
	if statusdata['status']=='hidden':
		return False
	if statusdata['status']=='trash':
		return False
	if statusdata['status']=='exemplar':
		return True
	return None

#================
def setImgViewerStatus(imgdata, status=None, msg=True):
	"""
	Function that sets the image status in the viewer
	False: Image was hidden
	True: Image is an exemplar
	None: Image is visible

	see 'ViewerImageStatus' table in dbemdata
	"""

	if status is False:
		statusVal = 'hidden'
	elif status is True:
		statusVal = 'exemplar'
	else:
		print "skipping set viewer status"
		return

	currentstatus = getImgViewerStatus(imgdata)

	if currentstatus is None:
		#insert new
		statusq = leginon.leginondata.ViewerImageStatus()
		statusq['image'] = imgdata
		statusq['status'] = statusVal
		statusq.insert()
	elif currentstatus != status:
		#update column
		dbconf=sinedon.getConfig('leginondata')
		db=sinedon.sqldb.sqlDB(**dbconf)
		q= ( "UPDATE "+dbconf['db']+".`ViewerImageStatus` "
			+"SET status = '"+statusVal
			+ ("' WHERE `REF|AcquisitionImageData|image`=%d" % (imgdata.dbid,)))
		db.execute(q)

	#check assessment
	if msg is True:
		finalassess = getImgViewerStatus(imgdata)
		imgname = apDisplay.short(imgdata['filename'])
		if finalassess is True:
			astr = apDisplay.colorString("exemplar", "green")
		elif finalassess is False:
			astr = apDisplay.colorString("hidden", "red")
		elif finalassess is None:
			astr = apDisplay.colorString("none", "yellow")
		apDisplay.printMsg("Final image assessment: "+astr+" ("+imgname+")")

	return

#================
def checkMag(imgdata,goodmag):
	mag = imgdata['scope']['magnification']
	if mag ==goodmag:
		return True
	else:
		return False

#================
def getDoseFromSessionPresetNames(sessionname, presetname):
	''' returns dose, in electrons per Angstrom '''
	sessiondata = leginondata.SessionData(name=sessionname).query()[0]
	presetdata = leginondata.PresetData(name=presetname,session=sessiondata).query(results=1)[0]
	dose = presetdata['dose']
	if not dose:
		raise RunTimeError("dose not available for %s session and preset %s" % (sessionname,presetname))
	return dose / 1e20

#================
def getDoseFromImageData(imgdata):
	''' returns dose, in electrons per Angstrom '''
	try:
		dose = imgdata['preset']['dose']
	except:
		apDisplay.printWarning("dose not available for this image, try another image")
		return None
	return dose / 1e20

#================
def getDimensionsFromImageData(imgdata):
	''' returns dictionary, x & y dimensions, for image '''
	return imgdata['preset']['dimension']

#================
def checkInspectDB(imgdata):
	status = getImgViewerStatus(imgdata)
	if status is False:
		return False
	elif status is True:
		return True
	else:
		keep = getImgAssessmentStatus(imgdata)
		return keep

#================
def isTomoInDB(md5sum, full=False,recfile=''):
	abspath = os.path.abspath(recfile)
	rundir = os.path.dirname(abspath)
	basename = os.path.basename(abspath)
	rootname = os.path.splitext(basename)
	if not full:
		tomoq = appiondata.ApTomogramData(name=rootname[0])
		tomoq['md5sum'] = md5sum
	else:
		tomoq = appiondata.ApFullTomogramData(name=rootname[0])
	tomod = tomoq.query(results=1)
	if tomod:
		tomodata = tomod[0]
		# old style
		if tomodata['path'] is not None and tomodata['path']['path'] == rundir:
			return True
		# new style
		if tomodata['reconrun']['path']['path'] == rundir:
			return True
	return False

#================
def isTemplateInDB(md5sum):
	templq = appiondata.ApTemplateImageData()
	templq['md5sum'] = md5sum
	templd = templq.query(results=1)
	if templd:
		return True
	return False

#================
def queryDirectory(path):
	pathq = appiondata.ApPathData()
	pathq['path'] = os.path.abspath(path)
	pathdata = pathq.query()
	return pathdata

#================
def getJobDataFromPath(path):
	pathq = appiondata.ApPathData()
	pathq['path'] = os.path.abspath(path)
	jobq = appiondata.ApAppionJobData()
	jobq['path'] = pathq
	jobdatas = jobq.query()
	return jobdatas

#================
def getJobDataFromType(jobtype):
	jobq = appiondata.ApAppionJobData()
	jobq['jobtype'] = jobtype
	jobdatas = jobq.query()
	return jobdatas

#================
def getJobDataFromPathAndType(path, jobtype):
	pathq = appiondata.ApPathData()
	pathq['path'] = os.path.abspath(path)
	jobq = appiondata.ApAppionJobData()
	jobq['path'] = pathq
	jobq['jobtype'] = jobtype
	jobdatas = jobq.query(results=1)
	if not jobdatas:
		return None
	return jobdatas[0]

#================
def getJobDataFromID(jobid):
	jobdata = appiondata.ApAppionJobData.direct_query(jobid)
	return jobdata

####
# This is a database connections file with no file functions
# Please keep it this way
####

#================
#================
#================
if __name__ == '__main__':
	stackid = 442
	stackdata = appiondata.ApStackData.direct_query(stackid)
	print stackdata



