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
		'maximum exposure time': 2000,
		'maximum attempts': 8,
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs + [event.UpdatePresetEvent]

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.aetarget = None
		self.original_exptime = None
		self.ae_attempt = None

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None):
		'''
		this replaces Acquisition.acquire()
		'''

		# If first attempt at metering on this target, record original exposure
		# time.  Use target list and number as the "key" to the target.
		targetkey = (target['list'], target['number'])
		if targetkey != self.aetarget:
			self.aetarget = targetkey
			self.original_exptime = presetdata['exposure time']
			self.ae_attempt = 1
		else:
			self.ae_attempt += 1

		status = acquisition.Acquisition.acquire(self, presetdata, emtarget, attempt=attempt, target=target)

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
			status = self.adjustExposureTime(self.imagedata, scale)
		else:
			status = 'ok'

		return status

	def adjustExposureTime(self, imagedata, scale):
		preset = self.imagedata['preset']
		old_exposure_time = preset['exposure time']
		new_exposure_time = old_exposure_time * scale
		max_exposure_time = self.settings['maximum exposure time']
		max_attempts = self.settings['maximum attempts']
		if self.ae_attempt > max_attempts:
			self.logger.error('Exceded maximum %s attempts' % (max_attempts,))
			new_exposure_time = self.original_exptime
			# not really ok, but we don't want to repeat or abort
			status = 'ok'
		elif new_exposure_time > max_exposure_time:
			self.logger.error('New exposure time (%s) excedes maximum (%s)' % (new_exposure_time, max_exposure_time))
			new_exposure_time = self.original_exptime
			# not really ok, but we don't want to repeat or abort
			status = 'ok'
		else:
			# adjustment will be made, so need to repeat
			status = 'repeat'

		if new_exposure_time == old_exposure_time:
			self.logger.info('Not adjusting exposure time.')
		else:
			self.logger.info('Adjusting exposure time from %.1f ms to %.1f ms' % (old_exposure_time, new_exposure_time))
			presetname = preset['name']
			params = {'exposure time': new_exposure_time}
			self.presetsclient.updatePreset(presetname, params)

		return status

	def alreadyAcquired(self, targetdata, presetname):
		## for now, always do acquire
		return False
