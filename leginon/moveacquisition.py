#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
import math
import time
import acquisition
import leginondata
import gui.wx.MoveAcquisition
import threading

debug = False

class MoveAcquisition(acquisition.Acquisition):
	panelclass = gui.wx.MoveAcquisition.Panel
	settingsclass = leginondata.MoveAcquisitionSettingsData
	defaultsettings = acquisition.Acquisition.defaultsettings
	defaultsettings.update({
		'acquire during move': False,
		'imaging delay': 0.0,
		'tilt to': 0.0,
		'total move time': 0.0,
		'nsteps': 1,
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.move_done_event = threading.Event()
		self.step_done_event = threading.Event()

	def getParentTilt(self,targetdata):
		if targetdata['image']:
			parent_tilt = targetdata['image']['scope']['stage position']['a']
		else:
			if len(self.tilts):
				parent_tilt = self.tilts[0]
			else:
				parent_tilt = 0.0
		return parent_tilt

	def setStageTilt(self,angle):
		self.instrument.tem.setStagePosition({'a':tilt0})
		self.logger.info('Set stage alpha to %.1f degrees' % (math.degrees(angle)))

	def processTargetData(self, targetdata, attempt=None):
		self.move_done_event.clear()
		if self.settings['acquire during move']:
			tilt0 = self.getParentTilt(targetdata)
			self.setStageTilt(tilt0)
			super(MoveAcquisition, self).processTargetData(targetdata, attempt)
			self.waitMoveDone()
			self.setStageTilt(tilt0)
		else:
			# process as normal
			super(MoveAcquisition, self).processTargetData(targetdata, attempt)

	def waitMoveDone(self):
		self.move_done_event.wait()

	def waitStepDone(self):
		self.step_done_event.wait()

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		reduce_pause = self.onTarget

		if debug:
			try:
				tnum = emtarget['target']['number']
				tkey = emtarget.dbid
			except:
				tnum = None
				tkey = None
			t0 = time.time()
			self.timedebug[tkey] = t0
			if 'consecutive' in self.timedebug:
				print tnum, '************************************* CONSECUTIVE', t0 - self.timedebug['consecutive']
			self.timedebug['consecutive'] = t0

		status = self.moveAndPreset(presetdata, emtarget)
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this target')
			return status

		pausetime = self.settings['pause time']
		if reduce_pause:
			pausetime = min(pausetime, 2.5)
		elif self.is_firstimage and self.settings['first pause time'] > 0.1:
			# pause longer for the first image of the first target
			# this is used for the first image taken that touches the edge of the hole
			# in a multiple high mag target in a c-flat or quantifoil hole
			extra_pausetime = self.settings['first pause time']
			self.logger.info('Pause extra %s s for first image' % extra_pausetime)
			pausetime += extra_pausetime

		self.logger.info('pausing for %s s' % (pausetime,))

		self.startTimer('pause')
		t = threading.Thread(target=self.positionCamera)
		t.start()
		time.sleep(pausetime)
		self.waitPositionCameraDone()
		self.stopTimer('pause')
		# the next image will not be first even if repeated
		self.is_firstimage = False

		if debug:
			print tnum, 'MOVEANDPRESETPAUSE DONE', time.time() - t0

		## pre-exposure
		pretime = presetdata['pre exposure']
		if pretime:
			self.exposeSpecimen(pretime)
		if channel is None:
			try:
				defaultchannel = int(presetdata['alt channel'])
			except:
				# back compatible since imported old presetdata would have value if
				# database column is not yet created by sinedon
				defaultchannel = None
		else:
			defaultchannel = channel

		# Start a separate thread to tilt
		tilt = math.radians(self.settings['tilt to'])
		delay = self.settings['imaging delay']
		t1 = threading.Thread(target=self.moveToTilt, args=(tilt,))
		t1.start()
		time.sleep(delay)
		# Do normal acquisition
		args = (presetdata, emtarget, defaultchannel)
		if self.settings['background']:
			self.clearCameraEvents()
			t2 = threading.Thread(target=self.acquirePublishDisplayWait, args=args)
			t2.start()
			self.waitExposureDone()
		else:
			self.acquirePublishDisplayWait(*args)
		return status

	def waitAtStep(self, step_time):
		time.sleep(step_time)
		self.step_done_event.set()

	def moveToTilt(self,tilt):
		nsteps = self.settings['nsteps']
		step_time = self.settings['total move time'] / nsteps

		p0 = self.instrument.tem.StagePosition
		tilt_increment = (tilt - p0['a']) / nsteps
		self.logger.info('start tilting')
		for i in range(nsteps):
			# spend step_time at each tilt
			self.step_done_event.clear()
			new_tilt = p0['a'] + tilt_increment * (i+1)
			t3 = threading.Thread(target=self.waitAtStep, args=(step_time,))
			t3.start()
			self.instrument.tem.StagePosition = {'a':new_tilt}
			p = self.instrument.tem.StagePosition
			self.waitStepDone()
		self.logger.info('tilt %.1f degrees reached' % math.degrees(tilt))
		# ready to go to next target
		self.logger.info('return tilt to %.1f degrees' % math.degrees(p0['a']))
		self.instrument.tem.StagePosition = p0
		self.logger.info('return tilt done' % math.degrees(p0['a']))
		self.move_done_event.set()
