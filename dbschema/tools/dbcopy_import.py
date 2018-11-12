import sys
import sinedon
import sinedon.importdata
from leginon import leginondata
from leginon import projectdata
import time

'''
This is an example for copying a session from one database to another.
DEF_id will be reassigned. The values in the followings need to be
specified.
'''
# set direct_query values
dbhost = 'localhost'
# both source and destination need to allow the same sinedon.cfg
# access as specified.  Also need importdata module specified in
# sinedon.cfg.  Note that importdata can be set to either source or
# destination dbname
source_dbname = 'old_leginondb'
destination_dbname = 'new_leginondb'
# source session name.  The rest of the info comes from source_dbname
source_sessionname = '18nov12a'
# destination session info.  Need to specify all typical info
destination_sessionname = '18nov12dbcopy_test'
imagepath = '/ImageStorage/leginon/18nov12dbcopy_test/rawdata'
newcomment = 'dbcopy test'
# associate the new session to a project in the projectdata in sinedon.cfg
projectid = 1
# associate the new session with a user and group.
username = 'dbcopy'
userfirstname = 'Unique'
userlastname = 'User'
# group 4 is typically the user group.
newgroupid = 4

# DO NOT CHANGE AFTER THIS.

'''
q = sinedon.importdata.ImportDBConfigData(host=dbhost,db=source_dbname)
r = q.query()
if r:
	source_importdb = r[0]
else:
	q.insert()
	source_importdb = q
q = sinedon.importdata.ImportDBConfigData(host=dbhost,db = destination_dbname)
r = q.query()
if r:
	destination_importdb = r[0]
else:
	q.insert()
	destination_importdb = q
'''
def research(q,most_recent=False):
	sinedon.setConfig('leginondata', db=source_dbname)
	if most_recent:
		r = q.query(results=1)
		if r:
			return r[0]
	else:
		r = q.query()
		r.reverse()
	return r

def researchcal(q,source_session):
	sinedon.setConfig('leginondata', db=source_dbname)
	r = q.query()
	if len(r) > 2:
		r =keepOnesInAndOneBeforeSession(r,source_session)
	r.reverse()
	print 'found %d calibration for class %s' % (len(r), q.__class__.__name__)
	return r

def researchsettings(q,source_session):
	sinedon.setConfig('leginondata', db=source_dbname)
	r = q.query()
	r =keepOnesInAndOneBeforeByUser(r,source_session)
	r.reverse()
	return r

def publish(results):
	sinedon.setConfig('leginondata', db=destination_dbname)
	for q in results:
		q.insert()

def replaceItem(data,key,value):
	if data.has_key(key):
		data.__setitem__(key, value, force=True)

def keepOnesInAndOneBeforeSession(datalist,source_session):
	sinedon.setConfig('leginondata', db=source_dbname)
	newlist = []
	for data in datalist:
		if 'session' in data.keys() and data['session'].dbid == source_session.dbid:
			newlist.append(data)
		else:
			if data.timestamp < source_session.timestamp:
				newlist.append(data)
				break
	if not newlist:
		newlist = keepOnesInAndOneBeforeByUser(datalist,source_session)
	return newlist

def keepOnesInAndOneBeforeByUser(datalist,source_session):
	sinedon.setConfig('leginondata', db=source_dbname)
	newlist = []
	found_by_user = False
	for data in datalist:
		if 'session' in data.keys():
			if data['session'].dbid == source_session.dbid:
				newlist.append(data)
			else:
				if data.timestamp < source_session.timestamp and data['session']['user'].dbid == source_session['user'].dbid:
					newlist.append(data)
					found_by_user = True
					break
		else:
			print "Error: not an insession class"
	if found_by_user == False:
		for data in datalist:
			if 'session' in data.keys():
				if data.timestamp < source_session.timestamp and data['session']['user']['username'] == 'administrator':
					replaceItem(data,'isdefault',False)
					newlist.append(data)
					break
	return newlist

def getSource_session():
	sinedon.setConfig('leginondata', db=source_dbname)
	q = leginondata.SessionData(name=source_sessionname)
	session = research(q,most_recent=True)
	return session

def importSession(imagepath=''):
	print "Importing session...."
	sinedon.setConfig('leginondata', db=source_dbname)
	q = leginondata.SessionData(name=source_sessionname)
	session = research(q,most_recent=True)
	q = leginondata.SessionData()
	source_sessiondata = q.direct_query(session.dbid)
	if imagepath:
		replaceItem(session,'image path',imagepath)
	replaceItem(session,'name',destination_sessionname)
	if newcomment:
		replaceItem(session,'comment',newcomment)


	user = session['user']
	replaceItem(user,'username',username)
	replaceItem(user,'firstname',userfirstname)
	replaceItem(user,'lasttname',userlastname)

	sinedon.setConfig('leginondata', db=destination_dbname)
	groupq = leginondata.GroupData()
	newgroup = groupq.direct_query(newgroupid)
	replaceItem(user,'group',newgroup)
	user.insert()
	
	session.insert()
	q = leginondata.SessionData()
	sessiondata = q.direct_query(session.dbid)

	if not sessiondata:
		print "Empty ImportMapping table of previous import before importing as anoter session"
		sys.exit(1)
	#projectexperiment
	newq = projectdata.projects()
	project = newq.direct_query(projectid)
	newq = projectdata.projectexperiments(session=session,project=project)
	newq.insert()

	# Map all sessions, users, groups to newly created session's value 
	# so that new sessions etc. won't be created from recursive insert
	# project|privileges is not needed, probably a bug in disgise
	sinedon.setConfig('leginondata', db=source_dbname)
	q = leginondata.SessionData()
	sessions = q.query()
	sinedon.setConfig('leginondata', db=destination_dbname)
	for old_session in sessions:
		old_session.copyImportMapping(session)
	return source_sessiondata, sessiondata

def importInstrument():
	source_session = getSource_session()
	print "Importing instrument...."
	# guess instrument from the last image
	sinedon.setConfig('leginondata', db=source_dbname)
	q = leginondata.AcquisitionImageData(session=source_session)
	last_image = research(q,True)
	tem = last_image['scope']['tem']
	camera = last_image['camera']['ccdcamera']
	high_tension = last_image['scope']['high tension']
	q = leginondata.InstrumentData()
	source_temdata = q.direct_query(tem.dbid)
	source_cameradata = q.direct_query(camera.dbid)

	sinedon.setConfig('leginondata', db=destination_dbname)
	tem.insert()
	camera.insert()
	return source_cameradata, source_temdata, high_tension

def importCalibrations(source_cam, source_tem,high_tension):
	source_session = getSource_session()
	print "Importing calibrations...."
	sinedon.setConfig('leginondata', db=source_dbname)
	#magnifications
	q = leginondata.MagnificationsData(instrument=source_tem)
	mags = q.query()
	if mags:
		magnifications = mags[0]['magnifications']
		print "Found magnifications"
		#projection submode mapping
		q = leginondata.ProjectionSubModeMappingData()
		q['magnification list']=mags[0]
		submodes = q.query()
		print '%d Submodes found' % (len(submodes))
	else:
		print "Did not Find magnifications for %d" % (source_tem.dbid)
		# simulator magnifications
		magnifications=[50,100,500,1000,5000,25000,50000]
		submodes = None
	
	#camera sensitivity calibrations
	q = leginondata.CameraSensitivityCalibrationData(tem=source_tem,ccdcamera=source_cam)
	q['high tension'] = high_tension
	senses = researchcal(q,source_session)

	#Modeled Stage calibrations
	model = {}
	for axis in ('x','y'):
		q = leginondata.StageModelCalibrationData(tem=source_tem,ccdcamera=source_cam,axis=axis)
		model[axis] = researchcal(q,source_session)

	pixel = {}
	matrix = {}
	modelmag = {}
	ucenter = {}
	rcenter = {}
	for mag in magnifications:
		#pixelsize calibrations
		q = leginondata.PixelSizeCalibrationData(tem=source_tem,ccdcamera=source_cam,magnification=mag)
		pixel[mag] = researchcal(q,source_session)
		#matrix calibrations
		matrix[mag] = {}
		for matrixtype in ('image shift','stage position','defocus','stigx','stigy','beam shift','beam-tilt coma','image-shift coma','image-shift stig', 'image-shift defocus'):
			q = leginondata.MatrixCalibrationData(tem=source_tem,ccdcamera=source_cam,magnification=mag,type=matrixtype)
			q['high tension'] = high_tension
			matrix[mag][matrixtype] = researchcal(q,source_session)

		#Modeled Mag Stage calibrations
		modelmag[mag]={}
		for axis in ('x','y'):
			q = leginondata.StageModelMagCalibrationData(tem=source_tem,ccdcamera=source_cam,magnification=mag,axis=axis)
			q['high tension'] = high_tension
			modelmag[mag][axis] = researchcal(q,source_session)

		#eucenter focus calibrations
		ucenter[mag]={}
		q = leginondata.EucentricFocusData(tem=source_tem,magnification=mag)
		ucenter[mag] = researchcal(q,source_session)

		#eucenter focus calibrations
		rcenter[mag]={}
		q = leginondata.RotationCenterData(tem=source_tem,magnification=mag)
		rcenter[mag] = researchcal(q,source_session)

	sinedon.setConfig('leginondata', db=destination_dbname)
	#magnifications
	if mags:
		for m in mags:
			m.insert()
	else:
		# simulator magnifications
		magdata=leginondata.MagnificationsData()
		magdata['magnifications']=[50,100,500,1000,5000,25000,50000]
	# projection submode mappings
	if submodes:
		for s in submodes:
			s.insert()

	#camera sensitivity calibrations
	for sense in senses:
		sense.insert()
	#Modeled Stage calibrations
	for axis in ('x','y'):
		if model[axis]:
			for m in model[axis]:
				m.insert()

	for mag in magnifications:
		#pixelsize calibrations
		if pixel[mag]:
			for p in pixel[mag]:
				p.insert()
		#matrix calibrations
		for matrixtype in ('image shift','stage position','defocus','stigx','stigy','beam shift','beam-tilt coma','image-shift coma','image-shift stig', 'image-shift defocus'):
			if matrix[mag][matrixtype]:
				for m in matrix[mag][matrixtype]:
					m.insert()
		#Modeled Mag Stage calibrations
		for axis in ('x','y'):
			if modelmag[mag][axis]:
				for m in modelmag[mag][axis]:
					m.insert()

		#eucentric focus
		if ucenter[mag]:
			for u in ucenter[mag]:
				u.insert()

		#rotation center
		if rcenter[mag]:
			for r in rcenter[mag]:
				r.insert()

def importQueue():
	source_session = getSource_session()
	print "Importing queuing...."
	sinedon.setConfig('leginondata', db=source_dbname)
	q = leginondata.QueueData(session=source_session)
	r = q.query()
	r.reverse()

	sinedon.setConfig('leginondata', db=destination_dbname)
	for queue in r:
		queue.insert()

def importDeQueue():
	source_session = getSource_session()
	# ImageTargetLists that have no targets on will also be imported in this function
	print "Importing dequeuing...."
	sinedon.setConfig('leginondata', db=source_dbname)
	q = leginondata.DequeuedImageTargetListData(session=source_session)
	r = q.query()
	r.reverse()

	sinedon.setConfig('leginondata', db=destination_dbname)
	for queue in r:
		queue.insert()

def importImageComment():
	source_session = getSource_session()
	print "Importing image comments...."
	sinedon.setConfig('leginondata', db=source_dbname)
	q = leginondata.ImageCommentData(session=source_session)
	r = q.query()
	r.reverse()

	sinedon.setConfig('leginondata', db=destination_dbname)
	for stats in r:
		stats.insert()

def importImageStats():
	source_session = getSource_session()
	print "Importing image stats...."
	sinedon.setConfig('leginondata', db=source_dbname)
	q = leginondata.AcquisitionImageStatsData(session=source_session)
	r = q.query()
	r.reverse()

	sinedon.setConfig('leginondata', db=destination_dbname)
	for stats in r:
		stats.insert()

def importMosaicTiles():
	source_session = getSource_session()
	print "Importing mosaic tiles...."
	sinedon.setConfig('leginondata', db=source_dbname)
	q = leginondata.MosaicTileData(session=source_session)
	r = q.query()
	r.reverse()

	sinedon.setConfig('leginondata', db=destination_dbname)
	for tiles in r:
		tiles.insert()

def importDrifts():
	source_session = getSource_session()
	print "Importing drift...."
	sinedon.setConfig('leginondata', db=source_dbname)
	q = leginondata.DriftData(session=source_session)
	drifts = q.query()
	drifts.reverse()

	allmonitors = []
	# driftmonitor result has no session
	for source_drift in drifts:
		q = leginondata.DriftMonitorResultData(final=source_drift)
		monitors = q.query()
		monitors.reverse()
		allmonitors.extend(monitors)

	sinedon.setConfig('leginondata', db=destination_dbname)
	for drift in drifts:
		drift.insert()
	for monitor in allmonitors:
		monitor.insert()

def importFocus():
	source_session = getSource_session()
	print "Importing focus results...."
	sinedon.setConfig('leginondata', db=source_dbname)
	qfocus = leginondata.FocuserResultData(session=source_session)
	focii = qfocus.query()
	focii.reverse()

	sinedon.setConfig('leginondata', db=destination_dbname)
	for focus in focii:
		focus.insert()

def findBrightImageFromNorm(normdata):
	sinedon.setConfig('leginondata', db=source_dbname)
	timestamp = normdata.timestamp
	normcam = normdata['camera']
	qcam = leginondata.CameraEMData(dimension=normcam['dimension'],
			offset=normcam['offset'], binning=normcam['binning'],
			ccdcamera=normcam['ccdcamera'])
	qcam['exposure type'] = 'normal'
	qcam['energy filtered'] = normcam['energy filtered']

	normscope = normdata['scope']
	qscope = leginondata.ScopeEMData(tem=normscope['tem'])
	qscope['high tension'] = normscope['high tension']
	q = leginondata.BrightImageData(camera=qcam,scope=qscope,channel=normdata['channel'])
	brightlist = q.query()
	for brightdata in brightlist:
		if brightdata.timestamp < timestamp:
			break
	return brightdata

def importBrightImages(destination_session):
	sinedon.setConfig('leginondata', db=destination_dbname)
	q = leginondata.NormImageData(session=destination_session)
	r = q.query()
	allbrights = []
	for normdata in r:
		allbrights.append(findBrightImageFromNorm(normdata))
	sinedon.setConfig('leginondata', db=destination_dbname)
	for bright in allbrights:
		if bright:
			bright.insert()

def importByTargets():
	source_session = getSource_session()
	print "Importing targets...."
	sinedon.setConfig('leginondata', db=source_dbname)
	q = leginondata.AcquisitionImageTargetData(session=source_session)
	targets = q.query()
	targets.reverse()

	print 'number of targets = %d' % len(targets)
	for target in targets:
		sinedon.setConfig('leginondata', db=source_dbname)
		q = leginondata.AcquisitionImageData(target=target)
		images = q.query()
		images.reverse()
		targetlist = {}
		for image in images:
			q = leginondata.ImageTargetListData(image=image)
			targetlist[image.dbid] = research(q,True)

		sinedon.setConfig('leginondata', db=destination_dbname)
		for image in images:
			imageid = image.dbid
			image.insert()
			if targetlist[imageid]:
				targetlist[imageid].insert()
		target.insert()
		print 'imported target %d' % target.dbid

def importSettings():
	source_session = getSource_session()
	q = leginondata.LaunchedApplicationData(session=source_session)
	results = research(q)
	applications = {}
	for launchedapp in results:
		if launchedapp['application'].dbid not in applications.keys():
			applications[launchedapp['application'].dbid] = launchedapp['application']
		sinedon.setConfig('leginondata', db=destination_dbname)
		q = leginondata.ApplicationData(name=launchedapp['application']['name'])
		r = q.query(results=1)
		new_app = r[0]
		replaceItem(launchedapp,'application',new_app)
	publish(results)	
	allalias = {}
	for application in applications.values():
		q = leginondata.NodeSpecData(application=application)
		results = research(q)
		for r in results:
			if r['class string'] not in allalias.keys():
				allalias[r['class string']] = []
			allalias[r['class string']].append(r['alias'])
	# import settings
	# for some reason the session is pointed to destination after this if not mapped
	source_session = getSource_session()
	print 'importing AcquisitionSettings....'
	for node_name in (allalias['Acquisition']):
		q = leginondata.AcquisitionSettingsData(name=node_name)
		results = researchsettings(q,source_session)
		publish(results)
	print 'importing FocuserSettings....'
	for node_name in (allalias['Focuser']):
		q = leginondata.FocuserSettingsData(name=node_name)
		results = researchsettings(q,source_session)
		publish(results)
	sequence_names = []
	for node_name in (allalias['Focuser']):
		q = leginondata.FocusSequenceData()
		q['node name'] = node_name
		results = researchsettings(q,source_session)
		publish(results)
		for r in results:
			sequence = r['sequence']
			for s in sequence:
				if s not in sequence_names:
					sequence_names.append(s)
	for node_name in (allalias['Focuser']):
		for seq_name in sequence_names:
			q = leginondata.FocusSettingData(name=seq_name)
			q['node name'] = node_name
			results = researchsettings(q,source_session)
			publish(results)
	print 'importing JAHCFinder Settings....'
	for node_name in (allalias['JAHCFinder']):
		q = leginondata.JAHCFinderSettingsData(name=node_name)
		results = researchsettings(q,source_session)
		publish(results)
	print 'importing JAHCFinderPrefs of images....'
	q = leginondata.HoleFinderPrefsData(session=source_session)
	results = research(q)
	publish(results)
	print 'importing Other MSI-T Settings....'
	q = leginondata.MosaicClickTargetFinderSettingsData(name='Square Targeting')
	results = researchsettings(q,source_session)
	publish(results)
	q = leginondata.MosaicTargetMakerSettingsData(name='Grid Targeting')
	results = researchsettings(q,source_session)
	publish(results)
	q = leginondata.PresetsManagerSettingsData(name='Presets Manager')
	results = researchsettings(q,source_session)
	publish(results)
	q = leginondata.CorrectorSettingsData(name='Correction')
	results = researchsettings(q,source_session)
	publish(results)
	q = leginondata.TransformManagerSettingsData(name='Target Adjustment')
	results = researchsettings(q,source_session)
	publish(results)
	q = leginondata.DriftManagerSettingsData(name='Drift Monitor')
	results = researchsettings(q,source_session)
	publish(results)
	q = leginondata.NavigatorSettingsData(name='Navigation')
	results = researchsettings(q,source_session)
	publish(results)
	q = leginondata.DriftManagerSettingsData(name='Fix Beam')
	results = researchsettings(q,source_session)
	publish(results)
	q = leginondata.BeamTiltCalibratorSettingsData(name='Beam Tilt')
	results = researchsettings(q,source_session)
	publish(results)

def importViewerImageStatus():
	source_session = getSource_session()
	print "Importing ViewerImageStatus...."
	q = leginondata.ViewerImageStatus(session=source_session)
	results = research(q)
	publish(results)

def importIceThickness():
	source_session = getSource_session()
	print "Importing HoleStats...."
	q = leginondata.HoleStatsData(session=source_session)
	results = research(q)
	publish(results)

source_session, destination_session = importSession(imagepath)
source_cam, source_tem,high_tension = importInstrument()
importCalibrations(source_cam,source_tem,high_tension)
importQueue()
importByTargets()
importImageStats()
importImageComment()
importMosaicTiles()
importDeQueue()
importDrifts()
importFocus()
importBrightImages(destination_session)
#importSettings()
importViewerImageStatus()
importIceThickness()
