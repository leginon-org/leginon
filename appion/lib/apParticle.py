#Part of the new pyappion

#pythonlib

import os
#leginon
import data
import particleData
#appion
import apDB
import appionData
import apImage
import apDisplay

#partdb = apDB.apdb
appiondb = apDB.apdb
leginondb = apDB.db


def getParticles(imgdict,params):
	"""
	returns paticles (as a list of dicts) for a given image
	ex: particles[0]['xcoord'] is the xcoord of particle 0
	"""
	
	imq=particleData.image()
	imq['dbemdata|AcquisitionImageData|image']=imgdict.dbid

	selexonrun=appiondb.direct_query(data.run,params['selexonId'])
	prtlq=particleData.particle(imageId=imq,runId=selexonrun)

	particles=appiondb.query(prtlq)
	shift={'shiftx':0, 'shifty':0}
	return particles,shift

def getDBparticledataImage(imgdict, expid):
	"""
	This function queries and creates, if not found, dpparticledata.image data
	using dbemdata.AcquisitionImageData image name
	"""

	legimgid=int(imgdict.dbid)
	legpresetid=None
	if 'preset' in imgdict and imgdict['preset']:
		legpresetid =int(imgdict['preset'].dbid)

	imgname = imgdict['filename']
	imgq = particleData.image()
	imgq['dbemdata|SessionData|session']=expid
	imgq['dbemdata|AcquisitionImageData|image']=legimgid
	imgq['dbemdata|PresetData|preset']=legpresetid
	pdimgData=appiondb.query(imgq, results=1)

	# if no image entry, make one
	if not (pdimgData):
		print "Inserting image entry for",apDisplay.short(imgname)
		appiondb.insert(imgq)
		imgq=None
		imgq = particleData.image()
		imgq['dbemdata|SessionData|session']=expid
		imgq['dbemdata|AcquisitionImageData|image']=legimgid
		imgq['dbemdata|PresetData|preset']=legpresetid
		pdimgData=appiondb.query(imgq, results=1)

	return pdimgData

def getDBparticledataImage(imgdict,expid):
	"""
	This function is a dummy now that the output imgdict since we removed
	the image table in dbappiondata
	"""
	return imgdict

def getTemplateDBInfo(tmpldbid):
	return appiondb.direct_query(data.ApTemplateImageData, tmpldbid)

def insertParticlePeaks(peaktree, imgdict, expid, params):
	"""
	takes an image dict (imgdict) and inserts particles into DB from pik file
	"""
	#INFO
	legimgid=int(imgdict.dbid)
	imgname=imgdict['filename'] 

	#GET RUNID
	runq=appionData.ApSelectionRunData()
	runq['name'] = params['runid']
	runq['dbemdata|SessionData|session'] = expid
	runids=appiondb.query(runq, results=1)

	# WRITE PARTICLES TO DATABASE
	print "Inserting particles into database for",apDisplay.shortenImageName(imgname),"..."

	### WRITE PARTICLES TO DATABASE
	for peakdict in peaktree:
		particlesq = appionData.ApParticleData()
		particlesq['selectionrun'] = runids[0]
		particlesq['dbemdata|AcquisitionImageData|image'] = legimgid
		particlesq['template'] = getTemplateDBInfo(peakdict['template'])
		# use an update function???, maybe best not to
		for key in 'xcoord','ycoord','correlation','peakmoment','peakstddev','peakarea':
			particlesq[key] = peakdict[key]
		### INSERT VALUES
		presult = appiondb.query(particlesq)
		if not (presult):
			appiondb.insert(particlesq)
	return

def insertParticlePicks(params,imgdict,expid,manual=False):
	#INFO
	legimgid=int(imgdict.dbid)
	imgname=imgdict['filename'] 

	#GET RUNID
	runq=appionData.ApSelectionRunData()
	runq['name'] = params['runid']
	runq['dbemdata|SessionData|session'] = expid
	runids=appiondb.query(runq, results=1)

	# WRITE PARTICLES TO DATABASE
	print "Inserting particles into database for",apDisplay.shortenImageName(imgname),"..."

	# first open pik file, or create a temporary one if uploading a box file
	if manual is True and params['prtltype']=='box':
		pikfilename = convertBoxToPikFile(imgname, params)
	elif manual is True and params['prtltype']=='pik':
		pikfilename = imgname+"."+params['extension']
	else:
		pikfilename = "pikfiles/"+imgname+".a.pik"

	# read through the pik file
	pfile=open(pikfilename, "r")
	piklist=[]
	for line in pfile:
		if(line[0] != "#"):
			elements=line.split(' ')
			xcenter=int(elements[1])
			ycenter=int(elements[2])
			corr=float(elements[3])

			particlesq=appionData.ApParticleData()
			particlesq['selectionrun']=runids[0]
			particlesq['dbemdata|AcquisitionImageData|image']=legimgid
			particlesq['xcoord']=xcenter
			particlesq['ycoord']=ycenter
			particlesq['correlation']=corr

			presult=appiondb.query(particlesq)
			if not (presult):
				appiondb.insert(particlesq)
	pfile.close()
	
	return 

def convertBoxToPikFile(imgname,params):
	pikfilename=os.path.join(params['rundir'],"tempPikFileForUpload.pik")
	boxfilename=os.path.join(params['rundir'],imgname+".box")

	if not os.path.isfile(boxfilename):
		apDisplay.printError("manual box file, "+boxfilename+" does not exist")

	# read through the pik file
	boxfile = open(boxfilename, "r")
	piklist=[]
	for line in boxfile:
		elements=line.split('\t')
		xcoord=int(elements[0])
		ycoord=int(elements[1])
		xbox=int(elements[2])
		ybox=int(elements[3])
		xcenter=(xcoord + (xbox/2))*params['scale']
		ycenter=(ycoord + (ybox/2))*params['scale']
		if (xcenter < 4096 and ycenter < 4096):
			piklist.append(imgname+" "+str(xcenter)+" "+str(ycenter)+" 1.0\n")			
	boxfile.close()

	# write to the pik file
	pfile=open(pikfilename,"w")
	pfile.writelines(piklist)
	pfile.close()
	return pikfilename

def getMaskParamsByRunName(name,sessionname):
	sessionq = data.SessionData(name=sessionname)
	sessiondata = leginondb.query(sessionq)[0]
	sessionid = sessiondata.dbid
	maskRq=appionData.ApMaskMakerRunData()
	maskRq['name']=name
	maskRq['dbemdata|SessionData|session']=sessionid
	# get corresponding makeMaskParams entry
	result = appiondb.query(maskRq)[0]
	return result['params']
	
		
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

	return maskRq

def getMaskRegions(maskrun,imgid):
	maskRq=appionData.ApMaskRegionData()

	maskRq['mask']=maskrun
	maskRq['imageId']=imgid
	
	results=appiondb.query(maskRq)
	
	return results	

def pik2Box(params,file):
	box=params["box"]

	fname="pikfiles/"+file+".a.pik"

	# read through the pik file
	pfile=open(fname,"r")
	piklist=[]
	for line in pfile:
		elements=line.split(' ')
		xcenter=int(elements[1])
		ycenter=int(elements[2])
		xcoord=xcenter - (box/2)
		ycoord=ycenter - (box/2)
		if (xcoord>0 and ycoord>0):
			piklist.append(str(xcoord)+"\t"+str(ycoord)+"\t"+str(box)+"\t"+str(box)+"\t-3\n")
	pfile.close()

	# write to the box file
	bfile=open(file+".box","w")
	bfile.writelines(piklist)
	bfile.close()

	print "results written to \'"+file+".box\'"
	return
