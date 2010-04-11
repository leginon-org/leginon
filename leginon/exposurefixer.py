# $Source: /ami/sw/cvsroot/pyleginon/reference.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2006-10-13 04:13:07 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $
import math
import presetadjuster
import leginondata
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
		'max exposure time': 1000,
	})
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.FixBeamEvent]
		presetadjuster.PresetAdjuster.__init__(self, *args, **kwargs)


	def getAdjustment(self):
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
