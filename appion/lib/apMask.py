#pythonlib
import os
import numpy
import scipy.ndimage as nd
#sinedon
import sinedon.data as data
import sinedon.newdict as newdict
#pyami
import pyami.imagefun as imagefun
#leginon
import leginondata
#appion
import apImage
import appionData
import apDB
import apCrud
import apDatabase
leginondb = apDB.db
appiondb = apDB.apdb

def getMaskParamsByRunName(name,sessiondata):
	maskRq=appionData.ApMaskMakerRunData()
	maskRq['name']=name
	maskRq['session']=sessiondata
	# get corresponding makeMaskParams entry
	result = appiondb.query(maskRq)
	if len(result) > 0:
		return result[0],result[0]['params']
	else:
		return None,None
	
def getSessionDataByName(name):
	sessiondata = apDatabase.getSessionDataFromSessionName(name)
	return sessiondata
			
def insertManualMaskParams(bin):
	maskPdata=appionData.ApMaskMakerParamsData()
	
	maskPdata['bin']=bin
	maskPdata['mask type']='manual'

	appiondb.insert(maskPdata)
		
	return maskPdata

def insertManualMaskRun(sessiondata,path,name,bin):
	paramdata=insertManualMaskParams(bin)
	maskRdata=createMaskMakerRun(sessiondata,path,name,paramdata)

	appiondb.insert(maskRdata)

	return maskRdata
		
def createMaskMakerRun(sessiondata,path,name,paramdata):
	if path is None:
		savepath = None
	else:
		savepath = os.path.normpath(path)
	maskRdata=appionData.ApMaskMakerRunData()
	maskRdata['session'] = sessiondata
	maskRdata['path']= appionData.ApPathData(path=savepath)
	maskRdata['name']=name
	maskRdata['params']=paramdata

	return maskRdata
	
def insertMaskRegion(rundata,imgdata,regionInfo):

	maskRq = createMaskRegionData(rundata,imgdata,regionInfo)
	result=appiondb.query(maskRq)
	if not (result):
		appiondb.insert(maskRq)
	
	return

def createMaskRegionData(rundata,imgdata,regionInfo):
	maskRq=appionData.ApMaskRegionData()

	maskRq['maskrun']=rundata
	maskRq['image']=imgdata
	maskRq['x']=regionInfo[4][1]
	maskRq['y']=regionInfo[4][0]
	maskRq['area']=regionInfo[0]
	maskRq['perimeter']=regionInfo[3]
	maskRq['mean']=regionInfo[1]
	maskRq['stdev']=regionInfo[2]
	maskRq['label']=regionInfo[5]

	return maskRq

def getMaskRegions(maskrun,imgdata):
	maskRq=appionData.ApMaskRegionData()

	maskRq['maskrun']=maskrun
	maskRq['image']=imgdata
	
	results=appiondb.query(maskRq, readimages=False)
	
	return results

def getRegionsByAssessment(assessrun):
	maskRq=appionData.ApMaskAssessmentData()

	maskRq['run']=assessrun
	results=appiondb.query(maskRq, readimages=False)
	return results
	
def getAssessedMasks(assessrun,maskrun):
	regionassesstree = getRegionsByAssessment(assessrun)
	imagefiles = []
	for regionassessdata in regionassesstree:
		regiondata = regionassessdata['region']
		maskofregion = regiondata['maskrun']
		if maskofregion.dbid == maskrun.dbid:
			imageref = regiondata.special_getitem('image',dereference = False)
			imagedata = leginondb.direct_query(leginondata.AcquisitionImageData,imageref.dbid, readimages = False)
			imagefile = imagedata['filename']
			try:
				imagefiles.index(imagefile)
			except ValueError:
				imagefiles.append(imagefile)
	return map((lambda x: x + '_mask.png'),imagefiles)

def insertMaskAssessmentRun(sessiondata,maskrundata,name):
	assessRdata=appionData.ApMaskAssessmentRunData()
	assessRdata['session'] = sessiondata
	assessRdata['name'] = name
	assessRdata['maskrun'] = maskrundata

	result=appiondb.query(assessRdata)
	if not (result):
		appiondb.insert(assessRdata)
		exist = False
	else:
		exist = True

	return assessRdata,exist
	
def insertMaskAssessment(rundata,regiondata,keep):

	assessMq = createMaskAssessmentData(rundata,regiondata,keep)
	appiondb.insert(assessMq,force=True)
	
	return

def createMaskAssessmentData(rundata,regiondata,keep):
	assessMq=appionData.ApMaskAssessmentData()
	
	assessMq['run']=rundata
	assessMq['region']=regiondata
	assessMq['keep']=keep

	return assessMq
	
def getMaskAssessRunData(sessiondata,maskassessname):
	query = appionData.ApMaskAssessmentRunData()
	query['session'] = sessiondata
	query['name'] = maskassessname
	results = appiondb.query(query)
	
	return results


def getMaskPath(maskrundata):
	maskpath = os.path.join(maskrundata['path']['path'],"masks")
	return maskpath

def getMaskFilename(maskrundata,imagedata):
	maskpath = getMaskPath(maskrundata)
	maskfile = imagedata['filename']+"_mask.png"
	return maskfile

def getMaskArray(maskrundata,imgdata):
	maskpath = getMaskPath(maskrundata)
	maskfile = getMaskFilename(maskrundata,imgdata)
	mask = apImage.PngAlphaToBinarryArray(os.path.join(maskpath,maskfile))
	return mask

def getMaskRunInfo(maskpath,maskfilename):
	parent=maskfilename.replace('_mask.png','')
	sessionname=maskfilename.split('_')[0]
	sessiondata= getSessionDataByName(sessionname)
	maskrun=maskpath.split('/')[-2]
	maskrundata,maskparamsdata=getMaskParamsByRunName(maskrun,sessiondata)
	return maskrundata,maskparamsdata

def getMaskMakerRunNamesFromSession(sessiondata):
	query = appionData.ApMaskMakerRunData(session=sessiondata)
	results = appiondb.query(query)
	
	if not results:
		return []
	masknames = map((lambda x:x['name']),results)
	return masknames
	
def getRegionsAsTargets(maskrun,maskshape,imgdata):
	regiondata = getMaskRegions(maskrun,imgdata)
	halfrow=maskshape[0]/2
	halfcol=maskshape[1]/2
	targets = []
	for region in regiondata:
		target = {}
		target['x'] = region['x']
		target['y'] = region['y']
		target['stats'] = newdict.OrderedDict()
		target['stats']['Label'] = region['label']
		target['stats']['Mean Intensity'] = region['mean']
		target['stats']['Mean Thickness'] = region['stdev']
		target['stats']['Area'] = region['area']
		targets.append(target)
	return targets

def saveAssessmentFromTargets(maskrun,assessrun,imgdata,keeplist):
	regiontree = getMaskRegions(maskrun,imgdata)
	for regiondata in regiontree:
		if regiondata['label'] in keeplist:
			insertMaskAssessment(assessrun,regiondata,True)
		else:
			insertMaskAssessment(assessrun,regiondata,False)

def getRegionKeepList(assessrundata,maskregiondata):
	keeplist = []
	assessquery = appionData.ApMaskAssessmentData()
	assessquery['run'] = assessrundata
	for regiondata in maskregiondata:
		assessquery['region'] = regiondata
		assessdata = appiondb.query(assessquery,results=1)
		if len(assessdata) == 0:
			continue
		if assessdata[0]['keep'] == 1:
			keeplist.append(regiondata['label'])
	keeplist.sort()
	return keeplist


def getMaskbins(sessiondata,maskassessname):
	assessruntree = getMaskAssessRunData(sessiondata,maskassessname)
	
	allmaskarray = None
	maskbins = []
	for i,assessrundata in enumerate(assessruntree):
		maskrundata = assessrundata['maskrun']
		maskbins.append(maskrundata['params']['bin'])
	return maskbins,max(maskbins)

def makeInspectedMask(sessiondata,maskassessname,imgdata):

	assessruntree = getMaskAssessRunData(sessiondata,maskassessname)
	
	maskbins,maxbin = getMaskbins(sessiondata,maskassessname)
	allmaskarray = None
	for i,assessrundata in enumerate(assessruntree):
	
		maskrundata = assessrundata['maskrun']
		maskregiondata = getMaskRegions(maskrundata,imgdata)
		if len(maskregiondata) == 0:
			continue
	
		keeplist = getRegionKeepList(assessrundata,maskregiondata)
	
		if len(keeplist) == 0:
			continue
		
		maskarray = getMaskArray(maskrundata,imgdata)
		maskarray = apCrud.makeKeepMask(maskarray,keeplist)
		extrabin = maxbin/maskbins[i]
		if extrabin > 1:
			maskarray = apImage.binImg(maskarray, extrabin)
			
		try:
			allmaskarray = allmaskarray+maskarray
		except:
			allmaskarray = maskarray
	
	allmaskarray = numpy.where(allmaskarray==0,0,1)
	
	if allmaskarray.shape == ():
		allmaskarray = None
	
	return allmaskarray,maxbin
	
def overlayMask(image,mask):
	if mask is None:
		return image
	imageshape=image.shape
	maskshape=mask.shape
	alpha = 0.25

	if maskshape != imageshape:
		binning = float(maskshape[0])/imageshape[0]
		if binning > 1:
			maskbinned = imagefun.bin(mask,binning)
		else:
			maskbinned = nd.zoom(mask,1/binning)
	else:
		maskbinned = mask
	if mask.max() !=0:
		overlay=image+maskbinned*alpha*(image.max()-image.min())/mask.max()
	else:
		overlay=image
					
	return overlay

if __name__ == '__main__':
	assessrun = appiondb.direct_query(appionData.ApMaskAssessmentRunData,11)
	sessiondata = assessrun['session']
	imgdata = leginondb.direct_query(leginondata.AcquisitionImageData,500598)
	maskarray,maskbin = makeInspectedMask(sessiondata,'run1',imgdata)
#	maskrun = appiondb.direct_query(appionData.ApMaskMakerRunData,44)
