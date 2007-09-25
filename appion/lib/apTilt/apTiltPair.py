import numpy
try:
#sinedon
	import sinedon.data as data
#pyami
	import pyami.peakfinder as peakfinder
	import pyami.correlator as correlator
#leginon
	import leginondata
except:
	import data
	import data as leginondata
	import peakfinder
	import correlator
	print "sinedon/pyami not available"

#appion
import appionData
import apDB
import apImage
import apDisplay
import pprint

leginondb = apDB.db
appiondb  = apDB.apdb

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
	sessionq = leginondata.SessionData(name=session)
	presetq=leginondata.PresetData(name=preset)
	imgquery = leginondata.AcquisitionImageData()
	imgquery['preset']  = presetq
	imgquery['session'] = sessionq
	imgtree = leginondb.query(imgquery, readimages=False)
"""

def getTiltPair(imgdata):
	#queries
	#tiltq   = leginondata.TiltSeriesData()
	#presetq = leginondata.PresetData()
	imageq  = leginondata.AcquisitionImageData()
	#tiltq = imgdata['tilt series']
	#pprint.pprint(imgdata['tilt series'])
	#pprint.pprint(imgdata['preset'])
	imageq['tilt series'] = imgdata['tilt series']
	imageq['preset'] = imgdata['preset']
	origid=imgdata.dbid
	alltilts = leginondb.query(imageq, readimages=False)
	tiltpair = None
	if len(alltilts) > 1:
		#could be multiple tiltpairs but we are taking only the most recent
		for tilt in alltilts:
			if tilt.dbid != origid:
				tiltpair = tilt
				break
	return tiltpair

def tiltPickerToDbNames(tiltparams):
	#('dbemdata|AcquisitionImageData|image1', int),
	#('dbemdata|AcquisitionImageData|image2', int),
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
	return newdict

def insertTiltTransform(imgdata1, imgdata2, tiltparams, params):
	#First we need to sort imgdata
	#'07aug30b_a_00013gr_00010sq_v01_00002sq_v01_00016en_00'
	#'07aug30b_a_00013gr_00010sq_v01_00002sq_01_00016en_01'
	#last two digits confer order, but then the transform changes...

	### first find the runid
	runq = appionData.ApSelectionRunData()
	runq['name'] = params['runid']
	runq['dbemdata|SessionData|session'] = imgdata1['session'].dbid
	runids=appiondb.query(runq, results=1)
	if not runids:
		apDisplay.printError("could not find runid in database")

	### the order is specified by 1,2; so don't change it let makestack figure it out
	for imgdata in (imgdata1, imgdata2):
		for index in ("1","2"):
			transq = appionData.ApImageTiltTransformData()
			transq["dbemdata|AcquisitionImageData|image"+index] = imgdata.dbid
			transq['tiltrun'] = runids[0]
			transdata = appiondb.query(transq)
			if transdata:
				apDisplay.printWarning("Transform values already in database for "+imgdata['filename'])
				return transdata[0]

	### prepare the insertion
	transq = appionData.ApImageTiltTransformData()
	transq['dbemdata|AcquisitionImageData|image1'] = imgdata1.dbid
	transq['dbemdata|AcquisitionImageData|image2'] = imgdata2.dbid
	transq['tiltrun'] = runids[0]
	dbdict = tiltPickerToDbNames(tiltparams)
	if dbdict is None:
		return None
	#Can I do for key in appionData.ApImageTiltTransformData() ro transq???
	for key in ('image1_x','image1_y','image1_rotation','image2_x','image2_y','image2_rotation','scale_factor','tilt_angle'):
		if key not in dbdict:
			apDisplay.printError("Key: "+key+" was not found in transformation data")

	for i,v in dbdict.items():
		transq[i] = v
		#print i,v

	apDisplay.printMsg("Inserting transform beteween "+apDisplay.short(imgdata1['filename'])+\
		" and "+apDisplay.short(imgdata2['filename'])+" into database")
	appiondb.insert(transq)
	return transq



