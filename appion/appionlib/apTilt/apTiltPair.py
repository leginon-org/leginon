#python
import re
import numpy
import time
import math
import datetime
#leginon
import leginon.leginondata
#appion
from appionlib import appiondata
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apDatabase
from appionlib.apTilt import apTiltTransform
import sinedon
import MySQLdb

####
# This is a database connections file with no file functions
# Please keep it this way
####


"""
Denis's query
$q="select "
	."a2.DEF_id, a2.`MRC|image` as filename "
	."from AcquisitionImageData a1 "
	."left join AcquisitionImageData a2 "
	."on (a1.`REF|TiltSeriesData|tilt series`=a2.`REF|TiltSeriesData|tilt series` "
	."and a1.`REF|PresetData|preset`=a2.`REF|PresetData|preset` "
	."and a1.DEF_id<>a2.DEF_id) "
	."where a1.DEF_id=$imageId";
"""

"""
	sessionq = leginon.leginondata.SessionData(name=session)
	presetq=leginon.leginondata.PresetData(name=preset)
	imgquery = leginon.leginondata.AcquisitionImageData()
	imgquery['preset']  = presetq
	imgquery['session'] = sessionq
	imgtree = imgquery.query(readimages=False)
"""

#===============================
def getTiltPair(imgdata):
	imageq  = leginon.leginondata.AcquisitionImageData()
	imageq['tilt series'] = imgdata['tilt series']
	if imgdata['preset'] is None:
		return None
	presetq = leginon.leginondata.PresetData()
	presetname = imgdata['preset']['name']
	if presetname != "Zproj":
		presetq['name'] = imgdata['preset']['name']
	imageq['preset'] = presetq
	#if beam changed between tilting, presets would be different
	origid=imgdata.dbid
	alltilts = imageq.query(readimages=False)
	tiltpair = None
	if len(alltilts) > 1:
		#could be multiple tiltpairs but we are taking only the most recent
		for tilt in alltilts:
			if tilt.dbid != origid and tilt['preset']['name'] != 'Zproj':
				tiltpair = tilt
				break
	return tiltpair

#===============================
def tiltPickerToDbNames(tiltparams):
	#('image1', leginon.leginondata.AcquisitionImageData),
	#('image2', leginon.leginondata.AcquisitionImageData),
	#('shiftx', float),
	#('shifty', float),
	#('correlation', float),
	#('scale', float),
	#('tilt', float),
	#('image1_rotation', float),
	#('image2_rotation', float),
	#('rmsd', float),
	newdict = {}
	if 'theta' in tiltparams:
		newdict['tilt_angle'] = tiltparams['theta']
	if 'gamma' in tiltparams:
		newdict['image1_rotation'] = tiltparams['gamma']
	if 'phi' in tiltparams:
		newdict['image2_rotation'] = tiltparams['phi']
	if 'rmsd' in tiltparams:
		newdict['rmsd'] = tiltparams['rmsd']
	if 'scale' in tiltparams:
		newdict['scale_factor'] = tiltparams['scale']
	if 'point1' in tiltparams:
		newdict['image1_x'] = tiltparams['point1'][0]
		newdict['image1_y'] = tiltparams['point1'][1]
	if 'point2' in tiltparams:
		newdict['image2_x'] = tiltparams['point2'][0]
		newdict['image2_y'] = tiltparams['point2'][1]
	if 'overlap' in tiltparams:
		newdict['overlap'] = tiltparams['overlap']
	return newdict

#===============================
def getBestTiltTransform(imgdata):
	"""
	For a given image get the best tilt transform 
	parameters in the database
	"""
	transdatas = []
	## case 1: check if imgdata is image1
	transq = appiondata.ApImageTiltTransformData()
	transq['image1'] = imgdata
	transdatas1 = transq.query()
	if transdatas1:
		transdatas.extend(transdatas1)
	## case 2: check if imgdata is image2
	transq = appiondata.ApImageTiltTransformData()
	transq['image2'] = imgdata
	transdatas2 = transq.query()
	if transdatas2:
		transdatas.extend(transdatas2)

	### case 1: no transformation
	if len(transdatas) == 0:
		apDisplay.printWarning("no transformation found for image %s"
			%(apDisplay.short(imgdata['filename'])))
		return None
	### case 2: single transformation, no sorting required
	if len(transdatas) == 1:
		apDisplay.printMsg("single transformation found with rmsd %.2f for image %s"
			%(transdatas[0]['rmsd'], apDisplay.short(imgdata['filename'])))
		return transdatas[0]
	### case 3: more than one transformation, get one with lowest rmsd
	besttransdata = transdatas[0]
	bestrmsd = transdatas[0]['rmsd']
	for transdata in transdatas:
		if transdata['rmsd'] > 0 and transdata['rmsd'] < bestrmsd:
			besttransdata = transdata
			bestrmsd = transdata['rmsd']
	apDisplay.printMsg("returning best transformation with rmsd %.2f for image %s"
		%(bestrmsd, apDisplay.short(imgdata['filename'])))
	return besttransdata

#===============================
def insertTiltTransform(imgdata1, imgdata2, tiltparams, params):
	#First we need to sort imgdata
	#'07aug30b_a_00013gr_00010sq_v01_00002sq_v01_00016en_00'
	#'07aug30b_a_00013gr_00010sq_v01_00002sq_01_00016en_01'
	#last two digits confer order, but then the transform changes...
	bin = params['bin']

	### first find the runid
	runq = appiondata.ApSelectionRunData()
	runq['name'] = params['runname']
	runq['session'] = imgdata1['session']
	rundatas = runq.query(results=1, readimages=False)
	if not rundatas:
		apDisplay.printError("could not find runid in database")

	### the order is specified by 1,2; so don't change it let makestack figure it out
	for imgdata in (imgdata1, imgdata2):
		for index in ("1","2"):
			transq = appiondata.ApImageTiltTransformData()
			transq["image"+index] = imgdata
			transq['tiltrun'] = rundatas[0]
			transdata = transq.query(readimages=False)
			if transdata:
				apDisplay.printWarning("Transform values already in database for "+imgdata['filename'])
				return transdata[0]

	### prepare the insertion
	transq = appiondata.ApImageTiltTransformData()
	transq['image1'] = imgdata1
	transq['image2'] = imgdata2
	transq['tiltrun'] = rundatas[0]
	dbdict = tiltPickerToDbNames(tiltparams)
	if dbdict is None:
		return None
	#Can I do for key in appiondata.ApImageTiltTransformData() ro transq???
	for key in ('image1_x','image1_y','image1_rotation','image2_x','image2_y','image2_rotation','scale_factor','tilt_angle', 'overlap'):
		if key not in dbdict:
			apDisplay.printError("Key: "+key+" was not found in transformation data")

	for key,val in dbdict.items():
		#print key
		if re.match("image[12]_[xy]", key):
			transq[key] = round(val*bin,2)
		else:
			transq[key] = val
		#print i,v


	### this overlap is wrong because the images are binned by 'bin' and now we give it the full image
	"""
	imgShape1 = numpy.asarray(imgdata1['image'].shape, dtype=numpy.int8)/params['bin']
	image1 = numpy.ones(imgShape1)
	imgShape2 = numpy.asarray(imgdata2['image'].shape, dtype=numpy.int8)/params['bin']
	image2 = numpy.ones(imgShape2)
	bestOverlap, tiltOverlap = apTiltTransform.getOverlapPercent(image1, image2, tiltparams)
	print "image overlaps", bestOverlap, tiltOverlap
	transq['overlap'] = round(bestOverlap,5)
	"""

	apDisplay.printMsg("Inserting transform between "+apDisplay.short(imgdata1['filename'])+\
		" and "+apDisplay.short(imgdata2['filename'])+" into database")
	transq.insert()
	apDisplay.printMsg("done")
	return transq

#===============================
def getStackParticleTiltPair(stackid, partnum, tiltstackid=None):
	"""
	takes a stack id and particle number (1+) spider-style
	returns the stack particle number for the tilt pair
	"""
	#print stackid, partnum
	if tiltstackid is None:
		tiltstackid = stackid

	t0 = time.time()
	stackpartdata1 = apStack.getStackParticle(stackid, partnum)
	partdata = stackpartdata1['particle']

	### figure out if its particle 1 or 2
	tiltpartq1 = appiondata.ApTiltParticlePairData()
	tiltpartq1['particle1'] = partdata
	tiltpartdatas1 = tiltpartq1.query(results=1, readimages=False)

	tiltpartq2 = appiondata.ApTiltParticlePairData()
	tiltpartq2['particle2'] = partdata
	tiltpartdatas2 = tiltpartq2.query(results=1, readimages=False)

	if not tiltpartdatas1 and tiltpartdatas2:
		#print "image1"
		otherpart = tiltpartdatas2[0]['particle1']
	elif tiltpartdatas1 and not tiltpartdatas2:
		#print "image2"
		otherpart = tiltpartdatas1[0]['particle2']
	else:
		print partdata
		print tiltpartdatas1
		print tiltpartdatas2
		apDisplay.printError("failed to get tilt pair data")

	### get tilt stack particle
	tiltstackdata = apStack.getOnlyStackData(tiltstackid, msg=False)
	stackpartq = appiondata.ApStackParticleData()
	stackpartq['stack'] = tiltstackdata
	stackpartq['particle'] = otherpart
	stackpartdatas2 = stackpartq.query(results=1, readimages=False)
	if not stackpartdatas2:
		#print otherpart.dbid
		#apDisplay.printError("particle "+str(partnum)+" has no tilt pair in stackid="+str(tiltstackid))
		return None
	stackpartdata = stackpartdatas2[0]

	#print partnum,"-->",stackpartnum
	if time.time()-t0 > 1.0:
		apDisplay.printMsg("long getStackPartTiltPair "+apDisplay.timeString(time.time()-t0))
	return stackpartdata

#===============================
def getTiltTransformFromParticle(partdata):
	t0 = time.time()

	### figure out if its particle 1 or 2
	tiltpartq1 = appiondata.ApTiltParticlePairData()
	tiltpartq1['particle1'] = partdata
	tiltpartdatas1 = tiltpartq1.query(results=1, readimages=False)

	tiltpartq2 = appiondata.ApTiltParticlePairData()
	tiltpartq2['particle2'] = partdata
	tiltpartdatas2 = tiltpartq2.query(results=1, readimages=False)

	if tiltpartdatas1 and not tiltpartdatas2:
		imgnum = 1
		transformdata = tiltpartdatas1[0]['transform']
		otherpartdata = tiltpartdatas1[0]['particle2']
	elif not tiltpartdatas1 and tiltpartdatas2:
		imgnum = 2
		transformdata = tiltpartdatas2[0]['transform']
		otherpartdata = tiltpartdatas2[0]['particle1']
	else:
		print partdata
		print tiltpartdatas1
		print tiltpartdatas2
		apDisplay.printError("failed to get tilt pair data")

	if time.time()-t0 > 1.0:
		apDisplay.printMsg("long getTiltTransFromPart1 "+apDisplay.timeString(time.time()-t0))
	return imgnum, transformdata, otherpartdata

#===============================
def getParticleTiltRotationAngles(stackpartdata):
	partdata = stackpartdata['particle']
	imgnum, transformdata, otherpartdata = getTiltTransformFromParticle(partdata)

	t0 = time.time()
	tiltangle1, tiltangle2 = apDatabase.getTiltAnglesDegFromTransform(transformdata)
	if time.time()-t0 > 1.0:
		apDisplay.printMsg("long angle query "+apDisplay.timeString(time.time()-t0))

	if imgnum == 1 and transformdata['tilt_angle'] < 2:
		### negative case, tilt picker theta < 0
		tiltrot = transformdata['image1_rotation']
		theta = transformdata['tilt_angle']
		notrot   = transformdata['image2_rotation']
		tiltangle = tiltangle1 - tiltangle2
	elif imgnum == 2 and transformdata['tilt_angle'] > -2:
		### positive case, tilt picker theta > 0
		tiltrot = transformdata['image2_rotation']
		theta = transformdata['tilt_angle']
		notrot   = transformdata['image1_rotation']
		tiltangle = tiltangle2 - tiltangle1
	else:
		#no particle pair info was found or some other problem
		print partdata
		apDisplay.printWarning("failed to get tilt pair data or some other problem")
		return None,None,None,None

	if transformdata.timestamp < datetime.datetime(2009, 2, 19, 0, 0, 0):
		### bugfix for switched tilt axis angles, before Feb 19, 2009
		#apDisplay.printWarning("Switching angles")
		temprot = notrot
		notrot = tiltrot
		tiltrot = temprot

	#print "tr=%.2f, th=%.2f, nr=%.2f, tilt=%.2f"%(tiltrot, theta, notrot, tiltangle)
	return tiltrot, theta, notrot, tiltangle


#===============================
def getParticleTiltRotationAnglesOTR(stackpartdata):
	partdata = stackpartdata['particle']
	imgnum, transformdata, otherpartdata = getTiltTransformFromParticle(partdata)

	t0 = time.time()
	tiltangle1, tiltangle2 = apDatabase.getTiltAnglesDegFromTransform(transformdata)
	if time.time()-t0 > 1.0:
		apDisplay.printMsg("long angle query "+apDisplay.timeString(time.time()-t0))

	if imgnum == 1:
		### negative case, tilt picker theta < 0
		tiltrot = transformdata['image1_rotation']
		theta = transformdata['tilt_angle']
		notrot   = transformdata['image2_rotation']
		tiltangle = tiltangle1 - tiltangle2
	elif imgnum == 2:
		### positive case, tilt picker theta > 0
		tiltrot = transformdata['image2_rotation']
		theta = transformdata['tilt_angle']
		notrot   = transformdata['image1_rotation']
		tiltangle = tiltangle2 - tiltangle1
	else:
		#no particle pair info was found or some other problem
		print partdata
		apDisplay.printError("failed to get tilt pair data or some other problem")

	if transformdata.timestamp < datetime.datetime(2009, 2, 19, 0, 0, 0):
		### bugfix for switched tilt axis angles, before Feb 19, 2009
		#apDisplay.printWarning("Switching angles")
		temprot = notrot
		notrot = tiltrot
		tiltrot = temprot

	#print "tr=%.2f, th=%.2f, nr=%.2f, tilt=%.2f"%(tiltrot, theta, notrot, tiltangle)
	return tiltrot, theta, notrot, tiltangle


#===============================
def getTransformImageIds(transformdata):
	t0 = time.time()
	img1 = transformdata.special_getitem('image1', dereference=False).dbid
	img2 = transformdata.special_getitem('image2', dereference=False).dbid
	if time.time()-t0 > 0.3:
		apDisplay.printMsg("long image query "+apDisplay.timeString(time.time()-t0))
	return img1, img2

####
# This is a database connections file with no file functions
# Please keep it this way
####


