# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/intensitycalibrator.py,v $
# $Revision: 1.11 $
# $Name: not supported by cvs2svn $
# $Date: 2007-05-22 19:21:07 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import numpy
import numpy.linalg
import calibrator
from leginon import leginondata
import gui.wx.BeamSizeCalibrator

class BeamSizeCalibrator(calibrator.Calibrator):
	panelclass = gui.wx.BeamSizeCalibrator.Panel
	settingsclass = leginondata.BeamSizeCalibratorSettingsData
	defaultsettings = calibrator.Calibrator.defaultsettings
	defaultsettings.update({
		'beam diameter': 4e-2,
	})

	def __init__(self, *args, **kwargs):
		calibrator.Calibrator.__init__(self, *args, **kwargs)

		self.beamvalues = {}
		self.start()

	def uiMeasureFocusedIntensityDialValue(self):
		self.storeIntensityDialValue(0)

	def uiMeasureIntensityDialValue(self):
		self.storeIntensityDialValue(self.settings['beam diameter'])

	def storeIntensityDialValue(self,diameter):
		if self.initInstruments():
			return 'error'
		try:
			scope = self.instrument.getData(leginondata.ScopeEMData)
		except:
			return 'error'
		screen_mag = scope['main screen magnification']
		if not screen_mag:
			self.logger.error['screen magnification unknown']
			return 'error'
		beam_diameter_on_screen = diameter
		beam_diameter_on_specimen = beam_diameter_on_screen / screen_mag
		intensity = scope['intensity']
		spotsize = scope['spot size']
		if spotsize not in self.beamvalues.keys():
			self.beamvalues[spotsize] = [(beam_diameter_on_specimen,intensity)]
		else:
			self.beamvalues[spotsize].append((beam_diameter_on_specimen,intensity))
			self.storeCalibration(scope)

	def linearFitData(self, spotsize):
		x = numpy.array(map((lambda x: x[0]),self.beamvalues[spotsize]))
		y = numpy.array(map((lambda x: x[1]),self.beamvalues[spotsize]))
		print x
		print y
		A = numpy.vstack([x,numpy.ones(len(x))]).T
		return numpy.linalg.lstsq(A,y)[0]

	def storeCalibration(self,scope):
		self.logger.info('Calculating beam size - intensity dial relationship...')
		slope, intercept = self.linearFitData(scope['spot size'])
		self.logger.info('Saving calibration with focused beam at %3.1e' % intercept)
		temdata = self.instrument.getTEMData()
		caldata = leginondata.BeamSizeCalibrationData()
		caldata['spot size'] = scope['spot size']
		caldata['probe mode'] = scope['probe mode']
		caldata['focused beam'] = intercept
		caldata['scale'] = slope
		caldata['session'] = self.session
		caldata['tem'] = temdata
		self.publish(caldata, database=True)
