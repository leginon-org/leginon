#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#
import calibrator
import calibrationclient
import event, leginondata
from pyami import imagefun
import node
import math
import scipy
import gui.wx.ScaleRotationCalibrator

class ScaleRotationCalibrator(calibrator.Calibrator):
	'''
	calibrate the image rotation for different mags
	'''
	panelclass = gui.wx.ScaleRotationCalibrator.Panel
	settingsclass = leginondata.ScaleRotationCalibratorSettingsData
	defaultsettings = dict(calibrator.Calibrator.defaultsettings)

	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)
		self.calclient = calibrationclient.ImageScaleRotationCalibrationClient(self)

		self.start()

	def getCalibrations(self):
		'''
		Safely get all calibrations in a list mapped to magnification.
		An item is included even if there is no calibration.  This is used
		by the gui.
		'''
		scale_rotations = []
		if self.initInstruments():
			return scale_rotations
		rotate_calibrations = self.calclient.retrieveLastImageRotations(None, None)
		scale_calibrations = self.calclient.retrieveLastImageScaleAdditions(None, None)
		mag, mags = self.getMagnification()
		scale_mags = map((lambda x: x['magnification']),scale_calibrations)
		for calibration in rotate_calibrations:
			if mags is None or calibration['magnification'] in mags:
				mag = calibration['magnification']
				if mag is None:
					continue
				if mag in scale_mags:
					index1 = scale_mags.index(mag)
					v1 = scale_calibrations[index1]['scale addition'] # fractional number
				else:
					v1 = 0.0
				v2 = calibration['rotation']
				comment = calibration['comment']
				if comment is None:
					comment = ''
				scale_rotations.append([mag, v1, v2, comment])
			 
		if mags is not None:
			has_cal_mags = map(lambda (mag, v1, v2, c): mag, scale_rotations)
			for m in mags:
				if m not in has_cal_mags:
					if m in scale_mags:
						index1 = scale_mags.index(m)
						v1 = scale_calibrations[index1]['scale addition']
						comment = scale_calibrations[index1]['comment']
					else:
						v1 = 0.0
						comment = ''
					scale_rotations.append((m, v1, 0.0, comment))
		return scale_rotations

	def store(self, mag, scale_addition, angle, comment):
		# scale as fractional addition to 1.0
		caldata = leginondata.ImageScaleAdditionCalibrationData()
		self._store(mag, caldata, comment, 'scale addition', scale_addition)
		self.logger.info('Scale adjustment saved at %dx as %.1f %s' % (int(mag), scale_addition*100, '%'))
		# rotation
		caldata = leginondata.ImageRotationCalibrationData()
		self._store(mag, caldata, comment, 'rotation', angle) #radians
		self.logger.info('Rotation adjustment saved at %dx as %.1f degrees' % (int(mag),math.degrees(angle)))

	def _store(self, mag, caldata, comment, key, value):
		temdata = self.instrument.getTEMData()
		camdata = self.instrument.getCCDCameraData()
		# store
		caldata['magnification'] = mag
		caldata[key] = value
		caldata['comment'] = comment
		caldata['session'] = self.session
		caldata['tem'] = temdata
		caldata['ccdcamera'] = camdata
		caldata['high tension'] = self.instrument.tem.HighTension
		caldata['probe'] = self.instrument.tem.ProbeMode
		self.publish(caldata, database=True, dbforce=True)

