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

class Acquisition(targetwatcher.TargetWatcher):
	def __init__(self, id, session, nodelocations, **kwargs):
		targetwatcher.TargetWatcher.__init__(self, id, session, nodelocations, **kwargs)
		self.addEventInput(event.ImageClickEvent, self.handleImageClick)
		self.addEventInput(event.TargetDoneEvent, self.handleTargetDone)
		self.cam = camerafuncs.CameraFuncs(self)

		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.presetsclient = presets.PresetsClient(self)
		self.targetevents = {}

		self.defineUserInterface()
		self.start()

	def handleTargetDone(self, targetevent):
		targetid = targetevent['targetid']
		print 'got targetdone event, setting threading event', targetid
		if targetid in self.targetevents:
			self.targetevents[targetid].set()

	def focus(self, focustargetdata):
		targetid = focustargetdata['id']
		## maybe should check if already waiting on this target?
		self.targetevents[targetid] = threading.Event()
		print 'publishing focustargetdata', targetid
		newtargetlist = data.ImageTargetListData(self.ID(), targets=[focustargetdata,])
		self.publish(newtargetlist, eventclass=event.ImageTargetListPublishEvent)
		## maybe should have timeout?
		print 'waiting for focus to complete'
		self.targetevents[targetid].wait()

	def processTargetData(self, targetdata):
		'''
		This is called by TargetWatcher.processData when targets available
		If called with targetdata=None, this simulates what occurs at
		a target (going to presets, acquiring images, etc.)
		'''
		### should make both target data and preset an option

		## pass focus targets to another node
		if isinstance(targetdata, data.FocusTargetData):
			print 'FFFFFFF this is a focus target'
			self.focus(targetdata)
			return

		if targetdata is None:
			newtargetemdata = None
		else:
			print 'TARGETDATA'
			print '   row,col', targetdata['array row'], targetdata['array column']
			print '   scope image shift', targetdata['scope']['image shift']
			print '   preset image shift', targetdata['preset']['image shift']

			oldtargetemdata = self.targetToEMData(targetdata)
			oldpreset = targetdata['preset']
			print 'OLDPRESET'
			print '   magnification', oldpreset['magnification']
			print '   image shift', oldpreset['image shift']
			if oldpreset is None:
				# I don't know if this works, but if there is no preset, don't remove
				newtargetemdata = oldtargetemdata
			else:
				newtargetemdata = self.removePreset(oldtargetemdata, oldpreset)

		if newtargetemdata is not None:
			print 'type', type(newtargetemdata)
			print 'NEWTARGETEMDATA'
			print '   magnification', newtargetemdata['em']['magnification']
			print '   image shift', newtargetemdata['em']['image shift']

		### do each preset for this acquisition
		presetnames = self.presetnames.get()
		if not presetnames:
			print 'NO PRESETS SPECIFIED'
		for presetname in presetnames:
			self.acquireTargetAtPreset(presetname, newtargetemdata, trial=False)

	def acquireTargetAtPreset(self, presetname, targetemdata=None, trial=False):
			presetlist = self.presetsclient.retrievePresets(presetname)
			presetdata = presetlist[0]
			### simulated target is easy, real target requires
			### merge with preset
			print 'PRESETDATA'
			print '   magnification', presetdata['magnification']
			print '   image shift', presetdata['image shift']
			if targetemdata is None:
				ptargetemdata = self.presetDataToEMData(presetdata)
			else:
				## make newtargetemdata with preset applied
				ptargetemdata = self.addPreset(targetemdata, presetdata)
				print 'PTARGETEMDATA'
				print '   magnification', ptargetemdata['em']['magnification']
				print '   image shift', ptargetemdata['em']['image shift']

			## set the scope/camera state
			self.publishRemote(ptargetemdata)

			print 'sleeping 2 sec'
			time.sleep(2)

#			print 'acquire'
			self.acquire(presetdata, trial)

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
		targetrow = targetinfo['array row']
		targetcol = targetinfo['array column']
		targetshape = targetinfo['array shape']
		targetscope = targetinfo['scope']
		targetcamera = targetinfo['camera']

		## calculate delta from image center
		deltarow = targetrow - targetshape[0] / 2
		deltacol = targetcol - targetshape[1] / 2

		## to shift targeted point to center...
		deltarow = -deltarow
		deltacol = -deltacol

		pixelshift = {'row':deltarow, 'col':deltacol}

		## figure out scope state that gets to the target
		movetype = self.movetype.get()
		calclient = self.calclients[movetype]
		print 'ORIGINAL', targetscope['image shift']
		newscope = calclient.transform(pixelshift, targetscope, targetcamera)
		print 'WITH TARGET', newscope['image shift']
		## create new EMData object to hole this
		emdata = data.EMData(('scope',), em=newscope)
		return emdata

	def removePreset(self, emdata, presetdata):
		# subtract the effects of a preset on an EMData object
		# Right now all this means is subtract image shift
		# It is assumed that other parameters of the preset
		# like magnification will be updated later.

		# make new EMData object
		print 'REMOVE PRESET'
		emdict = emdata['em']
		print 'TARGET BEFORE', emdict['image shift']
		newemdict = copy.deepcopy(emdict)
		newemdata = data.EMData(('scope',), em=newemdict)
		print 'REMOVING', presetdata['image shift']

		# update its values from PresetData object
		newemdict['image shift']['x'] -= presetdata['image shift']['x']
		newemdict['image shift']['y'] -= presetdata['image shift']['y']
		print 'TARGET AFTER', newemdata['em']['image shift']
		return newemdata

	def addPreset(self, emdata, presetdata):
		## applies a preset to an existing EMData object
		## the result is to overwrite values of the EMData
		## with new values from the preset.  However, image shift
		## has the special behavior that it added not overwritten,
		## because we don't want to interfere with the current
		## target.

		print 'ADD PRESET'

		# make new EMData object
		emdict = emdata['em']
		print 'TARGET BEFORE', emdict['image shift']
		newemdict = copy.deepcopy(emdict)
		newemdata = data.EMData(('scope',), em=newemdict)

		print 'ADDING', presetdata['image shift']
		# image shift is added, other parameter just overwrite
		ishift = newemdata['em']['image shift']
		ishift['x'] += presetdata['image shift']['x']
		ishift['y'] += presetdata['image shift']['y']
		## save a temp ishift because update() will overwrite it
		tempishift = copy.deepcopy(ishift)

		# overwrite values from preset into emdict
		newemdata['em'].update(presetdata)
		newemdata['em']['image shift'] = tempishift
		print 'TARGET AFTER', newemdata['em']['image shift']
		return newemdata

	def presetDataToEMData(self, presetdata):
		emdict = dict(presetdata)
		emdata = data.EMData(('scope',), em=emdict)
		return emdata

	def acquire(self, presetdata, trial=False):
		acqtype = self.acqtype.get()
		if acqtype == 'raw':
			imagedata = self.cam.acquireCameraImageData(None,0)
		elif acqtype == 'corrected':
			try:
				imagedata = self.cam.acquireCameraImageData(None,1)
			except:
				print 'image not acquired'
				imagedata = None

		if imagedata is None:
			return

		## attach preset to imagedata and create PresetImageData
		## use same id as original imagedata
		dataid = imagedata['id']

		if trial:
			trialimage = data.TrialImageData(dataid, initializer=imagedata, preset=presetdata)
			print 'publishing trial image'
			self.publish(trialimage, eventclass=event.TrialImagePublishEvent, database=False)
		else:
			pimagedata = data.AcquisitionImageData(dataid, initializer=imagedata, preset=presetdata)
#			print 'publishing image'
			self.publish(pimagedata, eventclass=event.AcquisitionImagePublishEvent, database=True)
			print 'PIMAGEDATA'
			print '   scope image shift', pimagedata['scope']['image shift']
			print '   preset image shift', pimagedata['preset']['image shift']
		print 'image published'


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
		emdat = data.EMData(('scope',), em=newstate)
		self.publishRemote(emdat)

		# wait for a while
		time.sleep(2)

		## acquire image
		#self.acquireTargetAtPreset(self.testpresetname, trial=True)
		self.acquire(presetdata=None, trial=True)

	def uiToScope(self):
		try:
			presetname = self.presetarg.get()['selected'][0]
		except (KeyError, IndexError):
			self.printerror('cannot determine preset name')
		print 'Going to preset %s' % (presetname,)
		presetlist = self.presetsclient.retrievePresets(presetname)
		presetdata = presetlist[0]
		self.presetsclient.toScope(presetdata)
		self.presetarg.set({'list': self.presetsNames(), 'selected': []})
		return ''

	def uiToScopeAcquire(self):
		try:
			presetname = self.presetarg.get()['selected'][0]
		except (KeyError, IndexError):
			self.printerror('cannot determine preset name')
		## remember this preset name for when a click event comes back
		self.testpresetname = presetname

		## acquire a trial image
		self.acquireTargetAtPreset(presetname, trial=True)
		self.presetarg.set({'list': self.presetsNames(), 'selected': []})
		return ''

	def uiFromScope(self):
		presetname = self.fromscopename.get()
		presetdata = self.presetsclient.fromScope(presetname)
		self.presetsclient.storePreset(presetdata)
		self.presetarg.set({'list': self.presetsNames(), 'selected': []})
		return ''

	def uiTrial(self):
		self.processTargetData(targetdata=None)
		return ''

	def presetsNames(self):
		presetsdata = self.presetsclient.retrievePresets()
		presetsnames = []
		for data in presetsdata:
			presetsnames.append(data['name'])
		return presetsnames

	def defineUserInterface(self):
		super = targetwatcher.TargetWatcher.defineUserInterface(self)

		movetypes = self.calclients.keys()
		temparam = self.registerUIData('temparam', 'array', default=movetypes)
		self.movetype = self.registerUIData('TEM Parameter', 'string', choices=temparam, permissions='rw', default='image shift')

		self.delaydata = self.registerUIData('Delay (sec)', 'float', default=2.5, permissions='rw')

		acqtypes = self.registerUIData('acqtypes', 'array', default=('raw', 'corrected'))
		self.acqtype = self.registerUIData('Acquisition Type', 'string', default='corrected', permissions='rw', choices=acqtypes)


		prefs = self.registerUIContainer('Preferences', (self.movetype, self.delaydata, self.acqtype))

		self.presetnames = self.registerUIData('Acquisition Presets', 'array', default=['spread1100'], permissions='rw')
		self.fromscopename = self.registerUIData('Preset Name', 'string', permissions='rw')
		fromscope = self.registerUIMethod(self.uiFromScope, 'Create Preset', ())
		self.presetarg = self.registerUIData('Preset', 'struct', default = {'list': self.presetsNames(), 'selected': []}, permissions='rw', subtype='selected list')
		toscope = self.registerUIMethod(self.uiToScope, 'Apply Preset', ())
		toscopeacq = self.registerUIMethod(self.uiToScopeAcquire, 'To Scope And Acquire', ())
		pre = self.registerUIContainer('Presets', (self.presetnames, self.fromscopename, fromscope, self.presetarg, toscope, toscopeacq))

		trial = self.registerUIMethod(self.uiTrial, 'Trial', ())

		myspec = self.registerUISpec('Acquisition', (prefs, pre, trial))
		myspec += super
		return myspec

