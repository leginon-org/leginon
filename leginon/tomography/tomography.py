import math
import time
import numpy

from pyami import correlator, peakfinder

import leginon.calibrationclient
import leginon.leginondata
import leginon.event
import leginon.acq as acquisition
import leginon.gui.wx.tomography.Tomography

import leginon.tomography.collection
import leginon.tomography.tilts
import leginon.tomography.exposure
import leginon.tomography.prediction

from leginon.targetwatcher import PauseRepeatException
from leginon.targetwatcher import PauseRestartException
from leginon.targetwatcher import BypassException
from leginon.node import PublishError

class CalibrationError(Exception):
	pass

class LimitError(Exception):
    pass

class Tomography(acquisition.Acquisition):
	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs + \
					[ leginon.event.MeasureDosePublishEvent]

	panelclass = leginon.gui.wx.tomography.Tomography.Panel
	settingsclass = leginon.leginondata.TomographySettingsData

	defaultsettings = acquisition.Acquisition.defaultsettings
	defaultsettings.update({
		'tilt min': -60.0,
		'tilt max': 60.0,
		'tilt start': 0.0,
		'tilt step': 1.0,
		'tilt order': 'sequential',
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
		'disable backlash correction': False,
		'backlash pause time': 2.5,
		'measure defocus': False,
		'integer': False,
		'intscale': 10,
#		'pausegroup': False,
		'model mag': 'this preset and lower mags',
		'z0 error': 2.0, #um
		'phi': 0.0,
		'phi2': 0.0,
		'offset': 0.0,
		'offset2': 0.0,
		'z0': 0.0,
		'z02': 0.0,
		'fixed model': False,
		'use lpf': True,
#		'use wiener': False,
		'taper size': 10,
		'use tilt': True,
#		'wiener max tilt': 45,
		'fit data points': 4,
		'fit data points2': 4,
		'use z0': False,
		'addon tilts':'()',
		'use preset exposure':False,
	})

	def __init__(self, *args, **kwargs):
		acquisition.Acquisition.__init__(self, *args, **kwargs)
		self.calclients['pixel size'] = \
				leginon.calibrationclient.PixelSizeCalibrationClient(self)
		self.calclients['beam tilt'] = \
				leginon.calibrationclient.BeamTiltCalibrationClient(self)
		self.calclients['image shift'] = \
			leginon.calibrationclient.ImageShiftCalibrationClient(self)
		self.btcalclient = self.calclients['beam tilt'] 
		self.tilts = leginon.tomography.tilts.Tilts()
		self.exposure = self.getExposureObject()
		#self.exposure = leginon.tomography.exposure.Exposure()
		#self.prediction = leginon.tomography.prediction.Prediction()
		self.prediction = self.getPredictionObject()
		self.loadPredictionInfo()
		self.updateTilts()
		self.start()

	def getExposureObject(self):
		return leginon.tomography.exposure.Exposure()
		 
	def getPredictionObject(self):
		return leginon.tomography.prediction.Prediction()

	def updateTilts(self):
		'''
		Update tilt values for data collection from settings.
		Should be done before updateExposures.
		'''
		try:
			self.tilts.update(equally_sloped=self.settings['equally sloped'],
							  min=math.radians(self.settings['tilt min']),
							  max=math.radians(self.settings['tilt max']),
							  start=math.radians(self.settings['tilt start']),
							  step=math.radians(self.settings['tilt step']),
							  n=self.settings['equally sloped n'],
							  add_on=self.convertDegreeTiltsToRadianList(self.settings['addon tilts'],True), tilt_order=self.settings['tilt order'])
		except ValueError as e:
			self.logger.warning('Tilt parameters invalid: %s.' % e)
		else:
			n = sum([len(tilts) for tilts in self.tilts.getTilts()])
			self.logger.info('%d tilt angle(s) for series.' % n)

	def updateExposures(self):
		'''
		Update exposure values for data collection from settings
		Should be done after updateTilts.
		'''
		tilts = self.tilts.getTilts()

		total_dose = self.settings['dose']
		exposure_min = self.settings['min exposure']
		exposure_max = self.settings['max exposure']

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
								 exposure_max=exposure_max,
								 fixed_exposure=self.settings['use preset exposure'],)
		except leginon.tomography.exposure.LimitError as e:
			self.logger.warning('Exposure dose out of range: %s.' % e)
			self.logger.warning('Adjust total exposure dose Or')
			msg = self.exposure.getExposureTimeLimits()
			self.logger.warning(msg)
			raise LimitError('Exposure limit error')
		except leginon.tomography.exposure.Default as e:
			self.logger.warning('Using preset exposure time: %s.' % e)
		else:
			try:
				exposure_range = self.exposure.getExposureRange()
			except ValueError:
				pass
			else:
				s = 'Exposure time range: %g to %g seconds.' % exposure_range
				self.logger.info(s)

	def getTiltDefocusDelta(self, temdata):
		r = leginon.leginondata.TiltDefocusCalibrationData(tem=temdata).query(results=1)
		if r:
			return r[0]
		else:
			return None

	def update(self):
		'''
		Update values for data collection from settings
		'''
		self.updateTilts()
		self.updateExposures()

	def checkDose(self):
		try:
			self.update()
		except LimitError:
			pass

	def acquireFilm(self, *args, **kwargs):
		self.logger.error('Film acquisition not currently supported.')
		return

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None):
		'''
		Tilt series data collection from emtarget.
		'''
		status = self.moveAndPreset(presetdata, emtarget)
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this target')
			return
		try:
			calibrations = self.getCalibrations(presetdata)
		except CalibrationError as e:
			self.logger.error('Calibration error: %s' % e) 
			return 'failed'
		high_tension, pixel_size = calibrations
				
		self.logger.info('Pixel size: %g meters.' % pixel_size)

		cal = self.getTiltDefocusDelta(presetdata['tem'])
		if cal:
			self.prediction.setCalibratedDefocusDeltas(cal['tilts'],cal['defocus deltas'])
		else:
			self.prediction.setCalibratedDefocusDeltas([-math.pi/2,math.pi/2],[0.0,0.0])
		try:
			self.update()
		except LimitError:
			return 'failed'

		tilts = self.tilts.getTilts()
		exposures = self.exposure.getExposures()
		tilt_index_sequence = self.tilts.getIndexSequence()
		target_adjust_points = self.tilts.getTargetAdjustIndices()
		
		# based on tilt group
		n_groups = len(tilts) 
		for g in range(n_groups):
			self.initGoodPredictionInfo(presetdata, g)

		collect = self.getCollectionObject(target)
		collect.node = self
		collect.session = self.session
		collect.logger = self.logger
		collect.instrument = self.instrument
		collect.settings = self.settings.copy()
		collect.preset = presetdata
		collect.target = target
		collect.parentpreset = target['preset']
		collect.emtarget = emtarget
		collect.viewer = self.panel.viewer
		collect.player = self.player
		collect.pixel_size = pixel_size
		collect.tilts = tilts
		collect.target_adjust_points = target_adjust_points
		# use settings
		collect.tilt_order = self.settings['tilt order']
		collect.tilt_index_sequence = tilt_index_sequence
		collect.exposures = exposures
		collect.prediction = self.prediction
		collect.setStatus = self.setStatus
		collect.reset_tilt = self.targetlist_reset_tilt
		#TODO add tracking preset to this....

		self.logger.info('Set stage position alpha to %.2f degrees according to targetlist' % math.degrees(self.targetlist_reset_tilt))
		self.instrument.tem.StagePosition = {'a': self.targetlist_reset_tilt}
		time.sleep(self.settings['tilt pause time'])
		try:
			collect.start()
		except leginon.tomography.collection.Abort:
			return 'aborted'
		except leginon.tomography.collection.Fail:
			return 'failed'

		# ignoring wait for process
		#self.publishDisplayWait(imagedata)

		return 'ok'
	
	def getCollectionObject(self,target):
		return leginon.tomography.collection.Collection()

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
		except leginon.calibrationclient.NoMatrixCalibrationError as e:
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
		except leginon.calibrationclient.NoMatrixCalibrationError as e:
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
		try:
			self.update()
			tilts = self.tilts.getTilts()
			# need to do both tilt groups
			for g in range(len(tilts)):
				self.initGoodPredictionInfo(tiltgroup=g)
		except LimitError:
			pass

	def adjusttarget(self,preset_name,target,emtarget):
		self.declareDrift('tilt')
		# Force transform adjustment on tomography
		if self.settings['adjust for transform'] == 'no':
			self.logger.warning('Force target adjustment for tomography')
			self.settings['adjust for transform'] = 'one'
		targetonimage = target['delta column'],target['delta row']
		target = self.adjustTargetForTransform(target)
		self.logger.info('target adjusted by (%.1f,%.1f) (column, row)' % (target['delta column']-targetonimage[0],target['delta row']-targetonimage[1]))
		emtarget = self.targetToEMTargetData(target)
		presetdata = self.presetsclient.getPresetFromDB(preset_name)
		status = self.moveAndPreset(presetdata, emtarget)
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this adjusted target')
		return emtarget, status

	def removeStageAlphaBacklash(self, tilts, sequence, preset_name, target, emtarget):
		if self.settings['disable backlash correction']:
			# TFS autoloader stage has even weight, and should not need backlash correction.
			sleep_time = max(self.settings['backlash pause time'], 1.0)
			self.logger.info('pausing %.2f s before acquiring first image' % (sleep_time))
			time.sleep(sleep_time)
			return
		self.logger.info('Removing tilt backlash...')
		if len(sequence) < 2:
			raise ValueError

		## change to parent preset
		try:
			parentname = target['image']['preset']['name']
		except:
			self.logger.info('no parent preset name. skip alpha backlash correction')
			adjust = False
		else:
			adjust = True

		## acquire parent preset image, initial image
		if adjust:
			isoffset = self.getImageShiftOffset()
			self.presetsclient.toScope(parentname)
			self.setImageShiftOffset(isoffset)
			sleep_time = max(self.settings['backlash pause time'], 1.0)
			self.logger.info('pausing %.2f s before acquiring image' % (sleep_time))
			time.sleep(sleep_time)
			imagedata0 = self.acquireCorrectedCameraImageData(0)
			self.panel.viewer.addImage(imagedata0['image'])

		## tilt then return in slow increments
		delta = math.radians(5.0)
		n = 5
		increment = delta/n
		if not sequence:
			self.logger.warning('Abort stage alpha backlash correction for lack of tilt sequence')
			return
		seq0 = sequence[0]
		seq1 = sequence[1]
		tilt0 = tilts[seq0[0]][seq0[1]]
		tilt1 = tilts[seq1[0]][seq1[1]]
		if tilt1 - tilt0 > 0:
			sign = -1
		else:
			sign = 1
		alpha = tilt0 + sign*delta
		self.instrument.tem.StagePosition = {'a': alpha}
		time.sleep(1.0)
		for i in range(n):
			alpha -= sign*increment
			self.instrument.tem.StagePosition = {'a': alpha}
			time.sleep(1.0)

		if adjust:
			## acquire parent preset image, final image
			imagedata1 = self.acquireCorrectedCameraImageData(1)
			self.panel.viewer.addImage(imagedata1['image'])

			## return to tomography preset
			if emtarget['movetype'] == 'image shift':
				presetdata = self.presetsclient.getPresetFromDB(preset_name)
				self.moveAndPreset(presetdata, emtarget)
			else:
				self.presetsclient.toScope(preset_name)
				self.setImageShiftOffset(isoffset)				# apply image shift to instrument. 
			
			## find shift between image0, image1
			pc = correlator.phase_correlate(imagedata0['image'], imagedata1['image'], False)
			peakinfo = peakfinder.findSubpixelPeak(pc, lpf=1.5)
			subpixelpeak = peakinfo['subpixel peak']
			shift = correlator.wrap_coord(subpixelpeak, imagedata0['image'].shape)
			shift = {'row': shift[0], 'col': shift[1]}
			s = (shift['col'], shift['row'])
			self.panel.viewer.setXC(pc, s)
			## transform pixel to image shift
			oldscope = imagedata0['scope']
			newscope = self.calclients['image shift'].transform(shift, oldscope, imagedata0['camera'])
			ishiftx = newscope['image shift']['x'] - oldscope['image shift']['x']
			ishifty = newscope['image shift']['y'] - oldscope['image shift']['y']

			oldishift = self.instrument.tem.ImageShift
			newishift = {'x': oldishift['x'] + ishiftx, 'y': oldishift['y'] + ishifty}
			self.logger.info('adjusting imageshift after backlash: dx,dy = %s,%s' % (ishiftx,ishifty))
			self.instrument.tem.ImageShift = newishift			
			self.panel.viewer.clearImages()

	def initGoodPredictionInfo(self,presetdata=None, tiltgroup=0):
		# FIX ME: This can be simplified now that we define tilt group in prediction
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
				query_data['tilt group'] = tiltgroup
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
						# If only Tomography2 tracking was run previously, models are not in paramdict
						if 'phi' not in list(paramdict.keys()):
							continue
						# Tomography2 tracking leaves these as None.  They are not useful
						if paramdict['phi'] is None and paramdict['optical axis'] is None and paramdict['z0'] is None:
							continue
						if paramdict['phi']==0 and paramdict['optical axis']==0 and paramdict['z0']==0:
							continue
						cor = predictinfo['correlation']
						dist = math.hypot(cor['x'],cor['y'])
						if dist and dist <= model_error_limit:
								goodprediction = predictinfo
								self.logger.info('good calibration found at %d x mag' % (mag,))
								break
					if goodprediction is not None:
						break
				if goodprediction is not None:
						break
		
		if self.settings['model mag'] == 'custom values':
			goodprediction = None
		if goodprediction is None:
			if self.settings['model mag'] == 'custom values':
				# initialize phi, offset by tilt direction
				offsetlist = [self.settings['offset'],self.settings['offset2']]
				philist = [self.settings['phi'],self.settings['phi2']]
				if tiltgroup == 1:
					# tilt toward negative
					axis_offset = offsetlist[1]
					phi = math.radians(philist[1])
					custom_z0 = self.settings['z02']
				else:
					# tilt toward positive
					axis_offset = offsetlist[0]
					phi = math.radians(philist[0])
					custom_z0 = self.settings['z0']
				custom_z0 *= (1e-6)/presetimage_pixel_size
				optical_axis = axis_offset*(1e-6)/presetimage_pixel_size
				params = [phi, optical_axis, custom_z0]
			else:
				params = [0, 0, 0]
		else:
			scale = prediction_pixel_size / presetimage_pixel_size
			paramsdict = goodprediction['predicted position']
			params = [paramsdict['phi'], paramsdict['optical axis']*scale, paramsdict['z0']*scale]
		if not self.settings['use z0'] and self.settings['model mag'] != 'custom values':
			params[2] = 0

		# specify which tilt group to set value on
		self.prediction.setCurrentTiltGroup(tiltgroup)
		# set values in prediction
		self.prediction.setParameters(tiltgroup,params)
		self.prediction.setFixedParameters(tiltgroup,params)
		self.prediction.image_pixel_size = presetimage_pixel_size
		self.prediction.ucenter_limit = self.settings['z0 error']*(1e-6)
		self.prediction.fixed_model = self.settings['fixed model']
		# need to specify tilt group

		phi_degree = math.degrees(params[0])
		offset_um = params[1]*presetimage_pixel_size/(1e-6)
		z0_um = params[2]*presetimage_pixel_size/(1e-6)

		# tilt direction group string for display
		s = ['positive','negative']
		self.logger.info('Initialize %s tilt model to (phi,offset,z0) = (%.2f deg, %.2f um, %.2f um)' % (s[tiltgroup],phi_degree,offset_um,z0_um))
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
		'''
		Add previous tilt series data points in the session to Prediction class instance.
		'''
		initializer = {
			'session': self.session,
		}
		query_data = leginon.leginondata.TiltSeriesData(initializer=initializer)
		results = self.research(query_data)
		results.reverse()

		series_ids = []
		settings = {}
		positions = {}
		image_pixel_sizes = {}
		
		for result in results:
			key = result.dbid
			series_ids.append(key)
			settings[key] = result
			positions[key] = []
			image_pixel_sizes[key] = []

		initializer = {
			'session': self.session,
		}
		query_data = leginon.leginondata.TomographyPredictionData(initializer=initializer)
		results = self.research(query_data)
		results.reverse()
				
		# Load Prediction sorted by tilt series 
		for result in results:
			image = result.special_getitem('image', True, readimages=False)
			tilt_series = image['tilt series']
			image_pixel_sizes[tilt_series.dbid] = result['pixel size']
			tilt = image['scope']['stage position']['a']
			position = result['position']
			group = result['tilt group']
			positions[tilt_series.dbid].append((group, tilt, position))

		# series_ids are tilt series dbid
		for key in series_ids:
			self.prediction.image_pixel_size = image_pixel_sizes[key]
			start = settings[key]['tilt start']
			tmin = settings[key]['tilt min']
			tmax = settings[key]['tilt max']

			# add a tilt series to prediction
			self.prediction.newTiltSeries()
			# add a new tilt group in that tilt series
			self.prediction.newTiltGroup()
			self.prediction.newTiltGroup()
			# add tilt angles and positions in the tilt group
			for group, tilt, position in positions[key]:
				self.prediction.setCurrentTiltGroup(group)
				self.prediction.addPosition(tilt, position)

		n_groups = len(self.prediction.tilt_series_list)
		n_points = 0
		for tilt_series in self.prediction.tilt_series_list:
			for tilt_group in tilt_series.tilt_groups:
				n_points += len(tilt_group)
		m = 'Loaded %d points from %d previous series' % (n_points, n_groups)
		self.logger.info(m)		

	def measureDose(self, preset_name):
		request_data = leginon.leginondata.MeasureDoseData()
		request_data['session'] = self.session
		request_data['preset'] = preset_name
		self.publish(request_data, database=True, pubevent=True, wait=True)

	def tuneEnergyFilter(self, presetname):
		'''
		Overwrite the same function in Acquisition.py so that it does
		not do anything when accessed from tilt series acquisition.
		'''
		pass
	
	def processTargetData(self, *args, **kwargs):
		self.setStatus('waiting')
		# unlike acquisition, tomography condition need to be fixed per target.
		self.fixCondition()
		self.setStatus('processing')
		preset_name = self.settings['preset order'][-1]
		if self.settings['align zero loss peak']:
			self.alignZeroLossPeak(preset_name)
		if self.settings['measure dose']:
			self.measureDose(preset_name)
		try:

			acquisition.Acquisition.processTargetData(self, *args, **kwargs)
		except Exception as e:
			raise
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
		except leginon.calibrationclient.NoMatrixCalibrationError as e:
			self.logger.error('Measurement failed without calibration: %s' % e)
			return None
		delta_defocus = result['defocus']
		fit = result['min']
		return delta_defocus, fit
	
if __name__ == '__main__':
	import pickle as pickle
	tomoargs = pickle.load(open('tomoargs.p','rb'))
	tomonode = Tomography('Tomography',tomoargs,None) 
	pdb.set_trace()

