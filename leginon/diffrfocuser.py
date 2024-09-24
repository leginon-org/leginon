#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#

import math
import time
import threading
from leginon import singlefocuser
from leginon import acq as acquisition
from leginon import leginondata
import leginon.gui.wx.DiffrFocuser
from leginon import calibrationclient

class DiffrFocuser(singlefocuser.SingleFocuser):
	panelclass = leginon.gui.wx.DiffrFocuser.Panel
	settingsclass = leginondata.DiffrFocuserSettingsData
	defaultsettings = dict(singlefocuser.SingleFocuser.defaultsettings)
	defaultsettings.update({
		'tilt start': -57.0,
		'tilt speed': 1.0,
		'tilt range': 114.0,
	})

	eventinputs = singlefocuser.SingleFocuser.eventinputs
	eventoutputs = singlefocuser.SingleFocuser.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		singlefocuser.SingleFocuser.__init__(self, id, session, managerlocation, **kwargs)
		self.speed_cal_client = calibrationclient.StageSpeedClient(self)

	def getParentTilt(self,targetdata):
		if targetdata['image']:
			parent_tilt = targetdata['image']['scope']['stage position']['a']
		else:
			parent_tilt = 0.0
		return parent_tilt

	def validateSettings(self):
		'''
		A chance for subclass to abort processTargetData.
		'''
		self.start_radian = math.radians(self.settings['tilt start'])
		self.end_radian = math.radians(self.settings['tilt range']+self.settings['tilt start'])
		limits = (math.radians(-72.0),math.radians(72.0))
		if self.start_radian < limits[0] or self.start_radian > limits[1]:
			raise acquisition.InvalidSettings('Start tilt %.1f deg is out of range' % (math.degrees(self.start_radian)))
		if self.end_radian < limits[0] or self.end_radian > limits[1]:
			raise acquisition.InvalidSettings('End tilt %.1f deg is out of range.' % (math.degrees(self.end_radian)))
		
		#if self.end_radian > limits['a'][1] or self.start_radian < limits['a'][0]:
		#	raise acquisition.BadImageStatsPause('Tilt angle out of range')

		if self.settings['tilt speed'] < 0.01 or self.settings['tilt speed'] > 25:
			raise acquisition.InvalidSettings('Invalid tilt speed %.3f' % (self.settings['tilt speed']))
		tilt_time = abs(self.settings['tilt range']) / self.settings['tilt speed']
		if tilt_time >= 3*60:
			raise acquisition.InvalidSettings('Tilt time %.1f s is too long' % (tilt_time))

	def acquirePublishDisplayWait(self, presetdata, emtarget, channel):
		'''
		Replace base class acquirePublishDisplayWait.  This does not
		set self.imagedata. Therefore it does not publish nor display
		any image.  It just save diffraction  series meta data so that
		the movie can be uploaded automatically.
		'''
		try:
			self.tiltAndWait(presetdata,emtarget)
			self.saveDiffractionSeriesData(presetdata,emtarget)
		except:
			self.logger.info('Return to %.1f deg tilt' % (math.degrees(self.tilt0)))
			self.returnToOriginalTilt()
			raise

	def returnToOriginalTilt(self):
		self.instrument.tem.BeamstopPosition = 'out'
		self.instrument.tem.StageSpeed = 50.0 # top speed in degrees per second
		self.instrument.tem.StagePosition={'a':self.tilt0}

	def tiltAndWait(self, presetdata, emtarget):
		position0 = self.instrument.tem.StagePosition
		self.tilt0 = position0['a']


		# go to start
		self.instrument.tem.BeamstopPosition = 'in'
		self.logger.info('Tilting to %s degrees to start' % self.settings['tilt start'])
		self.instrument.tem.StagePosition={'a':self.start_radian}
		self.logger.info('Start tilting')
		t= threading.Thread(target=self.tiltWithSpeed)
		t.daemen = True
		t.start()
		filename = self.getTiltMovieFilename(emtarget)
		self.startMovieCollection(filename, presetdata['exposure time'])
		t.join()
		self.logger.info('End tilting')
		self.stopMovieCollection(filename, presetdata['exposure time'])
		self.logger.info('Return to %.1f deg tilt' % (math.degrees(self.tilt0)))
		self.returnToOriginalTilt()
		#self.pauseForUser()

	def saveDiffractionSeriesData(self, presetdata, emtarget):
		q = leginondata.DiffractionSeriesData(session=self.session, preset=presetdata)
		q['parent'] = emtarget['target']['image']
		q['emtarget'] = emtarget
		q['tilt start'] = self.settings['tilt start']
		q['tilt range'] = self.settings['tilt range']
		q['tilt speed'] = self.settings['tilt speed']
		q['series length'] = self.instrument.ccdcamera.SeriesLength
		q.insert()

	def getTiltMovieFilename(self, emtarget):
		if emtarget['target']['image'] is None:
			raise RuntimeError('This node should not be run from simulation')
		parent_id = emtarget['target']['image'].dbid
		target_number = emtarget['target']['number']
		filename = '%d_%d.bin' % (parent_id, target_number)
		self.logger.info('tilt movie should be named: %s' % filename)
		return filename

	def tiltWithSpeed(self):
		time.sleep(0.5)
		speed = abs(self.settings['tilt speed'])
		corrected_speed = self.speed_cal_client.getCorrectedTiltSpeed(None, speed, self.settings['tilt range'])
		if corrected_speed != speed:
			self.logger.info('Using corrected speed of %.4f degrees/seconds' % corrected_speed)
		# set in degrees per second
		self.instrument.tem.StageSpeed = corrected_speed
		self.instrument.tem.StagePosition = {'a':self.end_radian}

	def startMovieCollection(self, filename, exposure_time):
		# notify both start and stop so it does not timeout easily
		self.notifyNodeBusy()
		self.logger.info('Start movie collection')
		# exposure_time is in ms
		self.instrument.ccdcamera.startMovie(filename, exposure_time)

	def stopMovieCollection(self, filename, exposure_time):
		# notify both start and stop
		self.notifyNodeBusy()
		self.logger.info('Stop movie collection')
		self.instrument.ccdcamera.stopMovie(filename, exposure_time)

	def pauseForUser(self):
		# just need to set player. Status will follow it in TargetWatcher.pauseCheck
		self.player.pause()
