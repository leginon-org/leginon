#Part of the new pyappion

#pythonlib

import os
import sys
import time
#leginon
import leginon.leginondata
#appion
from appionlib import appiondata
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib import apDefocalPairs

####
# This is a database connections file with no file functions
# Please keep it this way
####

#===========================
def getParticles(imgdata, selectionRunId, particlelabel=None):
	"""
	returns paticles (as a list of dicts) for a given image
	ex: particles[0]['xcoord'] is the xcoord of particle 0
	"""
	selexonrun = appiondata.ApSelectionRunData.direct_query(selectionRunId)
	prtlq = appiondata.ApParticleData()
	prtlq['image'] = imgdata
	prtlq['selectionrun'] = selexonrun
	if particlelabel is not None:
		prtlq['label'] = particlelabel
	particles = prtlq.query()

	return particles

#===========================
def getOneParticle(imgdata):
	"""
	returns paticles (as a list of dicts) for a given image
	ex: particles[0]['xcoord'] is the xcoord of particle 0
	"""
	partq = appiondata.ApParticleData()
	partq['image'] = imgdata
	partd = partq.query(results=1)
	return partd

#===========================
def getParticlesForImageFromRunName(imgdata,runname):
	"""
	returns particles for a given image and selection run name
	"""
	srunq=appiondata.ApSelectionRunData()
	srunq['name']=runname
	srunq['session']=imgdata['session']

	ptclq=appiondata.ApParticleData()
	ptclq['image'] = imgdata
	ptclq['selectionrun']=srunq

	particles = ptclq.query()
	return particles

#===========================
def getSelectionRunDataFromID(selectionRunId):
	return appiondata.ApSelectionRunData.direct_query(selectionRunId)

#===========================
def getSelectionRunDataFromName(imgdata, runname):
	srunq=appiondata.ApSelectionRunData()
	srunq['name'] = runname
	srunq['session'] = imgdata['session']
	selectionrundata = srunq.query()
	return selectionrundata[0]

#===========================
def getDefocPairParticles(imgdata, selectionid, particlelabel=None):
	### get defocal pair
	if imgdata['preset'] is not None:
		defimgdata = apDefocalPairs.getDefocusPair(imgdata)
	else:
		# For pairs from Leginon Manual Application
		defimgdata = apDefocalPairs.getManualDefocusPair(imgdata)
	if defimgdata is None:
		apDisplay.printWarning("Could not find defocal pair for image %s (id %d)"
			%(apDisplay.short(imgdata['filename']), imgdata.dbid))
		return ([], {'shiftx':0, 'shifty':0, 'scale':1})
	apDisplay.printMsg("Found defocus pair %s (id %d) for image %s (id %d)"
		%(apDisplay.short(defimgdata['filename']), defimgdata.dbid, apDisplay.short(imgdata['filename']), imgdata.dbid))

	### get particles
	partq = appiondata.ApParticleData()
	partq['image'] = defimgdata
	partq['selectionrun'] = appiondata.ApSelectionRunData.direct_query(selectionid)
	if particlelabel is not None:
		partq['label'] = particlelabel
	partdatas = partq.query()
	apDisplay.printMsg("Found %d particles for defocal pair %s (id %d)"
		%(len(partdatas), apDisplay.short(defimgdata['filename']), defimgdata.dbid,))

	if len(partdatas) == 0:
		return ([], {'shiftx':0, 'shifty':0, 'scale':1})

	### get shift information
	has_tried = False
	while True:
		shiftq = appiondata.ApImageTransformationData()
		shiftq['image1'] = defimgdata
		shiftdatas = shiftq.query()
		if shiftdatas:
			shiftdata = shiftdatas[0]
			apDisplay.printMsg("Shifting particles by %.1f,%.1f (%d X)"
				%(shiftdata['shiftx'], shiftdata['shifty'], shiftdata['scale']))
			break
		else:
			if has_tried == True:
				apDisplay.printError("No shift inserted to database after one try")
			apDisplay.printMsg("Calculating shift....")
			shiftpeak = apDefocalPairs.getShift(defimgdata, imgdata)
			apDefocalPairs.insertShift(defimgdata, imgdata, shiftpeak)
			has_tried = True
	return (partdatas, shiftdata)

#===========================
def insertParticlePeakPairs(peaktree1, peaktree2, peakerrors, imgdata1, imgdata2, transdata, runname):
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
	runq=appiondata.ApSelectionRunData()
	runq['name'] = runname
	runq['session'] = sessiondata
	selectionruns=runq.query(results=1)
	if not selectionruns:
		apDisplay.printError("could not find selection run in database")

	#GET TRANSFORM DATA
	transq = appiondata.ApImageTiltTransformData()
	transq['image1'] = imgdata1
	transq['image2'] = imgdata2
	transq['tiltrun'] = selectionruns[0]
	transids = transq.query(results=1)
	if not transids:
		apDisplay.printError("could not find transform id in database")

	### WRITE PARTICLES TO DATABASE
	count = 0
	t0 = time.time()
	last50 = time.time()
	apDisplay.printMsg("looping over "+str(len(peaktree1))+" particles")
	for i in range(len(peaktree1)):
		remaining_peaks = len(peaktree1)-count
		if count and remaining_peaks and remaining_peaks % 50 == 0:
			#sys.stderr.write("<"+str(len(peaktree1)-count))
			print ("%d particles remain, %s time remains, %s per particle, %s last 50 particles"
				%(len(peaktree1)-count, 
				apDisplay.timeString((time.time() - t0)/count*(remaining_peaks)),
				apDisplay.timeString((time.time() - t0)/count),
				apDisplay.timeString(time.time()-last50),))
			last50 = time.time()
		peakdict1 = peaktree1[i]
		peakdict2 = peaktree2[i]
		error = peakerrors[i]

		partq1 = appiondata.ApParticleData()
		partq1['selectionrun'] = selectionruns[0]
		partq1['image'] = imgdata1
		partq1['xcoord'] = peakdict1['xcoord']
		partq1['ycoord'] = peakdict1['ycoord']
		partq1['peakarea'] = 1

		partq2 = appiondata.ApParticleData()
		partq2['selectionrun'] = selectionruns[0]
		partq2['image'] = imgdata2
		partq2['xcoord'] = peakdict2['xcoord']
		partq2['ycoord'] = peakdict2['ycoord']
		partq2['peakarea'] = 1

		# I do NOT have to check if particles already exist, because this is a NEW selectionrun

		partpairq = appiondata.ApTiltParticlePairData()
		partpairq['particle1'] = partq1
		partpairq['particle2'] = partq2
		#NEED TO LOOK UP TRANSFORM DATA
		partpairq['transform'] = transdata
		#NEED TO CALCULATE ERROR, ALWAYS POSITIVE
		partpairq['error'] = error

		#presult = partpairq.query()
		#if not presult:
		count+=1
		partq1.insert(force=True)
		partq2.insert(force=True)
		partpairq.insert(force=True)

	apDisplay.printMsg("inserted "+str(count)+" of "+str(len(peaktree1))+" peaks into database"
		+" in "+apDisplay.timeString(time.time()-t0))
	return

#===========================
def insertParticlePeaks(peaktree, imgdata, runname, msg=False):
	"""
	takes an image data object (imgdata) and inserts particles into DB from peaktree
	"""
	#INFO
	sessiondata = imgdata['session']
	imgname=imgdata['filename']

	#GET RUN DATA
	runq=appiondata.ApSelectionRunData()
	runq['name'] = runname
	runq['session'] = sessiondata
	selectionruns=runq.query(results=1)

	if not selectionruns:
		apDisplay.printError("could not find selection run in database")

	### WRITE PARTICLES TO DATABASE
	count = 0
	t0 = time.time()
	for peakdict in peaktree:
		particlesq = appiondata.ApParticleData()
		particlesq['selectionrun'] = selectionruns[0]
		particlesq['image'] = imgdata

		if 'template' in peakdict and peakdict['template'] is not None:
			particlesq['template'] = appiondata.ApTemplateImageData.direct_query(peakdict['template'])

		for key in 'correlation','peakmoment','peakstddev','peakarea', 'label':
			if key in peakdict and peakdict[key] is not None:
				if isinstance(peakdict[key], float):
					### limit decimals
					particlesq[key] = round(peakdict[key], 6)
				else:
					particlesq[key] = peakdict[key]
		### must be integers
		particlesq['xcoord'] = int(round(peakdict['xcoord']))
		particlesq['ycoord'] = int(round(peakdict['ycoord']))
		if 'angle' in peakdict:
			particlesq['angle'] = peakdict['angle']
		if 'helixnum' in peakdict:
			particlesq['helixnum'] = peakdict['helixnum']
		if 'helicalstep' in peakdict:
			particlesq['helicalstep'] = peakdict['helicalstep']
		if 'diameter' in peakdict and peakdict['diameter'] is not None:
				peakdict['diameter'] = round(peakdict['diameter'], 6)

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
	if msg is True:
		apDisplay.printMsg("inserted "+str(count)+" of "+str(len(peaktree))+" peaks into database"
			+" in "+apDisplay.timeString(time.time()-t0))
	return

#===========================
def getParticleDiameter(particledata):
	selectionrun = particledata['selectionrun']
	selection_params = ['params','dogparams','manparams','tiltparams']
	for p in selection_params:
		if selectionrun[p]:
			return selectionrun[p]['diam']

#================
def getSelectionIdFromName(runname, sessionname):
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
	selectq = appiondata.ApSelectionRunData()
	selectq['name'] = runname
	selectq['session'] = sessiondata
	selectdatas = selectq.query(results=1)
	if not selectdatas:
		return None
	return selectdatas[0].dbid

#================
def getRecentSelectionIdFromSession(sessionname):
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
	selectq = appiondata.ApSelectionRunData()
	selectq['session'] = sessiondata
	selectdatas = selectq.query(results=1)
	if not selectdatas:
		return None
	return selectdatas[0].dbid

#================
def getNumSelectionRunsFromSession(sessionname):
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
	selectq = appiondata.ApSelectionRunData()
	selectq['session'] = sessiondata
	selectdatas = selectq.query()
	if not selectdatas:
		return 0
	return len(selectdatas)

####
# This is a database connections file with no file functions
# Please keep it this way
####

#===========================
#===========================
#===========================
if __name__ == '__main__':
	name = 'test2'
	sessionname = '07jan05b'
	params = 'test'
	print params

