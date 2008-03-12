#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
import calibrator
import calibrationclient
import event, data
import node
import gui.wx.DoseCalibrator
import time
from wx import CallAfter

class DoseCalibrator(calibrator.Calibrator):
	'''
	calibrate the camera sensitivity and other dose measurements
	'''
	panelclass = gui.wx.DoseCalibrator.Panel
	settingsclass = data.DoseCalibratorSettingsData
	defaultsettings = calibrator.Calibrator.defaultsettings
	defaultsettings.update({
		'beam diameter': 0.16,
		'scale factor': 0.88,
	})
	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)
		self.calclient = calibrationclient.DoseCalibrationClient(self)
		self.results = {}
		self.sens = None
		self.start()

	def screenDown(self):
		if self.initInstruments():
			return
		self.instrument.tem.MainScreenPosition = 'down'
		time.sleep(2)

	def screenUp(self):
		if self.initInstruments():
			return
		self.instrument.tem.MainScreenPosition = 'up'
		time.sleep(2)

	def uiMeasureDoseRate(self):
		if self.initInstruments():
			return
		self.instrument.tem.MainScreenPosition = 'down'
		time.sleep(2)
		status = self.getCurrentAndMag()
		if status == 'ok':
			pass
		elif status == 'screen':
			self.logger.error('Cannot measure current with main screen up')
		elif status == None:
			e = 'Unable to measure dose rate: unable to access instrument'
			self.logger.error(e)
			return

		screen_mag = self.results['screen magnification']
		beam_current = self.results['beam current']
		beam_diameter = self.settings['beam diameter']
		doserate = self.calclient.dose_from_screen(screen_mag, beam_current, beam_diameter)
		self.results['dose rate'] = doserate
		CallAfter(self.panel.dialog._setDoseResults, self.results)

	def getCurrentAndMag(self):
		if self.initInstruments():
			return
		try:
			scope = self.instrument.getData(data.ScopeEMData)
		except:
			return None
		if scope['main screen position'] == 'down':
			mag = scope['main screen magnification']
			current = scope['screen current']
			scale = self.settings['scale factor']
			self.results['screen magnification'] = mag
			self.results['beam current'] = current * scale
			return 'ok'
		else:
			return 'screen'

	def acquireImage(self):
		if self.initInstruments():
			self.panel.acquisitionDone()
			return
		self.instrument.tem.MainScreenPosition = 'up'
		time.sleep(2)
		return calibrator.Calibrator.acquireImage(self)

	def uiCalibrateCamera(self):
		imdata = self.acquireImage()
		if 'dose rate' not in self.results or self.results['dose rate'] is None:
			e = 'Unable to calibrate camera sensitivity: no dose measurement'
			self.logger.error(e)
			return
		try:
			sens = self.calclient.sensitivity_from_imagedata(imdata,
																											self.results['dose rate'])
		except ValueError:
			e = 'Unable to calibrate camera sensitivity: invalid dose measurement'
			self.logger.error(e)
			return

		self.sens = sens
		ht = imdata['scope']['high tension']
		self.calclient.storeSensitivity(ht, sens)
		CallAfter(self.panel.dialog._setSensitivityResults, sens)

	def onSetSensitivity(self,sens):
		try:
			scope = self.instrument.getData(data.ScopeEMData)
		except:
			return None
		ht = scope['high tension']
		if sens:
			self.calclient.storeSensitivity(ht,sens)
			self.logger.info('Camera sensitivity saved as %.3f counts/e and %d kV' %(sens,ht/1000))
		else:
			self.logger.warning('Enter a pre-measured value before saving')
		return
	def abortCalibration(self):
		raise NotImplementedError

