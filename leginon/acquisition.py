'''
Acquisition node is a TargetWatcher, so it receives either an ImageTargetData
or an ImageTargetListData.  The method processTargetData is called on each
ImageTargetData.
'''
import targetwatcher
import time
import data, event
import calibrationclient
import camerafuncs
import presets
import copy
import threading
import uidata

class Acquisition(targetwatcher.TargetWatcher):

	eventinputs = targetwatcher.TargetWatcher.eventinputs+[event.ImageClickEvent, event.DriftDoneEvent, event.ImageProcessDoneEvent]
	eventoutputs = targetwatcher.TargetWatcher.eventoutputs + [event.LockEvent, event.UnlockEvent, event.AcquisitionImagePublishEvent, event.TrialImagePublishEvent, event.ChangePresetEvent, event.DriftDetectedEvent]

	def __init__(self, id, session, nodelocations, target_type='acquisition', **kwargs):

		targetwatcher.TargetWatcher.__init__(self, id, session, nodelocations, target_type, **kwargs)
		self.addEventInput(event.ImageClickEvent, self.handleImageClick)
		self.addEventInput(event.DriftDoneEvent, self.handleDriftDone)
		self.addEventInput(event.ImageProcessDoneEvent, self.handleImageProcessDone)
		self.driftdone = threading.Event()
		self.cam = camerafuncs.CameraFuncs(self)

		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.presetsclient = presets.PresetsClient(self)
		self.doneevents = {}

		self.defineUserInterface()
		self.start()

	def handleDriftDone(self, ev):
		print 'HANDLING DRIFT DONE'
		self.driftdonestatus = ev['status']
		self.driftdone.set()

	def handleImageProcessDone(self, ev):
		imageid = ev['imageid']
		status = ev['status']
		if imageid in self.doneevents:
			self.doneevents[imageid]['status'] = status
			self.doneevents[imageid]['received'].set()

	def processTargetData(self, targetdata, trial=False):
		'''
		This is called by TargetWatcher.processData when targets available
		If called with targetdata=None, this simulates what occurs at
		a target (going to presets, acquiring images, etc.)
		'''
		if targetdata is None:
			emtarget = None
		else:
#			if targetdata['preset'] is None:
#				print 'preset image shift, no preset in target'
#			else:
#				print 'preset image shift', targetdata['preset']

			# this creates ScopeEMData from the ImageTargetData
			oldtargetemdata = self.targetToEMData(targetdata)
			if oldtargetemdata is None:
				return 'aborted'
			oldpreset = targetdata['preset']

			# now make EMTargetData to hold all this
			emtarget = data.EMTargetData(scope=oldtargetemdata, preset=oldpreset)

		presetnames = self.uipresetnames.getSelectedValues()

		if not presetnames:
			self.outputWarning('No presets specified for target acquisition')

		for newpresetname in presetnames:
			self.presetsclient.toScope(newpresetname, emtarget)
			print 'getting current preset'
			p = self.presetsclient.getCurrentPreset()
			print 'current preset', p['name']
			delay = self.uidelay.get()
			print 'pausing for %s sec.' % (delay,)
			time.sleep(delay)
			print 'acquire()'
			ret = self.acquire(p, target=targetdata, trial=trial, emtarget=emtarget)
			# in these cases, return immediately
			if ret in ('aborted', 'repeat'):
				return ret
			print 'done'

		return 'ok'

	def targetToEMData(self, targetdata):
		'''
		convert an ImageTargetData to an EMData object
		using chosen move type.
		The result is a valid scope state that will center
		the target on the camera, but not necessarily at the
		desired preset.  It is shifted from the preset of the 
		original targetdata.

		Certain fields are reset to None becuase they are not
		necessary, and cause problems if used between different
		magnification modes (LM, M, SA).
		'''
		# get relavent info from target data
		targetdeltarow = targetdata['delta row']
		targetdeltacolumn = targetdata['delta column']
		## make new copy because will be modified
		targetscope = data.ScopeEMData(targetdata['scope'])
		## camera is just read, not modified
		targetcamera = targetdata['camera']

		## ignore these fields:
		ignore = ('beam tilt', 'stigmator', 'holder type', 'holder status', 'stage status', 'vacuum status', 'column valves', 'turbo pump')
		for key in ignore:
			targetscope[key] = None

		## to shift targeted point to center...
		deltarow = -targetdeltarow
		deltacol = -targetdeltacolumn

		pixelshift = {'row':deltarow, 'col':deltacol}

		## figure out scope state that gets to the target
		movetype = self.uimovetype.getSelectedValue()
		calclient = self.calclients[movetype]
		try:
			newscope = calclient.transform(pixelshift, targetscope, targetcamera)
		except calibrationclient.NoMatrixCalibrationError:
			self.outputWarning('No calibration for acquisition move to target')
			return None
		# create new EMData object to hole this
		emdata = data.ScopeEMData(id=('scope',), initializer=newscope)
		return emdata

	def acquire(self, presetdata, target=None, trial=False, emtarget=None):
		cor = self.uicorrectimage.get()

		### corrected or not??
		imagedata = self.cam.acquireCameraImageData(correction=cor)

		if imagedata is None:
			return 'fail'

		imarray = imagedata['image']

		labelstring = self.labelstring.get()

		## attach preset to imagedata and create PresetImageData
		## use same id as original imagedata
		dataid = self.ID()

		if trial:
			trialimage = data.TrialImageData(id=dataid, initializer=imagedata, preset=presetdata, label=labelstring)
			print 'publishing trial image'
			self.publish(trialimage, pubevent=True, database=False)
			print 'image published'
			if self.displayimageflag.get():
				print 'displaying image'
				self.ui_image.set(imarray)
		else:
			pimagedata = data.AcquisitionImageData(id=dataid, initializer=imagedata, preset=presetdata, label=labelstring, target=target)

			## set up to handle done events
			self.doneevents[dataid] = {}
			self.doneevents[dataid]['received'] = threading.Event()
			self.doneevents[dataid]['status'] = 'waiting'

			self.publish(pimagedata, pubevent=True, database=self.databaseflag.get())
			print 'image published'
			if self.displayimageflag.get():
				print 'displaying image'
				self.ui_image.set(imarray)

			if self.waitfordone.get():
				self.waitForImageProcessDone()

#			print 'PIMAGEDATA'
#			print '   scope image shift', pimagedata['scope']['image shift']
#			print '   preset image shift', pimagedata['preset']['image shift']


		return 'ok'

	def waitForImageProcessDone(self):
		imageids = self.doneevents.keys()
		imageidstrs = map(str, imageids)
		self.waitingforimages.setList(imageidstrs)
		# wait for image processing nodes to complete
		for id, eventinfo in self.doneevents.items():
			print '%s WAITING for %s' % (self.id, id,)
			eventinfo['received'].wait()
			idstr = str(id)
			imageidstrs.remove(idstr)
			self.waitingforimages.setList(imageidstrs)
			print '%s DONE WAITING for %s' % (self.id, id,)
		self.doneevents.clear()
		print '%s DONE WAITING' % (self.id,)

	def stopWaitingForImage(self):
		imageidstr = self.waitingforimages.getSelectedValue()
		try:
			imageid = eval(imageidstr)
		except TypeError:
			return
		if imageid in self.doneevents:
			self.doneevents[imageid]['received'].set()
			self.doneevents[imageid]['status'] = 'forced'

	def handleImageClick(self, clickevent):
		'''
		for interaction with and image viewer during preset config
		'''
		print 'handling image click'
		clickinfo = copy.deepcopy(clickevent)
		## get relavent info from click event
		clickrow = clickinfo['array row']
		clickcol = clickinfo['array column']
		clickshape = clickinfo['array shape']
		clickscope = clickinfo['scope']
		clickcamera = clickinfo['camera']

		## calculate delta from image center
		deltarow = clickrow - clickshape[0] / 2
		deltacol = clickcol - clickshape[1] / 2

		## to shift clicked point to center...
		deltarow = -deltarow
		deltacol = -deltacol

		pixelshift = {'row':deltarow, 'col':deltacol}
		mag = clickscope['magnification']

		## figure out shift
		calclient = self.calclients['image shift']
		newstate = calclient.transform(pixelshift, clickscope, clickcamera)
		emdat = data.ScopeEMData(('scope',), initializer=newstate)
		self.outputEvent(event.LockEvent(self.ID()))
		self.publishRemote(emdat)

		# wait for a while
		time.sleep(2)

		## acquire image
		self.acquire(presetdata=None, target=None, trial=True)
		self.outputEvent(event.UnlockEvent(self.ID()))
		self.confirmEvent(clickevent)

	def uiToScope(self):
		presetname = self.presetsclient.uiGetSelectedName()
		print 'Going to preset %s' % (presetname,)
		self.presetsclient.toScope(presetname)
		print 'done'

	def uiToScopeAcquire(self):
		presetname = self.presetsclient.uiGetSelectedName()
		## acquire a trial image
		print 'Going to preset', presetname
		self.presetsclient.toScope(presetname)
		print 'Got to preset, getting current preset'
		p = self.presetsclient.getCurrentPreset()
		print 'CURRENT', p
		## trial image
		print 'Acquiring image'
		self.acquire(p, target=None, trial=True)
		print 'Acquired'

	def uiTrial(self):
		self.processTargetData(targetdata=None, trial=True)

	def getPresetNames(self):
		presetnames = []
		for preset in self.presetsclient.getPresets():
			presetnames.append(preset['name'])
		return presetnames

	def setDisplayImage(self, value):
		if not value:
			self.ui_image.set(None)
		return value

	def uiRefreshPresetNames(self):
		self.uipresetnames.setSelected([])
		self.uipresetnames.setList(self.getPresetNames())

	def driftDetected(self):
		'''
		notify DriftManager of drifting
		'''
		allemdata = self.researchByDataID(('all em',))
		print 'PASSING BEAM TILT', allemdata['beam tilt']
		allemdata['id'] = self.ID()
		self.driftdone.clear()
		self.publish(allemdata, pubevent=True, pubeventclass=event.DriftDetectedEvent)
		print '%s waiting for DriftManager' % (self.id,)
		self.driftdone.wait()

	def defineUserInterface(self):
		targetwatcher.TargetWatcher.defineUserInterface(self)

		self.ui_image = uidata.Image('Image', None, 'rw')

		self.displayimageflag = uidata.Boolean('Display Image', True, 'rw',
																						persist=True)
		uicontainer = uidata.Container('User Interface')
		uicontainer.addObjects((self.displayimageflag,))

		presetnames = self.getPresetNames()
		self.uipresetnames = uidata.SelectFromList('Sequence', presetnames, [], 'r')
		refreshpresetnames = uidata.Method('Refresh', self.uiRefreshPresetNames)
		presetscontainer = uidata.Container('Presets Sequence')
		presetscontainer.addObjects((self.uipresetnames, refreshpresetnames))

		self.uimovetype = uidata.SingleSelectFromList('Move Type',
																									self.calclients.keys(),
																									0, persist=True)
		self.uidelay = uidata.Float('Delay (sec)', 2.5, 'rw', persist=True)
		self.uicorrectimage = uidata.Boolean('Correct image', True, 'rw',
																			persist=True)

		self.waitfordone = uidata.Boolean('Wait for "Done"', True, 'rw',
																				persist=True)

		acquirecontainer = uidata.Container('Acquisition')
		acquirecontainer.addObjects((self.uicorrectimage, self.uimovetype,
																	self.uidelay, self.waitfordone))

		self.databaseflag = uidata.Boolean('Publish to Database', True, 'rw')
		self.labelstring = uidata.String('Label', self.id[-1], 'rw', persist=True)

		databasecontainer = uidata.Container('Database')
		databasecontainer.addObjects((self.databaseflag, self.labelstring))

		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((uicontainer, presetscontainer,
																	acquirecontainer, databasecontainer))

		#statuscontainer = uidata.Container('Status')

		trialmethod = uidata.Method('Trial Image', self.uiTrial)
		self.waitingforimages = uidata.SingleSelectFromList('Waiting For', [], 0)
		stopwaiting = uidata.Method('Stop Waiting', self.stopWaitingForImage)

		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((self.waitingforimages, stopwaiting,
																	trialmethod))

		container = uidata.LargeContainer('Acquisition')
		container.addObjects((self.ui_image, settingscontainer, controlcontainer))

		self.uiserver.addObject(container)

