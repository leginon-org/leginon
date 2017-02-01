# $Source: /ami/sw/cvsroot/pyleginon/reference.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2006-10-13 04:13:07 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import threading
import time
from leginon import leginondata
import calibrationclient
import event
import instrument
import presets
import targethandler
import watcher
import player
import gui.wx.Reference

class MoveError(Exception):
	pass

class Reference(watcher.Watcher, targethandler.TargetHandler):
	panelclass = gui.wx.Reference.ReferencePanel
	settingsclass = leginondata.ReferenceSettingsData
	eventinputs = watcher.Watcher.eventinputs + \
				  presets.PresetsClient.eventinputs + \
				  [event.ReferenceTargetPublishEvent]
	eventoutputs = watcher.Watcher.eventoutputs + \
					presets.PresetsClient.eventoutputs

	defaultsettings = {
		'bypass': True,
		'move type': 'stage position',
		'pause time': 3.0,
		'interval time': 0.0,
	}
	requestdata = None

	def __init__(self, *args, **kwargs):
		kwargs['watchfor'] = self.addWatchFor(kwargs)
		watcher.Watcher.__init__(self, *args, **kwargs)
		targethandler.TargetHandler.__init__(self)

		self.instrument = instrument.Proxy(self.objectservice, self.session)

		self.calibration_clients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self),
			'image beam shift': calibrationclient.ImageBeamShiftCalibrationClient(self),
			'beam shift': calibrationclient.BeamShiftCalibrationClient(self),
		}

		self.presets_client = presets.PresetsClient(self)

		self.player = player.Player(callback=self.onPlayer)
		self.panel.playerEvent(self.player.state())
		self.lock = threading.RLock()
		self.reference_target = None
		self.preset_name = None

		self.last_processed = None


		if self.__class__ == Reference:
			print 'isReference'
			self.start()

	def addWatchFor(self,kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		return watch + [event.ReferenceTargetPublishEvent]

	def processData(self, incoming_data):
		'''
		Process Watcher watchfor data. Return immediately if bypass
		'''
		if self.settings['bypass']:
			return False
		self._processData(incoming_data)

	def _processData(self, incoming_data):
		'''
		Preocess ReferenceTargetData and more.  Subclass should set
		self.requestdata
		'''
		if isinstance(incoming_data, leginondata.ReferenceTargetData):
			self.processReferenceTarget(incoming_data)
		if self.requestdata and isinstance(incoming_data, self.requestdata):
			self.processRequest(incoming_data)

	def processReferenceTarget(self, target_data):
		'''
		Set reference_target
		'''
		self.lock.acquire()
		self.reference_target = target_data
		self.lock.release()

	def getEMTargetData(self,check_preset_name=None):
		'''
		Setup EMTargetData using self.reference_target
		'''
		target_data = self.reference_target
		if target_data is None:
			raise MoveError('no reference target available')
		move_type = self.settings['move type']
		calibration_client = self.calibration_clients[move_type]

		target_delta_row = target_data['delta row']
		target_delta_column = target_data['delta column']
		pixel_shift = {'row': -target_delta_row, 'col': -target_delta_column}
		target_scope = leginondata.ScopeEMData(initializer=target_data['scope'])
		for i in ['image shift', 'beam shift', 'stage position']:
			target_scope[i] = dict(target_data['scope'][i])
		target_camera = target_data['camera']

		args = (pixel_shift, target_scope, target_camera)
		try:
			scope = calibration_client.transform(*args)
		except calibrationclient.NoMatrixCalibrationError, e:
			message = 'no %s calibration to move to reference target: %s'
			raise MoveError(message % (move_type, e))

		em_target_data = leginondata.EMTargetData()
		if check_preset_name is None:
			em_target_data['preset'] = target_data['preset']
		else:
			check_preset_data = self.presets_client.getPresetByName(check_preset_name)
			em_target_data['preset'] = check_preset_data
		for i in ['image shift', 'beam shift']:
			em_target_data[i] = em_target_data['preset'][i]
		em_target_data['stage position'] = scope['stage position']
		em_target_data['movetype'] = move_type
		if move_type == 'modeled stage position':
			scope_move_type = 'stage position'
		else:
			scope_move_type = move_type
		em_target_data[scope_move_type] = scope[scope_move_type]
		em_target_data['target'] = leginondata.AcquisitionImageTargetData(initializer=target_data)

		return em_target_data

	def moveToTarget(self, preset_name):
		'''
		Set Preset and EMTarget to scope
		'''
		em_target_data = self.getEMTargetData(preset_name)

		self.publish(em_target_data, database=True)

		self.presets_client.toScope(preset_name, em_target_data)
		preset = self.presets_client.getCurrentPreset()
		if preset['name'] != preset_name:
			message = 'failed to set preset \'%s\'' % preset_name
			raise MoveError(message)

	def _processRequest(self, request_data):
		# This is the function that would be different between Timer and Counter
		interval_time = self.settings['interval time']
		if interval_time is not None and self.last_processed is not None:
			interval = time.time() - self.last_processed
			if interval < interval_time:
				message = '%d second(s) since last request, ignoring request'
				self.logger.info(message % interval)
				return
		self.moveAndExecute(request_data)
		self.last_processed = time.time()

	def moveAndExecute(self, request_data):
		pause_time = self.settings['pause time']

		preset_name = request_data['preset']
		self.preset_name = preset_name
		position0 = self.instrument.tem.StagePosition
		try:
			self.moveToTarget(preset_name)
			self.declareDrift('stage')
		except Exception, e:
			self.logger.error('Error moving to target, %s' % e)
			return

		if pause_time is not None:
			self.logger.info('Pausing %.1f second before execution' % (pause_time,))
			time.sleep(pause_time)
		try:
			self.execute(request_data)
		except Exception, e:
			self.logger.error('Error executing request, %s' % e)
			self.instrument.tem.StagePosition = position0
			return

		self.instrument.tem.StagePosition = position0

	def processRequest(self, request_data):
		self.reference_target = self.getReferenceTarget()
		self.logger.info('Processing reference target request')
		self.lock.acquire()
		self.setStatus('processing')
		self.panel.playerEvent('play')
		try:
			self._processRequest(request_data)
		finally:
			self.setStatus('idle')
			self.panel.playerEvent('stop')
			self.lock.release()
		self.logger.info('Done processing reference target request')

	def execute(self, request_data):
		pass

	def onTest(self, request_data=None):
		self.logger.info('Testing...')
		self.setStatus('processing')
		self.player.play()
		try:
			self.execute(request_data)
		finally:
			self.panel.playerEvent('stop')
			self.setStatus('idle')
			self.logger.info('Done testing')

	def onPlayer(self, state):
		infostr = ''
		if state == 'pause':
			infostr += 'Paused'
		elif state == 'stop':
			infostr += 'Aborting...'
		if infostr:
			self.logger.info(infostr)
		self.panel.playerEvent(state)

