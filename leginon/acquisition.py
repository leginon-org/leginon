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
	def __init__(self, id, session, nodelocations, targetclass=data.ImageTargetData, **kwargs):
		targetwatcher.TargetWatcher.__init__(self, id, session, nodelocations, targetclass, **kwargs)
		self.addEventInput(event.ImageClickEvent, self.handleImageClick)
		self.addEventInput(event.TargetDoneEvent, self.handleTargetDone)
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
		## wait for focus targets to complete
		for tid,tevent in self.targetevents.items():
			print 'waiting for target %s to complete' % (tid,)
			tevent.wait()

		if targetdata is None:
			newtargetemdata = None
		else:
			print 'TARGETDATA'
			print '   row,col', targetdata['delta row'], targetdata['delta column']
			print '   scope image shift', targetdata['scope']['image shift']
			if targetdata['preset'] is not None:
				print '   preset image shift', targetdata['preset']['image shift']
			else:
				print '   preset image shift, no preset in target'

			oldtargetemdata = self.targetToEMData(targetdata)
			oldpreset = targetdata['preset']

			if oldpreset is None:
				# I don't know if this works, but if there is no preset, don't remove
				newtargetemdata = oldtargetemdata
			else:
				print 'OLDPRESET'
				print '   magnification', oldpreset['magnification']
				print '   image shift', oldpreset['image shift']
				newtargetemdata = self.removePreset(oldtargetemdata, oldpreset)

		if newtargetemdata is not None:
			print 'type', type(newtargetemdata)
			print 'NEWTARGETEMDATA'
			print '   magnification', newtargetemdata['magnification']
			print '   image shift', newtargetemdata['image shift']

		### do each preset for this acquisition
		try:
			presetnames = eval(self.uipresetnames.get())
		except:
			print 'NO PRESETS SPECIFIED'
			return
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
				print '   magnification', ptargetemdata['magnification']
				print '   image shift', ptargetemdata['image shift']

			## set the scope/camera state
			self.outputEvent(event.LockEvent(self.ID()))
			self.publishRemote(ptargetemdata)

			print 'sleeping 2 sec'
			time.sleep(2)

#			print 'acquire'
			self.acquire(presetdata, trial)
			self.outputEvent(event.UnlockEvent(self.ID()))

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
		movetype = self.uimovetype.getSelectedValue()[0]
		calclient = self.calclients[movetype]
		print 'ORIGINAL', targetscope['image shift']
		newscope = calclient.transform(pixelshift, targetscope, targetcamera)
		print 'WITH TARGET', newscope['image shift']
		## create new EMData object to hole this
		emdata = data.ScopeEMData(('scope',), initializer=newscope)
		return emdata

	def removePreset(self, emdata, presetdata):
		# subtract the effects of a preset on an EMData object
		# Right now all this means is subtract image shift
		# It is assumed that other parameters of the preset
		# like magnification will be updated later.

		# make new EMData object
		newemdata = data.ScopeEMData(('scope',))
		newemdata.update(emdata)

		print 'REMOVING', presetdata['image shift']

		# update its values from PresetData object
		newemdata['image shift']['x'] -= presetdata['image shift']['x']
		newemdata['image shift']['y'] -= presetdata['image shift']['y']
		print 'TARGET AFTER', newemdata['image shift']
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
		newemdata = data.ScopeEMData(('scope',))
		newemdata.update(emdata)
		print 'TARGET BEFORE', newemdata['image shift']

		print 'ADDING', presetdata['image shift']
		# image shift is added, other parameter just overwrite
		ishift = newemdata['image shift']
		ishift['x'] += presetdata['image shift']['x']
		ishift['y'] += presetdata['image shift']['y']
		## save a temp ishift because update() will overwrite it
		tempishift = copy.deepcopy(ishift)

		# overwrite values from preset into emdict
		newemdata.update(presetdata)
		newemdata['image shift'] = tempishift
		print 'TARGET AFTER', newemdata['image shift']
		return newemdata

	def presetDataToEMData(self, presetdata):
		#emdict = dict(presetdata)
		emdata = data.ScopeEMData(('scope',))
		emdata.update(presetdata)
		return emdata

	def acquire(self, presetdata, trial=False):
		acqtype = self.uiacquiretype.getSelectedValue()[0]
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
			self.publish(trialimage, pubevent=True, database=False)
		else:
			pimagedata = data.AcquisitionImageData(dataid, initializer=imagedata, preset=presetdata)
#			print 'publishing image'
			self.publish(pimagedata, pubevent=True, database=True)
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
		emdat = data.ScopeEMData(('scope',), initializer=newstate)
		self.outputEvent(event.LockEvent(self.ID()))
		self.publishRemote(emdat)

		# wait for a while
		time.sleep(2)

		## acquire image
		#self.acquireTargetAtPreset(self.testpresetname, trial=True)
		self.acquire(presetdata=None, trial=True)
		self.outputEvent(event.UnlockEvent(self.ID()))

	def uiToScope(self):
		try:
			presetname = self.uiselectpreset.getSelectedValue()[0]
		except IndexError:
			self.printerror('cannot determine preset name')
			return
		print 'Going to preset %s' % (presetname,)
		presetlist = self.presetsclient.retrievePresets(presetname)
		presetdata = presetlist[0]
		self.presetsclient.toScope(presetdata)
		presetsnames = self.presetsNames()
		if presetsnames:
			selected = [0]
		else:
			selected = []
		self.uiselectpreset.set(presetsnames, selected)

	def uiToScopeAcquire(self):
		try:
			presetname = self.uiselectpreset.getSelectedValue()[0]
			print 'PRESETNAME', presetname
		except IndexError:
			self.printerror('cannot determine preset name')
			return
		else:
			## remember this preset name for when a click event comes back
			self.testpresetname = presetname

		## acquire a trial image
		self.acquireTargetAtPreset(presetname, trial=True)
		presetsnames = self.presetsNames()
		if presetsnames:
			selected = [0]
		else:
			selected = []
		self.uiselectpreset.set(presetsnames, selected)

	def uiFromScope(self):
		presetname = self.uifromscopename.get()
		presetdata = self.presetsclient.fromScope(presetname)
		self.presetsclient.storePreset(presetdata)
		presetsnames = self.presetsNames()
		if presetsnames:
			selected = [0]
		else:
			selected = []
		self.uiselectpreset.set(presetsnames, selected)

	def uiTrial(self):
		self.processTargetData(targetdata=None)

	def presetsNames(self):
		presetsdata = self.presetsclient.retrievePresets()
		presetsnames = []
		for data in presetsdata:
			if data['name'] not in presetsnames:
				presetsnames.append(data['name'])
		presetsnames.sort()
		return presetsnames

	def defineUserInterface(self):
		targetwatcher.TargetWatcher.defineUserInterface(self)
		self.uimovetype = uidata.UISelectFromList('Move Type',
																							self.calclients.keys(), [0], 'r')
		self.uidelay = uidata.UIFloat('Delay (sec)', 2.5, 'rw')
		self.uiacquiretype = uidata.UISelectFromList('Acquisition Type',
																							['raw', 'corrected'], [0], 'r')
		settingscontainer = uidata.UIContainer('Settings')
		settingscontainer.addUIObjects((self.uimovetype, self.uidelay,
																		self.uiacquiretype))

		self.uipresetsnames = uidata.UIString('Presets', '[\'spread1100\']', 'rw')
		self.uifromscopename = uidata.UIString('Preset Name', '', 'rw')
		fromscopemethod = uidata.UIMethod('Create Preset', self.uiFromScope)
		presetsnames = self.presetsNames()
		if presetsnames:
			selected = [0]
		else:
			selected = []
		self.uiselectpreset = uidata.UISelectFromList('Select Preset',
																									presetsnames, selected, 'r')
		toscopemethod = uidata.UIMethod('Apply Preset', self.uiToScope)
		toscopeandacquiremethod = uidata.UIMethod('Apply Preset and Acquire',
																							self.uiToScopeAcquire)
		presetscontainer = uidata.UIContainer('Presets')
		presetscontainer.addUIObjects((self.uipresetsnames, self.uifromscopename,
																		fromscopemethod, self.uiselectpreset,
																		toscopemethod, toscopeandacquiremethod))
		trialmethod = uidata.UIMethod('Trial', self.uiTrial)

		container = uidata.UIMediumContainer('Acquisition')
		container.addUIObjects((settingscontainer, presetscontainer, trialmethod))

		self.uiserver.addUIObject(container)

