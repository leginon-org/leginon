import math
import threading
import calibrationclient
import leginondata
import event
import acquisition
import gui.wx.tomography.TomographySimu
import collectionsimu as collection
import tilts
import exposure
import prediction
import time
from pyami import correlator, peakfinder

class CalibrationError(Exception):
	pass

class TomographySimu(acquisition.Acquisition):
	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs + \
					[event.AlignZeroLossPeakPublishEvent,
						event.MeasureDosePublishEvent]

	panelclass = gui.wx.tomography.TomographySimu.Panel
	settingsclass = leginondata.TomographySimuSettingsData

	defaultsettings = {
		'pause time': 2.5,
		'move type': 'image shift',
		'preset order': [],
		'correct image': True,
		'display image': True,
		'save image': True,
		'wait for process': False,
		'wait for rejects': False,
		'duplicate targets': False,
		'duplicate target type': 'focus',
		'iterations': 1,
		'wait time': 0,
		'adjust for drift': False,
		'model mag': 'saved value for this series',
		'z0 error': 2e-6,
		'phi': 0.0,
		'phi2': 0.0,
		'offset': 0.0,
		'offset2': 0.0,
		'fixed model': False,
		'use lpf': True,
		'use wiener': False,
		'use tilt': True,
		'simu tilt series': '1',
		'fit data points': 4,
	}

	def __init__(self, *args, **kwargs):
		acquisition.Acquisition.__init__(self, *args, **kwargs)
		self.calclients['pixel size'] = \
				calibrationclient.PixelSizeCalibrationClient(self)
		self.calclients['beam tilt'] = \
				calibrationclient.BeamTiltCalibrationClient(self)
		self.btcalclient = self.calclients['beam tilt'] 

		self.tilts = tilts.Tilts()
		self.exposure = exposure.Exposure()
		self.prediction = prediction.Prediction()
		self.simuseries = int(self.settings['simu tilt series'])
		self.simuseriesdata = self.getTiltSeries()
		if self.simuseriesdata is not None:
			self.getTiltImagedata(self.session,self.simuseriesdata)
			self.presetdata = self.getTiltSeriesPreset()
			self.loadPredictionInfo()
		self.first_tilt_direction = 1
		fake_settings = {
		'equally sloped': False,
		'equally sloped n': 8,
		'xcf bin': 1,
		'run buffer cycle': True,
		'align zero loss peak': True,
		'measure dose': True,
		'dose': 200.0,
		'min exposure': None,
		'max exposure': None,
		'mean threshold': 100.0,
		'collection threshold': 90.0,
		'tilt pause time': 1.0,
		'measure defocus': False,
		'integer': False,
		'intscale': 10,
		'pausegroup': False,
		}
		self.settings.update(fake_settings)
		self.start()

	def getTiltSeries(self):
		if self.simuseries is None:
			self.simuseries = 1
		allseries_num = self.getTiltSeriesNumbers()
		if len(allseries_num) == 0 or len(allseries_num) < 1 or allseries_num[0] is None:
			self.logger.error('No tomography tilt series in this session')
			return None
		if self.simuseries not in allseries_num:
			self.simuseries = allseries_num[0]
			self.logger.warning('previously chosen series invalid, reset to %d' % self.simuseries)
		series_num = self.simuseries
		qseries = leginondata.TiltSeriesData(session=self.session,number=series_num)
		result = qseries.query()
		if result:
			seriesdata = result[0]
		else:
			qseries = leginondata.TiltSeriesData(session=self.session)
			results = qseries.query()
			if len(results) >= series_num:
				seriesdata = results[-series_num]
			else:
				self.logger.error('Chosen tilt series not exist')
				return None
		self.settings['tilt min'] = seriesdata['tilt min']
		self.settings['tilt max'] = seriesdata['tilt max']
		self.settings['tilt start'] = seriesdata['tilt start']
		self.settings['tilt step'] = seriesdata['tilt step']
		self.simuseriesdata = seriesdata
		return seriesdata

	def getTiltSeriesPreset(self):
		q = leginondata.AcquisitionImageData(session=self.session)
		q['tilt series'] = self.simuseriesdata
		results = q.query(readimages = False)
		if len(results) > 0:
			return results[0]['preset']

	def getTiltImagedata(self,sessiondata=None,seriesdata=None):
		if sessiondata is None:
			sessiondata = self.session
		if seriesdata is None:
			seriesdata = self.simuseriesdata
		print "-----------------"
		print sessiondata.dbid,seriesdata.dbid,seriesdata['number']
		q = leginondata.AcquisitionImageData(session=sessiondata)
		q['tilt series'] = seriesdata
		results = q.query(readimages=False)
		if results:
			results.reverse()
			tilts = map((lambda x: x['scope']['stage position']['a']),results)
			files = map((lambda x: x['filename']+'.mrc'),results)
			firsttilt = tilts[0]
			tilts_in_groups=[[]]
			images_in_groups=[[]]
			self.first_tilt_imagedata = [results[0]]
			n = 0
			for i, tilt in enumerate(tilts):
				if tilt -firsttilt < 1e-4 and firsttilt - tilt < 1e-4 and i > 0:
					n = 1
					self.first_tilt_imagedata.append(results[i])
					tilts_in_groups.append([])
					images_in_groups.append([])
				tilts_in_groups[n].append(tilt)
				images_in_groups[n].append(results[i])
			self.presetdata = images_in_groups[0][0]['preset']
			self.tiltimagedata = images_in_groups
			print "images in 1st group:",len(images_in_groups[0])
			if len(images_in_groups) > 1:
				print "images in 2nd group:",len(images_in_groups[1])

	def getTiltSeriesNumbers(self):
		#To Do: NEED TO exclude aborted series
		seriesnumbers = []
		q = leginondata.TiltSeriesData(session=self.session)
		results = q.query()
		for result in results:
			q = leginondata.AcquisitionImageData()
			q['tilt series'] = result
			imageresults = q.query(readimages=False)
			if len(imageresults) > 0:
				seriesnumbers.append(result['number'])
		return seriesnumbers

	def reportTiltSeriesTargetListDone(self):
		self.targetlist = self.tiltimagedata[0][0]['target']['list']
		if self.targetlist is not None:
			self.reportTargetListDone(self.targetlist,'done')
		else:
			self.logger.warning('Tilt Series has no TargetList')

	def update(self):
		try:
			self.getTiltSeries()
			self.getTiltImagedata()
			self.tilts.update(equally_sloped=self.settings['equally sloped'],
							  min=math.radians(self.settings['tilt min']),
							  max=math.radians(self.settings['tilt max']),
							  start=math.radians(self.settings['tilt start']),
							  step=math.radians(self.settings['tilt step']),
							  n=self.settings['equally sloped n'])
		except ValueError, e:
			self.logger.warning('Tilt parameters invalid: %s.' % e)
		else:
			n = sum([len(tilts) for tilts in self.tilts.getTilts()])
			self.logger.info('%d tilt angle(s) for series.' % n)

		total_dose = self.settings['dose']
		exposure_min = self.settings['min exposure']
		exposure_max = self.settings['max exposure']

		tilts = self.tilts.getTilts()

		dose = 0.0
		exposure_time = 0.0
		try:
			preset = self.presetdata
		except (IndexError, ValueError):
			pass
		else:
			if preset['dose'] is not None:
				dose = preset['dose']*1e-20
			exposure_time = preset['exposure time']/1000.0

		try:
			self.exposure.update(total_dose=total_dose,
								 tilts=tilts,
								 dose=dose,
								 exposure=exposure_time,
								 exposure_min=exposure_min,
								 exposure_max=exposure_max)
		except exposure.LimitError, e:
			self.logger.warning('Exposure time out of range: %s.' % e)
		except exposure.Default, e:
			self.logger.warning('Using preset exposure time: %s.' % e)
		else:
			try:
				exposure_range = self.exposure.getExposureRange()
			except ValueError:
				pass
			else:
				s = 'Exposure time range: %g to %g seconds.' % exposure_range
				self.logger.info(s)

	def checkDose(self):
		self.update()

	def acquireFilm(self, *args, **kwargs):
		self.logger.error('Film acquisition not currently supported.')
		return

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None):
		status = 'ok'
		presetdata = self.presetdata
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this target')
			return
		try:
			calibrations = self.getCalibrations(presetdata)
		except CalibrationError, e:
			self.logger.error('Calibration error: %s' % e) 
			return 'failed'
		high_tension, pixel_size = calibrations

		self.logger.info('Pixel size: %g meters.' % pixel_size)

		# TODO: error check
		self.simuseries = int(self.settings['simu tilt series'])
		self.update()
		tilts = self.tilts.getTilts()
		exposures = self.exposure.getExposures()
		# Find first tilt group direction 
		tiltsum = sum(tilts[0])
		if tiltsum < len(tilts[0])*tilts[0][0]:
			self.first_tilt_direction = 2
		else:
			self.first_tilt_direction = 1
		self.initGoodPredictionInfo(presetdata)

		collect = collection.Collection()
		collect.node = self
		collect.session = self.session
		collect.logger = self.logger
		collect.tiltimagedata = self.tiltimagedata
#		collect.instrument = self.instrument
		collect.settings = self.settings.copy()
		collect.preset = presetdata
		collect.target = target
		collect.emtarget = emtarget
		collect.viewer = self.panel.viewer
		collect.player = self.player
		collect.pixel_size = pixel_size
		collect.tilts = tilts
		collect.exposures = exposures
		collect.prediction = self.prediction

		try:
			collect.start()
		except collection.Abort:
			return 'aborted'
		except collection.Fail:
			return 'failed'

		# ignoring wait for process
		#self.publishDisplayWait(imagedata)

		self.reportTiltSeriesTargetListDone()
		return 'ok'

	def getPixelPosition(self, move_type, position=None):
		scope_data = self.instrument.getData(leginondata.ScopeEMData)
		camera_data = self.instrument.getData(leginondata.CameraEMData, image=False)
		if position is None:
			position = {'x': 0.0, 'y': 0.0}
		else:
			scope_data[move_type] = {'x': 0.0, 'y': 0.0}
		client = self.calclients[move_type]
		try:
			pixel_position = client.itransform(position, scope_data, camera_data)
		except calibrationclient.NoMatrixCalibrationError, e:
			raise CalibrationError(e)
		# invert y and position
		return {'x': pixel_position['col'], 'y': -pixel_position['row']}

	def getParameterPosition(self, move_type, position=None):
		scope_data = self.instrument.getData(leginondata.ScopeEMData)
		camera_data = self.instrument.getData(leginondata.CameraEMData, image=False)
		if position is None:
			position = {'x': 0.0, 'y': 0.0}
		else:
			scope_data[move_type] = {'x': 0.0, 'y': 0.0}
		client = self.calclients[move_type]
		# invert y and position
		position = {'row': position['y'], 'col': -position['x']}
		try:
			scope_data = client.transform(position, scope_data, camera_data)
		except calibrationclient.NoMatrixCalibrationError, e:
			raise CalibrationError(e)
		return scope_data[move_type]

	def setPosition(self, move_type, position):
		position = self.getParameterPosition(move_type, position)
		initializer = {move_type: position}
		position = leginondata.ScopeEMData(initializer=initializer)
		self.instrument.setData(position)
		return position[move_type]

	def getDefocus(self):
		return self.instrument.tem.Defocus

	def setDefocus(self, defocus):
		self.instrument.tem.Defocus = defocus

	def getCalibrations(self, presetdata=None):
		presetdata = self.presetdata
		if presetdata is None:
			scope_data = self.instrument.getData(leginondata.ScopeEMData)
			camera_data = self.instrument.getData(leginondata.CameraEMData, image=False)
			tem = scope_data['tem']
			ccd_camera = camera_data['ccdcamera']
			high_tension = scope_data['high tension']
			magnification = scope_data['magnification']
		else:
			tem = presetdata['tem']
			ccd_camera = presetdata['ccdcamera']
			high_tension = self.instrument.tem.HighTension
			magnification = presetdata['magnification']

		args = (magnification, tem, ccd_camera)
		pixel_size = self.calclients['pixel size'].getPixelSize(*args)

		if pixel_size is None:
			raise CalibrationError('no pixel size for %gx' % magnification)

		return high_tension, pixel_size

	def resetTiltSeriesList(self):
		self.logger.info('Clear Tilt Series and Model History')
		self.prediction.resetTiltSeriesList()
		self.simuseries = int(self.settings['simu tilt series'])
		self.simuseriesdata = self.getTiltSeries()
		self.getTiltImagedata(self.session,self.simuseriesdata)
		self.presetdata = self.getTiltSeriesPreset()
		self.loadPredictionInfo()
		self.update()
		self.initGoodPredictionInfo()
		# For testing
		self.reportTiltSeriesTargetListDone()

	def adjusttarget(self,preset_name,target,emtarget):
		self.declareDrift('tilt')
		target = self.adjustTargetForDrift(target)
		emtarget = self.targetToEMTargetData(target)
		presetdata = self.presetsclient.getPresetFromDB(preset_name)
		status = self.moveAndPreset(presetdata, emtarget)
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this adjusted target')
		return emtarget, status

	def removeStageAlphaBacklash(self, tilts, preset_name, target, emtarget):
		pass

	def initGoodPredictionInfo(self,presetdata=None, tiltgroup=1):
		presetdata = self.presetdata
		if presetdata == None:
			presets = self.settings['preset order']
			try:
				presetname = presets[0]
			except IndexError:
				self.logger.error('Choose preset for this node before doing tilt series')
				return
			try:
				presetdata = self.presetsclient.getPresetFromDB(presetname)
			except:
				self.logger.error('Preset %s does not exist in this session.' % (presetname,))
				return

		tem = presetdata['tem']
		ccd = presetdata['ccdcamera']
		presetmag = presetdata['magnification']
		presetpixelsize = self.calclients['pixel size'].retrievePixelSize(tem=tem, ccdcamera=ccd, mag=presetmag)
		presetimage_pixel_size = presetpixelsize * presetdata['binning']['x']
		q = leginondata.MagnificationsData(instrument=tem)
		results = q.query(results=1)
		if len(results) > 0:
			allmags = results[0]['magnifications']
		else:
			allmags = [50,100,500,1000,5000,25000,50000]
		allmags.sort()
		allmags.reverse()
		try:
			preset_mag_index = allmags.index(presetmag)
		except ValueError:
			self.logger.error('Preset magnification not listed for TEM')
			return

		if not self.settings['model mag']:
			self.settings['model mag'] = 'saved value for this series'
		if self.settings['model mag'] == 'only this preset' or self.settings['model mag'] == 'saved value for this series':
			allmags = [presetmag]
		elif self.settings['model mag'] == 'custom values':
			allmags = []
		elif self.settings['model mag'] != 'this preset and lower mags':
			mag = int(self.settings['model mag'])
			try:
				mag_index = allmags.index(mag)
			except ValueError:
				self.logger.error('Initial model magnification not listed for TEM')
				return
			allmags = [mag]
		else:
			allmags = allmags[preset_mag_index:]	
		
		goodprediction = None
		if self.settings['model mag'] == 'saved value for this series':
			#overwrite with saved values for the simutiltseries		
			imagedata = self.first_tilt_imagedata[tiltgroup-1]
			q = leginondata.TomographyPredictionData(image=imagedata)
			results = q.query(results=1)
			if len(results) > 0:
				goodprediction = results[0]
				prediction_pixel_size = goodprediction['pixel size']


		if preset_mag_index is not None and goodprediction is not None:
			for i,mag in enumerate(allmags):
				self.logger.info('Looking for good model at mag of %d' %(mag))
				qpreset = leginondata.PresetData(tem=tem, ccdcamera=ccd, magnification=mag)
				qimage = leginondata.AcquisitionImageData(preset=qpreset)
				query_data = leginondata.TomographyPredictionData(image=qimage)
				maxshift = 2.0e-8
				raw_correlation_binning = 6
				for n in (10, 100, 500, 1000):
					predictions = query_data.query(results=n, readimages=False)
					for predictinfo in predictions:
						prediction_pixel_size = predictions[0]['pixel size']
						if prediction_pixel_size is None:
							continue
						image = predictinfo.special_getitem('image', dereference=True, readimages=False)
						a = image['scope']['stage position']['a']
						model_error_limit = maxshift /prediction_pixel_size
						# correlation is recorded as multiples of raw_correlation_binning
						if model_error_limit < raw_correlation_binning:
							model_error_limit = raw_correlation_binning
						paramdict = predictinfo['predicted position']
						if paramdict['phi']==0 and paramdict['optical axis']==0 and paramdict['z0']==0:
							continue
						cor = predictinfo['correlation']
						dist = math.hypot(cor['x'],cor['y'])
						if dist and dist <= model_error_limit:
							if (self.first_tilt_direction == tiltgroup and a > self.settings['tilt start']) or (self.first_tilt_direction != tiltgroup and a < self.settings['tilt start']):
								goodprediction = predictinfo
								self.logger.info('good calibration found at %d x mag' % (mag,))
								break
					if goodprediction is not None:
						break
				if goodprediction is not None:
						break

		if goodprediction is None:
			if self.settings['model mag'] == 'custom values':
				# initialize phi, offset by tilt direction
				if self.first_tilt_direction == 1:
					offsetlist = [self.settings['offset'],self.settings['offset2']]
					philist = [self.settings['phi'],self.settings['phi2']]
				else:
					offsetlist = [self.settings['offset2'],self.settings['offset']]
					philist = [self.settings['phi2'],self.settings['phi']]
				if tiltgroup == 2:
					axis_offset = offsetlist[1]
					phi = math.radians(philist[1])
				else:
					axis_offset = offsetlist[0]
					phi = math.radians(philist[0])
				optical_axis = axis_offset*(1e-6)/presetimage_pixel_size
				params = [phi, optical_axis, 0]
			else:
				params = [0, 0, 0]
		else:
			scale = prediction_pixel_size / presetimage_pixel_size
			paramsdict = goodprediction['predicted position']
			params = [paramsdict['phi'], paramsdict['optical axis']*scale, paramsdict['z0']*scale]
		self.prediction.parameters = params
		self.prediction.image_pixel_size = presetimage_pixel_size
		self.prediction.ucenter_limit = self.settings['z0 error']*(1e-6)
		self.prediction.fixed_model = self.settings['fixed model']
		self.prediction.phi0 = params[0]
		self.prediction.offset0 = params[1]
		self.prediction.z00 = params[2]
		phi_degree = math.degrees(params[0])
		offset_um = params[1]*presetimage_pixel_size/(1e-6)
		z0_um = params[2]*presetimage_pixel_size/(1e-6)
		self.logger.info('Initialize prediction parameters to (phi,offset,z0) = (%.2f deg, %.2f um, %.2f um)' % (phi_degree,offset_um,z0_um))
		pixelshift={}
		pixelshift['col'] = params[1]*math.cos(params[0])
		# reverse y as in getPixelPosition
		pixelshift['row'] = -params[1]*math.sin(params[0])
		if pixelshift is not None:
			fakescope = leginondata.ScopeEMData()
			fakescope.friendly_update(presetdata)
			fakecam = leginondata.CameraEMData()
			fakecam.friendly_update(presetdata)

			# get high tension from scope	
			try:
				fakescope['high tension'] = tem['high tension']
			except:
				fakescope['high tension'] = 120000

			## convert pixel shift to image shift
			newscope = self.calclients['image shift'].transform(pixelshift, fakescope, fakecam)
			ishift = newscope['image shift']
			shift0x = ishift['x'] - presetdata['image shift']['x']
			shift0y = (ishift['y'] - presetdata['image shift']['y'])
			self.logger.info('calculated image shift to center tilt axis (x,y): (%.4e, %.4e)' % (shift0x,shift0y))

	def loadPredictionInfo(self):
		initializer = {
			'session': self.session,
		}
		query_data = leginondata.TiltSeriesData(initializer=initializer)
		results = self.research(query_data)
		results.reverse()
		keys = []
		settings = {}
		positions = {}
		image_pixel_sizes = {}
		for result in results:
			key = result.dbid
			keys.append(key)
			settings[key] = result
			positions[key] = []
			image_pixel_sizes[key] = []

		initializer = {
			'session': self.session,
		}
		query_data = leginondata.TomographyPredictionData(initializer=initializer)
		results = self.research(query_data)
		results.reverse()
		first_tilt_series_number = 1

		for result in results:
			image = result.special_getitem('image', True, readimages=False)
			tilt_series = image['tilt series']
			image_pixel_sizes[tilt_series.dbid] = result['pixel size']
			tilt = image['scope']['stage position']['a']
			position = result['position']
			if tilt_series.dbid >= self.simuseriesdata.dbid or tilt_series['number'] < first_tilt_series_number:
				pass
			else:	
				positions[tilt_series.dbid].append((tilt, position))

		self.prediction.resetTiltSeriesList()
		for key in keys:
			self.prediction.image_pixel_size = image_pixel_sizes[key]
			start = settings[key]['tilt start']
			self.prediction.newTiltSeries()
			for tilt, position in positions[key]:
				if round(tilt, 3) == round(start, 3):
					self.prediction.newTiltGroup()
				self.prediction.addPosition(tilt, position)

		n_groups = len(self.prediction.tilt_series_list)
		n_points = 0
		for tilt_series in self.prediction.tilt_series_list:
			for tilt_group in tilt_series.tilt_groups:
				n_points += len(tilt_group)
		m = 'Loaded %d points from %d previous series' % (n_points, n_groups-1)
		self.logger.info(m)

	def alignZeroLossPeak(self, preset_name):
		pass

	def measureDose(self, preset_name):
		pass

	def processTargetData(self, *args, **kwargs):
		try:
			acquisition.Acquisition.processTargetData(self, *args, **kwargs)
		except Exception, e:
			self.logger.error('Failed to process the tomo target: %s' % e)
			raise

	def measureDefocus(self):
		pass
