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
from leginon import calibrationclient

class BeamSizeCalibrator(calibrator.Calibrator):
	panelclass = gui.wx.BeamSizeCalibrator.Panel
	settingsclass = leginondata.BeamSizeCalibratorSettingsData
	defaultsettings = calibrator.Calibrator.defaultsettings
	defaultsettings.update({
		'beam diameter': 4e-2,
	})

	def __init__(self, *args, **kwargs):
		calibrator.Calibrator.__init__(self, *args, **kwargs)

		self.beamsizecalclient = calibrationclient.BeamSizeCalibrationClient(self)
		self.beamvalues = {}
		self.c2size = None
		self.start()

	def uiSetC2Size(self,size):
		temdata = self.instrument.getTEMData()
		self.setC2Size(temdata,size)
	
	def uiMeasureFocusedIntensityDialValue(self):
		if self.getC2Size() is None:
			self.logger.error('Illumination Aperture not known. Calibration not saved')
			return
		temdata = self.instrument.getTEMData()
		self.storeIntensityDialValue(0)

	def uiMeasureIntensityDialValue(self):
		self.storeIntensityDialValue(self.settings['beam diameter'])

	def uiMeasureBeamDiameter(self):
		try:
			scope = self.instrument.getData(leginondata.ScopeEMData)
		except:
			return 'error'
		beam_diameter = self.beamsizecalclient.getBeamSize(scope)
		if beam_diameter is not None:
			self.logger.info('Current Beam Diameter is %.1f um' % (beam_diameter * 1e6,))
		else:
			self.logger.error('Beam size measurement failed.')

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
		# simulated TEM always gives back 0 as intensity dial value
		if 'Sim' in scope['tem']['name'] and diameter == 0:
			intensity = 0.5
		else:
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
		A = numpy.vstack([x,numpy.ones(len(x))]).T
		return numpy.linalg.lstsq(A,y)[0]

	def setC2Size(self, temdata,size):
		c2sizedata = leginondata.C2ApertureSizeData(session=self.session,tem=temdata,size=size).insert()
		self.c2size = size

	def getC2Size(self):
		temdata = self.instrument.getTEMData()
		if temdata:
			r = leginondata.C2ApertureSizeData(session=self.session,tem=temdata).query(results=1)
			if r:
				return r[0]['size']

	def storeCalibration(self,scope):
		self.logger.info('Calculating beam size - intensity dial relationship...')
		slope, intercept = self.linearFitData(scope['spot size'])
		self.logger.info('Saving calibration with focused beam at %3.1e' % intercept)
		temdata = self.instrument.getTEMData()
		caldata = leginondata.BeamSizeCalibrationData()
		caldata['c2 size'] = self.getC2Size()
		caldata['spot size'] = scope['spot size']
		caldata['probe mode'] = scope['probe mode']
		caldata['focused beam'] = intercept
		caldata['scale'] = slope
		caldata['session'] = self.session
		caldata['tem'] = temdata
		self.publish(caldata, database=True)
