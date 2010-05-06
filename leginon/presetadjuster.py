# $Source: /ami/sw/cvsroot/pyleginon/reference.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2006-10-13 04:13:07 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $
import math
import reference
import leginondata
import event
import gui.wx.BeamFixer
from pyami import arraystats

class PresetAdjuster(reference.Reference):
	# relay measure does events
	eventinputs = reference.Reference.eventinputs + [event.FixBeamEvent]
	eventoutputs = reference.Reference.eventoutputs + [event.UpdatePresetEvent]
	panelclass = gui.wx.BeamFixer.BeamFixerPanel
	settingsclass = leginondata.PresetAdjusterSettingsData
	defaultsettings = reference.Reference.defaultsettings
	defaultsettings.update({
		'override preset': False,
		'instruments': {'tem':None, 'ccdcamera':None},
		'camera settings':
			leginondata.CameraSettingsData(
				initializer={
					'dimension': {
						'x': 1024,
						'y': 1024,
					},
					'offset': {
						'x': 0,
						'y': 0,
					},
					'binning': {
						'x': 1,
						'y': 1,
					},
					'exposure time': 200.0,
				}
			),
		'stage position': {
			'x': 0.0,
			'y': 0.0,
			'z': 0.0,
		},
		'correction presets': [],
	})
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.FixBeamEvent]
		reference.Reference.__init__(self, *args, **kwargs)
		self.start()

	def processData(self, incoming_data):
		reference.Reference.processData(self, incoming_data)
		if issubclass(incoming_data.__class__, leginondata.FixBeamData):
			newdata = incoming_data.toDict()
			newdata['preset'] = self.settings['correction presets'][0]
			self.processRequest(newdata)

	def acquire(self):
		if self.settings['override preset']:
			## use override
			instruments = self.settings['instruments']
			try:
				self.instrument.setTEM(instruments['tem'])
				self.instrument.setCCDCamera(instruments['ccdcamera'])
			except ValueError, e:
				self.logger.error('Cannot set instruments: %s' % (e,))
				return
			try:
				self.instrument.ccdcamera.Settings = self.settings['camera settings']
			except Exception, e:
				errstr = 'Acquire image failed: %s'
				self.logger.error(errstr % e)
				return
		else:
			# default to current camera config set by preset
			if self.presets_client.getCurrentPreset() is None:
				self.logger.error('Preset is unknown and preset override is off')
				return
		return self._acquire()

	def _acquire(self):
		try:
			imagedata = self.acquireCorrectedCameraImageData()
		except:
			self.logger.error('unable to get corrected image')
			return
		return imagedata

	def execute(self, request_data=None):
		params = self.getAdjustment()
		scale_factor = None
		if 'scale exposure time' in params.keys():
			scale_factor = params['scale exposure time']
			del params['scale exposure time']
			params['exposure time'] = None
		# update the preset beam shift
		correction_presets = self.settings['correction presets']
		if request_data and params:
			if request_data['preset'] not in correction_presets:
				correction_presets.append(request_data['preset'])
			for preset_name in correction_presets:
				# exposure time scaling
				if scale_factor:
					presetdata = self.presets_client.getPresetByName(preset_name)
					params['exposure time'] = presetdata['exposure time'] * scale_factor
				self.presets_client.updatePreset(preset_name, params)

	def getAdjustment(self):
		# return preset parameters to be adjusted as a dictionary
		raise NotImplementedError()
