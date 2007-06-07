import sinedon.data as data
import newdict
import apImage
import os
import appionData
import apDB
import apCrud

appiondb = apDB.apdb

def getMaskParamsByRunName(name,sessionname):
	sessionq = data.SessionData(name=sessionname)
	sessiondata = leginondb.query(sessionq)[0]
	sessionid = sessiondata.dbid
	maskRq=appionData.ApMaskMakerRunData()
	maskRq['name']=name
	maskRq['dbemdata|SessionData|session']=sessionid
	# get corresponding makeMaskParams entry
	result = appiondb.query(maskRq)
	return result[0],result[0]['params']
	
		
def insertMaskRegion(rundata,imgdata,regionInfo):

	maskRq = createMaskRegionData(rundata,imgdata,regionInfo)
	result=appiondb.query(maskRq)
	if not (result):
		appiondb.insert(maskRq)
	
	return

def createMaskRegionData(rundata,imgdata,regionInfo):
	maskRq=appionData.ApMaskRegionData()

	maskRq['maskrun']=rundata
	maskRq['dbemdata|AcquisitionImageData|image']=imgdata.dbid
	maskRq['x']=regionInfo[4][1]
	maskRq['y']=regionInfo[4][0]
	maskRq['area']=regionInfo[0]
	maskRq['perimeter']=regionInfo[3]
	maskRq['mean']=regionInfo[1]
	maskRq['stdev']=regionInfo[2]
	maskRq['label']=regionInfo[5]

	return maskRq

def getMaskRegions(maskrun,imgid):
	maskRq=appionData.ApMaskRegionData()

	maskRq['maskrun']=maskrun
	maskRq['dbemdata|AcquisitionImageData|image']=imgid
	
	results=appiondb.query(maskRq)
	
	return results

def insertMaskAssessmentRun(sessiondata,maskrundata,name):
	assessRdata=appionData.ApMaskAssessmentRunData()
	assessRdata['dbemdata|SessionData|session'] = sessiondata.dbid
	assessRdata['maskrun'] = maskrundata
	assessRdata['name'] = name

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
	query['dbemdata|SessionData|session'] = sessiondata.dbid
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
	maskrun=maskpath.split('/')[-2]
	maskrundata,maskparamsdata=getMaskParamsByRunName(maskrun,sessionname)
	return maskrundata,maskparamsdata

def getRegionsAsTargets(maskrun,maskshape,imgdata):
	regiondata = getMaskRegions(maskrun,imgdata.dbid)
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

def insertMaskAssessmentRun(sessiondata,maskrundata,name):
	assessRdata=insertMaskAssessmentRun(sessiondata,maskrundata,name)

	return assessRdata

def saveAssessmentFromTargets(maskrun,assessrun,imgdata,keeplist):
	regiontree = getMaskRegions(maskrun,imgdata.dbid)
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
		if assessdata[0]['keep'] == 0:
			keeplist.append(regiondata['label'])
	keeplist.sort()
	return keeplist


def makeInspectedMask(sessiondata,maskassessname,imgdata):

	assessrundata = getMaskAssessRunData(sessiondata,maskassessname)[0]
	
	maskrundata = assessrundata['maskrun']
	
	maskregiondata = getMaskRegions(maskrundata,imgdata.dbid)
	
	keeplist = getRegionKeepList(assessrundata,maskregiondata)
	
	maskarray = getMaskArray(maskrundata,imgdata)
	
	maskarray = apCrud.makeKeepMask(maskarray,keeplist)
	
	return maskarray
	
				


if __name__ == '__main__':
	maskpath='/home/acheng/testcrud/test'
	maskfilename='07jan05b_00018gr_00021sq_v01_00002sq_01_00033en_01_mask.png'

	getMaskRunInfo(maskpath,maskfilename)
