# $Source: /ami/sw/cvsroot/pyleginon/reference.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2006-10-13 04:13:07 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import threading
import time
import numpy
from leginon import leginondata
import calibrationclient
import event
import appclient
import instrument
import presets
import navigator
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
				  [event.ReferenceTargetPublishEvent] + \
				  navigator.NavigatorClient.eventinputs
	eventoutputs = watcher.Watcher.eventoutputs + \
					presets.PresetsClient.eventoutputs \
					+ navigator.NavigatorClient.eventoutputs

	defaultsettings = {
		'bypass': True,
		'move type': 'stage position',
		'mover': 'presets manager',
		'move precision': 5e-7,
		'accept precision': 1e-6,
		'pause time': 3.0,
		'return settle time': 2.5,
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
		self.navclient = navigator.NavigatorClient(self)

		self.player = player.Player(callback=self.onPlayer)
		self.panel.playerEvent(self.player.state())
		self.lock = threading.RLock()
		self.reference_target = None
		self.preset_name = None
		self.navigator_bound = False
		self.at_reference_target = False
		self.last_processed = None


		if self.__class__ == Reference:
			print 'isReference'
			self.start()

	def handleApplicationEvent(self,evt):
		'''
		Find a class or its subclass instance bound
		to this node upon application loading.
		'''
		super(Reference, self).handleApplicationEvent(evt)
		app = evt['application']
		self.navigator_bound = appclient.getNextNodeThruBinding(app,self.name,'MoveToTargetEvent','Navigator')

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
		Setup EMTargetData needed by presets manager using self.reference_target
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

	def makeFakeTarget(self):
		targetdata = leginondata.AcquisitionImageTargetData()
		for k in self.reference_target.keys():
			targetdata[k] = self.reference_target[k]
		return targetdata

	def moveToTarget(self, preset_name):
		'''
		Set Preset and EMTarget to scope
		'''
		self.logger.info('Setting preset and move to reference target')
		if self.at_reference_target == True:
			self.logger.info('Already at reference target. Change preset only')
			self.presets_client.toScope(preset_name)
			preset = self.presets_client.getCurrentPreset()
			if preset['name'] != preset_name:
				message = 'failed to set preset \'%s\'' % preset_name
				raise MoveError(message)
			return
			
		em_target_data = self.getEMTargetData(preset_name)

		self.publish(em_target_data, database=True)
		self.setStageZAlpha(self.reference_target)
		if self.settings['mover'] == 'presets manager':
			self.presets_client.toScope(preset_name, em_target_data)
			if self.presets_client.stage_targeting_failed:
				message = 'target toScope failed'
				raise MoveError(message)
		else:
			if not self.navigator_bound or self.navigator_bound['is_direct_bound']==False:
				self.logger.warning('Navigator not bound with MoveToTargetEvent. Use presets manager instead')
				self.presets_client.toScope(preset_name, em_target_data)
				if self.presets_client.stage_targeting_failed:
					message = 'target toScope failed'
					raise MoveError(message)
			else:
				# Move with navigator
				precision = self.settings['move precision']
				accept_precision = self.settings['accept precision']
				fake_target = self.makeFakeTarget()
				status = self.navclient.moveToTarget(fake_target, 'stage position', precision, accept_precision, final_imageshift=False, use_current_z=True)
				if status == 'error':
					message = 'iterative move failed'
					raise MoveError(message)
				self.presets_client.toScope(preset_name)
		self.at_reference_target = True
		# check results
		p = self.instrument.tem.StagePosition
		self.logger.info('Reference target position x: %.1f um, y:%.1f um, z:%.1f um' % (p['x']*1e6,p['y']*1e6,p['z']))
		preset = self.presets_client.getCurrentPreset()
		if preset['name'] != preset_name:
			message = 'failed to set preset \'%s\'' % preset_name
			raise MoveError(message)

	def setStageZAlpha(self,target_data):
		try:
			parent = target_data['image']
			z = parent['scope']['stage position']['z']
			alpha = parent['scope']['stage position']['a']
			p = {'z':z}
			a0 = self.instrument.tem.StagePosition['a']
			# Do not set alpha unless very different
			if abs(a0-alpha) > 0.1:
				p['a'] = alpha
			self.instrument.tem.StagePosition = p
		except:
			raise

	def _processRequest(self, request_data):
		# This is the function that would be different between Timer and Counter
		# See subclass ReferenceTimer and ReferenceCounter for implementation
		message = 'always process request'
		self.logger.info(message)
		self.moveAndExecute(request_data)
		# subclass need to define self.last_processed in resetProcess

	def moveBack(self,position0):
		self.logger.info('Returning to the original position....')
		try:
			self.instrument.tem.StagePosition = position0
		except ValueError as e:
			self.logger.error('Error setting position back. %s' % e)
			self.handleFailToMoveBack(position0)
		except RuntimeError as e:
			self.logger.error('%s' % (e,))
			self.handleFailToMoveBack(position0)
		# need to pause if failed to move back
		self.player.wait()
		self.at_reference_target = False
		self.setStatus('processing')
		self.pauseBeforeReturn()

	def handleFailToMoveBack(self, position):
		self.player.pause()
		self.panel.playerEvent('play')
		self.setStatus('user input')
		moves = []
		keys = position.keys()
		keys.sort()
		for k in keys:
			if k not in ('a','b'):
				moves.append('%s: %.1f um' % (k,position[k]*1e6))
			else:
				moves.append('%s: %.1f degs' % (k,position[k]*180.0/3.14159))
		position_str = ','.join(moves)
		self.logger.error('Stage error. Manually move required to continue by clicking STOP tool')
		self.logger.error('Position to move to: %s' % position_str)

	def moveAndExecute(self, request_data):
		'''
		move to reference target, set to the preset in request_data
		, execute and then move back.  self.last_processed is reset in here.
		Request_data must exist
		'''
		pause_time = self.settings['pause time']
		# Moving part
		preset_name = request_data['preset']
		self.preset_name = preset_name
		position0 = self.instrument.tem.StagePosition
		try:
			self.moveToTarget(preset_name)
			self.declareDrift('stage')
		except Exception, e:
			self.logger.error('Error moving to target, %s' % e)
			self.moveBack(position0)
			return
		# Execution part
		if pause_time is not None:
			self.logger.info('Pausing %.1f second before execution' % (pause_time,))
			time.sleep(pause_time)
		if self.player.state() == 'stop':
			self.moveBack(position0)
			return
		try:
			self.execute(request_data)
			# default behavior: reset only if successful
			self.resetProcess()
		except Exception, e:
			self.logger.error('Error executing request, %s' % e)
		finally:
			# Must move back
			self.moveBack(position0)
			return

	def pauseBeforeReturn(self):
		pause_time = self.settings['return settle time']
		if pause_time is not None:
			self.logger.info('Settling the stage for %.1f second' % (pause_time,))
			time.sleep(pause_time)

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
		'''
		Subclass should overwrite this.
		'''
		# request_data input may be None if from onTest
		pass

	def onMakeReference(self, request_data=None):
		self.logger.info('Acquiring image as parent of the reference target...')
		self.setStatus('processing')
		self.player.play()
		try:
			self.setReferenceTarget()
			self.logger.info('Done setting reference target')
		except:
			self.logger.error('can not set reference target at current position')
		finally:
			self.panel.playerEvent('stop')
			self.setStatus('idle')

	def onTest(self):
		'''
		Testing with or without reference target. It uses current preset.
		'''
		# This is different from moveAndExecute
		self.logger.info('Testing...')
		self.setStatus('processing')
		self.player.play()
		try:
			self._testRun()
		except Exception, e:
			self.logger.error(e)
			raise
		finally:
			self.panel.playerEvent('stop')
			self.setStatus('idle')
			self.logger.info('Done testing')

	def _getTestPreset(self):
		'''
		Test Preset is normally the current preset
		'''
		preset = self.presets_client.getCurrentPreset()
		self.logger.info('Use current preset %s for testing' % preset['name'])
		return preset

	def _testRun(self):
		preset_name = None
		pause_time = self.settings['pause time']
		# must have preset
		try:
			preset = self._getTestPreset()
		except TypeError:
			self.logger.error('No current preset. Send desired preset for testing first')
			return
		self.preset_name = preset['name']
		self.reference_target = self.getReferenceTarget()
		if self.reference_target:
			# move to reference target with preset
			self.logger.info('Use reference target for testing')
			request_data = {'preset':preset['name']}
			self.moveAndExecute(request_data)
		else:
			self.logger.warning('No reference target')
			self.logger.info('Use current position for testing')
			if pause_time is not None:
				self.logger.info('Pausing %.1f second before execution' % (pause_time,))
				time.sleep(pause_time)
			if self.player.state() == 'stop':
				return
			try:
				self.execute(None)
			finally:
				self.resetProcess()

	def resetProcess(self):
		# self.last_processed is different between Timer and Counter
		# See subclass ReferenceTimer and ReferenceCounter for implementation
		self.logger.info('Reset Request Process')
		self.last_processed = None

	def getImageFilename(self,imagedata):
		'''
		Set image filename by timestamp because the image
		does not come from a target list.
		'''
		if imagedata['filename'] is not None:
			return
		parts = []
		parts.append(self.session['name'])
		nodename = self.name.lower()
		nodename = '-'.join(nodename.split(' '))
		parts.append(nodename)
		time_name = time.strftime('%Y%m%d_%H%M%S', time.localtime())
		parts.append(time_name)
		# join them
		filename = '_'.join(parts)
		return filename

	def setReferenceTarget(self):
		'''
		Set Reference target at current stage position with an image acquired
		with current preset as the parent.
		This makes it possible to use navigator move to iteratively move the
		reference target.
		'''
		# acquire an image with current preset
		preset = self.presets_client.getCurrentPreset()
		if preset:
			# check image size. This is used as parent image to move, so it need
			#to be reasonably large
			cam_pixelsize = self.calibration_clients['stage position'].getPixelSize(preset['magnification'],preset['tem'],preset['ccdcamera'])
			image_length = cam_pixelsize*preset['binning']['x']*preset['dimension']['x']
			if image_length < 3e-6:
				self.logger.error('Preset image length smaller than 3 um, Not reliable as parent image for navigation')
				raise RuntimeError('Bad preset')
			preset_name = preset['name']
			self.logger.info('Use current preset %s to make reference parent image and target' % preset_name)
		else:
			self.logger.error('Send a preset to scope/camera first.')
			raise RuntimeError('No preset')
		emtarget = leginondata.EMTargetData(preset=preset,movetype='stage position')
		emtarget['image shift'] = preset['image shift']
		emtarget['beam shift'] = preset['beam shift']
		emtarget['stage position'] = self.instrument.tem.StagePosition
		imagedata = self.acquireCorrectedCameraImageData(force_no_frames=True)
		## convert CameraImageData to AcquisitionImageData
		dim = imagedata['camera']['dimension']
		pixels = dim['x'] * dim['y']
		try:
			pixeltype = str(imagedata['image'].dtype)
		except:
			self.logger.error('array not returned from camera')
			raise RuntimeError('Parent image for reference target failed to be acquired')
		filename = self.getImageFilename(imagedata)
		imagedata = leginondata.AcquisitionImageData(initializer=imagedata, preset=preset, label=self.name, emtarget=emtarget, pixels=pixels, pixeltype=pixeltype, filename=filename)
		# make reference target on the image
		drow, dcol = (0,0)
		targetdata = self.newReferenceTarget(imagedata, drow, dcol)
		try:
			self.publish(targetdata, database=True)
			image_array = imagedata['image']
			self.setImage(numpy.asarray(image_array, numpy.float32), 'Image')
		except:
			raise RuntimeError('Failed to publish reference target')

	def newReferenceTarget(self, image_data, drow, dcol):
		target_data = leginondata.ReferenceTargetData()
		target_data['image'] = image_data
		target_data['scope'] = image_data['scope']
		target_data['camera'] = image_data['camera']
		target_data['preset'] = image_data['preset']
		target_data['grid'] = image_data['grid']
		target_data['delta row'] = drow
		target_data['delta column'] = dcol
		target_data['session'] = self.session
		return target_data

	def onPlayer(self, state):
		infostr = ''
		if state == 'pause':
			infostr += 'Paused'
		elif state == 'stop':
			infostr += 'Aborting...'
		if infostr:
			self.logger.info(infostr)
		self.panel.playerEvent(state)

