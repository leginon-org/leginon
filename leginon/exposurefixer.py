# $Source: /ami/sw/cvsroot/pyleginon/reference.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2006-10-13 04:13:07 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $
import math
from leginon import presetadjuster
from leginon import leginondata
import event
import gui.wx.ExposureFixer

class ExposureFixer(presetadjuster.PresetAdjuster):
	# relay measure does events
	eventinputs = presetadjuster.PresetAdjuster.eventinputs + [event.FixBeamEvent]
	eventoutputs = presetadjuster.PresetAdjuster.eventoutputs
	panelclass = gui.wx.ExposureFixer.ExposureFixerPanel
	settingsclass = leginondata.ExposureFixerSettingsData
	defaultsettings = presetadjuster.PresetAdjuster.defaultsettings
	defaultsettings.update({
		'required dose': 10.0,
		'adjust method': 'exposure time',
		'max exposure time': 1000,
		'max beam diameter': 1e-5,
	})
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.FixBeamEvent]
		self.adjust_methods = ['exposure time','illuminated diameter']
		presetadjuster.PresetAdjuster.__init__(self, *args, **kwargs)

	def getAdjustMethods(self):
		return self.adjust_methods

	def getAdjustment(self):
		if self.settings['adjust method'] == 'exposure time':
			return self.getExposureTimeAdjustment()
		elif self.settings['adjust method'] == 'illuminated diameter':
			return self.getIlluminatedDiameterAdjustment()

	def getExposureTimeAdjustment(self):
		good_exposure = False
		while not good_exposure:
			if self.player.state() == 'stop':
				return {}
			cameradata0 = self.instrument.getData(leginondata.CameraEMData)
			scopedata0 = self.instrument.getData(leginondata.ScopeEMData)
			preset_name = self.settings['correction presets'][0]
			self.presets_client.measureDose(preset_name)
			preset = self.presets_client.getPresetByName(preset_name)
			dose = preset['dose']/1e20
			scale_factor = self.settings['required dose'] / dose
			new_exposure = preset['exposure time'] * scale_factor
			if self.player.state() == 'stop':
				return {}
			if 7 > new_exposure or new_exposure > self.settings['max exposure time']:
				self.logger.error('unacceptable exposure time: Align Gun before continue')
				self.setStatus('user input')
				self.player.pause()
				state = self.player.wait()
				if state == 'stop':
					return {}
				elif state == 'play':
					self.player.play()
					continue
			else:
				self.setStatus('processing')
				good_exposure = True
			self.logger.info('exposure time scale factor: %.2f' % (scale_factor,))
		return {'scale exposure time':scale_factor}

	def measureDose(self, preset_name):
		em_target_data = self.getEMTargetData(preset_name)
		self.publish(em_target_data, database=True)
		self.presets_client.measureDose(preset_name, em_target_data)

	def processScaling(self,presetdata):
		'''
		Returns new preset key and value according to the scale factor.
		The scale factor is based on a linear scale while preset value is not
		necessary so.
		'''
		if self.scale_factor is None:
			return None, None
		# return preset parameter after scaling
		if self.settings['adjust method'] == 'exposure time':
			preset_key = 'exposure time'
			preset_value = presetdata['exposure time'] * self.scale_factor
		elif self.settings['adjust method'] == 'illuminated diameter':
			preset_key = 'intensity'
			preset_value = self.beamsize_client.getIntensityFromAreaScale(presetdata,self.scale_factor)
			if not preset_value:
				self.logger.error('Scaling failed. No beam size calibration available')
		return preset_key, preset_value

	def getImageDimensionLimits(self,preset,scale_factor):
		image_dimension = self.presets_client.getPresetImageDimension(preset['name'])
		beam_radius_min = math.hypot(image_dimension['x'],image_dimension['y'])/2
		self.illuminated_area_min = math.pi * beam_radius_min**2
		self.illuminated_area_max = math.pi * (self.settings['max beam diameter']/2)**2

	def getIlluminatedDiameterAdjustment(self):
		good_illuminated_area = False
		while not good_illuminated_area:
			if self.player.state() == 'stop':
				return {}
			cameradata0 = self.instrument.getData(leginondata.CameraEMData)
			scopedata0 = self.instrument.getData(leginondata.ScopeEMData)
			preset_name = self.settings['correction presets'][0]
			self.presets_client.measureDose(preset_name)
			preset = self.presets_client.getPresetByName(preset_name)
			dose = preset['dose']/1e20
			scale_factor = self.settings['required dose'] / dose
			# The following works only if intensity is from tem illuminated area property
			illuminated_area = self.beamsize_client.getIlluminatedArea(preset)
			new_illuminated_area = illuminated_area / scale_factor
			if self.player.state() == 'stop':
				return {}
			self.getImageDimensionLimits(preset,scale_factor)
			if self.illuminated_area_min > new_illuminated_area or self.illuminated_area_max < new_illuminated_area:
				self.logger.error('unacceptable adjutment: Align Gun before continue')
				self.setStatus('user input')
				self.player.pause()
				state = self.player.wait()
				if state == 'stop':
					return {}
				elif state == 'play':
					self.player.play()
					continue
			else:
				self.setStatus('processing')
				good_illuminated_area = True
			self.logger.info('intensity scale factor: %.2f' % (scale_factor,))
		return {'scale illuminated diameter':scale_factor}

	def updatePreset(self,preset_name, params):
		super(ExposureFixer,self).updatePreset(preset_name, params)
		# also update dose
		self.presets_client.measureDose(preset_name)

