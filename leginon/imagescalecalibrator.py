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

class ImageScaleAdditionCalibrator(calibrator.Calibrator):
	'''
	calibrate the image scale_addition for different mags
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
		scale_additions = []
		if self.initInstruments():
			return scale_additions
		calibrations = self.calclient.retrieveLastImageScaleAdditions(None, None)
		mag, mags = self.getMagnification()
		for calibration in calibrations:
			if mags is None or calibration['magnification'] in mags:
				mag = calibration['magnification']
				if mag is None:
					continue
				ps = calibration['scale addition']
				comment = calibration['comment']
				if comment is None:
					comment = ''
				scale_additions.append((mag, ps, comment))
		if mags is not None:
			scale_additionmags = map(lambda (mag, ps, c): mag, scale_additions)
			for m in mags:
				if m not in scale_additionmags:
					scale_additions.append((m, 0.0, ''))
			
		return scale_additions

	def _store(self, mag, scale_addition, comment):
		temdata = self.instrument.getTEMData()
		camdata = self.instrument.getCCDCameraData()
		caldata = leginondata.ImageScaleAdditionCalibrationData()
		caldata['magnification'] = mag
		caldata['scale addition'] = scale_addition
		caldata['comment'] = comment
		caldata['session'] = self.session
		caldata['tem'] = temdata
		caldata['ccdcamera'] = camdata
		caldata['high tension'] = self.instrument.tem.HighTension
		caldata['probe'] = self.instrument.tem.ProbeMode
		self.publish(caldata, database=True, dbforce=True)

