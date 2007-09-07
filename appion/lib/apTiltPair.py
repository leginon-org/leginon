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

def tiltPickerToDbNames(**kwargs):
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
	if 'theta' in kwargs:
		newdict['tilt'] = kwargs['theta']
	if 'gamma' in kwargs:
		newdict['image1_rotation'] = kwargs['gamma']
	if 'phi' in kwargs:
		newdict['image2_rotation'] = kwargs['phi']
	if 'scale' in kwargs:
		newdict['scale'] = kwargs['scale']
	if 'shiftx' in kwargs:
		newdict['shiftx'] = kwargs['shiftx']
	if 'shifty' in kwargs:
		newdict['shifty'] = kwargs['shifty']



def insertTransform(imgdata1, imgdata2, **kwargs):
	#First we need to sort imgdata
	#'07aug30b_a_00013gr_00010sq_v01_00002sq_v01_00016en_00'
	#'07aug30b_a_00013gr_00010sq_v01_00002sq_01_00016en_01'
	#last two digits confer order, but then the transform changes...

	for imgdata in (imgdata1, imgdata2):
		for index in ("1","2"):
			transq = appionData.ApImageTransformationData()
			transq["dbemdata|AcquisitionImageData|image"+index] = imgdata.dbid
			transdata = appiondb.query(transq)
			if transdata:
				apDisplay.printWarning("Transform values already in database for "+imgdata['filename'])
				return False
	transq['dbemdata|AcquisitionImageData|image1'] = imgdata1.dbid
	transq['dbemdata|AcquisitionImageData|image2'] = imgdata2.dbid
	transq = appionData.ApImageTransformationData()
	for i in kwargs:
		print i
		transq[i]=kwargs[i]
	apDisplay.printMsg("Inserting shift beteween "+apDisplay.short(imgdata1['filename'])+\
		" and "+apDisplay.short(imgdata2['filename'])+" into database")
	#appiondb.insert(transq)
	return



