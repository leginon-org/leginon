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
	eventinputs = acquisition.Acquisition.eventinputs+[event.DriftDoneEvent]
	eventoutputs = acquisition.Acquisition.eventoutputs+[event.DriftDetectedEvent]
	def __init__(self, id, sesison, nodelocations, **kwargs):
		self.focus_methods = {
			'None': self.correctNone,
			'Stage Z': self.correctZ,
			'Defocus': self.correctDefocus
		}

		self.cam = camerafuncs.CameraFuncs(self)

		self.manualchecklock = threading.Lock()

		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.abortfail = threading.Event()
		self.manual_check_done = threading.Event()
		acquisition.Acquisition.__init__(self, id, sesison, nodelocations, target_type='focus', **kwargs)

	def acquire(self, presetdata, target=None, emtarget=None):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we do autofocus
		'''
		info = {'target':target}
		self.abortfail.clear()
		btilt = self.btilt.get()
		pub = self.publishimages.get()

		## Need to melt only once per target, event though
		## this method may be called multiple times on the same
		## target.
		## To be sure, we flag a target as having been melted.
		## This is only safe if we can be sure that we don't
		## use different copies of the same target each time.
		melt_time = self.melt.get()
		if melt_time and not target['pre_exposure']:
			melt_time_ms = int(round(melt_time * 1000))
			camstate = self.cam.currentCameraEMData()
			current_exptime = camstate['exposure time']
			camstate['exposure time'] = melt_time_ms
			camstate = self.cam.currentCameraEMData(camstate)

			print 'Melting for %s seconds' % (melt_time,)
			self.cam.acquireCameraImageData()
			print 'Done melting, resetting exposure time'

			camstate['exposure time'] = current_exptime
			camstate = self.cam.currentCameraEMData(camstate)
			target['pre_exposure'] = True

		## pre manual check
		if self.pre_manual_check.get():
			self.manualCheckLoop(presetdata['name'], emtarget)

		if self.drifton.get():
			driftthresh = self.driftthresh.get()
		else:
			driftthresh = None

		## send the autofocus preset to the scope
		autofocuspreset = self.presetsclient.uiGetSelectedName()
		self.presetsclient.toScope(autofocuspreset, emtarget)

		try:
			correction = self.btcalclient.measureDefocusStig(btilt, pub, drift_threshold=driftthresh, image_callback=self.ui_image.set)
		except calibrationclient.Abort:
			print 'measureDefocusStig was aborted'
			return 'aborted'
		except calibrationclient.Drifting:
			self.driftDetected()
			return 'repeat'

		print 'MEASURED DEFOCUS AND STIG', correction
		defoc = correction['defocus']
		stigx = correction['stigx']
		stigy = correction['stigy']
		min = correction['min']

		info.update({'defocus':defoc, 'stigx':stigx, 'stigy':stigy, 'min':min})

		### validate defocus correction
		# possibly use min (value minimized during least square fit)
		#   mag: 50000, tilt: 0.02, defoc: 30e-6
		#     84230 was bad
		#   mag: 50000, tilt: 0.02, defoc: 25e-6
		#     5705 was bad
		#   mag: 50000, tilt: 0.02, defoc: 22e-6
		#     4928 was maybe
		#   mag: 50000, tilt: 0.02, defoc: 20e-6
		#     3135 was maybe
		#   mag: 50000, tilt: 0.02, defoc: 18e-6
		#     1955 was maybe
		#   mag: 50000, tilt: 0.02, defoc: 14e-6
		#      582 was good
		# for now, assum it is valid
		validdefocus = 1

		### validate stig correction
		# stig is only valid for large defocus
		if validdefocus and (abs(defoc) > self.stigfocthresh.get()):
			validstig = True
		else:
			validstig = False
		
		if validstig and self.stigcorrection.get():
			print 'Stig correction'
			self.correctStig(stigx, stigy)
			info['stig correction'] = 1
		else:
			info['stig correction'] = 0

		if validdefocus:
			print 'Defocus correction'
			try:
				focustype = self.focustype.getSelectedValue()
				focusmethod = self.focus_methods[focustype]
			except (IndexError, KeyError):
				print 'no method selected for correcting defocus'
			else:
				info['defocus correction'] = focustype
				focusmethod(defoc)

		## manual focus
		if self.post_manual_check.get():
			self.manualCheckLoop(presetdata['name'], emtarget)

		## aquire and save the focus image
		if self.acquirefinal.get():
			## go back to focus preset and target
			self.presetsclient.toScope(presetdata['name'], emtarget)
			delay = self.uidelay.get()
			print 'pausing for %s sec.' % (delay,)
			time.sleep(delay)

			## acquire and publish image, like superclass does
			acquisition.Acquisition.acquire(self, presetdata, target, emtarget)

		## add target to this sometime
		frd = data.FocuserResultData(initializer=info)
		self.publish(frd, database=True)

		return 'ok'

	def alreadyAcquired(self, targetdata, presetname):
		## for now, always do acquire
		return False

	def manualNow(self):
		presetnames = self.uipresetnames.getSelectedValues()
		### Warning:  not target is being used, you are exposing
		### whatever happens to be under the beam
		t = threading.Thread(target=self.manualCheckLoop, args=(presetnames[0],))
		t.setDaemon(1)
		t.start()

	def notifyManualFocus(self):
		myname = self.id[-1]
		title = 'manual focus ' + myname
		message = 'Please confirm defocus in Focuser %s' % (myname,)
		self.outputMessage(title, message)

	def manualCheckLoop(self, presetname, emtarget=None):
		## go to preset and target
		self.presetsclient.toScope(presetname, emtarget)
		delay = self.uidelay.get()
		print 'pausing for %s sec.' % (delay,)
		time.sleep(delay)
		self.manual_check_done.clear()
		print 'starting manual focus loop'
		self.notifyManualFocus()
		while 1:
			if self.manual_check_done.isSet():
				break
			# acquire image, show image and power spectrum
			# allow user to adjust defocus and stig
			cor = self.uicorrectimage.get()
			self.manualchecklock.acquire()
			try:
				imagedata = self.cam.acquireCameraImageData(correction=cor)
			finally:
				self.manualchecklock.release()
			imarray = imagedata['image']
			pow = imagefun.power(imarray)
			self.man_image.set(imarray)
			self.man_power.set(pow)
		print 'manual focus loop done'

	def uiFocusUp(self):
		self.changeFocus('up')

	def uiFocusDown(self):
		self.changeFocus('down')

	def uiResetDefocus(self):
		self.manualchecklock.acquire()
		print 'reset defocus'
		try:
			newemdata = data.ScopeEMData(id=('scope',))
			newemdata['reset defocus'] = True
			self.publishRemote(newemdata)
		finally:
			self.manualchecklock.release()

	def uiChangeToZero(self):
		self.manualchecklock.acquire()
		print 'changing to zero defocus'
		try:
			newemdata = data.ScopeEMData(id=('scope',))
			newemdata['defocus'] = 0.0
			self.publishRemote(newemdata)
		finally:
			self.manualchecklock.release()

	def changeFocus(self, direction):
		parameter = self.manual_parameter.getSelectedValue()
		delta = self.manual_delta.get()
		self.manualchecklock.acquire()
		print 'changing %s %s %s' % (parameter, direction, delta)
		try:
			if parameter == 'Stage Z':
				emdata = self.researchByDataID(('stage position',))
				value = emdata['stage position']['z']
			elif parameter == 'Defocus':
				emdata = self.researchByDataID(('defocus',))
				value = emdata['defocus']
			if direction == 'up':
				value += delta
			elif direction == 'down':
				value -= delta
			
			newemdata = data.ScopeEMData(id=('scope',))
			if parameter == 'Stage Z':
				newemdata['stage position'] = {'z':value}
			elif parameter == 'Defocus':
				newemdata['defocus'] = value
			self.publishRemote(newemdata)
		finally:
			self.manualchecklock.release()


		print 'changed %s %s %s' % (parameter, direction, delta,)

	def manualDone(self):
		print 'will quit manual focus loop after this iteration'
		self.manual_check_done.set()

	def correctStig(self, deltax, deltay):
		stig = self.researchByDataID(('stigmator',))
		stig['stigmator']['objective']['x'] += deltax
		stig['stigmator']['objective']['y'] += deltay
		emdata = data.ScopeEMData(id=('scope',), initializer=stig)
		print 'correcting stig by %s,%s' % (deltax,deltay)
		self.publishRemote(emdata)

	def correctDefocus(self, delta):
		defocus = self.researchByDataID(('defocus',))
		defocus['defocus'] += delta
		defocus['reset defocus'] = 1
		emdata = data.ScopeEMData(id=('scope',), initializer=defocus)
		print 'correcting defocus by %s' % (delta,)
		self.publishRemote(emdata)

	def correctZ(self, delta):
		stage = self.researchByDataID(('stage position',))
		newz = stage['stage position']['z'] + delta
		newstage = {'stage position': {'z': newz }}
		newstage['reset defocus'] = 1
		emdata = data.ScopeEMData(id=('scope',), initializer=newstage)
		print 'correcting stage Z by %s' % (delta,)
		self.publishRemote(emdata)

	def correctNone(self, delta):
		print 'not applying defocus correction'

	def uiTest(self):
		self.acquire(None)

	def uiAbortFailure(self):
		self.btcalclient.abortevent.set()

	def defineUserInterface(self):
		acquisition.Acquisition.defineUserInterface(self)

		self.melt = uidata.Float('Melt Time (s)', 0.0, 'rw', persist=True)

		## auto focus
		autocont = uidata.Container('Auto Focus')

		self.drifton = uidata.Boolean('Check Drift', True, 'rw', persist=True)
		self.driftthresh = uidata.Float('Drift Threshold (pixels)', 2.0, 'rw', persist=True)

		self.btilt = uidata.Float('Beam Tilt', 0.02, 'rw', persist=True)
		self.stigfocthresh = uidata.Float('Stig Threshold', 1e-6, 'rw', persist=True)

		autofocuspreset = self.presetsclient.uiPresetSelector()
		focustypes = self.focus_methods.keys()
		focustypes.sort()
		self.focustype = uidata.SingleSelectFromList('Correction Type', focustypes, 0, persist=True)
		self.stigcorrection = uidata.Boolean('Stigmator Correction', False, 'rw', persist=True)
		self.publishimages = uidata.Boolean('Publish Tilt Images', False, 'rw', persist=True)


		autocont.addObjects((self.drifton, self.driftthresh, self.btilt, self.publishimages, autofocuspreset, self.focustype, self.stigcorrection, self.stigfocthresh))

		## manual focus check
		self.pre_manual_check = uidata.Boolean('Manual Check Before Auto', False, 'rw', persist=True)
		self.post_manual_check = uidata.Boolean('Manual Check After Auto', False, 'rw', persist=True)
		manualmeth = uidata.Method('Manual Check Now', self.manualNow)
		manualdone = uidata.Method('Done', self.manualDone)

		manualreset = uidata.Method('Reset Defocus', self.uiResetDefocus)
		manualtozero = uidata.Method('Change To Zero', self.uiChangeToZero)

		self.manual_parameter = uidata.SingleSelectFromList('Defocus or Stage Z', ['Defocus','Stage Z'], 0)
		self.manual_delta = uidata.Float('Manual Change Delta', 5e-7, 'rw', persist=True)
		manchangeup = uidata.Method('Up', self.uiFocusUp)
		manchangedown = uidata.Method('Down', self.uiFocusDown)
		self.man_image = uidata.Image('Manual Focus Image', None, 'rw')
		self.man_power = uidata.Image('Manual Focus Power Spectrum', None, 'rw')
		mancont = uidata.Container('Manual Focus')
		mancont.addObjects((self.pre_manual_check, self.post_manual_check, manualmeth, manualdone, manualreset, manualtozero, self.manual_parameter, self.manual_delta, manchangeup, manchangedown, self.man_power, self.man_image))

		self.acquirefinal = uidata.Boolean('Acquire Final Image', True, 'rw', persist=True)
		abortfailmethod = uidata.Method('Abort With Failure', self.uiAbortFailure)
		testmethod = uidata.Method('Test Autofocus (broken)', self.uiTest)
		container = uidata.LargeContainer('Focuser')
		container.addObjects((self.melt, autocont, mancont, self.acquirefinal, abortfailmethod, testmethod))
		self.uiserver.addObject(container)

