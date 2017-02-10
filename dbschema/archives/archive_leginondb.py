import os
import sys
import sinedon
from sinedon import dbconfig
from leginon import leginondata
from leginon import projectdata
from leginon import correctorclient
import time

# exclude preset label
exclude_preset_list = []

# exclude session name
exclude_session_list = []

# archive only session in and after this year
YEAR = 1999

# skip checking sessions probably archived.
# Do not turn this option on unless you know what you are doing
SKIP_ARCHIVED = False

def checkSinedon():
	try:
		destination_dbinfo = dbconfig.getConfig('importdata')
	except KeyError:
		print "Please define impordata module in sinedon.cfg"
		sys.exit(1)
	if not hasattr(sinedon.dbdatakeeper.DBDataKeeper,'initImported'):
		print "sinedon must be imported from myami-dbcopy branch"
		print "currently from %s",sinedon.__file__
		sys.exit(1)

class Archiver(object):
	def __init__(self):
		self.status = True # initialize status to o.k.
		source_dbinfo = dbconfig.getConfig('leginondata')
		destination_dbinfo = dbconfig.getConfig('importdata')
		if source_dbinfo['host'] != destination_dbinfo['host']:
			self.escape('leginondata and importdata not on the same host')
		self.dbhost = source_dbinfo['host']
		self.source_dbname = source_dbinfo['db']
		self.destination_dbname = destination_dbinfo['db']
		self.imageids = []

	def isStatusGood(self):
		return self.status

	def escape(self,msg=''):
		print msg
		self.reset()
		self.status = False

	def reset(self):
		'''
		reset configuration to source db to avoid confusion
		'''
		sinedon.setConfig('leginondata', db=self.source_dbname)

	def research(self,q,most_recent=False):
		'''
		Query results from source database. Sorted by entry time. Oldest fist
		'''
		# configuration must be set before any query
		sinedon.setConfig('leginondata', db=self.source_dbname)
		if most_recent:
			r = q.query(results=1)
			if r:
				return r[0]
		else:
			r = q.query()
			r.reverse()
		return r

	def publish(self,results):
		'''
		Publish query results to destination database.
		'''
		if not results:
			return
		# configuration must be set before any query
		sinedon.setConfig('leginondata', db=self.destination_dbname)
		for q in results:
			q.insert(archive=True)
		self.reset()

	def replaceItem(self,data,key,value):
		if data.has_key(key):
			data.__setitem__(key, value, force=True)

	def avoidExcludedImage(self,fulllist):
		shortlist = []
		for data in fulllist:
			if data['image'] and data['image']['label'] and data['image']['label'] in exclude_preset_list:
				continue
			else:
				shortlist.append(data)
		return shortlist

	def findBrightImageFromNorm(self,normdata):
		'''
		Find BrighetImageData based on imported NormImageData.
		This is needed for older data since BrightImageData was
		not linked to AcquisitionImages previously.
		'''
		if normdata['bright']:
			return normdata['bright']
		sinedon.setConfig('leginondata', db=self.source_dbname)
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

	def makequery(self,classname,kwargs):
		'''
		Make SQL query of leginondata from class name and keyword arguments.
		'''
		q = getattr(leginondata,classname)()
		for key in kwargs.keys():
			# leginondata keys never contains '_'
			realkey = key.replace('_',' ')
			q[realkey] = kwargs[key]
		return q

	def makeTimeStringFromTimeStamp(self,timestamp):
		t = timestamp
		return '%04d%02d%02d%02d%02d%02d' % (t.year,t.month,t.day,t.hour,t.minute,t.second)

class UserArchiver(Archiver):
	def __init__(self,projectid):
		super(UserArchiver,self).__init__()
		self.projectid = projectid

	def getEssentialUsers(self):
		'''
		EssentialUsers are those who are owners or need to share exeperiment with
		and the administrator who is needed if settings is to be restored.
		A file of the list is saved while using normal sinedon and now needs to
		be imported to the destination leginon database.
		'''
		useridfile = 'archive_users_%d.cfg' % (self.projectid,)
		if os.path.isfile(useridfile):
			f = open(useridfile,'r')
			lines = f.readlines()
			f.close()
			return map((lambda x: int(x)),lines)
		else:
			return []

	def run(self):
		userids = self.getEssentialUsers()
		for id in userids:
			sinedon.setConfig('leginondata', db=self.source_dbname)
			print 'querying user %d' % id
			userdata = leginondata.UserData().direct_query(id)
			self.publish([userdata,])

class SessionArchiver(Archiver):
	'''
	Archive a Session identified by session name
	'''
	def __init__(self,sessionname):
		super(SessionArchiver,self).__init__()
		self.sessionname = sessionname
		self.setSourceSession(sessionname)
		self.setDestinationSession(sessionname)
		self.bad_settings_class = []

	def isSessionInArchive(self):
		destination_session = self.getDestinationSession()
		if destination_session is None and self.sessionname not in exclude_session_list:
			return False
		else:
			return True

	def hasImagesInSession(self):
		source_session = self.getSourceSession()
		sinedon.setConfig('leginondata', db=self.source_dbname)
		images = leginondata.AcquisitionImageData(session=source_session).query()
		return bool(images)

	def researchCalibration(self, classname, **kwargs):
		'''
		Find calibration that may be used by the source session.
		This could be those in the session or the last one in a previous
		session.
		'''
		source_session = self.getSourceSession()
		sinedon.setConfig('leginondata', db=self.source_dbname)
		# search in the session
		q = self.makequery(classname,kwargs)
		q['session'] = source_session
		r1 = q.query()
		# seartch for one before session started
		q = self.makequery(classname,kwargs)
		t = source_session.timestamp
		sessiontime = self.makeTimeStringFromTimeStamp(t)
		r2 = q.query(results=1,timelimit='19000000000000\t%s' % (sessiontime,))
		if r2:
			r1.append(r2[0])
		r1.reverse()
		return r1

	def researchSettings(self, classname,**kwargs):
		'''
		Find Legion Settings that may be used by the source session.
		This could be those in the session or the last one in a previous
		session by the user.
		'''
		source_session = self.getSourceSession()
		t = source_session.timestamp
		sessiontime = self.makeTimeStringFromTimeStamp(t)
		# search in the session
		q = self.makequery(classname,kwargs)
		q['session'] = source_session
		r1 = q.query()
		# search by user
		found_by_user = False
		# query session again since for some reason it is mapped to destination
		source_session = self.getSourceSession()
		if source_session['user'] and source_session.dbid:
			sessionq = leginondata.SessionData(user=source_session['user'])
			q = self.makequery(classname,kwargs)
			q['session'] = sessionq
			r2 = q.query(results=1,timelimit='19000000000000\t%s' % (sessiontime,))
			if r2:
				r1.append(r2[0])
				found_by_user = True
		# search by isdefault
		if found_by_user == False:
			q = self.makequery(classname,kwargs)
			q['isdefault'] = True
			r2 = q.query(results=1,timelimit='19000000000000\tsessiontime')
			if r2:
				r1.append(r2[0])

		r1.reverse()
		return r1

	def setSourceSession(self, sessionname):
		sinedon.setConfig('leginondata', db=self.source_dbname)
		q = leginondata.SessionData(name=sessionname)
		self.source_session = self.research(q,most_recent=True)

	def getSourceSession(self):
		'''
		Get Source Session data reference.
		'''
		#This redo the query since the reference often get mapped to
		#the destination database for unknown reason after some queries.
		self.setSourceSession(self.sessionname)
		return self.source_session

	def setDestinationSession(self, sessionname):
		self.destination_session = None
		sinedon.setConfig('leginondata', db=self.destination_dbname)
		q = leginondata.SessionData(name=sessionname)
		r = q.query()
		if r:
			session = r[0]
			self.destination_session = session
		self.reset()

	def getDestinationSession(self):
		'''
		Get Destination Session data reference.
		'''
		# Redo query for the same reason as in getSourceSession
		self.setDestinationSession(self.sessionname)
		return self.destination_session

	def importSession(self, comment=''):
		print "Importing session...."
		session = self.getSourceSession()
		source_sessionid = session.dbid
		# change session description if needed
		if comment:
			self.replaceItem(session,'comment',comment)

		sinedon.setConfig('leginondata', db=self.destination_dbname)
		session.insert(force=False,archive=True)
		q = leginondata.SessionData()
		sessiondata = q.direct_query(session.dbid)

		if not sessiondata:
			self.escape("Session Not Inserted Successfully")
			return
		self.setDestinationSession(sessiondata)

	def importSessionDependentData(self,dataclassname):
		source_session = self.getSourceSession()
		print "Importing %s...." % (dataclassname[:-4])
		q = getattr(leginondata,dataclassname)(session=source_session)
		results = self.research(q)
		self.publish(results)

	def importInstrument(self):
		print "Importing instrument...."
		self.is_upload = False
		# guess instrument from the last image
		sinedon.setConfig('leginondata', db=self.source_dbname)
		q = leginondata.AcquisitionImageData(session=self.getSourceSession())
		last_image = self.research(q,True)
		# we know there are images for the session.
		tem = last_image['scope']['tem']
		camera = last_image['camera']['ccdcamera']
		if tem is None:
			# old uploaded session such as 12jun29b
			self.is_upload = True
			return None, None, 200000

		high_tension = last_image['scope']['high tension']
		q = leginondata.InstrumentData()
		source_temdata = q.direct_query(tem.dbid)
		source_cameradata = q.direct_query(camera.dbid)

		if 'appion' in source_temdata['name'].lower():
			self.is_upload = True

		sinedon.setConfig('leginondata', db=self.destination_dbname)
		tem.insert(archive=True)
		camera.insert(archive=True)

		return source_cameradata, source_temdata, high_tension

	def importGainReferences(self):
		print "Importing GainReferences...."
		q = leginondata.AcquisitionImageData(session=self.getSourceSession())
		images = self.research(q,False)
		c_client = correctorclient.CorrectorClient()
		norm_ids = []
		for image in images:
			if image['norm'] and image['norm'].dbid not in norm_ids:
				norm_ids.append(image['norm'].dbid)
				# also archive alternative channel
				altnorm = c_client.getAlternativeChannelNorm(image['norm'])
				if altnorm and altnorm.dbid not in norm_ids:
					norm_ids.append(altnorm.dbid)
		# ascending sort
		norm_ids.sort()
		norms = []
		for dbid in norm_ids:
			norms.append(leginondata.NormImageData.direct_query(dbid))
		sinedon.setConfig('leginondata', db=self.destination_dbname)
		for norm in norms:
			if norm:
				norm.insert(archive=True)
				if norm['dark']:
					norm['dark'].insert(archive=True)

	def importCalibrations(self, source_cam, source_tem,high_tension):
		print "Importing calibrations...."

		simumags = [50,100,500,1000,5000,25000,50000]
		matrixtypes = ('image shift','stage position','defocus','stigx','stigy','beam shift','beam-tilt coma','image-shift coma')
		sinedon.setConfig('leginondata', db=self.source_dbname)

		#magnifications
		# magnifications is not insession data
		mags = leginondata.MagnificationsData(instrument=source_tem).query(results=1)
		if mags:
			magnifications = mags[0]['magnifications']
		else:
			# simulator magnifications
			magnifications = simumags

		#camera sensitivity calibrations
		senses = self.researchCalibration('CameraSensitivityCalibrationData',tem=source_tem,ccdcamera=source_cam,high_tension=high_tension)

		#beam size calibrations
		beamsizes = []
		for probe in ('micro','nano'):
			beamsizes.extend(self.researchCalibration('BeamSizeCalibrationData',tem=source_tem,probe_mode=probe))

		#Modeled Stage calibrations
		model = {}
		for axis in ('x','y'):
			model[axis] = self.researchCalibration('StageModelCalibrationData',tem=source_tem,ccdcamera=source_cam,axis=axis)

		pixel = {}
		matrix = {}
		modelmag = {}
		ucenter = {}
		rcenter = {}
		for mag in magnifications:
			#pixelsize calibrations
			q = leginondata.PixelSizeCalibrationData(tem=source_tem,ccdcamera=source_cam,magnification=mag)
			pixel[mag] = self.researchCalibration('PixelSizeCalibrationData',tem=source_tem,ccdcamera=source_cam,magnification=mag)

			#matrix calibrations
			matrix[mag] = {}
			for matrixtype in matrixtypes:
				matrix[mag][matrixtype] = self.researchCalibration('MatrixCalibrationData',tem=source_tem,ccdcamera=source_cam,magnification=mag,type=matrixtype,high_tension=high_tension)

			#Modeled Mag Stage calibrations
			modelmag[mag]={}
			for axis in ('x','y'):
				modelmag[mag][axis] = self.researchCalibration('StageModelMagCalibrationData',tem=source_tem,ccdcamera=source_cam,magnification=mag,axis=axis,high_tension=high_tension)

			#eucenter focus calibrations
			ucenter[mag]={}
			ucenter[mag] = self.researchCalibration('EucentricFocusData',tem=source_tem,magnification=mag)

			#eucenter focus calibrations
			rcenter[mag]={}
			rcenter[mag] = self.researchCalibration('RotationCenterData',tem=source_tem,magnification=mag)

		sinedon.setConfig('leginondata', db=self.destination_dbname)
		#magnifications
		for m in mags:
			m.insert(archive=True)
		#camera sensitivity calibrations
		for sense in senses:
			sense.insert(archive=True)
		#beam size calibrations
		for beamsize in beamsizes:
			beamsize.insert(archive=True)
		#Modeled Stage calibrations
		for axis in ('x','y'):
			if model[axis]:
				for m in model[axis]:
					m.insert(archive=True)

		for mag in magnifications:
			#pixelsize calibrations
			if pixel[mag]:
				for p in pixel[mag]:
					p.insert(archive=True)
			#matrix calibrations
			for matrixtype in matrixtypes:
				if matrix[mag][matrixtype]:
					for m in matrix[mag][matrixtype]:
						m.insert(archive=True)
			#Modeled Mag Stage calibrations
			for axis in ('x','y'):
				if modelmag[mag][axis]:
					for m in modelmag[mag][axis]:
						m.insert(archive=True)

			#eucentric focus
			if ucenter[mag]:
				for u in ucenter[mag]:
					u.insert(archive=True)

			#rotation center
			if rcenter[mag]:
				for r in rcenter[mag]:
					r.insert(archive=True)

	def importC2ApertureSize(self):
		self.importSessionDependentData('C2ApertureSizeData')

	def importQueue(self):
		source_session = self.getSourceSession()
		print "Importing queuing...."
		sinedon.setConfig('leginondata', db=self.source_dbname)
		q = leginondata.QueueData(session=source_session)
		r = q.query()
		r.reverse()

		sinedon.setConfig('leginondata', db=self.destination_dbname)
		for queue in r:
			queue.insert(archive=True)

	def importDeQueue(self):
		source_session = self.getSourceSession()
		# ImageTargetLists that have no targets on will also be imported in this function
		print "Importing dequeuing...."
		sinedon.setConfig('leginondata', db=self.source_dbname)
		q = leginondata.DequeuedImageTargetListData(session=source_session)
		r = q.query()
		r.reverse()

		sinedon.setConfig('leginondata', db=self.destination_dbname)
		for queue in r:
			queue.insert(archive=True)

	def importImageDDinfo(self):
		'''
		Import DDInfoData based on imported image list.
		This must be done after images are imported.
		'''
		print "Importing image ddinfo...."
		#source_session = self.getSourceSession()
		for imageid in self.imageids:
			sinedon.setConfig('leginondata', db=self.source_dbname)
			image = leginondata.AcquisitionImageData().direct_query(imageid)
			q = leginondata.DDinfoValueData(camera=image['camera'])
			results = self.research(q)
			self.publish(results)

	def importImageStats(self):
		source_session = self.getSourceSession()
		print "Importing image stats...."
		q = leginondata.AcquisitionImageStatsData(session=source_session)
		results = self.research(q)
		results = self.avoidExcludedImage(results)
		self.publish(results)

	def importMosaicTiles(self):
		source_session = self.getSourceSession()
		print "Importing mosaic tiles...."
		sinedon.setConfig('leginondata', db=self.source_dbname)
		q = leginondata.MosaicTileData(session=source_session)
		results = self.research(q)
		self.publish(results)

	def importDrifts(self):
		source_session = self.getSourceSession()
		print "Importing drift...."
		sinedon.setConfig('leginondata', db=self.source_dbname)
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

		sinedon.setConfig('leginondata', db=self.destination_dbname)
		for drift in drifts:
			drift.insert(archive=True)
		for monitor in allmonitors:
			monitor.insert(archive=True)

	def importFocusResults(self):
		'''
		Import Focuser Results
		'''
		source_session = self.getSourceSession()
		print "Importing focus results...."
		sinedon.setConfig('leginondata', db=self.source_dbname)
		qfocus = leginondata.FocuserResultData(session=source_session)
		focii = qfocus.query()
		focii.reverse()

		sinedon.setConfig('leginondata', db=self.destination_dbname)
		for focus in focii:
			focus.insert(archive=True)

	def importBrightImages(self):
		'''
		Import BrighetImageData based on imported NormImageData.
		This is needed for older data since BrightImageData was
		not linked to AcquisitionImages previously.
		'''
		print "Importing old BrightImages...."
		destination_session = self.getDestinationSession()
		sinedon.setConfig('leginondata', db=self.destination_dbname)
		q = leginondata.NormImageData(session=destination_session)
		r = q.query()
		allbrights = []
		for normdata in r:
			allbrights.append(self.findBrightImageFromNorm(normdata))
		sinedon.setConfig('leginondata', db=self.destination_dbname)
		for bright in allbrights:
			if bright:
				bright.insert(archive=True)

	def importByImages(self):
		source_session = self.getSourceSession()
		sinedon.setConfig('leginondata', db=self.source_dbname)
		q = leginondata.AcquisitionImageData(session=source_session)
		images = q.query()
		images.reverse()

		print 'number of images in the session = %d' % len(images)
		targetlist = {}
		for image in images:
			q = leginondata.ImageTargetListData(image=image)
			targetlist[image.dbid] = self.research(q,True)
			self.imageids.append(image.dbid)
		sinedon.setConfig('leginondata', db=self.destination_dbname)
		skipped = 0
		for i,image in enumerate(images):
			if not (i+1) % 20:
				print ""
			else:
				print ".",
			if image['label'] in exclude_preset_list:
				skipped += 1
				continue
			imageid = image.dbid
			image.insert(archive=True)
			if targetlist[imageid]:
				targetlist[imageid].insert(archive=True)
		print '\nimported %d images' % (len(images) - skipped)

	def importFocusSequenceSettings(self, allalias):
		print 'importing Focus Sequence Settings....'
		if 'Focuser' not in allalias.keys():
			return
		sequence_names = []
		for node_name in (allalias['Focuser']):
			results = self.researchSettings('FocusSequenceData',node_name=node_name)
			self.publish(results)
			for r in results:
				sequence = r['sequence']
				for s in sequence:
					if s not in sequence_names:
						sequence_names.append(s)
		for node_name in (allalias['Focuser']):
			for seq_name in sequence_names:
				results = self.researchSettings('FocusSettingData',node_name=node_name,name=seq_name)
				self.publish(results)

	def importSettingsByClassAndAlias(self,allalias):
		unusual_settingsnames = {
				'AlignZeroLossPeak':None,
				'MeasureDose':None,
				'IntensityCalibrator':None,
				'AutoNitrogenFiller':'AutoFillerSettingsData',
				'EM':None,
				'FileNames':'ImageProcessorSettingsData',
		}
		for classname in allalias.keys():
			settingsname = classname+'SettingsData'
			if classname in unusual_settingsnames.keys():
				settingsname = unusual_settingsnames[classname]
			if not settingsname:
				continue
			if classname in allalias.keys():
				print 'importing %s Settings....' % (classname,)
				for node_name in (allalias[classname]):
					try:
						results = self.researchSettings(settingsname,name=node_name)
					except:
						if classname not in self.bad_settings_class:
							print 'ERROR: %s class node %s settings query failed' % (classname,node_name)
							self.bad_settings_class.append(classname)
					self.publish(results)
		# FocusSequence and FocusSettings needs a different importing method
		self.importFocusSequenceSettings(allalias)

	def importLaunchedApplications(self):
		print 'importing Applications....'
		source_session = self.getSourceSession()
		q = leginondata.LaunchedApplicationData(session=source_session)
		launched_apps = self.research(q)
		self.publish(launched_apps)

		for appdata in map((lambda x: x['application']), launched_apps):
			q = leginondata.NodeSpecData(application=appdata)
			nodespecs = self.research(q)
			self.publish(nodespecs)

			q = leginondata.BindingSpecData(application=appdata)
			bindingspecs = self.research(q)
			self.publish(bindingspecs)

	def importSettings(self):
		'''
		Import Settings based on launched applications of the session
		'''
		source_session = self.getSourceSession()
		q = leginondata.LaunchedApplicationData(session=source_session)
		launched_apps = self.research(q)
		allalias = {}
		for appdata in map((lambda x: x['application']), launched_apps):
			q = leginondata.NodeSpecData(application=appdata)
			results = self.research(q)
			for r in results:
				if r['class string'] not in allalias.keys():
					allalias[r['class string']] = []
				allalias[r['class string']].append(r['alias'])
		# import settings
		self.importSettingsByClassAndAlias(allalias)

	def importLastPresets(self):
		# some presets such as fa and fc is never used in image acquisition
		print 'importing all last version of presets....'
		source_session = self.getSourceSession()
		q = leginondata.PresetData(session=source_session)
		allpresets = self.research(q)
		lastpresets = {}
		for p in allpresets:
			if p['name'] not in lastpresets:
				lastpresets[p['name']] = p
		lastpreset_list = map((lambda x: lastpresets[x]),lastpresets.keys())
		self.publish(lastpreset_list)

	def importViewerImageStatus(self):
		print "Importing ViewerImageStatus...."
		source_session = self.getSourceSession()
		q = leginondata.ViewerImageStatus(session=source_session)
		results = self.research(q)
		results = self.avoidExcludedImage(results)
		self.publish(results)

		if not results:
			q = leginondata.ViewerImageStatus()
			results = self.research(q)
			if results:
				# fake entry with the oldest status
				# can not use q.insert since auto_increment for DEF_id is not activated
				results = [results[0],]
				self.publish(results)

	def importIceThickness(self):
		self.importSessionDependentData('HoleStatsData')
		self.importSessionDependentData('SquareStatsData')

	def importTomographyPrediction(self):
		self.importSessionDependentData('TomographyPredictionData')

	def importConnectToClients(self):
		self.importSessionDependentData('ConnectToClientsData')

	def runStep1(self):
		'''
		STEP 1: 
		import session and map basic information about it
		'''
		self.importSession()
		source_cam, source_tem,high_tension = self.importInstrument()
		self.importGainReferences()
		self.importBrightImages()
		if self.is_upload:
			return True
		self.importCalibrations(source_cam,source_tem,high_tension)
		self.importC2ApertureSize()
		return True

	def runStep2(self):
		'''
		STEP 2: recursively import image data.  This makes sure that
		images are entered in the destination in the same order as
		the source. 
		'''
		self.importByImages()

	def runStep3(self):
		'''
		STEP 3: import image dependent data and other data not
		recursively inserted by the first two steps.
		'''
		self.importViewerImageStatus()
		if self.is_upload:
			return
		# These are image dependent.
		self.importImageDDinfo()
		self.importImageStats()

		self.importQueue()
		self.importMosaicTiles()
		self.importDeQueue()
		self.importDrifts()
		self.importFocusResults()
		self.importLastPresets()
		self.importLaunchedApplications()
		self.importConnectToClients()
		self.importSettings()
		self.importIceThickness()
		self.importTomographyPrediction()

	def run(self):
		source_session = self.getSourceSession()
		print "****Session %s ****" % (source_session['name'])
		if self.hasImagesInSession():
			if self.isStatusGood():
				self.runStep1()
			if self.isStatusGood():
				self.runStep2()
				if self.isStatusGood():
					self.runStep3()
		self.reset()
		print ''

def archiveEssentialUsers(projectid):
	print "Importing Default Users for %d...." % (projectid,)
	userarchiver = UserArchiver(projectid)
	userarchiver.run()

def archiveProject(projectid):
	'''
	Archive all users and sessions in the project identified by id number
	'''
	archiveEssentialUsers(projectid)

	print 'Finding sessions for the project....'
	from leginon import projectdata
	p = projectdata.projects().direct_query(projectid)
	source_sessions = projectdata.projectexperiments(project=p).query()
	session_names = map((lambda x:x['session']['name']),source_sessions)
	session_names.reverse()  #oldest first
	
	print 'Found %d sessions for the project' %  (len(session_names))
	for session_name in session_names:
		# Don't archive sessions before 2011
		if int(session_name[:2]) < (YEAR-2000):
			continue
		app = SessionArchiver(session_name)
		if SKIP_ARCHIVED and app.isSessionInArchive():
			print 'Session %s already archived' % session_name
			continue
		app.run()
		app = None

if __name__ == '__main__':
	import sys
	if len(sys.argv) != 2:
		print "Usage: python archive_leginondb.py <project id number>"
		print ""
		print "sinedon.cfg should include a module"
		print "[importdata]"
		print "db: writable_archive_database"
		
		sys.exit()
	projectid = int(sys.argv[1])

	checkSinedon()
	archiveProject(projectid)
