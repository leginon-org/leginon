#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
import acquisition
import node, data
import calibrationclient
import threading
import event
import time
import imagefun
try:
	import numarray as Numeric
except:
	import Numeric
import copy
import gui.wx.Focuser
import player

class Focuser(acquisition.Acquisition):
	panelclass = gui.wx.Focuser.Panel
	settingsclass = data.FocuserSettingsData
	defaultsettings = {
		'pause time': 2.5,
		'move type': 'image shift',
		'preset order': [],
		'correct image': True,
		'display image': True,
		'save image': True,
		'wait for process': False,
		'wait for rejects': False,
		'duplicate targets': False,
		'duplicate target type': 'focus',
		'iterations': 1,
		'wait time': 0,
		'adjust for drift': False,
		'melt time': 0.0,
		'acquire final': True,
	}

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		self.correction_types = {
			'None': self.correctNone,
			'Stage Z': self.correctZ,
			'Defocus': self.correctDefocus
		}

		self.correlation_types = ['cross', 'phase']
		self.focus_methods = ['Manual', 'Beam Tilt', 'Stage Tilt']
		self.default_setting = {
			'switch': True,
			'preset name': 'Grid',
			'focus method': 'Beam Tilt',
			'tilt': 0.01,
			'correlation type': 'phase',
			'fit limit': 1000,
			'delta min': 0.0,
			'delta max': 1e-3,
			'correction type': 'Defocus',
			'stig correction': False,
			'stig defocus min': -4e-6,
			'stig defocus max': -2e-6,
			'check drift': False,
			'drift threshold': 3e-10,
			'reset defocus': None,
		}
		self.manualchecklock = threading.Lock()
		self.maskradius = 1.0
		self.increment = 5e-7
		self.man_power = None
		self.man_image = None
		self.manualplayer = player.Player(callback=self.onManualPlayer)
		acquisition.Acquisition.__init__(self, id, session, managerlocation, target_types=('focus',), **kwargs)
		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.stagetiltcalclient = calibrationclient.StageTiltCalibrationClient(self)
		self.euclient = calibrationclient.EucentricFocusClient(self)
		self.focus_sequence = self.researchFocusSequence()
		self.deltaz = 0.0

	def researchFocusSequence(self):
		user_data = data.UserData(initializer=self.session['user'].toDict())
		initializer = {
			'session': data.SessionData(user=user_data),
			'node name': self.name,
		}
		query = data.FocusSequenceData(initializer=initializer)
		try:
			focus_sequence_data = self.research(query, results=1)[0]
		except IndexError:
			return []

		sequence = []
		for name in focus_sequence_data['sequence']:
			focus_setting = self.researchFocusSetting(name)
			if focus_setting is None:
				warning = 'Unable to find focus setting \'%s\'.' % name
				self.logger.warning(warning)
			else:
				sequence.append(focus_setting)
		return sequence

	def researchFocusSetting(self, name):
		initializer = {
			'session': data.SessionData(user=self.session['user']),
			'node name': self.name,
			'name': name,
		}
		query = data.FocusSettingData(initializer=initializer)
		try:
			focus_setting_data = self.research(query, results=1)[0]
		except IndexError:
			return None
		focus_setting = focus_setting_data.toDict()
		del focus_setting['session']
		del focus_setting['node name']
		return focus_setting

	def getFocusSequence(self):
		return [setting.copy() for setting in self.focus_sequence]

	def setFocusSequence(self, sequence):
		sequence_names = [s['name'] for s in sequence]
		if sequence_names != [s['name'] for s in self.focus_sequence]:
			initializer = {
				'session': self.session,
				'sequence': sequence_names,
				'node name': self.name,
			}
			sequence_data = data.FocusSequenceData(initializer=initializer)
			self.publish(sequence_data, database=True, dbforce=True)
		for setting in sequence:
			if setting != self.researchFocusSetting(setting['name']):
				initializer = setting.copy()
				initializer['session'] = self.session
				initializer['node name'] = self.name
				setting_data = data.FocusSettingData(initializer=initializer)
				self.publish(setting_data, database=True, dbforce=True)
		self.focus_sequence = sequence

	def eucentricFocusToScope(self):
		errstr = 'Eucentric focus to instrument failed: %s'
		try:
			ht = self.instrument.tem.HighTension
			mag = self.instrument.tem.Magnification
		except:
			self.logger.error(errstr % 'unable to access instrument')
			return
		eufocdata = self.euclient.researchEucentricFocus(ht, mag)
		if eufocdata is None:
			self.logger.error('No eucentric focus found for HT: %s and Mag.: %s' % (ht, mag))
		else:
			eufoc = eufocdata['focus']
			self.instrument.tem.Focus = eufoc

	def eucentricFocusFromScope(self):
		errstr = 'Eucentric focus from instrument failed: %s'
		try:
			ht = self.instrument.tem.HighTension
			mag = self.instrument.tem.Magnification
			foc = self.instrument.tem.Focus
		except:
			self.logger.error(errstr % 'unable to access instrument')
			return
		try:
			self.euclient.publishEucentricFocus(ht, mag, foc)
		except node.PublishError, e:
			self.logger.error(errstr % 'unable to save')
			return
		self.logger.info('Eucentric focus saved to database, HT: %s, Mag.: %s, Focus: %s' % (ht, mag, foc))

	def autoFocus(self, setting, emtarget, resultdata):
		presetname = setting['preset name']
		stiglens = 'objective'
		## need btilt, pub, driftthresh
		btilt = setting['tilt']
		pub = False
		if setting['check drift']:
			driftthresh = setting['drift threshold']
		else:
			driftthresh = None

		## send the autofocus preset to the scope
		self.presetsclient.toScope(presetname, emtarget)
		target = emtarget['target']

		## set to eucentric focus if doing Z correction
		## WARNING:  this assumes that user will not change
		## to another focus type before doing the correction
		focustype = setting['correction type']
		if focustype == 'Stage Z':
			self.logger.info('Setting eucentric focus...')
			self.eucentricFocusToScope()
			self.logger.info('Eucentric focus set')
			self.eucset = True
		else:
			self.eucset = False
		self.reset = True

		delay = self.settings['pause time']
		self.logger.info('Pausing for %s seconds' % (delay,))
		time.sleep(delay)

		### report the current focus and defocus values
		self.logger.info('Before autofocus...')
		try:
			defoc = self.instrument.tem.Defocus
			foc = self.instrument.tem.Focus
			self.logger.info('Defocus: %s, Focus: %s' % (defoc, foc))
		except Exception, e:
			self.logger.exception('Autofocus failed: %s' % e)

		try:
			correction = self.btcalclient.measureDefocusStig(btilt, pub, drift_threshold=driftthresh, image_callback=self.setImage, target=target, correct_tilt=True, correlation_type=setting['correlation type'], stig=True)
		except calibrationclient.Abort:
			self.logger.info('Measurement of defocus and stig. has been aborted')
			return 'aborted'
		except calibrationclient.Drifting:
			self.driftDetected(presetname, emtarget, driftthresh)
			self.logger.info('Drift detected (will try again when drift is done)')
			return 'repeat'
		except calibrationclient.NoMatrixCalibrationError, e:
			self.player.pause()
			self.logger.error('Measurement failed without calibration: %s' % e)
			self.logger.info('Calibrate and then continue...')
			self.beep()
			return 'repeat'

		self.logger.info('Measured defocus and stig %s' % correction)
		defoc = correction['defocus']
		stigx = correction['stigx']
		stigy = correction['stigy']
		fitmin = correction['min']
		lastdrift = correction['lastdrift']

		resultdata.update({'defocus':defoc, 'stigx':stigx, 'stigy':stigy, 'min':fitmin, 'drift': lastdrift})

		###### focus validity checks
		validdefocus = True
		status = 'ok'
		logmessage = 'Good focus measurement'

		### check fit limit
		fitlimit = setting['fit limit']
		if fitmin > fitlimit:
			status = 'fit untrusted (%s>%s)' % (fitmin, fitlimit)
			validdefocus = False
			logmessage = 'Focus measurement failed: fit = %s (fit limit = %s)' % (fitmin, fitlimit)
			if focustype == 'Defocus':
				self.logger.info('Setting eucentric focus...')
				self.eucentricFocusToScope()
				self.logger.info('Eucentric focus set')
				self.eucset = True
				self.resetDefocus()
			else:
				self.eucset = False
		### check change limit
		delta_min = setting['delta min']
		delta_max = setting['delta max']
		if not (delta_min <= abs(defoc) <= delta_max):
			status = 'invalid'
			validdefocus = False
			logmessage = 'Focus measurement failed: change = %s (change limit = %s to %s)' % (defoc, delta_min, delta_max)

		if validdefocus:
			self.logger.info(logmessage)
		else:
			self.logger.warning(logmessage)

		### validate stig correction
		# stig is only valid in a certain defocus range
		if setting['stig correction']:
			if None in (stigx,stigy):
				self.logger.warning('No stig matrices, stig correction not solved')
				resultdata['stig correction'] = 0
			else:
				self.logger.info('Stig. correction...')
				stigdefocrange = [abs(setting['stig defocus min']),abs(setting['stig defocus max'])]
				stigdefocrange.sort()
				stigdefocusmin = stigdefocrange[0]
				stigdefocusmax = stigdefocrange[1]
				if validdefocus and stigdefocusmin < abs(defoc) < stigdefocusmax:
					self.correctStig(stiglens, stigx, stigy)
					resultdata['stig correction'] = 1
				else:
					self.logger.info('Stig. correction invalid due to invalid defocus')
					resultdata['stig correction'] = 0
		else:
			resultdata['stig correction'] = 0

		if validdefocus:
			self.logger.info('Defocus correction...')
			try:
				focustype = setting['correction type']
				correctmethod = self.correction_types[focustype]
			except (IndexError, KeyError):
				self.logger.warning('No method selected for correcting defocus')
			else:
				resultdata['defocus correction'] = focustype
				newdefoc = defoc - self.deltaz
				correctmethod(newdefoc, setting)
			resultstring = 'corrected focus by %.3e (measured) - %.3e (z due to tilt) = %.3e (total) using %s (min=%s)' % (defoc, self.deltaz, newdefoc, focustype,fitmin)
		else:
			resultstring = 'invalid focus measurement (min=%s)' % (fitmin,)
		if resultdata['stig correction']:
			resultstring = resultstring + ', corrected stig by x,y=%.4f,%.4f' % (stigx, stigy)
		self.logger.info(resultstring)
		return status

	def autoStage(self, setting, emtarget, resultdata):
		presetname = setting['preset name']
		## need btilt, pub, driftthresh
		atilt = setting['tilt']

		# fake eucset, because we don't need it, but still need to correct z later
		self.eucset = True
		# don't reset defocus after it is corrected
		self.reset = False

		# not working yet
		#if setting['check drift']:
		#	driftthresh = setting['drift threshold']
		#else:
		#	driftthresh = None

		## send the autofocus preset to the scope
		self.presetsclient.toScope(presetname, emtarget)
		target = emtarget['target']

		delay = self.settings['pause time']
		self.logger.info('Pausing for %s seconds' % (delay,))
		time.sleep(delay)

		z = self.stagetiltcalclient.measureZ(atilt, image_callback=self.setImage, correlation_type=setting['correlation type'])

		self.logger.info('Measured Z: %.4e' % z)
		resultdata['defocus'] = z

		###### focus validity checks
		validdefocus = True
		status = 'ok'
		logmessage = 'Good focus measurement'

		### check change limit
		delta_min = setting['delta min']
		delta_max = setting['delta max']
		deltarange = [abs(setting['delta min']),abs(setting['delta max'])]
		deltarange.sort()
		delta_min = deltarange[0]
		delta_max = deltarange[1]
		if not (delta_min <= abs(z) <= delta_max):
			status = 'invalid'
			validdefocus = False
			logmessage = 'Focus measurement failed: change = %s (change limit = %s to %s)' % (z, delta_min, delta_max)

		if not validdefocus:
			self.logger.warning(logmessage)
		else:
			self.logger.info(logmessage)

			self.logger.info('Defocus correction...')
			try:
				focustype = setting['correction type']
				correctmethod = self.correction_types[focustype]
			except (IndexError, KeyError):
				self.logger.warning('No method selected for correcting defocus')
			else:
				resultdata['defocus correction'] = focustype
				correctmethod(z, setting)
			resultstring = 'corrected focus by %.3e using %s' % (z, focustype)

			self.logger.info(resultstring)
		return status

	def processFocusSetting(self, setting, target=None, emtarget=None):
		resultdata = data.FocuserResultData(session=self.session)
		resultdata['target'] = target
		resultdata['method'] = setting['focus method']
		status = 'unknown'
		preset_name = setting['preset name']

		if setting['focus method'] == 'Manual':
			self.setStatus('user input')
			self.manualCheckLoop(preset_name, emtarget)
			self.setStatus('processing')
			status = 'ok'
		elif setting['focus method'] == 'Beam Tilt':
			status = self.autoFocus(setting, emtarget, resultdata)
		elif setting['focus method'] == 'Stage Tilt':
			status = self.autoStage(setting, emtarget, resultdata)

		resultdata['status'] = status
		self.publish(resultdata, database=True, dbforce=True)

		return status

	def acquire(self, presetdata, target=None, emtarget=None, attempt=None):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we do autofocus
		'''
		## sometimes have to apply or un-apply deltaz if image shifted on
		## tilted specimen
		if emtarget is None:
			self.deltaz = 0
		else:
			self.deltaz = emtarget['delta z']

		## Need to melt only once per target, even though
		## this method may be called multiple times on the same
		## target.
		melt_time = self.settings['melt time']
		if melt_time and attempt > 1:
			self.logger.info('Target attempt %s, not melting' % (attempt,))
		elif melt_time:
			self.logger.info('Melting ice...')
			self.exposeSpecimen(melt_time)

		status = 'unknown'

		for setting in self.focus_sequence:
			if not setting['switch']:
				message = 'Skipping focus setting \'%s\'...' % setting['name']
				self.logger.info(message)
				continue
			message = 'Processing focus setting \'%s\'...' % setting['name']
			self.logger.info(message)
			status = self.processFocusSetting(setting, target=target, emtarget=emtarget)
			## repeat means give up and do the whole target over
			if status == 'repeat':
				return 'repeat'

		# aquire and save the focus image
		if self.settings['acquire final']:
			## go back to focus preset and target
			self.presetsclient.toScope(presetdata['name'], emtarget)
			delay = self.settings['pause time']
			self.logger.info('Pausing for %s seconds' % (delay,))
			time.sleep(delay)

			## acquire and publish image, like superclass does
			acquisition.Acquisition.acquire(self, presetdata, target, emtarget)

		return status

	def alreadyAcquired(self, targetdata, presetname):
		## for now, always do acquire
		return False

	def manualNow(self):
		errstr = 'Manual focus failed: %s'
		presetnames = self.settings['preset order']
		try:
			presetname = presetnames[0]
		except IndexError:
			message = 'no presets specified for manual focus'
			self.logger.error(errstr % message)
			return
		istr = 'Using preset \'%s\' for manual focus check' % (presetname,)
		self.logger.info(istr)
		### Warning:  no target is being used, you are exposing
		### whatever happens to be under the beam
		t = threading.Thread(target=self.manualCheckLoop, args=())
		t.setDaemon(1)
		t.start()

	def onManualCheck(self):
		evt = gui.wx.Focuser.ManualCheckEvent(self.panel)
		self.panel.GetEventHandler().AddPendingEvent(evt)

	def onManualCheckDone(self):
		evt = gui.wx.Focuser.ManualCheckDoneEvent(self.panel)
		self.panel.GetEventHandler().AddPendingEvent(evt)

	def manualCheckLoop(self, presetname=None, emtarget=None):
		## go to preset and target
		if presetname is not None:
			self.presetsclient.toScope(presetname, emtarget)
			delay = self.settings['pause time']
			self.logger.info('Pausing for %s seconds' % (delay,))
			time.sleep(delay)
		self.logger.info('Starting manual focus loop, please confirm defocus...')
		self.beep()
		self.manualplayer.play()
		self.onManualCheck()
		while True:
			state = self.manualplayer.state()
			if state == 'stop':
				break
			elif state == 'pause':
				if self.manualplayer.wait() == 'stop':
					break
				if presetname is not None:
					self.logger.info('Reseting preset and target after pause')
					self.logger.debug('preset %s' % (presetname,))
					self.presetsclient.toScope(presetname, emtarget)
			# acquire image, show image and power spectrum
			# allow user to adjust defocus and stig
			correction = self.settings['correct image']
			self.manualchecklock.acquire()
			try:
				if correction:
					imagedata = self.instrument.getData(data.CorrectedCameraImageData)
				else:
					imagedata = self.instrument.getData(data.CameraImageData)
				imarray = imagedata['image']
			except:
				raise
				self.manualchecklock.release()
				self.manualplayer.pause()
				self.logger.error('Failed to acquire image, pausing...')
				continue
			self.manualchecklock.release()
			pow = imagefun.power(imarray, self.maskradius)
			self.man_power = pow.astype(Numeric.Float32)
			self.man_image = imarray.astype(Numeric.Float32)
			self.panel.setManualImage(self.man_image, 'Image')
			self.panel.setManualImage(self.man_power, 'Power')
		self.onManualCheckDone()
		self.logger.info('Manual focus check completed')

	def onFocusUp(self, parameter):
		self.changeFocus(parameter, 'up')
		self.panel.manualUpdated()

	def onFocusDown(self, parameter):
		self.changeFocus(parameter, 'down')
		self.panel.manualUpdated()

	def onResetDefocus(self):
		self.manualchecklock.acquire()
		self.logger.info('Reseting defocus...')
		if self.deltaz:
			self.logger.info('temporarily applying defocus offset due to z offset %.3e of image shifted target' % (self.deltaz,))
			origdefocus = self.instrument.tem.Defocus
			tempdefocus = origdefocus - self.deltaz
			self.instrument.tem.Defocus = tempdefocus
		try:
			self.resetDefocus()
			self.logger.info('Defocus reset')
		finally:
			if self.deltaz:
				self.instrument.tem.Defocus = self.deltaz
				self.logger.info('returned to defocus offset for image shifted target')
			self.manualchecklock.release()
			self.panel.manualUpdated()

	def resetDefocus(self):
		errstr = 'Reset defocus failed: %s'
		try:
			self.instrument.tem.resetDefocus(True)
		except:
			self.logger.error(errstr % 'unable to access instrument')

	def onChangeToEucentric(self):
		self.manualchecklock.acquire()
		self.logger.info('Changing to eucentric focus')
		try:
			self.eucentricFocusToScope()
		finally:
			self.manualchecklock.release()
			self.panel.manualUpdated()

	def onEucentricFromScope(self):
		self.eucentricFocusFromScope()
		self.panel.manualUpdated()

	def setFocus(self, value):
		self.manualchecklock.acquire()
		if self.deltaz:
			final = value + self.deltaz
			self.logger.info('Setting defocus to %.3e + z offset %.3e = %.3e' % (value,self.deltaz, final))
		else:
			final = value
			self.logger.info('Setting defocus to %.3e' % (value,))
		try:
			self.instrument.tem.Defocus = final
		finally:
			self.manualchecklock.release()
			self.panel.manualUpdated()

	def changeFocus(self, parameter, direction):
		delta = self.increment
		self.manualchecklock.acquire()
		self.logger.info('Changing %s %s %s' % (parameter, direction, delta))
		try:
			if parameter == 'Stage Z':
				value = self.instrument.tem.StagePosition['z']
			elif parameter == 'Defocus':
				value = self.instrument.tem.Defocus
			if direction == 'up':
				value += delta
			elif direction == 'down':
				value -= delta
			
			if parameter == 'Stage Z':
				self.instrument.tem.StagePosition = {'z': value}
			elif parameter == 'Defocus':
				self.instrument.tem.Defocus = value
		except Exception, e:
			self.logger.exception('Change focus failed: %s' % e)
			self.manualchecklock.release()
			return

		self.manualchecklock.release()

		#self.logger.info('Changed %s %s %s' % (parameter, direction, delta,))

	def correctStig(self, stiglens, deltax, deltay):
		stig = self.instrument.tem.Stigmator
		stig[stiglens]['x'] += deltax
		stig[stiglens]['y'] += deltay
		self.logger.info('Correcting %s stig by %s, %s' % (stiglens, deltax, deltay))
		self.instrument.tem.Stigmator = stig

	def correctDefocus(self, delta, setting):
		reset = setting['reset defocus']
		defocus = self.instrument.tem.Defocus
		self.logger.info('Defocus before applying correction %s' % defocus)
		defocus += delta
		self.logger.info('Correcting defocus by %s' % (delta,))
		self.instrument.tem.Defocus = defocus
		if reset or reset is None:
			self.resetDefocus()

	def correctZ(self, delta, setting):
		reset = setting['reset defocus']
		if not self.eucset:
			self.logger.warning('Eucentric focus was not set before measuring defocus because \'Stage Z\' was not selected then, but is now. Skipping Z correction.')
			return

		## We are not smart enough to center the "Stage Tilt" method around
		## the current tilt, so we center it around 0.0
		## We must take this into account for the cos() correction
		stage = self.instrument.tem.StagePosition
		if setting['focus method'] == 'Stage Tilt':
			alpha = 0.0
		else:
			alpha = stage['a']

		deltaz = delta * Numeric.cos(alpha)
		newz = stage['z'] + deltaz
		self.logger.info('Correcting stage Z by %s (defocus change %s at alpha %s)' % (deltaz,delta,alpha))
		self.instrument.tem.StagePosition = {'z': newz}
		if reset or (reset is None and self.reset):
			self.resetDefocus()

		# declare drift
		self.logger.info('Declaring drift after correcting stage Z')
		self.declareDrift(type='stage')

	def correctNone(self, delta, setting):
		self.logger.info('Not applying defocus correction')

	def onTest(self):
		self.acquire(None)

	def onAbortFailure(self):
		self.btcalclient.abortevent.set()

	def onManualPlayer(self, state):
		self.panel.playerEvent(state, self.panel.manualdialog)
