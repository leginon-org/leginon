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
	shift={'shiftx':0, 'shifty':0}
	return(particles,shift)

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
	shift={'shiftx':0, 'shifty':0}
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
	shiftx=shiftdata['shiftx']*shiftdata['scale']
	shifty=shiftdata['shifty']*shiftdata['scale']
	shift={}
	shift['shiftx']=shiftx
	shift['shifty']=shifty
	print "shifting particles by", shiftx, shifty
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
	shiftx=shiftdata['shiftx']*shiftdata['scale']
	shifty=shiftdata['shifty']*shiftdata['scale']
	shift={}
	shift['shiftx']=shiftx
	shift['shifty']=shifty
	print "shifting particles by", shiftx, shifty
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

	if not runids:
		apDisplay.printError("could not find runid in database")

	# WRITE PARTICLES TO DATABASE
	print "Inserting particles into database for",apDisplay.shortenImageName(imgname),"..."

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

def insertParticlePeaksREFLEGINON(peaktree, imgdict, params):
	"""
	takes an image dict (imgdict) and inserts particles into DB from pik file
	"""
	#INFO
	imgname=imgdict['filename'] 

	#GET RUNID
	runq=appionData.ApSelectionRunData()
	runq['name'] = params['runid']
	runq['session'] = imgdict['session']
	runids=appiondb.query(runq, results=1)

	if not runids:
		apDisplay.printError("could not find runid in database")

	# WRITE PARTICLES TO DATABASE
	print "Inserting particles into database for",apDisplay.shortenImageName(imgname),"..."

	### WRITE PARTICLES TO DATABASE
	count = 0
	for peakdict in peaktree:
		particlesq = appionData.ApParticleData()
		particlesq['selectionrun'] = runids[0]
		particlesq['image'] = imagdict

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
	sys.exit(1)
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

def insertParticlePicksREFLEGINON(params,imgdict,manual=False):
	sys.exit(1)
	#INFO
	imgname=imgdict['filename'] 

	#GET RUNID
	runq=appionData.ApSelectionRunData()
	runq['name'] = params['runid']
	runq['session'] = imgdict['session']
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
			particlesq['image']=imgdict
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

def insertSelexonParams(params,expid):
	### query for identical params ###
	selexonparamsq=appionData.ApSelectionParamsData()
 	selexonparamsq['diam']=params['diam']
 	selexonparamsq['bin']=params['bin']
 	selexonparamsq['manual_thresh']=params['thresh']
 	selexonparamsq['auto_thresh']=params['autopik']
 	selexonparamsq['lp_filt']=params['lp']
 	selexonparamsq['hp_filt']=params['hp']
	selexonparamsdata = appiondb.query(selexonparamsq, results=1)

	### query for identical run name ###
	runq = appionData.ApSelectionRunData()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid

	runids = appiondb.query(runq, results=1)

 	# if no run entry exists, insert new run entry into dbappiondata
 	if not(runids):
		runq['params']=selexonparamsq
		if not selexonparamsdata:
			appiondb.insert(selexonparamsq)
		appiondb.insert(runq)
		#insert template params
 		for n in range(0, len(params['templateIds'])):
			apTemplate.insertTemplateRun(params,runq,n)

	# if continuing a previous run, make sure that all the current
 	# parameters are the same as the previous
 	else:
		if not selexonparamsdata or runids[0]['params'] != selexonparamsdata[0]:
			if selexonparamsdata:
				for i in selexonparamsdata[0]:
					if selexonparamsdata[0][i] != runids[0]['params'][i]:
						apDisplay.printWarning("the value for parameter '"+str(i)+"' is different from before")
			apDisplay.printError("All parameters for a single selexon run must be identical! \n"+\
					     "please check your parameter settings.")
		apTemplate.checkTemplateParams(params,runq)
	return

def insertSelexonParamsREFLEGINON(params,sessiondata):
	### query for identical params ###
	selexonparamsq=appionData.ApSelectionParamsData()
 	selexonparamsq['diam']=params['diam']
 	selexonparamsq['bin']=params['bin']
 	selexonparamsq['manual_thresh']=params['thresh']
 	selexonparamsq['auto_thresh']=params['autopik']
 	selexonparamsq['lp_filt']=params['lp']
 	selexonparamsq['hp_filt']=params['hp']
	selexonparamsdata = appiondb.query(selexonparamsq, results=1)

	### query for identical run name ###
	runq = appionData.ApSelectionRunData()
	runq['name']=params['runid']
	runq['session']=sessiondata

	runids = appiondb.query(runq, results=1)

 	# if no run entry exists, insert new run entry into dbappiondata
 	if not(runids):
		runq['params']=selexonparamsq
		if not selexonparamsdata:
			appiondb.insert(selexonparamsq)
		appiondb.insert(runq)
		#insert template params
 		for n in range(0, len(params['templateIds'])):
			apTemplate.insertTemplateRun(params,runq,n)

	# if continuing a previous run, make sure that all the current
 	# parameters are the same as the previous
 	else:
		if not selexonparamsdata or runids[0]['params'] != selexonparamsdata[0]:
			if selexonparamsdata:
				for i in selexonparamsdata[0]:
					if selexonparamsdata[0][i] != runids[0]['params'][i]:
						apDisplay.printWarning("the value for parameter '"+str(i)+"' is different from before")
			apDisplay.printError("All parameters for a single selexon run must be identical! \n"+\
					     "please check your parameter settings.")
		apTemplate.checkTemplateParams(params,runq)
	return

if __name__ == '__main__':
	name = 'test2'
	sessionname = '07jan05b'
	params = 'test'
	print params
