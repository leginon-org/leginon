#Part of the new pyappion

import particleData
#import dbdatakeeper
import data
import os
import apImage
import ImageDraw
import apDB
import appionData

#partdb=dbdatakeeper.DBDataKeeper(db='dbappiondata')
partdb = apDB.apdb
leginondb = apDB.db

def getParticles(imgdict,params):
	"""
	returns paticles (as a list of dicts) for a given image
	ex: particles[0]['xcoord'] is the xcoord of particle 0
	"""
	
	imq=particleData.image()
	imq['dbemdata|AcquisitionImageData|image']=imgdict.dbid

	selexonrun=partdb.direct_query(data.run,params['selexonId'])
	prtlq=particleData.particle(imageId=imq,runId=selexonrun)

	particles=partdb.query(prtlq)
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
	pdimgData=partdb.query(imgq, results=1)

	# if no image entry, make one
	if not (pdimgData):
		print "Inserting image entry for",apDisplay.short(imgname)
		partdb.insert(imgq)
		imgq=None
		imgq = particleData.image()
		imgq['dbemdata|SessionData|session']=expid
		imgq['dbemdata|AcquisitionImageData|image']=legimgid
		imgq['dbemdata|PresetData|preset']=legpresetid
		pdimgData=partdb.query(imgq, results=1)

	return pdimgData

def getDBparticledataImage(imgdict,expid):
	"""
	This function is a dummy now that the output imgdict since we removed
	the image table in dbappiondata
	"""
	return imgdict
	

def insertParticlePeaks(peaktree, imgdict, expid, params):
	"""
	takes an image dict (imgdict) and inserts particles into DB from pik file
	"""
	particlesq = particleData.particle()
	imgname = imgdict['filename']

	runq=particleData.run()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	runids=partdb.query(runq, results=1)

	### GET CORRESPONDING SELECTIONPARAMS ENTRY
	selexonq = particleData.selectionParams(runId=runq)
	selexonresult = partdb.query(selexonq, results=1)

	pdimgData=getDBparticledataImage(imgdict,expid)

	### WRITE PARTICLES TO DATABASE
	for peakdict in peaktree:
		particlesq['runId']       = runq
		particlesq['imageId']     = imgdict.dbid
		particlesq['selectionId'] = selexonresult[0]
		# use an update function???, maybe best not to
		for key in 'xcoord','ycoord','correlation','peakmoment','peakstddev','peakarea','template':
			particlesq[key] = peakdict[key]
		### INSERT VALUES
		presult = partdb.query(particlesq)
		if not (presult):
			partdb.insert(particlesq)
	return

def insertParticlePicks(params,imgdict,expid,manual=False):
	"""
	takes an image dict (imgdict) and inserts particles into DB from pik file
	"""
	particlesq=particleData.particle()
	imgname = imgdict['filename']

	runq=particleData.run()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	runids=partdb.query(runq, results=1)

	# get corresponding selectionParams entry
	selexonq = particleData.selectionParams(runId=runq)
	selexonresult = partdb.query(selexonq, results=1)

	pdimgData = getDBparticledataImage(imgdict,expid)

	# WRITE PARTICLES TO DATABASE
	print "Inserting",apDisplay.short(imgname),"particles into Database..."

	# first open pik file, or create a temporary one if uploading a box file
	if (manual==True and params['prtltype']=='box'):
		fname="temporaryPikFileForUpload.pik"

		# read through the pik file
		boxfile=open(imgname+".box","r")
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
		pfile=open(fname,"w")
		pfile.writelines(piklist)
		pfile.close()
		
	elif (manual==True and params['prtltype']=='pik'):
		fname=imgname+"."+params['extension']
	else:
		if (params["crud"]==True):
			fname="pikfiles/"+imgname+".a.pik.nocrud"
		else:
			fname="pikfiles/"+imgname+".a.pik"
 
	# read through the pik file
	pfile=open(fname,"r")
	for line in pfile:
		if(line[0] != "#"):
			elements=line.split(' ')
			xcenter=int(elements[1])
			ycenter=int(elements[2])
			corr=float(elements[3])

			particlesq['runId']=runq
			particlesq['imageId']= imgdict.dbid
			particlesq['selectionId']=selexonresult[0]
			particlesq['xcoord']=xcenter
			particlesq['ycoord']=ycenter
			particlesq['correlation']=corr

			presult=partdb.query(particlesq)
			if not (presult):
				partdb.insert(particlesq)
	pfile.close()
	
	return

def getMaskParamsByRunName(name,sessionname):
	sessionq = data.SessionData(name=sessionname)
	sessiondata = leginondb.query(sessionq)[0]
	sessionid = sessiondata.dbid
	maskRq=appionData.ApMaskMakerRunData()
	maskRq['name']=name
	maskRq['dbemdata|SessionData|session']=sessionid
	# get corresponding makeMaskParams entry
	result = partdb.query(maskRq)[0]
	return result['params']
	
		
def insertMaskRegion(rundata,imgdata,regionInfo):

	maskRq = createMaskRegionData(rundata,imgdata,regionInfo)
	result=partdb.query(maskRq)
	if not (result):
		partdb.insert(maskRq)
	
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
	
	results=partdb.query(maskRq)
	
	return results	


