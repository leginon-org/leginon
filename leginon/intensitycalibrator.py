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
import threading
import calibrator
import calibrationclient
import leginondata
import gui.wx.IntensityCalibrator
from pyami import arraystats

class Abort(Exception):
	pass

class IntensityCalibrator(calibrator.Calibrator):
	panelclass = gui.wx.IntensityCalibrator.Panel
	settingsclass = leginondata.IntensityCalibratorSettingsData
	defaultsettings = calibrator.Calibrator.defaultsettings
	defaultsettings.update({
		'min': 0.3,
		'max': 0.7,
		'increment': 0.01,
		'label': '',
	})

	def __init__(self, *args, **kwargs):
		calibrator.Calibrator.__init__(self, *args, **kwargs)

		self.abort = threading.Event()

		self.start()

	def measureIntensity(self):
		self.measureIntensityLoop()

	def measureIntensityLoop(self):
		minint = self.settings['min']
		maxint = self.settings['max']
		incr = self.settings['increment']
		label = self.settings['label']

		for i in numpy.arange(minint, maxint, incr):
			self.instrument.tem.Intensity = i
			imdata = self.acquire(i)
			stats = self.calcStats(imdata)
			self.logger.info('%.4f: %s' % (i, stats,))
			self.storeIntensityMeasurement(label, i, stats)
			self.checkAbort()

	def bringHome(self):
		# start with a spread beam
		self.instrument.tem.Intensity = 0.8
		imdata0 = self.acquire()
		mean0 = arraystats.mean(imdata0['image'])
		
		# test if we can even see the beam
		self.instrument.tem.Intensity = 0.7
		imdata1 = self.acquire()
		mean1 = arraystats.mean(imdata1['image'])

		print 'mean0,mean1', mean0, mean1

	def acquire(self, intensity):
		imagedata = self.instrument.getData(leginondata.CorrectedCameraImageData)
		self.setImage(imagedata['image'])
		preset = self.presetsclient.getCurrentPreset()
		acqimdata = leginondata.AcquisitionImageData(initializer=imagedata, session=self.session, preset=preset)
		acqimdata['filename'] = '%s_%s_%s_%04d' % (self.session['name'], preset['name'], self.settings['label'], int(intensity*1000))
		self.publish(acqimdata, database=True)
		return acqimdata

	def calcStats(self, imdata):
		stats = {}
		stats['mean'] = arraystats.mean(imdata['image'])
		stats['stdev'] = arraystats.std(imdata['image'])
		return stats

	def storeIntensityMeasurement(self, label, intensity, stats):
		meas = leginondata.IntensityMeasurementData(session=self.session, label=label, intensity=intensity)
		meas.update(stats)
		self.publish(meas, database=True)

	def checkAbort(self):
		if not self.abort.isSet():
			return
		self.abort.clear()
		raise Abort('operation aborted')

	def abortCalibration(self):
		self.abort.set()
