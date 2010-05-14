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
import threading
import event
import time
import math
from pyami import imagefun, fftfun, ordereddict
import numpy
import copy
import gui.wx.Focuser
import player

class Focuser(acquisition.Acquisition):
	panelclass = gui.wx.Focuser.Panel
	settingsclass = leginondata.FocuserSettingsData
	defaultsettings = acquisition.Acquisition.defaultsettings
	defaultsettings.update({
		'process target type': 'focus',
		'melt time': 0.0,
		'melt preset': '',
		'acquire final': True,
        'process target type': 'focus',
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

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
		self.samecorrection = False
		self.manualchecklock = threading.Lock()
		self.maskradius = 1.0
		self.increment = 5e-7
		self.man_power = None
		self.man_image = None
		self.manualplayer = player.Player(callback=self.onManualPlayer)
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.stagetiltcalclient = calibrationclient.StageTiltCalibrationClient(self)
		self.imageshiftcalclient = calibrationclient.ImageShiftCalibrationClient(self)
		self.euclient = calibrationclient.EucentricFocusClient(self)
		self.focus_sequence = self.researchFocusSequence()
		self.deltaz = 0.0

	def validatePresets(self):
		### check normal acquisition presets
		try:
			acquisition.Acquisition.validatePresets(self)
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
			delta = eufocdata.timestamp.now() - eufocdata.timestamp
			if delta.days > 90:
				self.logger.warning('Not setting eucentric focus older than 90 days, HT: %s and Mag.: %s' % (ht, mag))
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

		### Drift check
		if setting['check drift']:
			driftthresh = setting['drift threshold']
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
		p = self.presetsclient.getCurrentPreset()
		if p is None or p['name'] != presetname:
			self.presetsclient.toScope(presetname, emtarget)

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

		try:
			correction = self.btcalclient.measureDefocusStig(btilt, correct_tilt=True, correlation_type=setting['correlation type'], stig=setting['stig correction'], settle=0.25, image0=lastdriftimage)
		except calibrationclient.Abort:
			self.logger.info('Measurement of defocus and stig. has been aborted')
			return 'aborted'
		except calibrationclient.NoMatrixCalibrationError, e:
			self.player.pause()
			self.logger.error('Measurement failed without calibration: %s' % e)
			self.logger.info('Calibrate and then continue...')
			self.beep()
			return 'repeat'

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
		self.presetsclient.toScope(presetname, emtarget)
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
		bt = self.btcalclient.measureRotationCenter(defocus1, defocus2, correlation_type=None, settle=0.5)
		self.logger.info('Misalignment correction: %.4f, %.4f' % (bt['x'],bt['y'],))
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

		return status

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None):
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
			self.startTimer('melt')
			self.logger.info('Melting ice...')

			#### change to melt preset
			meltpresetname = self.settings['melt preset']
			p = self.presetsclient.getCurrentPreset()
			if p is None or p['name'] != meltpresetname:
				self.presetsclient.toScope(meltpresetname, emtarget)
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
			status = self.processFocusSetting(setting, emtarget=emtarget)
			self.stopTimer('processFocusSetting')
			## repeat means give up and do the whole target over
			if status == 'repeat':
				return 'repeat'

		# aquire and save the focus image
		if self.settings['acquire final']:
			acquisition.Acquisition.acquire(self, presetdata, emtarget)

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
		setting = {'preset name': presetname}
		t = threading.Thread(target=self.manualCheckLoop, args=(setting,None))
		t.setDaemon(1)
		t.start()

	def onManualCheck(self):
		evt = gui.wx.Focuser.ManualCheckEvent(self.panel)
		self.panel.GetEventHandler().AddPendingEvent(evt)

	def onManualCheckDone(self):
		evt = gui.wx.Focuser.ManualCheckDoneEvent(self.panel)
		self.panel.GetEventHandler().AddPendingEvent(evt)

	def initSameCorrection(self):
		self.resetRepeatConfig()

	def acquireManualFocusImage(self):
		t0 = time.time()
		correction = self.settings['correct image']
		self.manualchecklock.acquire()
		if correction:
			imdata = self.acquireCorrectedCameraImageData(repeatconfig=True)
		else:
			imdata = self.acquireCameraImageData(repeatconfig=True)
		imarray = imdata['image']
		self.manualchecklock.release()
		pow = imagefun.power(imarray, self.maskradius)
		self.man_power = pow.astype(numpy.float32)
		self.man_image = imarray.astype(numpy.float32)
		self.panel.setManualImage(self.man_image, 'Image')
		self.panel.setManualImage(self.man_power, 'Power')
		#sleep if too fast in simulation
		safetime = 1.0
		t1 = time.time()
		if t1-t0 < safetime:
			time.sleep(safetime-(t1-t0))

	def manualCheckLoop(self, setting, emtarget=None, focusresult=None):
		## go to preset and target
		presetname = setting['preset name']
		if presetname is not None:
			self.presetsclient.toScope(presetname, emtarget)
		pixelsize,center = self.getReciprocalPixelSizeFromPreset(presetname)
		self.ht = self.instrument.tem.HighTension
		self.panel.onNewPixelSize(pixelsize,center,self.ht)
		self.logger.info('Starting manual focus loop, please confirm defocus...')
		self.beep()
		self.manualplayer.play()
		self.onManualCheck()
		self.initSameCorrection()
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
			try:
				self.acquireManualFocusImage()
			except:
				raise
				self.manualchecklock.release()
				self.manualplayer.pause()
				self.logger.error('Failed to acquire image, pausing...')
				continue

		self.onManualCheckDone()
		self.logger.info('Manual focus check completed')
		return 'ok'

	def getReciprocalPixelSizeFromPreset(self,presetname):
		if presetname is None:
			return None, None
		q = leginondata.PresetData(session=self.session,name=presetname)
		results = q.query(results=1)
		if not results:
			return None, None
		presetdata = results[0]
		scope = presetdata['tem']
		ccd = presetdata['ccdcamera']
		mag = presetdata['magnification']
		unbinned_rpixelsize = self.btcalclient.getPixelSize(mag,tem=scope, ccdcamera=ccd)
		if unbinned_rpixelsize is None:
			return None, None
		binning = presetdata['binning']
		dimension = presetdata['dimension']
		rpixelsize = {'x':1.0/(unbinned_rpixelsize*binning['x']*dimension['x']),'y':1.0/(unbinned_rpixelsize*binning['y']*dimension['y'])}
		# This will not work for non-square image
		self.rpixelsize = rpixelsize['x']
		center = {'x':dimension['x'] / 2, 'y':dimension['y'] / 2}
		return rpixelsize, center

	def estimateAstigmation(self,params):
		z0, zast, ast_ratio, angle = fftfun.getAstigmaticDefocii(params,self.rpixelsize,self.ht)
		self.logger.info('z0 %.2f um, zast %.2f um (%.0f %%), angle= %.0f deg' % (z0*1e6,zast*1e6,ast_ratio*100, angle*180.0/math.pi))

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
			self.instrument.tem.resetDefocus()
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
		self.instrument.tem.StagePosition = {'z': newz}
		if reset or (reset is None and self.reset):
			self.resetDefocus()
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

	def onManualPlayer(self, state):
		self.panel.playerEvent(state, self.panel.manualdialog)
	
