#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import acquisition
import node, data
import calibrationclient
import camerafuncs
import uidata
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

class Focuser(acquisition.Acquisition):
	panelclass = gui.wx.Focuser.Panel
	settingsclass = data.FocuserSettingsData
	# oops
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
		'correction type': 'Defocus',
		'preset': '',
		'melt time': 0.0,
		'beam tilt': 0.01,
		'drift threshold': 2.0,
		'fit limit': 1000,
		'check drift': True,
		'check before': False,
		'check after': False,
		'stig correction': False,
		'stig defocus min': 1e-6,
		'stig defocus max': 4e-6,
		'acquire final': True,
		'drift on z': True,
	}

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		self.focus_methods = {
			'None': self.correctNone,
			'Stage Z': self.correctZ,
			'Defocus': self.correctDefocus
		}

		self.manualchecklock = threading.Lock()
		self.abortfail = threading.Event()
		self.manual_check_done = threading.Event()
		self.manual_pause = threading.Event()
		self.manual_continue = threading.Event()
		self.parameter = 'Defocus'
		self.maskradius = 0.01
		self.increment = 5e-7
		self.man_power = None
		self.man_image = None
		acquisition.Acquisition.__init__(self, id, session, managerlocation, target_types=('focus',), **kwargs)
		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.euclient = calibrationclient.EucentricFocusClient(self)

	def eucentricFocusToScope(self):
		scope = self.emclient.getScope()
		ht = scope['high tension']
		mag = scope['magnification']
		eufoc = self.euclient.researchEucentricFocus(ht, mag)
		if eufoc is None:
			self.logger.error('no eucentric focus found for this ht=%s and mag=%s' % (ht, mag))
		else:
			eufoc = eufoc['focus']
			emdata = data.ScopeEMData(focus=eufoc)
			self.emclient.setScope(emdata)

	def eucentricFocusFromScope(self):
		scope = self.emclient.getScope()
		ht = scope['high tension']
		mag = scope['magnification']
		foc = scope['focus']
		self.euclient.publishEucentricFocus(ht, mag, foc)
		self.logger.info('eucentric focus saved to database, ht=%s, mag=%s, focus=%s' % (ht, mag, foc))

	def autoFocus(self, resultdata, presettarget):
		## need btilt, pub, driftthresh
		btilt = self.settings['beam tilt']
		pub = False
		if self.settings['check drift']:
			driftthresh = self.settings['drift threshold']
		else:
			driftthresh = None

		## send the autofocus preset to the scope
		autofocuspreset = presettarget['preset']
		self.presetsclient.toScope(autofocuspreset, presettarget['emtarget'])
		target = presettarget['emtarget']['target']

		## set to eucentric focus if doing Z correction
		## WARNING:  this assumes that user will not change
		## to another focus type before doing the correction
		focustype = self.settings['correction type']
		if focustype == 'Stage Z':
			self.logger.info('setting eucentric focus')
			self.eucentricFocusToScope()
			self.eucset = True
		else:
			self.eucset = False

		delay = self.settings['pause time']
		self.logger.info('Pausing for %s seconds' % (delay,))
		time.sleep(delay)

		### report the current focus and defocus values
		self.logger.info('Before autofocus...')
		try:
			scope = self.emclient.getScope()
			defoc = scope['defocus']
			foc = scope['focus']
			self.logger.info('Defocus %s' % defoc)
			self.logger.info('Focus %s' % foc)
		except:
			self.logger.exception('')

		try:
			correction = self.btcalclient.measureDefocusStig(btilt, pub, drift_threshold=driftthresh, image_callback=self.setImage, target=target)
		except calibrationclient.Abort:
			self.logger.info('measureDefocusStig was aborted')
			self.logger.info('aborted')
			return 'aborted'
		except calibrationclient.Drifting:
			self.driftDetected(presettarget)
			self.logger.info('drift detected (will try again when drift is done)')
			return 'repeat'

		self.logger.info('Measured defocus and stig %s' % correction)
		defoc = correction['defocus']
		stigx = correction['stigx']
		stigy = correction['stigy']
		fitmin = correction['min']
		lastdrift = correction['lastdrift']

		resultdata.update({'defocus':defoc, 'stigx':stigx, 'stigy':stigy, 'min':fitmin, 'drift': lastdrift})

		status = 'ok'

		### validate defocus correction
		fitlimit = self.settings['fit limit']
		if fitmin <= fitlimit:
			validdefocus = True
			self.logger.info('Good focus measurement')
		else:
			status = 'untrusted (%s>%s)' % (fitmin, fitlimit)
			validdefocus = False
			self.logger.info('Focus measurement failed: fitmin = %s (limit = %s)' % (fitmin, fitlimit))

		### validate stig correction
		# stig is only valid in a certain defocus range
		if validdefocus and (self.settings['stig defocus min'] < abs(defoc) < self.self.settings['stif defocus max']):
			validstig = True
		else:
			validstig = False

		if validstig and self.settings['stig correction']:
			self.logger.info('Stig correction...')
			self.correctStig(stigx, stigy)
			resultdata['stig correction'] = 1
		else:
			resultdata['stig correction'] = 0

		if validdefocus:
			self.logger.info('Defocus correction...')
			try:
				focustype = self.settings['correction type']
				focusmethod = self.focus_methods[focustype]
			except (IndexError, KeyError):
				self.logger.warning('No method selected for correcting defocus')
			else:
				resultdata['defocus correction'] = focustype
				focusmethod(defoc)
		if 'defocus correction' in resultdata:
			resultstring = 'corrected focus by %.3e using %s (min=%s)' % (defoc, focustype,fitmin)
		else:
			resultstring = 'invalid focus measurement (min=%s)' % (fitmin,)
		if resultdata['stig correction']:
			resultstring = resultstring + ', corrected stig by x,y=%.4f,%.4f' % (stigx, stigy)
		self.logger.info(resultstring)
		return status

	def acquire(self, presetdata, target=None, presettarget=None, attempt=None):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we do autofocus
		'''
		self.abortfail.clear()
		resultdata = data.FocuserResultData(session=self.session)
		resultdata['target'] = target

		## Need to melt only once per target, event though
		## this method may be called multiple times on the same
		## target.
		melt_time = self.settings['melt time']
		if melt_time and attempt > 1:
			self.logger.info('target attempt %s, so not melting' % (attempt,))
		elif melt_time:
			melt_time_ms = int(round(melt_time * 1000))
			camstate0 = self.cam.getCameraEMData()
			camstate1 = copy.copy(camstate0)
			camstate1['exposure time'] = melt_time_ms
			## make small image
			camsize = self.session['instrument']['camera size']
			bin = 8
			dim = camsize / bin
			camstate1['dimension'] = {'x':dim,'y':dim}
			camstate1['binning'] = {'x':bin,'y':bin}
			camstate1['offset'] = {'x':0,'y':0}
			self.cam.setCameraEMData(camstate1)

			self.logger.info('Melting for %s seconds' % (melt_time,))
			self.cam.acquireCameraImageData(correction=False)
			self.logger.info('Done melting, resetting camera')

			self.cam.setCameraEMData(camstate0)

		status = 'unknown'

		## pre manual check
		if self.settings['check before']:
			self.manualCheckLoop(presettarget)
			resultdata['pre manual check'] = True
			status = 'ok'
		else:
			resultdata['pre manual check'] = False

		## autofocus
		if self.autofocus:
			autofocuspreset = self.settings['preset']
			autopresettarget = data.PresetTargetData(emtarget=presettarget['emtarget'], preset=autofocuspreset)
			autostatus = self.autoFocus(resultdata, autopresettarget)
			resultdata['auto status'] = autostatus
			if autostatus == 'ok':
				status = 'ok'
			elif autostatus == 'repeat':
				### when we need to repeat, return immediately 
				return 'repeat'
			else:
				status = autostatus
		else:
			resultdata['auto status'] = 'skipped'

		## post manual check
		if self.settings['check after']:
			self.manualCheckLoop(presettarget)
			resultdata['post manual check'] = True
			status = 'ok'
		else:
			resultdata['post manual check'] = False

		## aquire and save the focus image
		if self.settings['acquire final']:
			## go back to focus preset and target
			self.presetsclient.toScope(presetdata['name'], presettarget['emtarget'])
			delay = self.settings['pause time']
			self.logger.info('Pausing for %s seconds' % (delay,))
			time.sleep(delay)

			## acquire and publish image, like superclass does
			acquisition.Acquisition.acquire(self, presetdata, target, presettarget)

		## publish results
		self.publish(resultdata, database=True, dbforce=True)

		return status

	def alreadyAcquired(self, targetdata, presettarget):
		## for now, always do acquire
		return False

	def manualNow(self):
		presetnames = self.settings['preset order']
		try:
			presetname = presetnames[0]
		except IndexError:
			message = 'no presets specified for manual focus'
			self.logger.error(message)
			return
		self.logger.info('using preset %s for manual check' % (presetname,))
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

	def manualCheckLoop(self, presettarget=None):
		## go to preset and target
		self.onManualCheck()
		if presettarget is not None:
			self.presetsclient.toScope(presettarget['preset'], presettarget['emtarget'])
			delay = self.settings['pause time']
			self.logger.info('Pausing for %s seconds' % (delay,))
			time.sleep(delay)
		self.manual_check_done.clear()
		self.logger.info('Starting manual focus loop...')
		self.logger.info('Please confirm defocus')
		node.beep()
		while 1:
			if self.manual_check_done.isSet():
				break
			if self.manual_pause.isSet():
				self.waitForContinue()
				if presettarget is not None:
					self.logger.info('reseting preset and target after pause')
					self.logger.debug('preset %s' % (presettarget['preset'],))
					self.presetsclient.toScope(presettarget['preset'], presettarget['emtarget'])
			# acquire image, show image and power spectrum
			# allow user to adjust defocus and stig
			cor = self.settings['correct image']
			self.logger.info('Correct image %s' % cor)
			self.manualchecklock.acquire()
			try:
				imagedata = self.cam.acquireCameraImageData(correction=cor)
			finally:
				self.manualchecklock.release()
			imarray = imagedata['image']
			pow = imagefun.power(imarray, self.maskradius)
			self.man_power = pow.astype(Numeric.Float32)
			self.man_image = imarray.astype(Numeric.Float32)
			self.panel.updateManualImages(self.panel)
		self.onManualCheckDone()
		self.logger.info('Manual focus loop done')

	def waitForContinue(self):
		self.logger.info('Manual focus paused')
		self.manual_continue.wait()
		self.manual_continue.clear()
		self.manual_pause.clear()

	def uiFocusUp(self):
		self.changeFocus('up')

	def uiFocusDown(self):
		self.changeFocus('down')

	def uiResetDefocus(self):
		self.manualchecklock.acquire()
		self.logger.info('Reset defocus')
		try:
			self.resetDefocus()
		finally:
			self.manualchecklock.release()

	def resetDefocus(self):
		newemdata = data.ScopeEMData()
		newemdata['reset defocus'] = True
		self.emclient.setScope(newemdata)

	def uiChangeToEucentric(self):
		self.manualchecklock.acquire()
		self.logger.info('Changing to eucentric focus')
		try:
			self.eucentricFocusToScope()
		finally:
			self.manualchecklock.release()

	def uiEucentricFromScope(self):
		self.eucentricFocusFromScope()

	def uiChangeToZero(self):
		self.manualchecklock.acquire()
		self.logger.info('Changing to zero defocus')
		try:
			newemdata = data.ScopeEMData()
			newemdata['defocus'] = 0.0
			self.emclient.setScope(newemdata)
		finally:
			self.manualchecklock.release()

	def changeFocus(self, direction):
		delta = self.increment
		self.manualchecklock.acquire()
		self.logger.info('Changing %s %s %s' % (self.parameter, direction, delta))
		try:
			scope = self.emclient.getScope()
			if self.parameter == 'Stage Z':
				value = scope['stage position']['z']
			elif self.parameter == 'Defocus':
				value = scope['defocus']
			if direction == 'up':
				value += delta
			elif direction == 'down':
				value -= delta
			
			newemdata = data.ScopeEMData()
			if self.parameter == 'Stage Z':
				newemdata['stage position'] = {'z':value}
			elif self.parameter == 'Defocus':
				newemdata['defocus'] = value
			self.emclient.setScope(newemdata)
		finally:
			self.manualchecklock.release()


		self.logger.info('Changed %s %s %s' % (self.parameter, direction, delta,))

	def manualDone(self):
		self.logger.info('Will quit manual focus loop after this iteration...')
		self.manual_check_done.set()

	def manualPause(self):
		self.logger.info('Will pause manual focus loop after this iteration...')
		self.manual_pause.set()

	def manualContinue(self):
		self.logger.info('Continuing manual focus')
		self.manual_continue.set()

	def correctStig(self, deltax, deltay):
		stig = self.emclient.getScope()['stigmator']
		stig['objective']['x'] += deltax
		stig['objective']['y'] += deltay
		emdata = data.ScopeEMData(stigmator=stig)
		self.logger.info('Correcting stig by %s, %s' % (deltax, deltay))
		self.emclient.setScope(emdata)

	def correctDefocus(self, delta):
		defocus = self.emclient.getScope()['defocus']
		self.logger.info('Defocus before applying correction %s' % defocus)
		defocus += delta
		emdata = data.ScopeEMData(defocus=defocus)
		emdata['reset defocus'] = 1
		self.logger.info('Correcting defocus by %s' % (delta,))
		self.emclient.setScope(emdata)

	def correctZ(self, delta):
		if not self.eucset:
			self.logger.warning('Eucentric focus was not set before measuring defocus because "Stage Z" was not selected then, but is now.  Changing Z now is a bad idea, so I will skip it.')
			return
		stage = self.emclient.getScope()['stage position']
		alpha = stage['a']
		deltaz = delta * Numeric.cos(alpha)
		newz = stage['z'] + deltaz
		newstage = {'stage position': {'z': newz }}
		newstage['reset defocus'] = 1
		emdata = data.ScopeEMData(initializer=newstage)
		self.logger.info('Correcting stage Z by %s (defocus change %s at alpha %s)' % (deltaz,delta,alpha))
		self.emclient.setScope(emdata)
		### this is to notify DriftManager that it is responsible
		### for updating the X,Y side effect of changing Z
		if self.settings['drift on z']:
			self.logger.info('Declaring drift after correcting stage Z')
			self.declareDrift()

	def correctNone(self, delta):
		self.logger.info('Not applying defocus correction')

	def uiTest(self):
		self.acquire(None)

	def uiAbortFailure(self):
		self.btcalclient.abortevent.set()

