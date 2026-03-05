
import threading
import time
import math
import traceback
from leginon import leginondata
from leginon import calibrationclient
from leginon import event
from leginon import instrument
from leginon import referencetimer
from leginon import lppfit
import leginon.gui.wx.ReferenceTimer
import leginon.gui.wx.LppAlignTimer

class LppAlignTimer(referencetimer.ReferenceTimer):
	settingsclass = leginondata.LppAlignTimerSettingsData
	# defaultsettings are not the same as the parent class.  Therefore redefined.
	defaultsettings = dict(referencetimer.ReferenceTimer.defaultsettings)
	defaultsettings.update (
		{'xlpp': False,
		'xt offset x': 0.0,
		'xt offset y': 0.0,
		'delta xt threshold': 0.000015,
		}
	)
	eventinputs = referencetimer.ReferenceTimer.eventinputs + [event.AlignLppPublishEvent,]
	panelclass = leginon.gui.wx.LppAlignTimer.LppAlignTimerPanel
	requestdata = leginondata.AlignLppRequestData

	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.AlignLppPublishEvent]
		referencetimer.ReferenceTimer.__init__(self, *args, **kwargs)
		self.ref_position = None
		self.calibration_clients['phase plate plane shift'] = calibrationclient.PhasePlatePlaneShiftCalibrationClient(self)
		self.calibration_clients['lpp fringe'] = calibrationclient.LppCalibrationClient(self)
		self.start()

	def _setRequestPreset(self, request_preset_name):
		preset = self.presets_client.getCurrentPreset()
		if preset['name'] != request_preset_name:
			self.logger.info('Change preset to requested %s' % request_preset_name)
			self.presets_client.toScope(request_preset_name)
		return self.presets_client.getCurrentPreset()

	def execute(self, request_data=None):
		'''
		Execute without moving. Used in testing and handling the
		request after moving and set preset. request_data is not used.
		'''
		self.calibration_clients['lpp fringe'].setIsXLpp(self.settings['xlpp'])
		self.lpp_axes = self.calibration_clients['lpp fringe'].lpp_axes
		self.xtilt_cal = self.calibration_clients['lpp fringe'].xtilt_cal
		#
		preset = self.presets_client.getCurrentPreset()
		tem = preset['tem']
		ccdcamera = preset['ccdcamera']
		ref_results = leginondata.LppOnNodeRefData(tem=tem,ccdcamera=ccdcamera, xlpp=self.settings['xlpp']).query(results=1)
		if not ref_results or not self.xtilt_cal:
			self.logger.error('No reference or xtilt cycle calibration for on-node lpp alignment.')
			return
		refdata = ref_results[0]
		self.logger.info('Using %s as the reference' % refdata['reference']['filename'])
		delta_f = refdata['delta lpp focus']
		self._setRequestPreset(refdata['reference']['preset']['name'])
		# apply offset for image shifted target
		self.addXtOffset(False)
		# acquire image with new_f
		self.f0 = self.instrument.tem.PhasePlateFocus
		self.xt0 = self.instrument.tem.PhasePlatePlaneShift
		self.new_xt0 = self.xt0.copy()
		self.new_f0 = self.f0
		lpp_focus = self.f0 + delta_f
		self.new_phase_shifts = {1:0.0}
		measure_preset = self.makeMeasurePreset(refdata['reference']['preset'])
		if refdata['xlpp']:
			self.new_phase_shifts[2]=0.0
		try:
			max_iter = 10
			# Iterate until stable
			i = 1
			# compare to the value before the request is executed in the
			# first iteration
			last_xt0 = self.new_xt0.copy()
			while True:
				self.logger.info('Iterate until stable, iter=%d' % i)
				new_xt0, delta_xt_magnitude = self._measureShift(refdata, measure_preset,lpp_focus, last_xt0)
				self.logger.info('delta_xt_magnitude %d: %s' % (i, delta_xt_magnitude))
				if delta_xt_magnitude < self.settings['delta xt threshold']:
					# accept the new value
					self.new_xt0 = new_xt0.copy()
					break
				i += 1
				# compare with the last iteration xt0 in the next iteration.
				last_xt0 = new_xt0.copy()
				if i > max_iter:
					self.logger.error('Maximal iteration reached without convergance')
					break
		except Exception as e:
			traceback.print_exc()
			self.logger.error('Error calculating on-node values: %s' % e)
			self.resetLppFocus()
			return
		msg = 'new xt calculated from correlation = (%s)' % self.new_xt0
		self.logger.info(msg)
		# setOnPlaneOnNode will set using self.new_xt0
		self.calibration_clients['lpp fringe'].setOnPlaneOnNode()
		#TODO: saving
		# reset default to the new value since recording correction image
		# will include use resetLppFocus().
		self.xt0 = self.new_xt0.copy()
		correct_preset = self.makeCorrectPreset(refdata['reference']['preset'])
		self._acquireAndSaveMeasureImage(correct_preset, refdata, self.f0)
		# convert back
		self.addXtOffset(True)
		return

	def _acquireAndSaveMeasureImage(self, measure_preset, refdata, lpp_focus):
		self.logger.info('setting phase plate focus to %.8f' % lpp_focus)
		self.cyclePhasePlateFocus(self.f0, lpp_focus)
		time.sleep(self.settings['pause time'])
		try:
			self.logger.info('acquiring image....')
			self.imagedata = self.newImageData(measure_preset,'%dref' % refdata.dbid)
			filename = self.getMeasureImageFilename(self.imagedata, refdata)
			self.imagedata['filename'] = filename
			self.imagedata.insert()
			myimage = self.imagedata['image']
			self.setImage(myimage, 'Image')
		except Exception as e:
			self.logger.error('failed to acquire image, aborting: %s' % e)
			raise
		self.resetLppFocus()

	def _measureShift(self, refdata, measure_preset, lpp_focus, last_xt0):
		self._acquireAndSaveMeasureImage(measure_preset, refdata, lpp_focus)
		try:
			# fringe fit method, not used for now.
			self.new_phase_shifts, status, r = self.calibration_clients['lpp fringe'].calculatePhaseShiftCorrectionFromFringeFit(refdata, self.imagedata)
			# correlation method
			new_xt0, cor_image, cor_pixelpeak = self.calibration_clients['phase plate plane shift'].calculateNewPhasePlatePlaneShiftByCorrelation(refdata, self.imagedata)
			delta_xt_magnitude = math.hypot(new_xt0['x']-last_xt0['x'], new_xt0['y']-last_xt0['y'])
			return new_xt0, delta_xt_magnitude
		except Exception as e:
			self.logger.warning('failed fitting, skipping: %s' % e)
		return

	def addXtOffset(self, is_positive_offset):
		xt0 = self.instrument.tem.PhasePlatePlaneShift
		offsetx = self.settings['xt offset x']
		offsety = self.settings['xt offset y']
		sign = 1 if is_positive_offset else -1
		new_xt0 = {'x':offsetx*sign+xt0['x'], 'y':offsety*sign+xt0['y']}
		self.instrument.tem.PhasePlatePlaneShift = new_xt0
		msg = 'new xt offset to = (%s)' % new_xt0
		self.logger.info(msg)
		return new_xt0

	def makeMeasurePreset(self, ref_preset):
		return self._makeMeasurePreset(ref_preset, 'm')

	def makeCorrectPreset(self, ref_preset):
		return self._makeMeasurePreset(ref_preset, 'c')

	def _makeMeasurePreset(self, ref_preset,postfix='m'):
		new_name = ref_preset['name']+'-'+postfix
		preset = leginondata.PresetData(initializer=ref_preset,name=new_name)
		availablepresets = self.presets_client.getPresetNames()
		if new_name not in availablepresets:
			# add new name and append ordernumber
			preset['number'] = len(availablepresets)+1
		else:
			# keep the old order number
			old_p = self.presets_client.getPresetByName(new_name)
			preset['number'] = old_p['number']
		preset.insert()
		return preset

	def getMeasureImageFilename(self, imagedata, lpp_refdata):
		'''
		Set image filename by next available name of the preset
		because the image does not come from a target list.
		'''
		parts = []
		parts.append(self.session['name'])
		parts.append('%05dlpp' % lpp_refdata['reference'].dbid)
		preset_name = imagedata['preset']['name']
		p = leginondata.PresetData(name=preset_name)
		r = leginondata.AcquisitionImageData(session=self.session, preset=p).query()
		parts.append('%05d%s' % (len(r)+1, preset_name))
		# join them
		filename = '_'.join(parts)
		return filename

	def resetLppFocus(self):
		self.instrument.tem.PhasePlateFocus = self.f0
		self.instrument.tem.PhasePlatePlaneShift = self.xt0
		msg = 'Reset LPP focus to %.8f, x-tilt to x:%.4e,y:%.4e' % (self.f0, self.xt0['x'],self.xt0['y'])
		self.logger.info(msg)
