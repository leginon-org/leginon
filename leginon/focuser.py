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

class Focuser(acquisition.Acquisition):
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
		btilt = self.btilt.get()
		pub = False
		if self.drifton.get():
			driftthresh = self.driftthresh.get()
		else:
			driftthresh = None

		## send the autofocus preset to the scope
		autofocuspreset = presettarget['preset']
		self.presetsclient.toScope(autofocuspreset, presettarget['emtarget'])

		## set to eucentric focus if doing Z correction
		## WARNING:  this assumes that user will not change
		## to another focus type before doing the correction
		focustype = self.focustype.getSelectedValue()
		if focustype == 'Stage Z':
			self.logger.info('setting eucentric focus')
			self.eucentricFocusToScope()
			self.eucset = True
		else:
			self.eucset = False

		delay = self.uidelay.get()
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
			correction = self.btcalclient.measureDefocusStig(btilt, pub, drift_threshold=driftthresh, image_callback=self.ui_image.set)
		except calibrationclient.Abort:
			self.logger.info('measureDefocusStig was aborted')
			return 'aborted'
		except calibrationclient.Drifting:
			self.driftDetected(presettarget)
			return 'repeat'

		self.logger.info('Measured defocus and stig %s' % correction)
		defoc = correction['defocus']
		stigx = correction['stigx']
		stigy = correction['stigy']
		fitmin = correction['min']

		resultdata.update({'defocus':defoc, 'stigx':stigx, 'stigy':stigy, 'min':fitmin})

		status = 'ok'

		### validate defocus correction
		fitlimit = self.fitlimit.get()
		if fitmin <= fitlimit:
			validdefocus = True
			self.logger.info('Good focus measurement')
		else:
			status = 'untrusted (%s>%s)' % (fitmin, fitlimit)
			validdefocus = False
			self.logger.info('Focus measurement failed: fitmin = %s (limit = %s)' % (fitmin, fitlimit))

		### validate stig correction
		# stig is only valid in a certain defocus range
		if validdefocus and (self.stigfocminthresh.get() < abs(defoc) < self.stigfocmaxthresh.get()):
			validstig = True
		else:
			validstig = False

		if validstig and self.stigcorrection.get():
			self.logger.info('Stig correction...')
			self.correctStig(stigx, stigy)
			resultdata['stig correction'] = 1
		else:
			resultdata['stig correction'] = 0

		if validdefocus:
			self.logger.info('Defocus correction...')
			try:
				focustype = self.focustype.getSelectedValue()
				focusmethod = self.focus_methods[focustype]
			except (IndexError, KeyError):
				self.logger.warning('No method selected for correcting defocus')
			else:
				resultdata['defocus correction'] = focustype
				focusmethod(defoc)

		return status

	def acquire(self, presetdata, target=None, presettarget=None):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we do autofocus
		'''
		self.abortfail.clear()
		resultdata = data.FocuserResultData()
		resultdata['target'] = target

		## Need to melt only once per target, event though
		## this method may be called multiple times on the same
		## target.
		## To be sure, we flag a target as having been melted.
		## This is only safe if we can be sure that we don't
		## use different copies of the same target each time.
		melt_time = self.melt.get()
		if melt_time and not target['pre_exposure']:
			melt_time_ms = int(round(melt_time * 1000))
			camstate = self.cam.getCameraEMData()
			current_exptime = camstate['exposure time']
			camstate['exposure time'] = melt_time_ms
			self.cam.setCameraEMData(camstate)

			self.logger.info('Melting for %s seconds' % (melt_time,))
			self.cam.acquireCameraImageData()
			self.logger.info('Done melting, resetting exposure time')

			camstate['exposure time'] = current_exptime
			self.cam.setCameraEMData(camstate)
			# is this any good?
			#target['pre_exposure'] = True

		## pre manual check
		if self.pre_manual_check.get():
			self.manualCheckLoop(presettarget)
			resultdata['pre manual check'] = True
		else:
			resultdata['pre manual check'] = False

		## autofocus
		if self.auto_on.get():
			autofocuspreset = self.autofocuspreset.get()
			autopresettarget = data.PresetTargetData(emtarget=presettarget['emtarget'], preset=autofocuspreset)
			status = self.autoFocus(resultdata, autopresettarget)
			resultdata['auto status'] = status
			if status != 'ok':
				self.publish(resultdata, database=True, dbforce=True)
				return status
		else:
			resultdata['auto status'] = 'skipped'

		## post manual check
		if self.post_manual_check.get():
			self.manualCheckLoop(presettarget)
			resultdata['post manual check'] = True
		else:
			resultdata['post manual check'] = False

		## aquire and save the focus image
		if self.acquirefinal.get():
			## go back to focus preset and target
			self.presetsclient.toScope(presetdata['name'], presettarget['emtarget'])
			delay = self.uidelay.get()
			self.logger.info('Pausing for %s seconds' % (delay,))
			time.sleep(delay)

			## acquire and publish image, like superclass does
			acquisition.Acquisition.acquire(self, presetdata, target, presettarget)

		## publish results
		self.publish(resultdata, database=True, dbforce=True)

		return 'ok'

	def alreadyAcquired(self, targetdata, presettarget):
		## for now, always do acquire
		return False

	def manualNow(self):
		presetnames = self.uipresetnames.get()
		try:
			presetname = presetnames[0]
		except IndexError:
			message = 'no presets specified for manual focus'
			self.messagelog.error(message)
			self.logger.error(message)
			return
		self.logger.info('using preset %s for manual check' % (presetname,))
		### Warning:  no target is being used, you are exposing
		### whatever happens to be under the beam
		t = threading.Thread(target=self.manualCheckLoop, args=())
		t.setDaemon(1)
		t.start()

	def manualCheckLoop(self, presettarget=None):
		## go to preset and target
		if presettarget is not None:
			self.presetsclient.toScope(presettarget['preset'], presettarget['emtarget'])
			delay = self.uidelay.get()
			self.logger.info('Pausing for %s seconds' % (delay,))
			time.sleep(delay)
		self.manual_check_done.clear()
		self.logger.info('Starting manual focus loop...')
		message = self.messagelog.information('Please confirm defocus')
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
			cor = self.uicorrectimage.get()
			self.logger.info('Correct image %s' % cor)
			self.manualchecklock.acquire()
			try:
				imagedata = self.cam.acquireCameraImageData(correction=cor, temp=True)
			finally:
				self.manualchecklock.release()
			imarray = imagedata['image']
			maskrad = self.maskrad.get()
			pow = imagefun.power(imarray, maskrad)
			self.man_power.set(pow)
			self.man_image.set(imarray)
		try:
			message.clear()
		except:
			pass
		self.logger.info('Manual focus loop done')

	def waitForContinue(self):
		self.logger.info('Manual focus paused')
		message = self.messagelog.information('manual focus is paused')
		self.manual_continue.wait()
		self.manual_continue.clear()
		self.manual_pause.clear()
		message.clear()

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
		parameter = self.manual_parameter.getSelectedValue()
		delta = self.manual_delta.get()
		self.manualchecklock.acquire()
		self.logger.info('Changing %s %s %s' % (parameter, direction, delta))
		try:
			scope = self.emclient.getScope()
			if parameter == 'Stage Z':
				value = scope['stage position']['z']
			elif parameter == 'Defocus':
				value = scope['defocus']
			if direction == 'up':
				value += delta
			elif direction == 'down':
				value -= delta
			
			newemdata = data.ScopeEMData()
			if parameter == 'Stage Z':
				newemdata['stage position'] = {'z':value}
			elif parameter == 'Defocus':
				newemdata['defocus'] = value
			self.emclient.setScope(newemdata)
		finally:
			self.manualchecklock.release()


		self.logger.info('Changed %s %s %s' % (parameter, direction, delta,))

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
		newz = stage['z'] + delta
		newstage = {'stage position': {'z': newz }}
		newstage['reset defocus'] = 1
		emdata = data.ScopeEMData(initializer=newstage)
		self.logger.info('Correcting stage Z by %s' % (delta,))
		self.emclient.setScope(emdata)
		### reset zero at eucentric focus for other preset
		linkedpreset = self.linkedpreset.get()
		if not linkedpreset:
			return
		self.logger.info('going to linked preset: %s' % (linkedpreset,))
		self.presetsclient.toScope(linkedpreset)
		self.logger.info('going to eucentric focus and reseting zero defocus')
		self.eucentricFocusToScope()
		self.resetDefocus()

	def correctNone(self, delta):
		self.logger.info('Not applying defocus correction')

	def uiTest(self):
		self.acquire(None)

	def uiAbortFailure(self):
		self.btcalclient.abortevent.set()

	def defineUserInterface(self):
		acquisition.Acquisition.defineUserInterface(self)
		self.messagelog = uidata.MessageLog('Messages')
		self.melt = uidata.Float('Melt Time (s)', 0.0, 'rw', persist=True)

		## auto focus
		autocont = uidata.Container('Auto Focus')
		self.auto_on = uidata.Boolean('Auto Focus On', True, 'rw', persist=True)

		self.drifton = uidata.Boolean('Check Drift', True, 'rw', persist=True)
		self.driftthresh = uidata.Float('Threshold (pixels)', 2.0, 'rw', persist=True)

		self.btilt = uidata.Float('Beam Tilt', 0.02, 'rw', persist=True)
		#self.publishimages = uidata.Boolean('Publish Tilt Images', False, 'rw', persist=True)

		self.autofocuspreset = self.presetsclient.uiSinglePresetSelector('Auto Focus Preset', '', 'rw', persist=True)
		self.linkedpreset = self.presetsclient.uiSinglePresetSelector('Linked Preset', '', 'rw', persist=True)
		self.fitlimit = uidata.Float('Fit Limit', 1000, 'rw', persist=True)
		focustypes = self.focus_methods.keys()
		focustypes.sort()
		self.focustype = uidata.SingleSelectFromList('Correction Type', focustypes, 0, persist=True)

		# stig
		self.stigcorrection = uidata.Boolean('Stig Correction', False, 'rw', persist=True)
		self.stigfocminthresh = uidata.Float('Stig Defocus Min', 1e-6, 'rw', persist=True)
		self.stigfocmaxthresh = uidata.Float('Stig Defocus Max', 4e-6, 'rw', persist=True)

		autocont.addObject(self.auto_on, position={'position':(0,0)})
		autocont.addObject(self.btilt, position={'position':(0,1)})
		autocont.addObject(self.drifton, position={'position':(1,0)})
		autocont.addObject(self.driftthresh, position={'position':(1,1)})

		autocont.addObject(self.autofocuspreset, position={'position':(3,0), 'span':(1,2)})
		autocont.addObject(self.linkedpreset, position={'position':(3,2), 'span':(1,2)})

		autocont.addObject(self.fitlimit, position={'position':(4,0)})
		autocont.addObject(self.focustype, position={'position':(4,1)})

		autocont.addObject(self.stigcorrection, position={'position':(5,0)})
		autocont.addObject(self.stigfocminthresh, position={'position':(5,1)})
		autocont.addObject(self.stigfocmaxthresh, position={'position':(5,2)})

		## manual focus check
		self.pre_manual_check = uidata.Boolean('Before Auto', False, 'rw', persist=True)
		self.post_manual_check = uidata.Boolean('After Auto', False, 'rw', persist=True)
		manualmeth = uidata.Method('Manual Check Now', self.manualNow)
		manualpause = uidata.Method('Pause', self.manualPause)
		manualcontinue = uidata.Method('Continue', self.manualContinue)
		manualdone = uidata.Method('Done', self.manualDone)

		manualreset = uidata.Method('Reset Defocus', self.uiResetDefocus)
		euctoscope = uidata.Method('Eucentric Focus To Scope', self.uiChangeToEucentric)
		eucfromscope = uidata.Method('Eucentric Focus From Scope', self.uiEucentricFromScope)
		manualtozero = uidata.Method('Change To Zero', self.uiChangeToZero)

		self.manual_parameter = uidata.SingleSelectFromList('Defocus or Stage Z', ['Defocus','Stage Z'], 0)
		self.manual_delta = uidata.Float('Manual Change Delta', 5e-7, 'rw', persist=True)
		manchangeup = uidata.Method('Up', self.uiFocusUp)
		manchangedown = uidata.Method('Down', self.uiFocusDown)
		self.man_image = uidata.Image('Manual Focus Image', None, 'rw')
		self.maskrad = uidata.Float('Mask Radius (% of image width)', 0.01, 'rw', persist=True)
		self.man_power = uidata.Image('Manual Focus Power Spectrum', None, 'rw')
		mancont = uidata.Container('Manual Focus')

		# row 0
		mancont.addObject(manualmeth, position={'position':(0,0)})
		mancont.addObject(self.pre_manual_check, position={'position':(0,1)})
		mancont.addObject(self.post_manual_check, position={'position':(0,2)})
		# row 1
		mancont.addObject(manualpause, position={'position':(1,0)})
		mancont.addObject(manualcontinue, position={'position':(1,1)})
		mancont.addObject(manualdone, position={'position':(1,2)})
		# row 2
		mancont.addObject(eucfromscope, position={'position':(2,0)})
		mancont.addObject(euctoscope, position={'position':(2,1)})
		mancont.addObject(manualreset, position={'position':(2,2)})
		# row 3
		mancont.addObject(self.manual_parameter, position={'position':(3,0), 'span':(1,3)})
		# row 4
		mancont.addObject(self.manual_delta, position={'position':(4,0), 'span':(1,3)})
		# row5
		mancont.addObject(manchangeup, position={'position':(5,0)})
		mancont.addObject(manchangedown, position={'position':(5,1)})
		mancont.addObject(manualtozero, position={'position':(5,2)})
		# row6
		mancont.addObject(self.maskrad, position={'position':(6,0), 'span':(1,3)})
		# row 7
		mancont.addObject(self.man_power, position={'position':(7,0), 'span':(1,3)})
		# row8
		mancont.addObject(self.man_image, position={'position':(8,0), 'span':(1,3)})

		#### other
		self.acquirefinal = uidata.Boolean('Acquire Final Image', True, 'rw', persist=True)
		abortfailmethod = uidata.Method('Abort With Failure', self.uiAbortFailure)
		testmethod = uidata.Method('Test Autofocus (broken)', self.uiTest)
		container = uidata.LargeContainer('Focuser')
		container.addObject(self.messagelog, position={'expand': 'all'})
		container.addObjects((self.melt, autocont, mancont, self.acquirefinal, abortfailmethod, testmethod))
		self.uicontainer.addObject(container)

