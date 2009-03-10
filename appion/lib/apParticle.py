#Part of the new pyappion

#pythonlib

import os
import sys
import time
#sinedon
import sinedon
try:
	import sinedon.directq as directq
except:
	pass
#leginon
import leginondata
#appion
import appionData
import apImage
import apDatabase
import apDisplay
import apDefocalPairs

def guessParticlesForSession(expid=None, sessionname=None):
	if expid is None and sessionname is not None:
		sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
	else: 
		if expid:
			seesiondata = leginondata.SessionData.direct_query(expid)
	if sessiondata is None:
		apDisplay.printError("Unknown expId in guessParticlesForSession")
	apDisplay.printMsg("getting most complete particle picking run from DB for session "+sessionname)

	selectionq = appionData.ApSelectionRunData()
	selectionq['session'] = sessiondata
	selectiondata = selectionq.query()
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
	selexonrun = appionData.ApSelectionRunData.direct_query(selectionRunId)
	prtlq = appionData.ApParticleData()
	prtlq['image'] = imgdata
	prtlq['selectionrun'] = selexonrun
	particles = prtlq.query()

	return particles

def getOneParticle(imgdata):
	"""
	returns paticles (as a list of dicts) for a given image
	ex: particles[0]['xcoord'] is the xcoord of particle 0
	"""
	partq = appionData.ApParticleData()
	partq['image'] = imgdata
	partd = partq.query(results=1)
	return partd

def getParticlesForImageFromRunName(imgdata,runname):
	"""
	returns particles for a given image and selection run name
	"""
	srunq=appionData.ApSelectionRunData()
	srunq['name']=runname
	srunq['session']=imgdata['session']
	
	ptclq=appionData.ApParticleData()
	ptclq['image'] = imgdata
	ptclq['selectionrun']=srunq
	
	particles = ptclq.query()
	return particles
	
def getSelectionRunDataFromID(selectionRunId):
	return appionData.ApSelectionRunData.direct_query(selectionRunId) 

def getSelectionRunDataFromName(imgdata, runname):
	srunq=appionData.ApSelectionRunData()
	srunq['name'] = runname
	srunq['session'] = imgdata['session']
	selectionrundata = srunq.query()
	return selectionrundata[0]

def getDefocPairParticles(imgdata, selectionid):
	### get defocal pair
	defimgdata = apDefocalPairs.getDefocusPair(imgdata)
	if defimgdata is None:
		apDisplay.printError("Could not find defocal pair for image %s (id %d)"
			%(apDisplay.short(imgdata['filename']), imgdata.dbid))
	apDisplay.printMsg("Found defocus pair %s (id %d) for image %s (id %d)"
		%(apDisplay.short(defimgdata['filename']), defimgdata.dbid, apDisplay.short(imgdata['filename']), imgdata.dbid))

	### get particles
	partq = appionData.ApParticleData()
	partq['image'] = defimgdata
	partq['selectionrun'] = appionData.ApSelectionRunData.direct_query(selectionid)
	partdatas = partq.query()
	apDisplay.printMsg("Found %d particles for defocal pair %s (id %d)"
		%(len(partdatas), apDisplay.short(defimgdata['filename']), defimgdata.dbid,))

	if len(partdatas) == 0:
		return ([], {'shiftx':0, 'shifty':0, 'scale':1})

	### get shift information
	shiftq = appionData.ApImageTransformationData()
	shiftq['image1'] = defimgdata
	shiftdatas = shiftq.query()
	if shiftdatas:
		shiftdata = shiftdatas[0]
		apDisplay.printMsg("Shifting particles by %.1f,%.1f (%d X)"
			%(shiftdata['shiftx'], shiftdata['shifty'], shiftdata['scale']))
	else:
		apDisplay.printError("Could not find defocal shift data, please run alignDefocalPairs.py")
	return (partdatas, shiftdata)


def insertParticlePeakPairs(peaktree1, peaktree2, peakerrors, imgdata1, imgdata2, transdata, params):
	"""
	takes both image data (imgdata) and inserts particle pairs into DB from peaktrees
	"""
	#INFO
	sessiondata = imgdata1['session']
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
	runq['name'] = params['runname']
	runq['session'] = sessiondata
	selectionruns=runq.query(results=1)
	if not selectionruns:
		apDisplay.printError("could not find selection run in database")

	#GET TRANSFORM DATA
	transq = appionData.ApImageTiltTransformData()
	transq['image1'] = imgdata1
	transq['image2'] = imgdata2
	transq['tiltrun'] = selectionruns[0]
	transids = transq.query(results=1)
	if not transids:
		apDisplay.printError("could not find transform id in database")

	### WRITE PARTICLES TO DATABASE
	count = 0
	t0 = time.time()
	apDisplay.printMsg("looping over "+str(len(peaktree1))+" particles")
	for i in range(len(peaktree1)):
		if (len(peaktree1)-count) % 50 == 0:
			sys.stderr.write("<"+str(len(peaktree1)-count))
		peakdict1 = peaktree1[i]
		peakdict2 = peaktree2[i]
		error = peakerrors[i]

		partq1 = appionData.ApParticleData()
		partq1['selectionrun'] = selectionruns[0]
		partq1['image'] = imgdata1
		partq1['xcoord'] = peakdict1['xcoord']
		partq1['ycoord'] = peakdict1['ycoord']
		partq1['peakarea'] = 1

		partq2 = appionData.ApParticleData()
		partq2['selectionrun'] = selectionruns[0]
		partq2['image'] = imgdata2
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

		presult = partpairq.query()
		if not presult:
			count+=1
			partpairq.insert()

	apDisplay.printMsg("inserted "+str(count)+" of "+str(len(peaktree1))+" peaks into database"
		+" in "+apDisplay.timeString(time.time()-t0))
	return

def insertParticlePeaks(peaktree, imgdata, params):
	"""
	takes an image data object (imgdata) and inserts particles into DB from peaktree
	"""
	#INFO
	sessiondata = imgdata['session']
	imgname=imgdata['filename']

	#GET RUN DATA
	runq=appionData.ApSelectionRunData()
	runq['name'] = params['runname']
	runq['session'] = sessiondata
	selectionruns=runq.query(results=1)

	if not selectionruns:
		apDisplay.printError("could not find selection run in database")

	### WRITE PARTICLES TO DATABASE
	count = 0
	t0 = time.time()
	for peakdict in peaktree:
		particlesq = appionData.ApParticleData()
		particlesq['selectionrun'] = selectionruns[0]
		particlesq['image'] = imgdata

		if 'template' in peakdict and peakdict['template'] is not None:
			particlesq['template'] = appionData.ApTemplateImageData.direct_query(peakdict['template'])

		for key in 'correlation','peakmoment','peakstddev','peakarea', 'diameter':
			if key in peakdict and peakdict[key] is not None:
				particlesq[key] = peakdict[key]
		particlesq['xcoord'] = int(round(peakdict['xcoord']))
		particlesq['ycoord'] = int(round(peakdict['ycoord']))

		if 'peakarea' in peakdict and peakdict['peakarea'] is not None and peakdict['peakarea'] > 0:
			peakhasarea = True
		else:
			apDisplay.printWarning("peak has no area")
			peakhasarea = False

		if 'correlation' in peakdict and peakdict['correlation'] is not None and peakdict['correlation'] > 2:
			apDisplay.printWarning("peak has correlation greater than 2.0")

		### INSERT VALUES
		if peakhasarea is True:
			presult = particlesq.query()
			if not presult:
				count+=1
				particlesq.insert()
	if params['background'] is False:
		apDisplay.printMsg("inserted "+str(count)+" of "+str(len(peaktree))+" peaks into database"
			+" in "+apDisplay.timeString(time.time()-t0))
	return

def insertParticlePicks(params,imgdata,manual=False):
	#INFO
	imgname=imgdata['filename'] 

	#GET RUN DATA
	runq=appionData.ApSelectionRunData()
	runq['name'] = params['runname']
	runq['session'] = imgdata['session']
	selectionruns=runq.query(results=1)

	# WRITE PARTICLES TO DATABASE
	apDisplay.printMsg("Inserting particles from pik file into database for "+apDisplay.shortenImageName(imgname))

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
			particlesq['selectionrun']=selectionruns[0]
			particlesq['image']=imgdata
			particlesq['xcoord']=xcenter
			particlesq['ycoord']=ycenter
			particlesq['correlation']=corr

			presult=particlesq.query()
			if not (presult):
				particlesq.insert()
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
	
def getImageMsgPKeepCount(imgdata,refinerundata):
	runid = str(refinerundata.dbid)
	imgid = str(imgdata.dbid)

	q = """
	SELECT stackp2.`REF|ApParticleData|particle` particle, result.* FROM
	(SELECT pcls.`REF|ApStackParticlesData|particle` as stackp,count(*) as count FROM
	`ApParticleClassificationData` pcls
	LEFT JOIN
	`ApRefinementData` rf
	ON pcls.`REF|ApRefinementData|refinement` = rf.`DEF_id`
	LEFT JOIN
	`ApRefinementRunData` rfr
	ON rf.`REF|ApRefinementRunData|refinementRun`=rfr.`DEF_id`
	"""
	q = q+"WHERE rfr.`DEF_id`="+runid
	q = q+"""
	AND pcls.`msgp_keep`=1
	AND pcls.`REF|ApStackParticlesData|particle`
	in
	(SELECT stackp.`DEF_id` as stackp FROM
	`ApStackParticlesData` stackp
	LEFT JOIN `ApStackData` stack
	ON stackp.`REF|ApStackData|stack` = stack.`DEF_id`
	LEFT JOIN `ApRefinementRunData` rfr
	ON rfr.`REF|ApStackData|stack` = stack.`DEF_id`
	"""
	q = q+ "where rfr.`DEF_id`="+runid
	q = q + """
	AND
	stackp.`REF|ApParticleData|particle`
	in 
	(SELECT p.`DEF_id` FROM
	`ApParticleData` p
	"""
	q = q + "WHERE p.`REF|leginondata|AcquisitionImageData|image` = " + imgid + ")"
	q = q + """
	)
	group by pcls.`REF|ApStackParticlesData|particle`) result
	LEFT JOIN
	`ApStackParticlesData` stackp2
	ON result.`stackp`=stackp2.`DEF_id` 
	"""
	results = directq.complexMysqlQuery('appionData',q)

	return results

if __name__ == '__main__':
	name = 'test2'
	sessionname = '07jan05b'
	params = 'test'
	print params
