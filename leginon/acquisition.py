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

	eventinputs = targetwatcher.TargetWatcher.eventinputs+[event.ImageClickEvent]
	eventoutputs = targetwatcher.TargetWatcher.eventoutputs + [event.LockEvent, event.UnlockEvent, event.AcquisitionImagePublishEvent, event.TrialImagePublishEvent, event.ChangePresetEvent]

	def __init__(self, id, session, nodelocations, targetclass=data.ImageTargetData, **kwargs):
		targetwatcher.TargetWatcher.__init__(self, id, session, nodelocations, targetclass, **kwargs)
		self.addEventInput(event.ImageClickEvent, self.handleImageClick)
		self.addEventOutput(event.LockEvent)
		self.addEventOutput(event.UnlockEvent)
		self.cam = camerafuncs.CameraFuncs(self)

		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.presetsclient = presets.PresetsClient(self)

		self.defineUserInterface()
		self.start()

	def processTargetData(self, targetdata):
		'''
		This is called by TargetWatcher.processData when targets available
		If called with targetdata=None, this simulates what occurs at
		a target (going to presets, acquiring images, etc.)
		'''
		## wait for focus target list to complete
		for tid,teventinfo in self.targetlistevents.items():
			print 'waiting for target list %s to complete' % (tid,)
			teventinfo['received'].wait()

		## check status of all done focus targets
		abort = True
		if not self.targetlistevents:
			abort = False
		for tid,teventinfo in self.targetlistevents.items():
			if teventinfo['status'] == 'success':
				abort = False

		self.targetlistevents.clear()
		
		if abort:
			print 'Aborting this target because focus failed'
			return 'failure'

		if targetdata is None:
			emtarget = None
		else:
			if targetdata['preset'] is None:
				print '   preset image shift, no preset in target'
			else:
				print '   preset image shift', targetdata['preset']

			#### this creates ScopeEMData from the ImageTargetData
			oldtargetemdata = self.targetToEMData(targetdata)
			oldpreset = targetdata['preset']
			#### now make EMTargetData to hold all this
			emtarget = data.EMTargetData(scope=oldtargetemdata,preset=oldpreset)

		### do each preset for this acquisition
#		try:
#			presetnames = self.uipresetnames.get()
#		except:
#			self.printException()
#			return

		presetnames = self.uipresetnames.getSelectedValues()

		if not presetnames:
			print 'NO PRESETS SPECIFIED'

		for newpresetname in presetnames:
			self.presetsclient.toScope(newpresetname, emtarget)
			print 'getting current preset'
			p = self.presetsclient.getCurrentPreset()
			print 'current preset'
			print p
			delay = self.uidelay.get()
			print 'pausing for %s sec.' % (delay,)
			time.sleep(delay)
			print 'acquire()'
			ret = self.acquire(p, target=targetdata)
			if ret:
				return 'failure'
			print 'done'
		return 'success'

	def targetToEMData(self, targetdata):
		'''
		convert an ImageTargetData to an EMData object
		using chosen move type.
		The result is a valid scope state that will center
		the target on the camera, but not necessarily at the
		desired preset.  It is shifted from the preset of the 
		original targetdata.
		'''
		#targetinfo = copy.deepcopy(targetdata.content)
		targetinfo = copy.deepcopy(targetdata)
		## get relavent info from target event
#		targetrow = targetinfo['array row']
#		targetcol = targetinfo['array column']
#		targetshape = targetinfo['array shape']
		targetdeltarow = targetinfo['delta row']
		targetdeltacolumn = targetinfo['delta column']
		targetscope = targetinfo['scope']
		targetcamera = targetinfo['camera']

#		## calculate delta from image center
#		deltarow = targetrow - targetshape[0] / 2
#		deltacol = targetcol - targetshape[1] / 2

		## to shift targeted point to center...
#		deltarow = -deltarow
#		deltacol = -deltacol
		deltarow = -targetdeltarow
		deltacol = -targetdeltacolumn

		pixelshift = {'row':deltarow, 'col':deltacol}

		## figure out scope state that gets to the target
		movetype = self.uimovetype.getSelectedValue()
		calclient = self.calclients[movetype]
		print 'ORIGINAL', targetscope['image shift']
		newscope = calclient.transform(pixelshift, targetscope, targetcamera)
		print 'WITH TARGET', newscope['image shift']
		## create new EMData object to hole this
		emdata = data.ScopeEMData(id=('scope',), initializer=newscope)
		return emdata

	def acquire(self, presetdata, target=None):
		acqtype = self.uiacquiretype.getSelectedValue()
		if acqtype == 'corrected':
			cor = True
		else:
			cor = False

		### corrected or not??
		imagedata = self.cam.acquireCameraImageData(correction=cor)

		if imagedata is None:
			return

		imarray = imagedata['image']

		labelstring = self.labelstring.get()

		## attach preset to imagedata and create PresetImageData
		## use same id as original imagedata
		dataid = self.ID()

		if target is None:
			trialimage = data.TrialImageData(id=dataid, initializer=imagedata, preset=presetdata, label=labelstring)
			print 'publishing trial image'
			self.publish(trialimage, pubevent=True, database=False)
		else:
			pimagedata = data.AcquisitionImageData(id=dataid, initializer=imagedata, preset=presetdata, label=labelstring, target=target)
			self.publish(pimagedata, pubevent=True, database=self.databaseflag.get())
			print 'PIMAGEDATA'
			print '   scope image shift', pimagedata['scope']['image shift']
			print '   preset image shift', pimagedata['preset']['image shift']
		print 'image published'
		print 'displaying image'
		self.ui_image.set(imarray)


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
		self.acquire(presetdata=None, target=None)
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
		self.acquire(p, target=None)
		print 'Acquired'

	def uiTrial(self):
		self.processTargetData(targetdata=None)

	def getPresetNames(self):
		presetnames = []
		for preset in self.presetsclient.getPresets():
			presetnames.append(preset['name'])
		return presetnames

	def uiRefreshPresetNames(self):
		self.uipresetnames.setSelected([])
		self.uipresetnames.setList(self.getPresetNames())

	def defineUserInterface(self):
		targetwatcher.TargetWatcher.defineUserInterface(self)
		self.uimovetype = uidata.SingleSelectFromList('Move Type',
																							self.calclients.keys(), 0)
		self.uidelay = uidata.Float('Delay (sec)', 2.5, 'rw')
		self.uiacquiretype = uidata.SingleSelectFromList('Acquisition Type',
																							['raw', 'corrected'], 0, persist=True)
		self.databaseflag = uidata.Boolean('Publish to Database', True, 'rw')
		self.labelstring = uidata.String('Label', self.id[-1], 'rw', persist=True)
		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((self.uimovetype, self.uidelay,
																		self.uiacquiretype, self.databaseflag, self.labelstring))

		presets = self.getPresetNames()
		self.uipresetnames = uidata.SelectFromList('Sequence', presets, [], 'r')
		refreshpresetnames = uidata.Method('Refresh', self.uiRefreshPresetNames)
		sequencecontainer = uidata.Container('Presets Sequence')
		sequencecontainer.addObjects((self.uipresetnames, refreshpresetnames))

		pselect = self.presetsclient.uiPresetSelector()

		toscopemethod = uidata.Method('Apply Preset', self.uiToScope)
		toscopeandacquiremethod = uidata.Method('Apply Preset and Acquire',
																							self.uiToScopeAcquire)
		presetscontainer = uidata.Container('Presets')
		presetscontainer.addObjects((sequencecontainer, pselect, toscopemethod,
																		toscopeandacquiremethod))
		trialmethod = uidata.Method('Trial', self.uiTrial)

		self.ui_image = uidata.Image('Image', None, 'rw')


		container = uidata.MediumContainer('Acquisition')
		container.addObjects((settingscontainer, presetscontainer, trialmethod, self.ui_image))

		self.uiserver.addObject(container)

