#pythonlib
import os
import numpy
import pyami.quietscipy
import scipy.ndimage as nd
#sinedon
import sinedon.data as data
import sinedon.newdict as newdict
#pyami
import pyami.imagefun as imagefun
#leginon
import leginon.leginondata
#appion
from appionlib import apImage
from appionlib import appiondata
from appionlib import apCrud
from appionlib import apDatabase

def getMaskParamsByRunName(name,sessiondata):
	maskRq=appiondata.ApMaskMakerRunData()
	maskRq['name']=name
	maskRq['session']=sessiondata
	# get corresponding makeMaskParams entry
	result = maskRq.query()
	if len(result) > 0:
		return result[0],result[0]['params']
	else:
		return None,None

def getSessionDataByName(name):
	sessiondata = apDatabase.getSessionDataFromSessionName(name)
	return sessiondata

def insertManualMaskParams(bin):
	maskPdata=appiondata.ApMaskMakerParamsData()

	maskPdata['bin']=bin
	maskPdata['mask_type']='manual'

	maskPdata.insert()

	return maskPdata

def insertManualMaskRun(sessiondata,path,name,bin):
	paramdata=insertManualMaskParams(bin)
	maskRdata=createMaskMakerRun(sessiondata,path,name,paramdata)

	maskRdata.insert()

	return maskRdata

def createMaskMakerRun(sessiondata,path,name,paramdata):
	if path is None:
		savepath = None
	else:
		savepath = os.path.normpath(path)
	maskRdata=appiondata.ApMaskMakerRunData()
	maskRdata['session'] = sessiondata
	if savepath is not None:
		maskRdata['path']= appiondata.ApPathData(path=os.path.abspath(savepath))
	maskRdata['name']=name
	maskRdata['params']=paramdata

	return maskRdata

def insertMaskRegion(rundata,imgdata,regionInfo):

	maskRq = createMaskRegionData(rundata,imgdata,regionInfo)
	result=maskRq.query()
	if not (result):
		maskRq.insert()

	return

def createMaskRegionData(rundata,imgdata,regionInfo):
	maskRq=appiondata.ApMaskRegionData()

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
	maskRq=appiondata.ApMaskRegionData()

	maskRq['maskrun']=maskrun
	maskRq['image']=imgdata

	results=maskRq.query(readimages=False)

	return results

def getRegionsByAssessment(assessrun):
	maskRq=appiondata.ApMaskAssessmentData()

	maskRq['run']=assessrun
	results=maskRq.query(readimages=False)
	return results

def getAssessedMasks(assessrun,maskrun):
	regionassesstree = getRegionsByAssessment(assessrun)
	imagefiles = []
	for regionassessdata in regionassesstree:
		regiondata = regionassessdata['region']
		maskofregion = regiondata['maskrun']
		if maskofregion.dbid == maskrun.dbid:
			imageref = regiondata.special_getitem('image',dereference = False)
			imagedata = leginon.leginondata.AcquisitionImageData.direct_query(imageref.dbid, readimages = False)
			imagefile = imagedata['filename']
			try:
				imagefiles.index(imagefile)
			except ValueError:
				imagefiles.append(imagefile)
	return map((lambda x: x + '_mask.png'),imagefiles)

def insertMaskAssessmentRun(sessiondata,maskrundata,name):
	assessRdata=appiondata.ApMaskAssessmentRunData()
	assessRdata['session'] = sessiondata
	assessRdata['name'] = name
	assessRdata['maskrun'] = maskrundata

	result=assessRdata.query()
	if not (result):
		assessRdata.insert()
		exist = False
	else:
		exist = True

	return assessRdata,exist

def insertMaskAssessment(rundata,regiondata,keep):

	assessMq = createMaskAssessmentData(rundata,regiondata,keep)
	assessMq.insert(force=True)

	return

def createMaskAssessmentData(rundata,regiondata,keep):
	assessMq=appiondata.ApMaskAssessmentData()

	assessMq['run']=rundata
	assessMq['region']=regiondata
	assessMq['keep']=keep

	return assessMq

def getMaskAssessRunData(sessiondata,maskassessname):
	mquery = appiondata.ApMaskAssessmentRunData()
	mquery['session'] = sessiondata
	mquery['name'] = maskassessname
	results = mquery.query()

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
	#mask = apImage.PngAlphaToBinarryArray(os.path.join(maskpath,maskfile))
	mask = apImage.PngToBinarryArray(os.path.join(maskpath,maskfile))
	return mask

def getMaskRunInfo(maskpath,maskfilename):
	parent=maskfilename.replace('_mask.png','')
	sessionname=maskfilename.split('_')[0]
	sessiondata= getSessionDataByName(sessionname)
	maskrun=maskpath.split('/')[-2]
	maskrundata,maskparamsdata=getMaskParamsByRunName(maskrun,sessiondata)
	return maskrundata,maskparamsdata

def getMaskMakerRunNamesFromSession(sessiondata):
	mquery = appiondata.ApMaskMakerRunData(session=sessiondata)
	results = mquery.query()

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
	assessquery = appiondata.ApMaskAssessmentData()
	assessquery['run'] = assessrundata
	for regiondata in maskregiondata:
		assessquery['region'] = regiondata
		assessdata = assessquery.query(results=1)
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
	assessrun = appiondata.ApMaskAssessmentRunData.direct_query(11)
	sessiondata = assessrun['session']
	imgdata = leginon.leginondata.AcquisitionImageData.direct_query(500598)
	maskarray,maskbin = makeInspectedMask(sessiondata,'run1',imgdata)
#	maskrun = appiondata.ApMaskMakerRunData.direct_query(44)



