
import threading
import time
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
		{'xlpp': False}
	)
	eventinputs = referencetimer.ReferenceTimer.eventinputs + [event.AlignLppPublishEvent, event.FixLppAlignmentEvent]
	panelclass = leginon.gui.wx.LppAlignTimer.LppAlignTimerPanel
	requestdata = leginondata.AlignLppRequestData

	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.AlignLppPublishEvent]
		referencetimer.ReferenceTimer.__init__(self, *args, **kwargs)
		self.addEventInput(event.FixLppAlignmentEvent, self.handleFixAlignmentEvent)
		self.ref_position = None
		self.start()

	def handleFixAlignmentEvent(self, evt):
		# called from another Reference Class to execute after target move
		# but before execution.
		self.logger.info('handling request to execute alignment in place')
		if self.settings['bypass']:
			self.logger.info('Bypass alignment fixing')
			status = 'bypass'
			self.confirmEvent(evt, status=status)
			return
		self.setStatus('processing')
		self.panel.playerEvent('play')
		status = self.align(None)
		self.confirmEvent(evt, status=status)
		self.setStatus('idle')
		self.panel.playerEvent('stop')

	def _setRequestPreset(self, request_preset_name):
		preset = self.presets_client.getCurrentPreset()
		if preset['name'] != request_preset_name:
			self.logger.info('Change preset to requested %s' % request_preset_name)
			self.presets_client.toScope(request_preset_name)
		return self.presets_client.getCurrentPreset()

	def align(self, ccd_camera=None):
		if not ccd_camera:
			ccd_camera = self.instrument.ccdcamera
		ccd_name = ccd_camera._name
		if not ccd_camera.EnergyFiltered:
			self.logger.warning('No energy filter on this instrument.')
			return
		try:
			# TODO acquire off-plane image
			if not ccd_camera.EnergyFilter:
				self.logger.warning('Energy filtering is not enabled.')
				return 'bypass'
			self.positionCamera(camera_name=ccd_name)
			self.openColumnValveBeforeExposure()
			self.logger.info('Aligning ZLP with %s camera' % ccd_name)
			ccd_camera.alignEnergyFilterZeroLossPeak()
			m = 'Energy filter zero loss peak aligned.'
			self.logger.info(m)
		except AttributeError:
			m = 'Energy filter methods are not available on this instrument.'
			self.logger.warning(m)
		except Exception as e:
			raise
			s = 'Energy filter align zero loss peak failed: %s.'
			self.logger.error(s % e)

	def execute(self, request_data=None):
		'''
		Execute without moving. Used in testing and handling the
		request after moving and set preset. request_data is not used.
		'''
		self.lpp_axes = [1]
		if self.settings['xlpp']:
			self.lpp_axes.append(2)
		preset = self.presets_client.getCurrentPreset()
		tem = preset['tem']
		ccdcamera = preset['ccdcamera']
		xtilt_results = leginondata.LppCalibrationData(tem=tem, ccdcamera=ccdcamera, xlpp=self.settings['xlpp']).query(results=1)
		ref_results = leginondata.LppOnNodeRefData(tem=tem,ccdcamera=ccdcamera, xlpp=self.settings['xlpp']).query(results=1)
		if not ref_results or not xtilt_results:
			self.logger.error('No reference or xtilt cycle calibration for on-node lpp alignment.')
			return
		refdata = ref_results[0]
		self.logger.info('Using %s as the reference' % refdata['reference']['filename'])
		self.xtilt_cal = xtilt_results[0]
		delta_f = refdata['delta lpp focus']
		measure_preset = self.makeMeasurePreset(refdata['reference']['preset'])
		self._setRequestPreset(refdata['reference']['preset']['name'])
		# acquire image with new_f
		self.f0 = self.instrument.tem.PhasePlateFocus
		self.xt0 = self.instrument.tem.PhasePlatePlaneShift
		self.new_f0 = self.f0
		lpp_focus = self.f0 + delta_f
		self.instrument.tem.PhasePlateFocus = lpp_focus
		self.logger.info('phase plate focus set to %.8f' % lpp_focus)
		time.sleep(self.settings['pause time'])
		try:
			self.imagedata = self.newImageData(measure_preset,'%dref' % refdata.dbid)
			filename = self.getMeasureImageFilename(self.imagedata, refdata)
			self.imagedata['filename'] = filename
			self.imagedata.insert()
		except Exception as e:
			self.logger.error(e)
			self.logger.error('failed to acquire image, aborting: %s' % e)
			self.resetLppFocus()
			return
		self.resetLppFocus()
		try:
			myimage = self.imagedata['image']
			self.setImage(myimage, 'Image')
			if self.settings['xlpp']:
					r = lppfit.run_2d_fringe_fit(myimage, (refdata['lpp1 rotation'], refdata['lpp2 rotation']))
			else:
					r = {1:lppfit.run_fringe_fit(myimage, refdata['lpp1 rotation'])}
		except Exception as e:
			self.logger.warning('failed fitting, skipping: %s' % e)
			return
		self.new_phase_shifts = {}
		try:
			# phase shift represent correction needed, so it needs to reverse sign.
			phases = []
			for k in r.keys():
				phase_shift_needed = r[k]['phase_shift_to_max']
				phase_diff = -(phase_shift_needed - refdata['lpp%d phase shift' % k])
				self.new_phase_shifts[k] = lppfit.convert_phase_degrees(phase_diff)
				phases.append('%.2f' % self.new_phase_shifts[k])
		except Exception as e:
			self.logger.error('Error calculating on-node values: %s' % e)
			return
		self.logger.info('phase shift correction = (%s)' % ', '.join(phases))
		#saving
		self.saveLppFitMeasurement(refdata, self.imagedata, r, self.new_phase_shifts)
		self.setOnPlaneOnNode()
		return

	def makeMeasurePreset(self, ref_preset):
		new_name = ref_preset['name']+'-m'
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
		self.logger.info('phase plate focus reset to %.8f' % self.f0)
		self.instrument.tem.PhasePlatePlaneShift = self.xt0

