#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import calibrator
import calibrationclient
import event, data
import node
try:
	import numarray as Numeric
except:
	import Numeric
import gui.wx.DoseCalibrator

class DoseCalibrator(calibrator.Calibrator):
	'''
	calibrate the camera sensitivity and other dose measurements
	'''
	panelclass = gui.wx.DoseCalibrator.Panel
	settingsclass = data.DoseCalibratorSettingsData
	defaultsettings = {
		'camera settings': None,
		'correlation type': 'cross',
		'beam diameter': 0.16,
		'scale factor': 0.88,
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)
		self.calclient = calibrationclient.DoseCalibrationClient(self)
		self.results = {}

		self.start()

	def uiMeasureDoseRate(self):
		self.screenDown()
		status = self.getCurrentAndMag()
		if status == 'ok':
			pass
		elif status == 'screen':
			self.logger.error('Cannot measure current with main screen down')

		screen_mag = self.results['screen magnification']
		beam_current = self.results['beam current']
		beam_diameter = self.settings['beam diameter']
		doserate = self.calclient.dose_from_screen(screen_mag, beam_current, beam_diameter)
		self.results['dose rate'] = doserate

	def screenDown(self):
		# check if screen is down
		scope = data.ScopeEMData()
		scope['main screen position'] = 'down'
		self.emclient.setScope(scope)

	def screenUp(self):
		# check if screen is down
		scope = data.ScopeEMData()
		scope['main screen position'] = 'up'
		self.emclient.setScope(scope)

	def getCurrentAndMag(self):
		scope = self.emclient.getScope()
		if scope['main screen position'] == 'down':
			mag = scope['magnification']
			current = scope['screen current']
			scale = self.settings['scale factor']
			self.results['screen magnification'] = mag
			self.results['beam current'] = current * scale
			return 'ok'
		else:
			return 'screen'

	def acquireImage(self):
		self.screenUp()
		self.cam.setCameraDict(self.settings['camera settings'])
		imdata = self.cam.acquireCameraImageData(correction=True)
		if imdata is not None:
			self.updateImage('Image', imdata['image'].astype(Numeric.Float32))
		return imdata

	def uiCalibrateCamera(self):
		imdata = self.acquireImage()
		screen_mag = self.results['screen magnification']
		beam_current = self.results['beam current']
		beam_diameter = self.settings['beam diameter']
		dose_rate = self.results['dose rate']
		sens = self.calclient.sensitivity_from_imagedata(imdata, dose_rate)
		self.sens = sens
		ht = imdata['scope']['high tension']
		self.calclient.storeSensitivity(ht, sens)

	def abortCalibration(self):
		raise NotImplementedError
