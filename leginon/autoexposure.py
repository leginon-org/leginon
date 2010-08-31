#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
import acquisition
import node, leginondata
import calibrationclient
import event
import time
import math
from pyami import arraystats
import numpy
import gui.wx.AutoExposure
import player

class AutoExposure(acquisition.Acquisition):
	panelclass = gui.wx.AutoExposure.Panel
	settingsclass = leginondata.AutoExposureSettingsData
	defaultsettings = acquisition.Acquisition.defaultsettings
	defaultsettings.update({
		'process target type': 'meter',
		'mean intensity': 50000,
		'mean intensity tolerance': 5.0,
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs + [event.UpdatePresetEvent]

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None):
		'''
		this replaces Acquisition.acquire()
		'''
		status = acquisition.Acquisition.acquire(self, presetdata, emtarget)

		## check settings for what we want intensity to be
		mean_target = self.settings['mean intensity'] 
		tolerance = self.settings['mean intensity tolerance']
		mean_min = mean_target - tolerance
		mean_max = mean_target + tolerance

		## check if image is close enough to target mean value
		mean_acquired = arraystats.mean(self.imagedata['image'])
		self.logger.info('Target Mean: %.1f += %s%%,  Acquired Mean: %.1f' % (mean_target, tolerance, mean_acquired,))
		scale = float(mean_target) / mean_acquired
		percent_error = abs(scale - 1.0) * 100
		self.logger.info('Error relative to target: %.1f%%' % (percent_error,))

		if percent_error > tolerance:
			self.adjustExposureTime(self.imagedata, scale)
			return 'repeat'
		else:
			return 'ok'

	def adjustExposureTime(self, imagedata, scale):
		self.imagedata['preset']
		old_exposure_time = imagedata['preset']['exposure time']
		presetname = imagedata['preset']['name']
		new_exposure_time = old_exposure_time * scale
		params = {'exposure time': new_exposure_time}
		self.logger.info('Adjusting exposure time from %.1f ms to %.1f ms' % (old_exposure_time, new_exposure_time))
		self.presetsclient.updatePreset(presetname, params)

	def alreadyAcquired(self, targetdata, presetname):
		## for now, always do acquire
		return False
