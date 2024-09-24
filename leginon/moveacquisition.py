#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#
import math
import time
from leginon import acq as acquisition
from leginon import leginondata
import leginon.gui.wx.MoveAcquisition
import threading

debug = False

class MoveAcquisition(acquisition.Acquisition):
	panelclass = leginon.gui.wx.MoveAcquisition.Panel
	settingsclass = leginondata.MoveAcquisitionSettingsData
	defaultsettings = dict(acquisition.Acquisition.defaultsettings)
	defaultsettings.update({
		'acquire during move': False,
		'imaging delay': 0.0,
		'move to': (0.0,),
		'total move time': 0.0,
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.move_done_event = threading.Event()
		self.step_done_event = threading.Event()

		# base class  move alpha
		# subclass may change this.
		self.move_params = ('a',)

	def prepareToAcquire(self,allow_retracted=False,exposure_type='normal'):
		'''
		Overwrite prepareToAcquire in cameraclient.py to not to do anything
		if moving since they would be blocked by scope movement.
		Do these before moving instead.
		'''
		if not self.settings['acquire during move']:
			# process as normal
			return super(MoveAcquisition, self).prepareToAcquire(allow_retracted, exposure_type)
		else:
			self.logger.info('Bypassed acquisition preparation')
			pass

	def getParentValue(self,targetdata):
		'''
		Get parent value in case a reset is required.
		'''
		parent_values = {}
		try:
			parent_position = targetdata['image']['scope']['stage position']
		except:
			# use current tilt as default
			parent_position  = self.instrument.tem.StagePosition
		for k in self.move_params:
			parent_values[k] = parent_position[k]
		return parent_values

	def _setStageValue(self, valuedict):
		self.instrument.tem.StagePosition = valuedict
			
	def processTargetData(self, targetdata, attempt=None):
		self.move_done_event.clear()
		if self.settings['acquire during move']:
			p0dict = self.getParentValue(targetdata)
			self._setStageValue(p0dict)
			# move is started during acquire function call.
			super(MoveAcquisition, self).processTargetData(targetdata, attempt)
			# need to wait for all moves are completed.
			self.waitMoveDone()
			#TODO generalize for all movement
			self.instrument.tem.StageSpeed = 50.0 # top speed in degrees per second
			self._setStageValue(p0dict)
		else:
			# process as normal
			super(MoveAcquisition, self).processTargetData(targetdata, attempt)

	def waitMoveDone(self):
		self.move_done_event.wait()

	def waitStepDone(self):
		self.step_done_event.wait()

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		if not self.settings['acquire during move']:
			# process as normal
			return super(MoveAcquisition, self).acquire(presetdata, emtarget, attempt, target, channel)

		reduce_pause = self.onTarget
		p0 = self.instrument.tem.StagePosition

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
				print(tnum, '************************************* CONSECUTIVE', t0 - self.timedebug['consecutive'])
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
		time.sleep(pausetime)
		self.stopTimer('pause')
		# not sure if need to thread. Will insert the camera
		self._prepareToAcquire()
		# the next image will not be first even if repeated
		self.is_firstimage = False

		if debug:
			print(tnum, 'MOVEANDPRESETPAUSE DONE', time.time() - t0)

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

		# Move thread is started
		try:
			self.startMoveThread()
		except:
			status == 'error'
			self.logger.warning('Move failed. skipping acquisition at this target')
			return status
		# delay imaging a bit if needed
		delay = self.settings['imaging delay']
		time.sleep(delay)
		# Do normal acquisition
		args = (presetdata, emtarget, defaultchannel)
		if self.settings['background']:
			self.clearCameraEvents()
			t2 = threading.Thread(target=self.acquirePublishDisplayWait, args=args)
			t2.start()
			self.waitExposureDone()
			t2.join()
		else:
			self.acquirePublishDisplayWait(*args)
		return status

	def calculateMoveTimes(self):
		'''
		Calculate needed move values to apply and step times.
		'''
		move_settings = self.settings['move to'] # list of tuples
		move_values = []
		step_times = []
		nsteps = len(move_settings)
		try:
			for move in move_settings:
				if len(move) > 2:
					# set step time if present
					step_time = move[2]
					move = move[:2]
				else:
					step_time = self.settings['total move time'] / nsteps
				step_times.append(step_time)
				move_values.append(self.moveToSettingToValue(move))
		except Exception as e:
			raise ValueError('Move to values invalid:%s' % (e,))
		if nsteps < 1:
			raise ValueError('Need at least one move')
		return list(map((lambda x: (move_values[x],step_times[x])), list(range(nsteps))))

	def startMoveThread(self):
		'''
		 Start a separate thread to move.
		'''
		move_times = self.calculateMoveTimes()
		self.t1 = threading.Thread(target=self.moveToValue, args=(move_times,))
		self.t1.start()

	def waitAtStep(self, step_time):
		time.sleep(step_time)
		self.t1.join()
		self.step_done_event.set()

	def moveToValue(self, move_times):
		'''
		Move to values with minimal step time.
		move_times = tuples of (move_to_values_in_setting_unit, step)
		'''
		p0 =self.getStageValue()
		self.logger.info('start moving')
		for move,step_time in move_times:
			# spend step_time at each tilt
			self.step_done_event.clear()
			t3 = threading.Thread(target=self.waitAtStep, args=(step_time,))
			t3.start()
			self.setStageValue(move)
			self.waitStepDone()
			t3.join()
			self.logFinal(move) # log intermediate move
		self.logFinal(move_times[-1][0]) # log last move value
		#TODO generalize for all movement
		self.instrument.tem.StageSpeed = 50.0 # top speed in degrees per second
		# ??? WHy here ?
		self.setStageValue(p0)
		self.move_done_event.set()

	##### Subclasses need to overwrite these if need different behavior#####
	def getStageValue(self):
		position = self.instrument.tem.StagePosition
		value = position['a']
		return value

	def setStageValue(self,value):
		'''
		Set stage position defined by the
		subclass.
		'''
		# Value is alpha in radians n this case
		valuedict = {'a': value}
		return self._setStageValue(valuedict)

	def logFinal(self, value):
		self.logger.info('tilt of %.1f degrees reached' % math.degrees(value))

	def moveToSettingToValue(self,setting):
		return math.radians(setting)

