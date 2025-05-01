
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
		preset = self.presets_client.getCurrentPreset()
		tem = preset['tem']
		ccdcamera = preset['ccdcamera']
		xtilt_results = leginondata.LppCalibrationData(tem=tem, ccdcamera=ccdcamera).query(results=1)
		ref_results = leginondata.LppOnNodeRefData(tem=tem,ccdcamera=ccdcamera).query(results=1)
		if not ref_results or not xtilt_results:
			self.logger.error('No reference or xtilt cycle calibration for on-node lpp alignment.')
			return
		refdata = ref_results[0]
		self.xtilt_cycle = xtilt_results[0]
		delta_f = refdata['delta lpp focus']
		self._setRequestPreset(refdata['reference']['preset']['name'])
		# acquire image with new_f
		self.f0 = self.instrument.tem.PhasePlateFocus
		self.xt0 = self.instrument.tem.PhasePlatePlaneShift
		self.new_f0 = self.f0
		lpp_focus = self.f0 + delta_f
		self.instrument.tem.PhasePlateFocus = lpp_focus
		self.logger.info('phase plate focus set to %.8f' % lpp_focus)
		time.sleep(self.settings['pause time'])
		self.imagedata = self.acquireCorrectedCameraImageData(force_no_frames=True)
		self.resetLppFocus()
		if self.imagedata is None:
			self.logger.error('failed to acquire image, aborting: %s' % e)
			return
		try:
			myimage = self.imagedata['image']
			self.setImage(myimage, 'Image')
			amp_fit, freq_fit, phase_fit, offset_fit, period_fit, phase_shift_needed = lppfit.run_fringe_fit(myimage, refdata['rotation'])
		except Exception as e:
			self.logger.warning('failed fitting, skipping: %s' % e)
			self.resetLppFocus()
			return
		finally:
			self.resetLppFocus()
		try:
			# phase shift represent correction needed, so it needs to reverse sign.
			phase_diff = -(phase_shift_needed - refdata['phase shift'])
			self.new_phase_shift = lppfit.convert_phase_degrees(phase_diff)
		except Exception as e:
			self.logger.error('Error calculating on-node values: %s' % e)
		self.logger.info('phase shift correction = %.5f' % self.new_phase_shift)
		self.setOnPlaneOnNode()
		return

	def resetLppFocus(self):
		self.instrument.tem.PhasePlateFocus = self.f0
		self.logger.info('phase plate focus reset to %.8f' % self.f0)
		self.instrument.tem.PhasePlatePlaneShift = self.xt0

	def setOnPlaneOnNode(self):
		try:
			if self.new_f0 != self.f0:
				self.instrument.tem.PhasePlateFocus = self.new_f0
			# set xtilt
			self.new_xtilt = self.instrument.tem.PhasePlatePlaneShift
			c = 1/360.0
			self.new_xtilt['x'] += self.new_phase_shift*c*self.xtilt_cycle['wave xtilt vector x']
			self.new_xtilt['y'] += self.new_phase_shift*c*self.xtilt_cycle['wave xtilt vector y']
			self.logger.info('Calculated LPP new xtilt as %s' % (self.new_xtilt))
			self.instrument.tem.PhasePlatePlaneShift = self.new_xtilt
			self.logger.info('Set LPP x1 lens to %.8f, x-tilt to x:%.6f,y:%6f' % (self.new_f0, self.new_xtilt['x'],self.new_xtilt['y']))
		except Exception as e:
			self.logger.error('Error setting on-plane and on-node values')
			self.resetLppFocus()
			raise
