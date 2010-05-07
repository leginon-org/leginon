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

splitdb = True

data.holdImages(False)

#================
def getAllImages(stats, params):
	startt = time.time()
	if 'sessionname' in params and params['preset'] is not None:
		imgtree = getImagesFromDB(params['sessionname'],params['preset'])
	elif 'mrcfileroot' in params and len(params['mrcfileroot']) > 0:
		imgtree = getSpecificImagesFromDB(params["mrcfileroot"])
		params['sessionname']=imgtree[0]['session']['name']
	elif 'mrclist' in params and params['mrclist'] is not None:
		mrcfileroot = self.params['mrcnames'].split(",")
		imgtree = getSpecificImagesFromDB(mrcfileroot)
		params['sessionname']=imgtree[0]['session']['name']
	elif 'sessionname' in params and params['preset'] is None:
		imgtree = getAllImagesFromDB(params['sessionname'])
	else:
		apDisplay.printError("no files specified")
	if imgtree is None or len(imgtree) < 1:
		apDisplay.printError("did not find any images")
	params['session'] = imgtree[0]['session']
	params['apix'] = getPixelSize(imgtree[0])
	stats['imagecount']=len(imgtree)
	print " ... found",stats['imagecount'],"in",apDisplay.timeString(time.time()-startt)
	return imgtree

#================
def getSpecificImagesFromDB(imglist):
	print "Querying database for "+str(len(imglist))+" specific images ... "
	imgtree=[]
	for imgname in imglist:
		if imgname[-4:] == ".mrc" or imgname[-4:] == ".box":
			imgname = imgname[:-4]
		if '/' in imgname:
			imgname = os.path.basename(imgname)
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
	sessionq = leginon.leginondata.SessionData(name=session)
	presetq=leginon.leginondata.PresetData(name=preset)
	imgquery = leginon.leginondata.AcquisitionImageData()
	imgquery['preset']  = presetq
	imgquery['session'] = sessionq
	imgtree = imgquery.query(readimages=False)
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
def getExpIdFromSessionName(sessionname):
	apDisplay.printMsg("Looking up session, "+sessionname)
	sessionq = leginon.leginondata.SessionData(name=sessionname)
	sessioninfo = sessionq.query(readimages=False, results=1)
	if sessioninfo:
		return sessioninfo[0].dbid
	else:
		apDisplay.printError("could not find session, "+sessionname)

#================
def getSessionDataFromSessionName(sessionname):
	apDisplay.printMsg("Looking up session, "+sessionname)
	sessionq = leginon.leginondata.SessionData(name=sessionname)
	sessioninfo = sessionq.query(readimages=False, results=1)
	if sessioninfo:
		return sessioninfo[0]
	else:
		apDisplay.printError("could not find session, "+sessionname)

#================
def getTiltSeriesDataFromTiltNumAndSessionId(tiltseries,sessiondata):
	apDisplay.printMsg("Looking up session, "+ str(sessiondata.dbid));
	tiltq = leginon.leginondata.TiltSeriesData()
	tiltseriesq = leginon.leginondata.TiltSeriesData(session=sessiondata,number=tiltseries)
	tiltseriesdata = tiltseriesq.query(readimages=False,results=1)
	if tiltseriesdata:
		return tiltseriesdata[0]
	else:
		apDisplay.printError("could not find tilt series, "+sessionname)

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
	"""
	pixelsizeq=leginon.leginondata.PixelSizeCalibrationData()
	pixelsizeq['magnification'] = imgdata['scope']['magnification']
	pixelsizeq['tem'] = imgdata['scope']['tem']
	pixelsizeq['ccdcamera'] = imgdata['camera']['ccdcamera']
	pixelsizedatas = pixelsizeq.query()
	### check to get one before image was taken
	i = 0
	pixelsizedata = pixelsizedatas[i]
	while pixelsizedata.timestamp > imgdata.timestamp:
		i += 1
		pixelsizedata = pixelsizedatas[i]
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
def getSiblingImgAssessmentStatus(imgdata):
	status = getImgAssessmentStatus(imgdata)
	if status is not None:
		return status
	siblingimgdata = apDefocalPairs.getDefocusPair(imgdata)
	if siblingimgdata:
		status = getImgAssessmentStatus(siblingimgdata)

	return status

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
	False: Image was hidden
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

	status = getImgViewerStatus(imgdata)

	if status is None:
		#insert new
		statusq = leginon.leginondata.ViewerImageStatus()
		statusq['image'] = imgdata
		statusq.insert()
	elif result['status'] != statusVal:
		#update column
		dbconf=sinedon.getConfig('leginondata')
		db=sinedon.sqldb.sqlDB(**dbconf)
		q= ( "UPDATE "+dbconf['db']+".`ViewerImageStatus` "
			+"SET status = '"+statusVal
			+ ("' WHERE `REF|AcquisitionImageData|image=%d" % (imageId,)))
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
		if tomodata['path']['path'] == rundir:
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

#================
def getSelectionIdFromName(runname, sessionname):
	sessiondata = getSessionDataFromSessionName(sessionname)
	selectq = appiondata.ApSelectionRunData()
	selectq['name'] = runname
	selectq['session'] = sessiondata
	selectdatas = selectq.query(results=1)
	if not selectdatas:
		return None
	return selectdatas[0].dbid

#================
#================
#================
if __name__ == '__main__':
	stackid = 442
	stackdata = appiondata.ApStackData.direct_query(stackid)
	print stackdata



