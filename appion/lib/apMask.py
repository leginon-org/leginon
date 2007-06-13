#pythonlib
import os
import numpy
#sinedon
import sinedon.data as data
import sinedon.newdict as newdict
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
	maskRdata=appionData.ApMaskMakerRunData()
	maskRdata['session'] = sessiondata
	maskRdata['path']=path
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
	
	results=appiondb.query(maskRq)
	
	return results

def getAllMaskRegionsByAssessment(assessrun,imgdata):
	maskRq=appionData.ApMaskRegionData()

	maskRq['maskrun']=maskrun
	maskRq['image']=imgdata
	
	results=appiondb.query(maskRq)
	
	return results

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
	maskpath = os.path.join(maskrundata['path'],"masks")
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
		if assessdata[0]['keep'] == 1:
			keeplist.append(regiondata['label'])
	keeplist.sort()
	return keeplist


def makeInspectedMask(sessiondata,maskassessname,imgdata):

	assessruntree = getMaskAssessRunData(sessiondata,maskassessname)
		
	for assessrundata in assessruntree:
		maskrundata = assessrundata['maskrun']
	
		maskbin = maskrundata['params']['bin']
	
		maskregiondata = getMaskRegions(maskrundata,imgdata)
	
		if len(maskregiondata) == 0:
			continue
	
		keeplist = getRegionKeepList(assessrundata,maskregiondata)
	
		if len(keeplist) == 0:
			continue
		
		maskarray = getMaskArray(maskrundata,imgdata)
		maskarray = apCrud.makeKeepMask(maskarray,keeplist)
		try:
			allmaskarray = allmaskarray+maskarray
		except:
			allmaskarray = maskarray
	
	allmaskarray = numpy.where(allmaskarray==0,0,1)
	apImage.arrayToJpeg(allmaskarray,'test.jpg')
	
	return allmaskarray,maskbin
	
				


if __name__ == '__main__':
	maskpath='/home/acheng/testcrud/test'
	maskfilename='07apr11anchitest_GridID00752_Insertion014_00001gr_00004hl_mask.png'
	sessiondata = getSessionDataByName('07apr11anchitest')
	rundata,paramdata = getMaskParamsByRunName('test',sessiondata)
	print rundata,paramdata
