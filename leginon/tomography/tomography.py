import math
import time

from pyami import correlator, peakfinder

import leginon.calibrationclient
import leginon.leginondata
import leginon.event
import leginon.acquisition
import leginon.gui.wx.tomography.Tomography

import leginon.tomography.collection
import leginon.tomography.tilts
import leginon.tomography.exposure
import leginon.tomography.prediction

class CalibrationError(Exception):
	pass

class Tomography(leginon.acquisition.Acquisition):
	eventinputs = leginon.acquisition.Acquisition.eventinputs
	eventoutputs = leginon.acquisition.Acquisition.eventoutputs + \
					[leginon.event.AlignZeroLossPeakPublishEvent,
						leginon.event.MeasureDosePublishEvent]

	panelclass = leginon.gui.wx.tomography.Tomography.Panel
	settingsclass = leginon.leginondata.TomographySettingsData

	defaultsettings = leginon.acquisition.Acquisition.defaultsettings
	defaultsettings.update({
		'tilt min': -60.0,
		'tilt max': 60.0,
		'tilt start': 0.0,
		'tilt step': 1.0,
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
#		'pausegroup': False,
		'model mag': 'this preset and lower mags',
		'z0 error': 2e-6,
		'phi': 0.0,
		'phi2': 0.0,
		'offset': 0.0,
		'offset2': 0.0,
		'z0': 0.0,
		'fixed model': False,
		'use lpf': True,
#		'use wiener': False,
		'taper size': 10,
		'use tilt': True,
#		'wiener max tilt': 45,
		'fit data points': 4,
		'use z0': False,
	})

	def __init__(self, *args, **kwargs):
		leginon.acquisition.Acquisition.__init__(self, *args, **kwargs)
		self.calclients['pixel size'] = \
				leginon.calibrationclient.PixelSizeCalibrationClient(self)
		self.calclients['beam tilt'] = \
				leginon.calibrationclient.BeamTiltCalibrationClient(self)
		self.btcalclient = self.calclients['beam tilt'] 

		self.tilts = leginon.tomography.tilts.Tilts()
		self.exposure = leginon.tomography.exposure.Exposure()
		self.prediction = leginon.tomography.prediction.Prediction()
		self.loadPredictionInfo()
		self.first_tilt_direction = 1

		self.start()

	'''
	def onPresetPublished(self, evt):
		leginon.acquisition.Acquisition.onPresetPublished(self, evt)

		preset = evt['data']

		if preset is None or preset['name'] is None:
			return

		if preset['name'] not in self.settings['preset order']:
			return

		dose = preset['dose']
		exposure_time = preset['exposure time']/1000.0

		try:
			self.exposure.update(dose=dose, exposure=exposure_time)
		except leginon.tomography.exposure.LimitError, e:
			s = 'Exposure time limit exceeded for preset \'%s\': %s.'
			s %= (preset['name'], e)
			self.logger.warning(s)

	def setSettings(self, *args, **kwargs):
		leginon.acquisition.Acquisition.setSettings(self, *args, **kwargs)
		self.update()
	'''

	def update(self):
		try:
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
			name = self.settings['preset order'][-1]
			preset = self.presetsclient.getPresetFromDB(name)
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
		except leginon.tomography.exposure.LimitError, e:
			self.logger.warning('Exposure time out of range: %s.' % e)
			raise
		except leginon.tomography.exposure.Default, e:
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
		status = self.moveAndPreset(presetdata, emtarget)
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

		collect = leginon.tomography.collection.Collection()
		collect.node = self
		collect.session = self.session
		collect.logger = self.logger
		collect.instrument = self.instrument
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
		collect.setStatus = self.setStatus

		try:
			collect.start()
		except leginon.tomography.collection.Abort:
			return 'aborted'
		except leginon.tomography.collection.Fail:
			return 'failed'

		# ignoring wait for process
		#self.publishDisplayWait(imagedata)

		return 'ok'

	def getPixelPosition(self, move_type, position=None):
		scope_data = self.instrument.getData(leginon.leginondata.ScopeEMData)
		camera_data = self.instrument.getData(leginon.leginondata.CameraEMData)
		if position is None:
			position = {'x': 0.0, 'y': 0.0}
		else:
			scope_data[move_type] = {'x': 0.0, 'y': 0.0}
		client = self.calclients[move_type]
		try:
			pixel_position = client.itransform(position, scope_data, camera_data)
		except leginon.calibrationclient.NoMatrixCalibrationError, e:
			raise CalibrationError(e)
		# invert y and position
		return {'x': pixel_position['col'], 'y': -pixel_position['row']}

	def getParameterPosition(self, move_type, position=None):
		scope_data = self.instrument.getData(leginon.leginondata.ScopeEMData)
		camera_data = self.instrument.getData(leginon.leginondata.CameraEMData)
		if position is None:
			position = {'x': 0.0, 'y': 0.0}
		else:
			scope_data[move_type] = {'x': 0.0, 'y': 0.0}
		client = self.calclients[move_type]
		# invert y and position
		position = {'row': position['y'], 'col': -position['x']}
		try:
			scope_data = client.transform(position, scope_data, camera_data)
		except leginon.calibrationclient.NoMatrixCalibrationError, e:
			raise CalibrationError(e)
		return scope_data[move_type]

	def setPosition(self, move_type, position):
		position = self.getParameterPosition(move_type, position)
		initializer = {move_type: position}
		position = leginon.leginondata.ScopeEMData(initializer=initializer)
		self.instrument.setData(position)
		return position[move_type]

	def getDefocus(self):
		return self.instrument.tem.Defocus

	def setDefocus(self, defocus):
		self.instrument.tem.Defocus = defocus

	def getCalibrations(self, presetdata=None):
		if presetdata is None:
			scope_data = self.instrument.getData(leginon.leginondata.ScopeEMData)
			camera_data = self.instrument.getData(leginon.leginondata.CameraEMData)
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
		self.initGoodPredictionInfo()

	def adjusttarget(self,preset_name,target,emtarget):
		self.declareDrift('tilt')
		target = self.adjustTargetForTransform(target)
		emtarget = self.targetToEMTargetData(target)
		presetdata = self.presetsclient.getPresetFromDB(preset_name)
		status = self.moveAndPreset(presetdata, emtarget)
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this adjusted target')
		return emtarget, status

	def removeStageAlphaBacklash(self, tilts, preset_name, target, emtarget):
		if len(tilts) < 2:
			raise ValueError

		## change to parent preset
		try:
			parentname = target['image']['preset']['name']
		except:
			adjust = False
		else:
			adjust = True

		## acquire parent preset image, initial image
		if adjust:
			isoffset = self.getImageShiftOffset()
			self.presetsclient.toScope(parentname)
			self.setImageShiftOffset(isoffset)
			imagedata0 = self.acquireCorrectedCameraImageData(0)

		## tilt then return in slow increments
		delta = math.radians(5.0)
		n = 5
		increment = delta/n
		if tilts[1] - tilts[0] > 0:
			sign = -1
		else:
			sign = 1
		alpha = tilts[0] + sign*delta
		self.instrument.tem.StagePosition = {'a': alpha}
		time.sleep(1.0)
		for i in range(n):
			alpha -= sign*increment
			self.instrument.tem.StagePosition = {'a': alpha}
			time.sleep(1.0)

		if adjust:
			## acquire parent preset image, final image
			imagedata1 = self.acquireCorrectedCameraImageData(1)

			self.presetsclient.toScope(preset_name)
			## return to tomography preset
			if emtarget['movetype'] == 'image shift':
				presetdata = self.presetsclient.getPresetFromDB(preset_name)
				self.moveAndPreset(presetdata, emtarget)
			else:
				isoffset = self.getImageShiftOffset()
				self.presetsclient.toScope(preset_name)
				self.setImageShiftOffset(isoffset)

			## find shift between image0, image1
			pc = correlator.phase_correlate(imagedata0['image'], imagedata1['image'], False)
			peakinfo = peakfinder.findSubpixelPeak(pc, lpf=1.5)
			subpixelpeak = peakinfo['subpixel peak']
			shift = correlator.wrap_coord(subpixelpeak, imagedata0['image'].shape)
			shift = {'row': shift[0], 'col': shift[1]}
			## transform pixel to image shift
			oldscope = imagedata0['scope']
			newscope = self.calclients['image shift'].transform(shift, oldscope, imagedata0['camera'])
			ishiftx = newscope['image shift']['x'] - oldscope['image shift']['x']
			ishifty = newscope['image shift']['y'] - oldscope['image shift']['y']

			oldishift = self.instrument.tem.ImageShift
			newishift = {'x': oldishift['x'] + ishiftx, 'y': oldishift['y'] + ishifty}
			self.logger.info('adjusting imageshift after backlash: dx,dy = %s,%s' % (ishiftx,ishifty))
			self.instrument.tem.ImageShift = newishift

	def initGoodPredictionInfo(self,presetdata=None, tiltgroup=1):
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
		allmags = self.instrument.tem.Magnifications
		allmags.sort()
		allmags.reverse()
		try:
			preset_mag_index = allmags.index(presetmag)
		except ValueError:
			self.logger.error('Preset magnification not listed for TEM')
			return

		if not self.settings['model mag']:
			self.settings['model mag'] = 'this preset and lower mags'
		if self.settings['model mag'] == 'only this preset':
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
		if preset_mag_index is not None:
			for i,mag in enumerate(allmags):
				self.logger.info('Looking for good model at mag of %d' %(mag))
				qpreset = leginon.leginondata.PresetData(tem=tem, ccdcamera=ccd, magnification=mag)
				qimage = leginon.leginondata.AcquisitionImageData(preset=qpreset)
				query_data = leginon.leginondata.TomographyPredictionData(image=qimage)
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
				custom_z0 = self.settings['z0']*(1e-6)/presetimage_pixel_size
				params = [phi, optical_axis, custom_z0]
			else:
				params = [0, 0, 0]
		else:
			scale = prediction_pixel_size / presetimage_pixel_size
			paramsdict = goodprediction['predicted position']
			params = [paramsdict['phi'], paramsdict['optical axis']*scale, paramsdict['z0']*scale]
		if not self.settings['use z0']:
			params[2] = 0

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
			fakescope = leginon.leginondata.ScopeEMData()
			fakescope.friendly_update(presetdata)
			fakecam = leginon.leginondata.CameraEMData()
			fakecam.friendly_update(presetdata)

			# get high tension from scope		
			fakescope['high tension'] = self.instrument.tem.HighTension

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
		query_data = leginon.leginondata.TiltSeriesData(initializer=initializer)
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
		query_data = leginon.leginondata.TomographyPredictionData(initializer=initializer)
		results = self.research(query_data)
		results.reverse()

		for result in results:
			image = result.special_getitem('image', True, readimages=False)
			tilt_series = image['tilt series']
			image_pixel_sizes[tilt_series.dbid] = result['pixel size']
			tilt = image['scope']['stage position']['a']
			position = result['position']
			positions[tilt_series.dbid].append((tilt, position))

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
		m = 'Loaded %d points from %d previous series' % (n_points, n_groups)
		self.logger.info(m)

	def alignZeroLossPeak(self, preset_name):
		request_data = leginon.leginondata.AlignZeroLossPeakData()
		request_data['session'] = self.session
		request_data['preset'] = preset_name
		self.publish(request_data, database=True, pubevent=True, wait=True)

	def measureDose(self, preset_name):
		request_data = leginon.leginondata.MeasureDoseData()
		request_data['session'] = self.session
		request_data['preset'] = preset_name
		self.publish(request_data, database=True, pubevent=True, wait=True)

	def processTargetData(self, *args, **kwargs):
		preset_name = self.settings['preset order'][-1]
		if self.settings['align zero loss peak']:
			self.alignZeroLossPeak(preset_name)
		if self.settings['measure dose']:
			self.measureDose(preset_name)
		try:
			leginon.acquisition.Acquisition.processTargetData(self, *args, **kwargs)
		except Exception, e:
			self.logger.error('Failed to process the tomo target: %s' % e)

	def measureDefocus(self):
		beam_tilt = 0.01
		stig = False
		correct_tilt = True
		correlation_type = 'phase'
		settle = 0.5
		image0 = None

		args = (beam_tilt, stig, correct_tilt, correlation_type, settle, image0)
		try:
				#This does not seem to work right
			result = self.calclients['beam tilt'].measureDefocusStig(*args)
		except leginon.calibrationclient.NoMatrixCalibrationError, e:
			self.logger.error('Measurement failed without calibration: %s' % e)
			return None
		delta_defocus = result['defocus']
		fit = result['min']
		return delta_defocus, fit

