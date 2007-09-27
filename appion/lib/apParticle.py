#Part of the new pyappion

#pythonlib

import os
import sys
import time
#leginon
try:
	import leginondata
except ImportError:
	import data as leginondata
#appion
import apDB
import appionData
import apImage
import apDatabase
import apDisplay
import apTemplate

appiondb = apDB.apdb
leginondb = apDB.db

def guessParticlesForSession(expid=None, sessionname=None):
	if expid is None and sessionname is not None:
		expid = apDatabase.getExpIdFromSessionName(sessionname)
	if expid is None:
		apDisplay.printError("Unknown expId is guessParticlesForSession")
	apDisplay.printMsg("getting most complete particle picking run from DB for session "+sessionname)
	#sessionq = leginondata.SessionData(name=sessionname)
	#sessiondata = leginondb.query(sessionq)
	#print sessiondata[0]

	selectionq = appionData.ApSelectionRunData()
	selectionq['dbemdata|SessionData|session'] = expid
	selectiondata = appiondb.query(selectionq)
	if len(selectiondata) == 1:
		apDisplay.printMsg("automatically selected only particle run: '"+selectiondata[0]['name']+"'")
		return selectiondata[0].dbid
	elif len(selectiondata) == 0:
		apDisplay.printError("Could not find any particle runs\nGo back and pick some particles")
	else:
		apDisplay.printMsg("found "+str(len(selectiondata))+" particle run(s) for this session")
		for selectionrun in selectiondata:
			apDisplay.printColor(selectionrun['name']+":\t prtlrunId="+str(selectionrun.dbid),"cyan")
		apDisplay.printError("Please select one of the above runids")

def guessParticlesForSessionREFLEGINON(sessiondata=None, sessionname=None):
	if sessiondata is None and sessionname is not None:
		sessionq = leginondata.SessionData(name=sessionname)
		sessiondata = leginondb.query(sessionq)
	if sessiondata is [] or None:
		apDisplay.printError("Unknown session in guessParticlesForSession")
	else:
		sessionname = sessiondata['name']
	apDisplay.printMsg("getting most complete particle picking run from DB for session "+sessionname)

	selectionq = appionData.ApSelectionRunData()
	selectionq['session'] = sessiondata
	selectiondata = appiondb.query(selectionq)
	if len(selectiondata) == 1:
		apDisplay.printMsg("automatically selected only particle run: '"+selectiondata[0]['name']+"'")
		return selectiondata[0].dbid
	elif len(selectiondata) == 0:
		apDisplay.printError("Could not find any particle runs\nGo back and pick some particles")
	else:
		apDisplay.printMsg("found "+str(len(selectiondata))+" particle run(s) for this session")
		for selectionrun in selectiondata:
			apDisplay.printColor(selectionrun['name']+":\t prtlrunId="+str(selectionrun.dbid),"cyan")
		apDisplay.printError("Please select one of the above runids")

def getParticles(imgdata, selectionRunId):
	"""
	returns paticles (as a list of dicts) for a given image
	ex: particles[0]['xcoord'] is the xcoord of particle 0
	"""
	selexonrun = appiondb.direct_query(appionData.ApSelectionRunData, selectionRunId)
	prtlq = appionData.ApParticleData()
	prtlq['dbemdata|AcquisitionImageData|image'] = imgdata.dbid
	prtlq['selectionrun'] = selexonrun
	particles = appiondb.query(prtlq)

	return particles

def getParticlesForImageFromRunName(imgdata,runname):
	"""
	returns particles for a given image and selection run name
	"""
	srunq=appionData.ApSelectionRunData()
	srunq['name']=runname
	srunq['dbemdata|SessionData|session']=imgdata['session'].dbid
	
	ptclq=appionData.ApParticleData()
	ptclq['dbemdata|AcquisitionImageData|image'] = imgdata.dbid
	ptclq['selectionrun']=srunq
	
	particles = appiondb.query(ptclq)
	return particles
	
def getSelectionRunDataFromID(selectionRunId):
	return appiondb.direct_query(appionData.ApSelectionRunData, selectionRunId) 

def getSelectionRunDataFromName(imgdata, runname):
	srunq=appionData.ApSelectionRunData()
	srunq['name'] = runname
	srunq['dbemdata|SessionData|session'] = imgdata['session'].dbid
	selectionrundata = appiondb.query(srunq)
	return selectionrundata[0]

def getParticlesREFLEGINON(imgdata, selectionRunId):
	"""
	returns paticles (as a list of dicts) for a given image
	ex: particles[0]['xcoord'] is the xcoord of particle 0
	"""
	selexonrun = appiondb.direct_query(appionData.ApSelectionRunData, selectionRunId)
	prtlq = appionData.ApParticleData()
	prtlq['image'] = imgdata
	prtlq['selectionrun'] = selexonrun
	particles = appiondb.query(prtlq)
	shift={'shiftx':0, 'shifty':0,'scale':1}
	return(particles,shift)

def getDefocPairParticles(imgdict, params):
	print "finding pair for", apDisplay.short(imgdict['filename'])
	selexonrun=appiondb.direct_query(appionData.ApSelectionRunData,params['selexonId'])
	prtlq=appionData.ApParticleData()
	prtlq['dbemdata|AcquisitionImageData|image'] = params['sibpairs'][imgdict.dbid]
	prtlq['selectionrun'] = selexonrun
	particles=appiondb.query(prtlq)
	
	shiftq=appionData.ApImageTransformationData()
	shiftq['dbemdata|AcquisitionImageData|image1'] = params['sibpairs'][imgdict.dbid]
	shiftdata=appiondb.query(shiftq,readimages=False)[0]
	shiftx=shiftdata['shiftx']
	shifty=shiftdata['shifty']
	shift={}
	shift['shiftx']=shiftx
	shift['shifty']=shifty
	shift['scale']=shiftdata['scale']
	print "shifting particles by", shiftx, shifty,shiftdata['scale']
	return(particles,shift)

def getDefocPairParticlesREFLEGINON(imgdata, params):
	print "finding pair for", apDisplay.short(imgdata['filename'])
	selexonrun=appiondb.direct_query(appionData.ApSelectionRunData,params['selexonId'])
	pairimgid = params['sibpairs'][imgdata.dbid]
	prtlq=appionData.ApParticleData()
	pairimgdata=leginondb.direct_query(leginondata.AcquisitionImageData,pairimgid)
	prtlq['image'] = pairimgdata
	prtlq['selectionrun'] = selexonrun
	particles=appiondb.query(prtlq)
	
	shiftq=appionData.ApImageTransformationData()
	shiftq['image1'] = pairimgdata
	shiftdata=appiondb.query(shiftq,readimages=False)[0]
	shiftx=shiftdata['shiftx']
	shifty=shiftdata['shifty']
	shift={}
	shift['shiftx']=shiftx
	shift['shifty']=shifty
	shift['scale']=shiftdata['scale']
	print "shifting particles by", shiftx, shifty,shiftdata['scale']
	return(particles,shift)


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
	imgq['dbemdata|SessionData|session'] = expid
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
	return appiondb.direct_query(appionData.ApTemplateImageData, tmpldbid)

def insertParticlePeakPairs(peaktree1, peaktree2, peakerrors, imgdata1, imgdata2, transdata, params):
	"""
	takes both image dicts (imgdict) and inserts particle pairs into DB from peaktrees
	"""
	#INFO
	expid = int(imgdata1['session'].dbid)
	legimgid1=int(imgdata1.dbid)
	legimgid2=int(imgdata2.dbid)
	imgname1=imgdata1['filename']
	imgname2=imgdata2['filename'] 

	#CHECK ARRAY LENGTHS
	len1 = len(peaktree1)
	len2 = len(peaktree2)
	len3 = len(peakerrors)
	if len1 != len2 or len2 != len3:
		apDisplay.printError("insertParticlePeakPairs particle arrays must have the same length "+\
			str(len1)+" "+str(len2)+" "+str(len3))

	#GET RUN DATA
	runq=appionData.ApSelectionRunData()
	runq['name'] = params['runid']
	runq['dbemdata|SessionData|session'] = expid
	runids=appiondb.query(runq, results=1)
	if not runids:
		apDisplay.printError("could not find runid in database")

	#GET TRANSFORM DATA
	transq = appionData.ApImageTiltTransformData()
	transq['dbemdata|AcquisitionImageData|image1'] = legimgid1
	transq['dbemdata|AcquisitionImageData|image2'] = legimgid2
	transq['tiltrun'] = runids[0]
	transids = appiondb.query(transq, results=1)
	if not transids:
		apDisplay.printError("could not find transform id in database")

	### WRITE PARTICLES TO DATABASE
	count = 0
	for i in range(len(peaktree1)):
		peakdict1 = peaktree1[i]
		peakdict2 = peaktree2[i]
		error = peakerrors[i]

		partq1 = appionData.ApParticleData()
		partq1['selectionrun'] = runids[0]
		partq1['dbemdata|AcquisitionImageData|image'] = legimgid1
		partq1['xcoord'] = peakdict1['xcoord']
		partq1['ycoord'] = peakdict1['ycoord']
		partq1['peakarea'] = 1

		partq2 = appionData.ApParticleData()
		partq2['selectionrun'] = runids[0]
		partq2['dbemdata|AcquisitionImageData|image'] = legimgid2
		partq2['xcoord'] = peakdict2['xcoord']
		partq2['ycoord'] = peakdict2['ycoord']
		partq2['peakarea'] = 1

		# I do NOT have to check if particles already exist, because this is a NEW selectionrun

		partpairq = appionData.ApTiltParticlePairData()
		partpairq['particle1'] = partq1
		partpairq['particle2'] = partq2
		#NEED TO LOOK UP TRANSFORM DATA
		partpairq['transform'] = transdata
		#NEED TO CALCULATE ERROR, ALWAYS POSITIVE
		partpairq['error'] = error

		presult = appiondb.query(partpairq)
		if not presult:
			count+=1
			appiondb.insert(partpairq)

	apDisplay.printMsg("inserted "+str(count)+" of "+str(len(peaktree1))+" peaks into database")
	return

def insertParticlePeaks(peaktree, imgdict, expid, params):
	"""
	takes an image dict (imgdict) and inserts particles into DB from peaktree
	"""
	#INFO
	legimgid=int(imgdict.dbid)
	imgname=imgdict['filename'] 

	#GET RUNID
	runq=appionData.ApSelectionRunData()
	runq['name'] = params['runid']
	runq['dbemdata|SessionData|session'] = expid
	runids=appiondb.query(runq, results=1)

	if not runids:
		apDisplay.printError("could not find runid in database")

	# WRITE PARTICLES TO DATABASE
	apDisplay.printMsg("Inserting "+str(len(peaktree))+" particles into database for "+apDisplay.shortenImageName(imgname))

	### WRITE PARTICLES TO DATABASE
	count = 0
	for peakdict in peaktree:
		particlesq = appionData.ApParticleData()
		particlesq['selectionrun'] = runids[0]
		particlesq['dbemdata|AcquisitionImageData|image'] = legimgid

		if 'template' in peakdict and peakdict['template'] is not None:
			particlesq['template'] = getTemplateDBInfo(peakdict['template'])

		for key in 'xcoord','ycoord','correlation','peakmoment','peakstddev','peakarea':
			if key in peakdict and peakdict[key] is not None:
				particlesq[key] = peakdict[key]

		if 'peakarea' in peakdict and peakdict['peakarea'] is not None and peakdict['peakarea'] > 0:
			peakhasarea = True
		else:
			apDisplay.printWarning("peak has no area")
			peakhasarea = False

		if 'correlation' in peakdict and peakdict['correlation'] is not None and peakdict['correlation'] > 2:
			apDisplay.printWarning("peak has correlation greater than 2.0")

		### INSERT VALUES
		if peakhasarea is True:
			presult = appiondb.query(particlesq)
			if not presult:
				count+=1
				appiondb.insert(particlesq)
	apDisplay.printMsg("inserted "+str(count)+" of "+str(len(peaktree))+" peaks into database")
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
	if not params['scale']:
		params['scale']=1
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

if __name__ == '__main__':
	name = 'test2'
	sessionname = '07jan05b'
	params = 'test'
	print params
