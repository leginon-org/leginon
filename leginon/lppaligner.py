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
		'rotation':0.0,
		'acquire type':'single off-plane image',
		#'phase plate defocus sequence': '(-0.002,-0.0025,-0.003,-0.004)',
		'phase plate defocus sequence': '(-0.002,-0.003,-0.004)',
		'ref on_node xtilt x': 0.0,
		'ref on_node xtilt y': 0.0,
		'one wavelength xtilt x': 0.0,
		'one wavelength xilt y': 0.000165,
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.deltaz = 0.0
		self.v0 = 0.0
		self.series_id = 1
		self.xt_cycle = 0.000165
		self.acquire_types = ['single off-plane image','on-node reference','global view','lpp defocus series']

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
		self.new_phase_shift = 0
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
		if self.settings['acquire type'] == 'single off-plane image':
			self._acquireAlignImage(presetdata, emtarget, attempt, target, channel)
		elif self.settings['acquire type'] == 'on-node reference':
			self._acquireOnNodeReference(presetdata, emtarget, attempt, target, channel)
		elif self.settings['acquire type'] == 'global view':
			self._acquireGlobal(presetdata, emtarget, attempt, target, channel)
		else:
			self._acquireFocusSeries(presetdata, emtarget, attempt, target, channel)

	def _acquireAlignImage(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		ref_results = leginondata.LppOnNodeData(tem=presetdata['tem'],ccdcamera=presetdata['ccdcamera']).query(results=1)
		if not ref_results:
			self.need_save_reference = True
			raise NoReferenceError('No reference for on-node lpp alignment found.')
		refdata = ref_results[0]
		delta_f = refdata['delta lpp focus']
		# acquire image with new_f
		status, period_fit, phase_shift_needed = self._acquireOffPlaneImage(presetdata, emtarget, attempt, target, channel, delta_f)
		print('focus, period, phase_shift_to_apply')
		try:
			phase_diff = phase_shift_needed - refdata['phase shift']
			self.new_phase_shift = phase_diff
		except Exception as e:
			self.logger.error('Error calculating on-node values: %s' % e)
			return status
		self.logger.info('phase shift correction = %.5f' % self.new_phase_shift)
		return status

	def _acquireOffPlaneImage(self, presetdata, emtarget=None, attempt=None, target=None, channel=None, lpp_delta_focus=None):
		'''
		save an image used as reference.
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
			self.logger.info('phase plate focus set to %.8f' % lpp_focus)
			self.instrument.tem.PhasePlateFocus = lpp_focus
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
			return 'error', 1, 0.0
		finally:
			try:
				amp_fit, freq_fit, phase_fit, offset_fit, period_fit, phase_shift_needed = lppfit.run_fringe_fit(myimage, self.settings['rotation'])
			except Exception as e:
				self.logger.warning('failed fitting, skipping: %s' % e)
			finally:
				self.resetLppFocus()
		is_failed = self.resetComaCorrection()
		if is_failed:
			self.player.pause()
		return status, period_fit, phase_shift_needed

	def _acquireOnNodeReference(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		'''
		save an image used as reference.
		'''
		self.x1_defocus_series = list(eval(self.settings['phase plate defocus sequence'])) #defocus in tfs unit
		self.x1_defocus_series.sort()
		if self.x1_defocus_series[0] < 0:
			# always starts from value closest to f0
			self.x1_defocus_series.reverse()
		delta_f = self.x1_defocus_series[-1]
		status, period_fit, phase_shift_needed = self._acquireOffPlaneImage(presetdata, emtarget, attempt, target, channel, delta_f)

		q = leginondata.LppOnNodeData(
				session=self.session,
				reference=self.imagedata,
				tem=self.imagedata['scope']['tem'],
				ccdcamera=self.imagedata['camera']['ccdcamera'],
		)
		q['phase shift'] = phase_shift_needed
		q['delta lpp focus'] = delta_f
		q.insert(force=True)
		self.logger.info('reference phase shift saved at %.1f.' % phase_shift_needed)

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
		self.x1_defocus_series = list(eval(self.settings['phase plate defocus sequence'])) #defocus in tfs unit
		self.x1_defocus_series.sort()
		if self.x1_defocus_series[0] < 0:
			# always starts from value closest to f0
			self.x1_defocus_series.reverse()
		data = []
		for i, df in enumerate(self.x1_defocus_series):
			self.series_id = i+1 #base 1
			try:
				new_f = self.f0 + df
				self.logger.info('phase plate focus set to %.8f' % new_f)
				self.instrument.tem.PhasePlateFocus = new_f
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
				print(e)
				self.logger.error('failed to acquire image, aborting: %s' % e)
				self.resetLppFocus()
				break
			finally:
				try:
					amp_fit, freq_fit, phase_fit, offset_fit, period_fit, phase_shift_needed = lppfit.run_fringe_fit(myimage, self.settings['rotation'])
					data.append((new_f, period_fit, phase_shift_needed))
				except Exception as e:
					self.logger.warning('failed fitting, skipping: %s' % e)
				finally:
					self.resetLppFocus()
		is_failed = self.resetComaCorrection()
		if is_failed:
			self.player.pause()
		print('focus, period, phase_shift_to_apply')
		print(numpy.array(data))
		try:
			self.new_f0, self.new_phase_shift = lppfit.calculateOnPlaneOnNode(numpy.array(data), is_over_focus=False)
			self.logger.info('Calculated LPP x1 lens at %.8f, phase shift needed at %.1f' % (self.new_f0, self.new_phase_shift))
		except Exception as e:
			self.logger.error('Error calculating on-plane and on-node values: %s' % e)
			return status

	def setOnPlaneOnNode(self):
		try:
			self.instrument.tem.PhasePlateFocus = self.new_f0
			# set xtilt
			self.new_xtilt = {'x':self.settings['ref on_node xtilt x'],
								'y': self.settings['ref on_node xtilt y'] }
			self.new_xtilt['x'] += self.new_phase_shift*self.settings['one wavelength xtilt x']
			self.new_xtilt['y'] += self.new_phase_shift*self.settings['one wavelength xtilt y']
			self.logger.info('Calculated LPP new xtilt as %s' % (self.new_xtilt))
			self.instrument.tem.PhasePlatePlaneShift = self.new_xtilt
			self.logger.info('Set LPP x1 lens to %.8f, x-tilt to %.6f' % (self.new_f0, self.new_xtilt))
		except Exception as e:
			self.logger.error('Error setting on-plane and on-node values')
			self.resetLppFocus()
			raise

	def resetLppFocus(self):
		self.instrument.tem.PhasePlateFocus = self.f0
		self.instrument.tem.PhasePlatePlaneShift = self.xt0

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
			myimage = self.imagedata['image']
			self.cmp_image = self.compress(myimage, self.settings['rotation'], self.settings['compress ratio'])
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
