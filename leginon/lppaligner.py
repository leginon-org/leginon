#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#
from leginon import acq as acquisition
from leginon import node, leginondata
from leginon import calibrationclient, lppfit, targetwatcher
import threading
from leginon import event
import time
import math
import traceback
from pyami import imagefun, fftfun, ordereddict
import numpy
import scipy.ndimage as nd
import copy
import leginon.gui.wx.LppAligner
from leginon import player

class NoReferenceBypass(targetwatcher.BypassException):
	pass

class LppAligner(acquisition.Acquisition):
	panelclass = leginon.gui.wx.LppAligner.Panel
	settingsclass = leginondata.LppAlignerSettingsData
	defaultsettings = dict(acquisition.Acquisition.defaultsettings)
	defaultsettings.update({
		'global view offset':0.0,
		'compress ratio':8,
		'xlpp':False,
		'acquire type':'single off-plane image',
		#'phase plate defocus sequence': '(-0.002,-0.0025,-0.003,-0.004)',
		'phase plate defocus sequence': '(-0.002,-0.003,-0.004)',
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.calclients['phase plate plane shift'] = calibrationclient.PhasePlatePlaneShiftCalibrationClient(self)
		self.calclients['ctf'] = calibrationclient.CtfCalibrationClient(self)
		self.deltaz = 0.0
		self.v0 = 0.0
		self.series_id = 1
		self.xt_cycle = 0.000085
		self.acquire_types = ['single off-plane image','on-node reference','global view','lpp defocus series','on-plane xtilt series']

	def setDefocusSeries(self):
		values = eval(self.settings['phase plate defocus sequence']) #defocus in tfs unit
		try:
			self.x1_defocus_series = list(values)
		except TypeError as e:
			if type(values) == type(0.1) or type(values) == type(1):
				values = [values,]
				self.x1_defocus_series = values #defocus in tfs unit
			else:
				raise
		except Exception as e:
			raise

	def setParallelIlluminationOffsetToScope(self,view_type='on-plane'):
		errstr = 'paralllel illumination offset to instrument failed: %s'
		settings_name = '%s view offset' % view_type
		value = self.settings[settings_name]
		try:
			self.instrument.tem.ParallelIlluminationOffset = value
		except:
			self.logger.error(errstr % 'unable to access instrument')
			return
		self.logger.info('set parallel illumination offset to %7.5f' % (value))

	def preAcquire(self, presetdata, emtarget=None, channel=None, reduce_pause=False):
		super(LppAligner,self).preAcquire(presetdata, emtarget, channel, reduce_pause)
		self.v0 = self.instrument.tem.ParallelIlluminationOffset
		self.f0 = self.instrument.tem.PhasePlateFocus
		self.xt0 = self.instrument.tem.PhasePlatePlaneShift
		self.new_f0 = self.f0
		self.new_xt0 = self.xt0.copy()
		self.new_phase_shifts = {}
		self.on_node_slopes = {}
		self.second_order_amps = {}
		for k in self.lpp_axes:
			self.new_phase_shifts[k] = 0.0
			self.on_node_slopes[k] = 0.0
			self.second_order_amps[k] = 0.0
		if self.settings['acquire type'] == 'global view':
			self.setParallelIlluminationOffsetToScope('global')

	def resetParallelIlluminationOffset(self):
		self.instrument.tem.ParallelIlluminationOffset = self.v0
		self.logger.info('Lpp set back to pre acquisition value of (c3 offset,x1): %7.4f' % self.v0)

	def compress(self, arr, rot_angle,ratio):
		shape0 = arr.shape
		arr = nd.rotate(arr, rot_angle,mode='nearest') # angle in degrees
		shape = arr.shape
		pad_axis_len = (shape[1]//ratio)*ratio + int(shape[1]%ratio > 0)*ratio
		pad_shape = list(shape)
		pad_shape[1] = pad_axis_len
		pad_arr = numpy.ones(pad_shape)*arr.mean()
		pad_arr[:,:shape[1]] = arr
		stack_shape = (shape[0],pad_axis_len//ratio,ratio)
		pad_arr = pad_arr.reshape(stack_shape)
		arr = numpy.sum(pad_arr, axis=2)
		cmp_shape = arr.shape
		crop_offset = 0
		if cmp_shape[0] > shape0[0]:
			crop_offset = (cmp_shape[0]-shape0[0]) // 2 # y-dimension may be larger than shape0
		pad_offset = (shape0[1]-cmp_shape[1]) // 2 # x-dimension should be smaller than shape0
		# pad result arr to original shape so that it is easier on webviewer to bin
		final = numpy.ones(shape0)*arr.mean()
		final[:,pad_offset:pad_offset+cmp_shape[1]]=arr[crop_offset:crop_offset+shape0[0],:]
		return final

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		self.lpp_axes = [1]
		if self.settings['xlpp']:
			self.lpp_axes.append(2)
		if self.settings['acquire type'] == 'single off-plane image':
			self._acquireAlignImage(presetdata, emtarget, attempt, target, channel)
		elif self.settings['acquire type'] == 'on-node reference':
			self._acquireOnNodeReference(presetdata, emtarget, attempt, target, channel)
			# also save this position to return to like in Reference nodes.
			# TODO: may need to specify the type of reference for Lpp tuning
			# TODO: would be nice to have a unique name like used in reference node
			targetdata = self.calclients['lpp fringe'].newReferenceTarget(self.imagedata, 0,0)
			targetdata.insert()
			self.calibratePhasePlatePlaneShiftMatrix()
		elif self.settings['acquire type'] == 'global view':
			self._acquireGlobal(presetdata, emtarget, attempt, target, channel)
		elif self.settings['acquire type'] == 'on-plane xtilt series':
			self._acquireOnPlaneXTiltSeries(presetdata, emtarget, attempt, target, channel)
		else:
			self._acquireFocusSeries(presetdata, emtarget, attempt, target, channel)

	def getBase(self):
		'''
		Use current scope data as base
		'''
		dataclass = leginondata.ScopeEMData
		dat = self.instrument.getData(dataclass)
		return dat[self.parameter]

	def makeBaseList(self, basebase, interval, naverage=1):
		baselist = []
		for i in range(naverage):
			delta = i * interval
			basex = basebase['x'] + delta
			basey = basebase['y'] + delta
			newbase = {'x':basex, 'y':basey}
			baselist.append(newbase)
		return baselist

	def makeState(self, value, axis):
		'''
		Make scope state with also lpp defocus
		'''
		scope_state = {self.parameter: {axis: value}}
		delta = self.x1_defocus_series[0]
		scope_state['phase plate focus'] = self.f0+delta
		self.logger.info('phase plate focus changed by %.4f for measurement' % delta)
		return scope_state

	def calibratePhasePlatePlaneShiftMatrix(self):
		'''
		Calibrate matrix that relates image pixel shift and phase plate plane
		shift.  This is copied from MatrixCalibrator.
		This calibration is very sensitive to electron focus on the lpp.
		Parameters used here are based on CZII Krios2 -0.0025 lpp defocus.
		'''
		calclient = self.calclients['phase plate plane shift']
		self.parameter = calclient.parameter()
		im1 = self.imagedata
		fringe_wavelength = 500e-9
		imaging_focal_length = 7e-3
		percent = 25/100.0
		# radians of xtilt value to shift by percentage of the fringe projection
		interval = percent*math.atan2(fringe_wavelength, imaging_focal_length)
		ht = self.imagedata['scope']['high tension']
		mag = self.imagedata['scope']['magnification']
		cam = self.instrument.ccdcamera
		pixsize = calclient.getPixelSize(mag)
		unit_delta = calclient.calculateUnitParameterDelta(cam, mag, pixsize)
		delta = percent * unit_delta
		basebase = self.getBase()
		naverage = 2
		baselist = self.makeBaseList(basebase, interval, naverage)
		settle = 1.0 # settle time in seconds
		corr_type = 'cross'
		peakfinder_lp = 9 # low pass filter to cross-correlation map for peak finding
		shifts = {}
		for axis in ('x','y'):
			shifts[axis] = {'row': 0.0, 'col': 0.0}
			n = 0
			for base in baselist:
				basevalue = base[axis]
				newvalue = basevalue + delta
				state1 = self.makeState(basevalue, axis)
				state2 = self.makeState(newvalue, axis)
				im1 = calclient.acquireImage(state1, settle=settle)
				shiftinfo = calclient.measureScopeChange(im1, state2, settle=settle,correlation_type=corr_type,lp=peakfinder_lp)
				rowpix = shiftinfo['pixel shift']['row']
				colpix = shiftinfo['pixel shift']['col']
				self.logger.info('Shift between images: (%.2f, %.2f)' % (colpix, rowpix))
				totalpix = abs(rowpix + 1j * colpix)
				if totalpix == 0.0:
					raise CalibrationError('total pixel shift is zero')

				actual1 = shiftinfo['previous']['scope'][self.parameter][axis]
				actual2 = shiftinfo['next']['scope'][self.parameter][axis]
				change = actual2 - actual1
				if change == 0.0:
					raise CalibrationError('change in %s is zero' % self.parameter)
				self.logger.info('scope %s axis % s change between images: %s' % (self.parameter,axis,change))

				rowpixelsper = rowpix / change
				colpixelsper = colpix / change
				shifts[axis]['row'] += rowpixelsper
				shifts[axis]['col'] += colpixelsper
				n += 1
			if n:
				shifts[axis]['row'] /= n
				shifts[axis]['col'] /= n
		matrix = calclient.measurementToMatrix(shifts)
		self.logger.debug('Matrix %s' % matrix)
		calclient.storeMatrix(ht, mag, self.parameter, matrix)
		self.resetLppFocus()

	def _acquireAlignImage(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		ref_results = leginondata.LppOnNodeRefData(tem=presetdata['tem'],ccdcamera=presetdata['ccdcamera'], xlpp=self.settings['xlpp']).query(results=1)
		if not ref_results:
			self.need_save_reference = True
			raise NoReferenceError('No reference for on-node lpp alignment found.')
		refdata = ref_results[0]
		delta_f = refdata['delta lpp focus']
		#
		calclient = self.calclients['phase plate plane shift']
		# acquire image with new_f
		try:
			status = self._acquireOffPlaneImage(presetdata, emtarget, attempt, target, channel, delta_f)
			self.calclients['lpp fringe'].setIsXLpp(self.settings['xlpp'])
			if status != 'error':
				self.new_phase_shifts, status, r = self.calclients['lpp fringe'].calculatePhaseShiftCorrectionFromFringeFit(refdata, self.imagedata)
				# correlation method
				self.new_xt0, cor_image, cor_pixelpeak = calclient.calculateNewPhasePlatePlaneShiftByCorrelation(refdata, self.imagedata)
				self.setImage(cor_image, 'Correlation')
				calclient.displayPeak(cor_pixelpeak)
		except Exception as e:
			traceback.print_exc()
			self.logger.error('Failed. off plane alignment not valid: %s' % e)
			return 'error'

	def fitFringe(self, myimage_array):
		self.calclients['lpp fringe'].setIsXLpp(self.settings['xlpp'])
		return self.calclients['lpp fringe'].fitFringe(myimage_array)

	def _acquireOffPlaneImage(self, presetdata, emtarget=None, attempt=None, target=None, channel=None, lpp_delta_focus=None):
		'''
		save an image used as reference or to compare with
		'''
		#
		reduce_pause = self.onTarget
		status = self.moveAndPreset(presetdata, emtarget)
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this target')
			return status
		defaultchannel = self.preAcquire(presetdata, emtarget, channel, reduce_pause)
		args = (presetdata, emtarget, defaultchannel)
		try:
			lpp_focus = self.f0 + lpp_delta_focus
			self.logger.info('setting phase plate to %.8f' % lpp_focus)
			self.cyclePhasePlateFocus(self.f0, lpp_focus)
			time.sleep(self.settings['pause time'])
			if self.settings['background']:
				self.clearCameraEvents()
				t = threading.Thread(target=self.acquirePublishDisplayWait, args=args)
				t.start()
				self.waitExposureDone()
			else:
				self.acquirePublishDisplayWait(*args)
			myimage = self.imagedata['image']
		except Exception as e:
			self.logger.error('failed to acquire image, aborting: %s' % e)
			raise RuntimeError('Acquisition Failed: %e' % e)
		self.resetLppFocus()
		is_failed = self.resetComaCorrection()
		if is_failed:
			self.player.pause()
		return status

	def _acquireOnNodeReference(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		'''
		save an image used as reference.
		'''
		self.setDefocusSeries()
		delta_f = self.x1_defocus_series[0]
		try:
			status = self._acquireOffPlaneImage(presetdata, emtarget, attempt, target, channel, delta_f)
			if status != 'error':
				r = self.fitFringe(self.imagedata['image'])
		except Exception as e:
			self.logger.error('Failed. on-node reference not saved: %s' % e)
			return

		q = leginondata.LppOnNodeRefData(
				session=self.session,
				reference=self.imagedata,
				tem=self.imagedata['scope']['tem'],
				ccdcamera=self.imagedata['camera']['ccdcamera'],
				xlpp=self.settings['xlpp'],
		)
		q['delta lpp focus'] = delta_f
		for k in r.keys():
			q['lpp%d rotation' % k] = r[k]['image_rotation']
			q['lpp%d phase shift' % k] = r[k]['phase_shift_to_max']
			self.logger.info('reference lpp%d phase shift saved at %.1f.' % (k,r[k]['phase_shift_to_max']))
		q.insert(force=True)
		self.calclients['lpp fringe'].saveLppFitInImageComment(self.imagedata, r, True)

	def _acquireFocusSeries(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we acquire a series of phase plate focus and use
		them to correct the on-plane and on-node condition
		'''
		reduce_pause = self.onTarget
		status = self.moveAndPreset(presetdata, emtarget)
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this target')
			return status
		defaultchannel = self.preAcquire(presetdata, emtarget, channel, reduce_pause)
		args = (presetdata, emtarget, defaultchannel)
		self.setDefocusSeries()
		data = {}
		for k in self.lpp_axes:
			data[k] = []
		for i, df in enumerate(self.x1_defocus_series):
			self.series_id = i+1 #base 1
			try:
				new_f = self.f0 + df
				self.logger.info('setting phase plate to %.8f' % new_f)
				self.cyclePhasePlateFocus(self.f0, new_f)
				time.sleep(self.settings['pause time'])
				if self.settings['background']:
					self.clearCameraEvents()
					t = threading.Thread(target=self.acquirePublishDisplayWait, args=args)
					t.start()
					self.waitExposureDone()
				else:
					self.acquirePublishDisplayWait(*args)
				myimage = self.imagedata['image']
			except Exception as e:
				self.logger.error('failed to acquire image, aborting: %s' % e)
				self.resetLppFocus()
				break
			finally:
				try:
					number_of_lpp = 1
					if self.settings['xlpp']:
						number_of_lpp = 2
					r = lppfit.run_fringe_fit(myimage, number_of_lpp)
					for k in r.keys():
						data[k].append((new_f, r[k]['wave_period'], r[k]['phase_shift_to_max']))
				except Exception as e:
					self.logger.warning('failed fitting, skipping: %s' % e)
				finally:
					self.resetLppFocus()
		is_failed = self.resetComaCorrection()
		if is_failed:
			self.player.pause()
		new_f0 = {} # sequence of new_f0 at each lpp axis
		# Note: result_phase_shifts are not good enough to find on-node.
		# Not applied as self.new_phase_shifts
		result_phase_shifts = {} # sequence of phase_shifts at each lpp axis
		try:
			for k in data.keys():
				new_f0[k], result_phase_shifts[k], self.on_node_slopes[k], self.second_order_amps[k] = lppfit.calculateOnPlaneOnNode(numpy.array(data[k]), is_over_focus=False)
				self.logger.info('Calculated LPP focus at %.8f, phase shift needed at %s' % (new_f0[k], result_phase_shifts[k]))
			self.new_f0 = sum(new_f0.values())/len(new_f0.keys())
		except Exception as e:
			self.logger.error('Error calculating on-plane and on-node values: %s' % e)
			return status

	def _acquireOnPlaneXTiltSeries(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we acquire a series of phase plate plane shift and use
		them to find and move to on-node.
		'''
		reduce_pause = self.onTarget
		status = self.moveAndPreset(presetdata, emtarget)
		self.calclients['lpp fringe'].setIsXLpp(self.settings['xlpp'])
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this target')
			return status
		defaultchannel = self.preAcquire(presetdata, emtarget, channel, reduce_pause)
		args = (presetdata, emtarget, defaultchannel)
		try:
			wave_transform = self.retrieveWaveTransformCalibration()
		except Exception as e:
			self.logger.error(e)
			return
		wave_xtlength = math.sqrt(numpy.sum(wave_transform*wave_transform)/2)
		step_fraction = 0.1
		self.xtilt_series = step_fraction*numpy.array(((-1,0),(0,0),(1,0),(0,-1),(0,1))).T
		self.xtilt_series = numpy.dot(wave_transform,self.xtilt_series)
		data_shape = self.xtilt_series.shape[1]
		# add to current value
		xt0 = numpy.array((self.xt0['x'],self.xt0['y']))
		xt0_series = numpy.tile(xt0,(data_shape,1)).T
		self.xtilt_series += xt0_series
		is_failed = False
		phase_search = (10,170)
		# initialize data record
		data = {'xt':self.xtilt_series,'mean':numpy.zeros(data_shape),'std':numpy.zeros(data_shape),'phase_shift':numpy.zeros(data_shape)}
		for i in range(data_shape):
			try:
				xt = {'x':data['xt'][0,i],'y':data['xt'][1,i]}
				self.instrument.tem.PhasePlatePlaneShift = xt
				time.sleep(self.settings['pause time'])
				if self.settings['background']:
					self.clearCameraEvents()
					t = threading.Thread(target=self.acquirePublishDisplayWait, args=args)
					t.start()
					self.waitExposureDone()
				else:
					self.acquirePublishDisplayWait(*args)
				myimage = self.imagedata['image']
			except Exception as e:
				self.logger.error('failed to acquire image, aborting: %s' % e)
				self.resetLppFocus()
				is_failed = True
				break
			finally:
				try:
					# calculate std
					data['mean'][i] = myimage.mean()
					data['std'][i] = myimage.std()
					defocus_avg, ctfvalues = self.calclients['ctf'].measureImageCtf(self.imagedata, phase_search,'temp1')
					data['phase_shift'] = ctfvalues['extra_phase_shift']
				except Exception as e:
					self.logger.warning('failed fitting, skipping: %s' % e)
				finally:
					self.resetLppFocus()
		is_failed = self.resetComaCorrection() or is_failed
		if is_failed:
			self.player.pause()
		for k in self.lpp_axes:
			self.new_phase_shifts[k]=0.0
		# Find and set the best xt state
		try:
			# use the state with the highest value
			ind = numpy.argmax(data['phase_shift'])
			new_xt0 = {'x':data['xt'][ind][0],'y':data['xt'][ind][1]}
			if abs(new_xt0['x'] -self.xt0['x']) > 0.5*step_fraction*wave_xtlength or abs(new_xt0['y']-self.xt0['y']) > 0.5*step_fraction*wave_xtlength:
				self.logger.warning('xt applied %.8f,%.8f' % (new_xt0['x'],new_xt0['y']))
				self.instrument.tem.PhasePlatePlaneShift = new_xt0
		except Exception as e:
			raise
			self.logger.error('Error calculating on-plane and on-node values: %s' % e)
			return status

	def setOnPlaneOnNode(self):
		self.calclients['lpp fringe'].setOnPlaneOnNode()

	def guiSetOnPlaneOnNode(self):
		'''
		set on-plane and on-node and save the xtilt calibration
		'''
		self.calclients['lpp fringe'].setIsXLpp(self.settings['xlpp'])
		self.xtilt_cal = self.settings
		self.setOnPlaneOnNode()

	def retrieveWaveTransformCalibration(self):
		caldata = self.calclients['lpp fringe'].retrieveLppCalibration()
		if caldata:
			wave_transform = numpy.array([
				[caldata['lpp1 wave xtilt vector x'],
				caldata['lpp1 wave xtilt vector y']],
				[caldata['lpp2 wave xtilt vector x'],
				caldata['lpp2 wave xtilt vector y']],
		])
		return wave_transform


	def resetLppFocus(self):
		self.instrument.tem.PhasePlateFocus = self.f0
		self.logger.info('phase plate focus reset to %.8f' % self.f0)
		self.instrument.tem.PhasePlatePlaneShift = self.xt0
		msg = 'Reset LPP focus to %.8f, x-tilt to x:%.4e,y:%.4e' % (self.f0, self.xt0['x'],self.xt0['y'])
		self.logger.info(msg)

	def setImageFilename(self, imagedata):
		super(LppAligner, self).setImageFilename(imagedata)
		if self.settings['acquire type'] == 'lpp defocus series':
			imagedata['filename'] = imagedata['filename']+'_%d' % self.series_id

	def _acquireGlobal(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we acquire an image and then compress along x-axis 
		'''
		reduce_pause = self.onTarget
		status = self.moveAndPreset(presetdata, emtarget)
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this target')
			return status

		defaultchannel = self.preAcquire(presetdata, emtarget, channel, reduce_pause)
		args = (presetdata, emtarget, defaultchannel)
		try:
			if self.settings['background']:
				self.clearCameraEvents()
				t = threading.Thread(target=self.acquirePublishDisplayWait, args=args)
				t.start()
				self.waitExposureDone()
			else:
				self.acquirePublishDisplayWait(*args)
			if self.settings['compress ratio'] > 1:
				myimage = self.imagedata['image']
				# guess 8 fringes.
				peaks = lppfit.get_fringe_angle_period(myimage, 1, 8)
				key = 1
				image_rotation = peaks[key]['image_rotation']
				self.cmp_image = self.compress(myimage, -image_rotation, self.settings['compress ratio'])
				self.setImage(self.cmp_image, 'Compressed')
				if self.settings['save image']:
					self.saveCompressed()
		except:
			self.resetParallelIlluminationOffset()
			self.resetComaCorrection()
			raise
		finally:
			self.resetParallelIlluminationOffset()
			is_failed = self.resetComaCorrection()
			if is_failed:
				self.player.pause()
		return status

	def saveCompressed(self):
		init = self.imagedata
		init_shape = init.imageshape()
		cmp_im = self.cmp_image
		cam = leginondata.CameraEMData(initializer=init['camera'])
		# preset
		availablepresets = self.getPresetNames()
		# filename just add to the imagedata preset
		filename = init['filename'] + '-cmpr'
		new_name = self.imagedata['preset']['name']+'-cmpr'
		preset = leginondata.PresetData(initializer=self.imagedata['preset'],name=new_name)
		if new_name not in availablepresets:
			# add new name and append ordernumber
			preset['number'] = len(availablepresets)+1
		else:
			# keep the old order number
			old_p = self.getPresetByName(new_name)
			preset['number'] = old_p['number']
		preset.insert()
		cmp_imdata = leginondata.AcquisitionImageData(initializer=self.imagedata, image=cmp_im, filename=filename, camera=cam, preset=preset)
		cmp_imdata.insert(force=True)
		self.logger.info('Compressed image saved to database.')
		cdata = leginondata.ImageCommentData(session=self.session, image=cmp_imdata)
		xtilt = self.instrument.tem.PhasePlatePlaneShift
		xshift = self.instrument.tem.PhasePlatePlaneTilt
		txt = 'xtilt (x,y): (%.5f,%5f); xshift: (%5f,%5f)' % (xtilt['x'],xtilt['y'], xshift['x'],xshift['y'])
		cdata['comment'] = txt
		cdata.insert(force=True)

	def xTiltToScope(self):
		calclient = self.calclients['phase plate plane shift']
		center = calclient.retrieveXTiltCenter()
		if center is None:
			return
		self.instrument.tem.PhasePlatePlaneShift = center
		self.logger.info('xtilt center sent as x: %.3f, y: %.3f mrad' % (center['x']*1e3, center['y']*1e3))

	def xTiltFromScope(self):
		calclient = self.calclients['phase plate plane shift']
		calclient.saveXTiltCenter()
