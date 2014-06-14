# $Source: /ami/sw/cvsroot/pyleginon/reference.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2006-10-13 04:13:07 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $
import math
from leginon import leginondata, reference, calibrationclient, cameraclient
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
		'camera settings': cameraclient.default_settings,
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
		self.beamsize_client = calibrationclient.BeamSizeCalibrationClient(self)
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
		self._resetScaleFactor()
		self.params = self.getAdjustment()
		self._setScaleFactor()
		# update the preset beam shift
		correction_presets = self.settings['correction presets']
		if request_data and self.params:
			if request_data['preset'] not in correction_presets:
				correction_presets.append(request_data['preset'])
			for preset_name in correction_presets:
				presetdata = self.presets_client.getPresetByName(preset_name)
				# get new preset key and value according to the scale factor
				preset_key, preset_value = self.processScaling(presetdata)
				if preset_key:
					self.params[preset_key] = preset_value
					self.logger.info('Adjusting preset %s %s to %s' % (preset_name, preset_key, preset_value))
					self.updatePreset(preset_name, self.params)

	def updatePreset(self,preset_name, params):
		self.presets_client.updatePreset(preset_name, params)

	def getAdjustment(self):
		# return preset parameters to be adjusted as a dictionary
		raise NotImplementedError()

	def _resetScaleFactor(self):
		# default has no scale factor
		self.scale_factor = None
	
	def _setScaleFactor(self):
		# Scale factor should be set only once based on the key in self.params
		if self.params and 'scale' in self.params.keys()[0]:
			key = self.params.keys()[0]
			self.scale_factor = self.params[key]
			self.params[key] = None
	
	def processScaling(self,presetdata):
		# return preset parameter after scaling with self.scale_factor
		if self.scale_factor:
			raise NotImplementedError()
		else:
			preset_key = None
			preset_value = None
			return preset_key, preset_value
