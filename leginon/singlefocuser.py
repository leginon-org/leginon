#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
import manualfocuschecker
import acquisition
import node, leginondata
import calibrationclient
import threading
import event
import time
import math
from pyami import imagefun, ordereddict
import numpy
import copy
import gui.wx.Focuser
import player

class Focuser(manualfocuschecker.ManualFocusChecker):
	panelclass = gui.wx.Focuser.Panel
	settingsclass = leginondata.FocuserSettingsData
	defaultsettings = manualfocuschecker.ManualFocusChecker.defaultsettings
	defaultsettings.update({
		'process target type': 'focus',
		'melt time': 0.0,
		'melt preset': '',
		'manual focus preset': '',
		'acquire final': True,
        'process target type': 'focus',
		'beam tilt settle time': 0.25,
	})

	eventinputs = manualfocuschecker.ManualFocusChecker.eventinputs
	eventoutputs = manualfocuschecker.ManualFocusChecker.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		self.focus_methods = ordereddict.OrderedDict((
			('Manual', self.manualCheckLoop),
			('Beam Tilt', self.autoFocus),
			('Stage Tilt', self.autoStage),
			('None', self.noMeasure),
		))

		self.correction_types = ordereddict.OrderedDict((
			('Defocus', self.correctDefocusStig),
			('Stage Z', self.correctZ),
			('None', self.correctNone),
		))

		self.correlation_types = ['cross', 'phase']
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
			'stig defocus min': 2e-6,
			'stig defocus max': 4e-6,
			'check drift': False,
			'drift threshold': 3e-10,
			'reset defocus': None,
		}
		self.manualplayer = player.Player(callback=self.onManualPlayer)
		manualfocuschecker.ManualFocusChecker.__init__(self, id, session, managerlocation, **kwargs)
		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.stagetiltcalclient = calibrationclient.StageTiltCalibrationClient(self)
		self.imageshiftcalclient = calibrationclient.ImageShiftCalibrationClient(self)
		self.euclient = calibrationclient.EucentricFocusClient(self)
		self.focus_sequence = self.researchFocusSequence()

	def validatePresets(self):
		### check normal manualfocuschecker presets
		try:
			manualfocuschecker.ManualFocusChecker.validatePresets(self)
		except:
			if self.settings['acquire final']:
				raise
		availablepresets = self.getPresetNames()

		### check melt preset
		if self.settings['melt time']:
			meltpreset = self.settings['melt preset']
			if meltpreset not in availablepresets:
				raise acquisition.InvalidPresetsSequence('bad melt preset: %s' % (meltpreset,))

		### check sequence presets
		for setting in self.focus_sequence:
			presetname = setting['preset name']
			settingname = setting['name']
			if presetname not in availablepresets:
				raise acquisition.InvalidPresetsSequence('bad preset %s in focus sequence %s' % (presetname, settingname))

	def researchFocusSequence(self):
		user_data = self.session['user']
		initializer = {
			'session': leginondata.SessionData(user=user_data),
			'node name': self.name,
		}
		query = leginondata.FocusSequenceData(initializer=initializer)
		try:
			focus_sequence_data = self.research(query, results=1)[0]
		except IndexError:
			# if that failed, try to load default settings from DB
			query = leginondata.FocusSequenceData(initializer={'isdefault': True, 'node name': self.name})
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
			'session': leginondata.SessionData(user=self.session['user']),
			'node name': self.name,
			'name': name,
		}
		query = leginondata.FocusSettingData(initializer=initializer)
		try:
			focus_setting_data = self.research(query, results=1)[0]
		except IndexError:
			# if that failed, try to load default settings from DB
			query = leginondata.FocusSettingData(initializer={'isdefault': True, 'node name': self.name, 'name': name})
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

	def setFocusSequence(self, sequence, isdefault=False):
		sequence_names = [s['name'] for s in sequence]
		if sequence_names != [s['name'] for s in self.focus_sequence]:
			initializer = {
				'session': self.session,
				'sequence': sequence_names,
				'node name': self.name,
			}
			if self.session['user']['username'] == 'administrator':
				initializer['isdefault'] = True
			else:
				initializer['isdefault'] = isdefault
			sequence_data = leginondata.FocusSequenceData(initializer=initializer)
			self.publish(sequence_data, database=True, dbforce=True)
		for setting in sequence:
			if setting != self.researchFocusSetting(setting['name']):
				initializer = setting.copy()
				initializer['session'] = self.session
				initializer['node name'] = self.name
				if self.session['user']['username'] == 'administrator':
					initializer['isdefault'] = True
				else:
					initializer['isdefault'] = isdefault
				setting_data = leginondata.FocusSettingData(initializer=initializer)
				self.publish(setting_data, database=True, dbforce=True)
		self.focus_sequence = sequence

	def autoFocus(self, setting, emtarget, resultdata):
		presetname = setting['preset name']
		stiglens = 'objective'
		## need btilt, pub, driftthresh
		btilt = setting['tilt']

		### Drift check
		if setting['check drift']:
			driftthresh = setting['drift threshold']
			# move first if needed
			# TO DO: figure out how drift monitor behaves in RCT if doing this
			self.conditionalMoveAndPreset(presetname, emtarget)
			driftresult = self.checkDrift(presetname, emtarget, driftthresh)
			if driftresult['status'] == 'drifted':
				self.logger.info('Drift was detected so target will be repeated')
				return 'repeat'
			if driftresult['status'] == 'timeout':
				self.logger.warning('still drifting after timeout')
				return 'aborted'
			lastdrift = driftresult['final']
			lastdriftimage = self.driftimage
			self.logger.info('using final drift image in focuser')
			self.setImage(lastdriftimage['image'], 'Image')
		else:
			lastdrift = None
			lastdriftimage = None

		## send the autofocus preset to the scope
		## drift check may have done this already
		self.conditionalMoveAndPreset(presetname,emtarget)

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
			# Make sure defocus is set according to the preset
			# Otherwise two defocus correction sequence 
			# using the same preset would have close
			# to zero defocus after the first correction
			p = self.presetsclient.getCurrentPreset()
			self.instrument.tem.Defocus = p['defocus']
			self.eucset = False
		self.reset = True
		# get original beam to use to reset before return for any reason.
		# failed in the process or not as a safety
		beamtilt0 = self.btcalclient.getBeamTilt()

		try:
			# increased settle time from 0.25 to 0.5 for Falcon protector
			settletime = self.settings['beam tilt settle time']
			### FIX ME temporarily switch off tilt correction because the calculation may be wrong Issue #3030
			correction = self.btcalclient.measureDefocusStig(btilt, correct_tilt=False, correlation_type=setting['correlation type'], stig=setting['stig correction'], settle=settletime, image0=lastdriftimage)
		except calibrationclient.Abort:
			self.btcalclient.setBeamTilt(beamtilt0)
			self.logger.info('Measurement of defocus and stig. has been aborted')
			return 'aborted'
		except calibrationclient.NoMatrixCalibrationError, e:
			self.btcalclient.setBeamTilt(beamtilt0)
			self.player.pause()
			self.logger.error('Measurement failed without calibration: %s' % e)
			self.logger.info('Calibrate and then continue...')
			self.beep()
			return 'repeat'
		except:
			# any other exception
			self.btcalclient.setBeamTilt(beamtilt0)
			raise

		if setting['stig correction'] and correction['stigx'] and correction['stigy']:
			sx = '%.3f' % correction['stigx']
			sy = '%.3f' % correction['stigy']
		else:
			sx = sy = 'N/A'
		self.logger.info('Measured defocus: %.3e, stigx: %s, stigy: %s, min: %.2f' % (correction['defocus'], sx, sy, correction['min']))
		defoc = correction['defocus']
		stigx = correction['stigx']
		stigy = correction['stigy']
		fitmin = correction['min']

		resultdata.update({'defocus':defoc, 'stigx':stigx, 'stigy':stigy, 'min':fitmin, 'drift': lastdrift})
		self.btcalclient.setBeamTilt(beamtilt0)
		return 'ok'

		#####################################################################

	def validateMeasurementResult(self, setting, resultdata):
		fitmin = resultdata['min']
		focustype = setting['correction type']
		defoc = resultdata['defocus']
		stigx = resultdata['stigx']
		stigy = resultdata['stigy']

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
			self.logger.warning(logmessage)
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
			self.logger.warning(logmessage)
		else:
			self.logger.info(logmessage)

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
					resultdata['stig correction'] = 0
				else:
					self.logger.info('Stig. correction invalid due to invalid defocus')
					resultdata['stig correction'] = 0
		else:
			resultdata['stig correction'] = 0
		return status
		
	def correctDefocusStig(self, setting, resultdata):
		correction_type = setting['correction type']
		fitmin = resultdata['min']
		if resultdata['stig correction']:
			self.correctStig(stiglens, stigx, stigy)
			resultstring = resultstring + ', corrected stig by x,y=%.4f,%.4f' % (stigx, stigy)
			self.logger.info(resultstring)

		self.logger.info('Defocus correction...')
		defoc = resultdata['defocus']
		resultdata['defocus correction'] = correction_type
		newdefoc = defoc - self.deltaz
		self.correctDefocus(newdefoc, setting)
		resultstring = 'corrected focus by %.3e (measured) - %.3e (z due to tilt) = %.3e (total) using %s (min=%s)' % (defoc, self.deltaz, newdefoc, correction_type,fitmin)
		self.logger.info(resultstring)

	def autoStage(self, setting, emtarget, resultdata):
		presetname = setting['preset name']
		## need btilt, driftthresh
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
		## drift check or melting may have done this already
		self.conditionalMoveAndPreset(presetname,emtarget)
		target = emtarget['target']
		try:
			z = self.stagetiltcalclient.measureZ(atilt, correlation_type=setting['correlation type'])
			self.logger.info('Measured Z: %.4e' % z)
			resultdata['defocus'] = z
		except:
			status = 'failed'
		else:
			status = 'ok'

		return status

	def noMeasure(self, *args, **kwargs):
		self.logger.info('no measurement selected')

	def alignRotationCenter(self, defocus1, defocus2):
		try:
			bt = self.btcalclient.measureRotationCenter(defocus1, defocus2, correlation_type=None, settle=0.5)
		except Exception, e:
			self.logger.error('Failed rotation center measurement: %s' % (e,))
		self.logger.info('Misalignment correction: %.4f, %.4f' % (bt['x'],bt['y'],))
		if bt['x'] == 0.0 and bt['y'] == 0.0:
			return
		oldbt = self.instrument.tem.BeamTilt
		self.logger.info('Old beam tilt: %.4f, %.4f' % (oldbt['x'],oldbt['y'],))
		newbt = {'x': oldbt['x'] + bt['x'], 'y': oldbt['y'] + bt['y']}
		self.instrument.tem.BeamTilt = newbt
		self.logger.info('New beam tilt: %.4f, %.4f' % (newbt['x'],newbt['y'],))

	def measureTiltAxis(self, atilt, anumtilts=1, atilttwice=False, update=False, asnr=10.0,
	  acorr='phase', amedfilt=False, usedefocus=False):

		atiltrad = atilt * math.pi / 180.0
		if usedefocus == False:
			im0, pixelshift = self.stagetiltcalclient.measureTiltAxisLocation(tilt_value=atiltrad, numtilts=anumtilts,
				tilttwice=atilttwice, update=update, snrcut=asnr, correlation_type=acorr, medfilt=amedfilt)
		else:
			im0, pixelshift = self.stagetiltcalclient.measureTiltAxisLocation2(atiltrad, atilttwice, update, acorr, 0.01)
		if pixelshift is not None:
			oldscope = im0['scope']
			newscope = self.imageshiftcalclient.transform(pixelshift, oldscope, im0['camera'])
			imx = newscope['image shift']['x'] - oldscope['image shift']['x']
			imy = newscope['image shift']['y'] - oldscope['image shift']['y']
			self.logger.info('Image shift offset:  x = %.3e, y = %.3e' % (imx, imy))

	def processFocusSetting(self, setting, emtarget=None):
		resultdata = leginondata.FocuserResultData(session=self.session)
		resultdata['target'] = emtarget['target']
		resultdata['preset'] = emtarget['preset']
		resultdata['method'] = setting['focus method']
		status = 'unknown'
		# measuremrnt
		try:
			measuretype = setting['focus method']
			meth = self.focus_methods[measuretype]
		except (IndexError, KeyError):
			self.logger.warning('No method selected for correcting defocus')
		else:
			self.startTimer(measuretype)
			status = meth(setting, emtarget, resultdata)
			self.stopTimer(measuretype)
		if status == 'ok' and measuretype != 'Manual':
			# validation
			status = self.validateMeasurementResult(setting, resultdata)
			if status == 'ok':
				# correction
				try:
					correcttype = setting['correction type']
					correctmethod = self.correction_types[correcttype]
				except (IndexError, KeyError):
					self.logger.warning('No method selected for correcting defocus')
				else:
					correctmethod(setting, resultdata)
		resultdata['status'] = status
		scopedata = self.instrument.getData(leginondata.ScopeEMData)
		scopedata.insert(force=True)
		resultdata['scope'] = scopedata
		self.publish(resultdata, database=True, dbforce=True)
		stagenow = self.instrument.tem.StagePosition
		self.logger.debug('z after step %s %.2f um' % (setting['name'], stagenow['z']*1e6))

		return status

	def conditionalMoveAndPreset(self,target_presetname, emtarget):
		'''
		Only call moveAndPreset if this is the first time the target is processed.
		This reduces time spent in moving.
		'''
		p = self.presetsclient.getCurrentPreset()
		if p is None or p['name'] != target_presetname or self.new_acquire:
			presetdata = self.presetsclient.getPresetFromDB(target_presetname)
			self.moveAndPreset(presetdata, emtarget)
			self.new_acquire = False
			return

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we do autofocus
		'''
		self.new_acquire = True

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
			self.startTimer('melt')
			self.logger.info('Melting ice...')

			#### change to melt preset
			meltpresetname = self.settings['melt preset']
			self.conditionalMoveAndPreset(meltpresetname,emtarget)
			self.logger.info('melt preset: %s' % (meltpresetname,))

			self.startTimer('melt exposeSpecimen')
			self.exposeSpecimen(melt_time)
			self.stopTimer('melt exposeSpecimen')
			self.stopTimer('melt')

		status = 'unknown'

		for setting in self.focus_sequence:
			if not setting['switch']:
				message = 'Skipping focus setting \'%s\'...' % setting['name']
				self.logger.info(message)
				continue
			message = 'Processing focus setting \'%s\'...' % setting['name']
			self.logger.info(message)
			self.startTimer('processFocusSetting')
			self.clearBeamPath()
			status = self.processFocusSetting(setting, emtarget=emtarget)
			self.stopTimer('processFocusSetting')
			## repeat means give up and do the whole target over
			if status == 'repeat':
				return 'repeat'

		# aquire and save the focus image
		if self.settings['acquire final']:
			self.clearBeamPath()
			manualfocuschecker.ManualFocusChecker.acquire(self, presetdata, emtarget)
		stagenow = self.instrument.tem.StagePosition
		msg = 'z after all adjustment %.2f um' % (1e6*stagenow['z'])
		self.testprint('Focuser: '+msg)
		self.logger.debug(msg)

		return status

	def alreadyAcquired(self, targetdata, presetname):
		## for now, always do acquire
		return False

	def onManualCheck(self):
		evt = gui.wx.Focuser.ManualCheckEvent(self.panel)
		self.panel.GetEventHandler().AddPendingEvent(evt)

	def onManualCheckDone(self):
		evt = gui.wx.Focuser.ManualCheckDoneEvent(self.panel)
		self.panel.GetEventHandler().AddPendingEvent(evt)

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
		self.logger.info('Correcting defocus by %.3e' % (delta,))
		self.instrument.tem.Defocus = defocus
		if reset or reset is None:
			self.resetDefocus()

	def correctZ(self, setting, resultdata):
		delta = resultdata['defocus']
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

		deltaz = delta * numpy.cos(alpha)
		newz = stage['z'] + deltaz
		self.logger.info('Correcting stage Z by %s (defocus change %s at alpha %s)' % (deltaz,delta,alpha))
		try:
			self.instrument.tem.StagePosition = {'z': newz}
			if reset or (reset is None and self.reset):
				self.resetDefocus()
		except ValueError:
			self.logger.warning('Stage Z correction to %.0f um failed. Likely Limit reached' % (newz*1e6))
		resultdata['defocus correction'] = setting['correction type']
		# declare drift
		self.logger.info('Declaring drift after correcting stage Z')
		self.declareDrift(type='stage')

	def correctNone(self, setting, resultdata):
		self.logger.info('Not applying defocus correction')

	def onTest(self):
		self.acquire(None)

	def onAbortFailure(self):
		self.btcalclient.abortevent.set()

	def avoidTargetAdjustment(self,target_to_adjust,recent_target):
		'''
		RCT Focus should not adjust targets. refs #2665. It would be better not
		having specify this by node name but through application node
		binding.
		'''
		if self.name != 'RCT Focus':
			return False
		else:
			return True
