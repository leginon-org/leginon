import data
import apParticle
import newdict

def getMaskRunInfo(maskpath,maskfilename):
	parent=maskfilename.replace('_mask.png','')
	sessionname=maskfilename.split('_')[0]
	maskrun=maskpath.split('/')[-2]
	maskrundata,maskparamsdata=apParticle.getMaskParamsByRunName(maskrun,sessionname)
	return maskrundata,maskparamsdata

def getRegionsAsTargets(maskrun,maskshape,imgdata):
	regiondata = apParticle.getMaskRegions(maskrun,imgdata.dbid)
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
	assessRdata=apParticle.insertMaskAssessmentRun(sessiondata,maskrundata,name)

	return assessRdata

def saveAssessmentFromTargets(maskrun,assessrun,imgdata,keeplist):
	regiontree = apParticle.getMaskRegions(maskrun,imgdata.dbid)
	for regiondata in regiontree:
		if regiondata['label'] in keeplist:
			apParticle.insertMaskAssessment(assessrun,regiondata,True)
		else:
			apParticle.insertMaskAssessment(assessrun,regiondata,False)
				


if __name__ == '__main__':
	maskpath='/home/acheng/testcrud/test'
	maskfilename='07jan05b_00018gr_00021sq_v01_00002sq_01_00033en_01_mask.png'

	getMaskRunInfo(maskpath,maskfilename)
