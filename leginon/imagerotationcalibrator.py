#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import calibrator
import calibrationclient
import event, leginondata
from pyami import imagefun
import node
import math
import scipy
import gui.wx.ImageRotationCalibrator

class ImageRotationCalibrator(calibrator.Calibrator):
	'''
	calibrate the image rotation for different mags
	'''
	panelclass = gui.wx.ImageRotationCalibrator.Panel
	settingsclass = leginondata.ImageRotationCalibratorSettingsData
	defaultsettings = calibrator.Calibrator.defaultsettings

	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)
		self.calclient = calibrationclient.ImageRotationCalibrationClient(self)

		self.start()

	def getCalibrations(self):
		'''
		Safely get all calibrations in a list mapped to magnification.
		An item is included even if there is no calibration.  This is used
		by the gui.
		'''
		rotations = []
		if self.initInstruments():
			return rotations
		calibrations = self.calclient.retrieveLastImageRotations(None, None)
		mag, mags = self.getMagnification()
		for calibration in calibrations:
			if mags is None or calibration['magnification'] in mags:
				mag = calibration['magnification']
				if mag is None:
					continue
				ps = calibration['rotation']
				comment = calibration['comment']
				if comment is None:
					comment = ''
				rotations.append((mag, ps, comment))
		if mags is not None:
			rotationmags = map(lambda (mag, ps, c): mag, rotations)
			for m in mags:
				if m not in rotationmags:
					rotations.append((m, 0.0, ''))
			
		return rotations

	def _store(self, mag, angle, comment):
		temdata = self.instrument.getTEMData()
		camdata = self.instrument.getCCDCameraData()
		caldata = leginondata.ImageRotationCalibrationData()
		caldata['magnification'] = mag
		caldata['rotation'] = angle
		caldata['comment'] = comment
		caldata['session'] = self.session
		caldata['tem'] = temdata
		caldata['ccdcamera'] = camdata
		caldata['high tension'] = self.instrument.tem.HighTension
		caldata['probe'] = self.instrument.tem.ProbeMode
		self.publish(caldata, database=True, dbforce=True)

