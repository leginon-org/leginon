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
			emtarget = None
		else:
			#### for debugging
			print 'TARGETDATA'
			print '   row,col', targetdata['delta row'], targetdata['delta column']
			print '   scope image shift', targetdata['scope']['image shift']
			if targetdata['preset'] is not None:
				print '   preset image shift', targetdata['preset']['image shift']
			else:
				print '   preset image shift, no preset in target'

			#### this creates ScopeEMData from the ImageTargetData
			oldtargetemdata = self.targetToEMData(targetdata)
			oldpreset = targetdata['preset']
			#### now make EMTargetData to hold all this
			emtarget = data.EMTargetData(scope=oldtargetemdata,preset=oldpreset)

		### do each preset for this acquisition
		try:
			presetnames = eval(self.uipresetnames.get())
		except:
			self.printException()
			return

		if not presetnames:
			print 'NO PRESETS SPECIFIED'

		for newpresetname in presetnames:
			self.presetsclient.toScope(newpresetname, emtarget)
			print 'getting current preset'
			p = self.getCurrentPreset()
			print 'current preset'
			print p
			print 'acquire()'
			self.acquire(p)
			print 'done'

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

	def acquire(self, presetdata, trial=False):
		acqtype = self.uiacquiretype.getSelectedValue()[0]

		### corrected or not??
		imagedata = self.cam.acquireCameraImageData(None,0)

		if imagedata is None:
			return

		imarray = imagedata['image']

		## attach preset to imagedata and create PresetImageData
		## use same id as original imagedata
		dataid = self.ID()

		if trial:
			trialimage = data.TrialImageData(id=dataid, initializer=imagedata, preset=presetdata)
			print 'publishing trial image'
			self.publish(trialimage, pubevent=True, database=False)
		else:
			pimagedata = data.AcquisitionImageData(id=dataid, initializer=imagedata, preset=presetdata)
			self.publish(pimagedata, pubevent=True, database=True)
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
		self.acquire(presetdata=None, trial=True)
		self.outputEvent(event.UnlockEvent(self.ID()))
		self.confirmEvent(clickevent)

	def uiToScope(self):
		try:
			presetname = self.uiselectpreset.getSelectedValue()[0]
		except IndexError:
			self.printerror('cannot determine preset name')
			return
		print 'Going to preset %s' % (presetname,)
		self.presetsclient.toScope(presetname)
		print 'done'

		### why is this here?
		#presetnames = self.presetsclient.presetNames()
		#if presetnames:
		#	selected = [0]
		#else:
		#	selected = []
		#self.uiselectpreset.set(presetnames, selected)

	def uiToScopeAcquire(self):
		try:
			presetname = self.uiselectpreset.getSelectedValue()[0]
			print 'PRESETNAME', presetname
		except IndexError:
			self.printerror('cannot determine preset name')
			return

		## acquire a trial image
		self.presetsclient.toScope(presetname)
		p = self.presetsclient.getCurrentPreset()
		## trial image
		self.acquire(p, trial=True)

		### why is this here?
		#presetsnames = self.presetsclient.presetNames()
		#if presetsnames:
		#	selected = [0]
		#else:
		#	selected = []
		#self.uiselectpreset.set(presetsnames, selected)

	def uiFromScope(self):
		raise NotImplementedError('this is not up to date with new presetsclient')
		presetname = self.uifromscopename.get()
		presetdata = self.presetsclient.fromScope(presetname)
		self.presetsclient.storePreset(presetdata)
		presetsnames = self.presetsclient.presetNames()
		if presetsnames:
			selected = [0]
		else:
			selected = []
		self.uiselectpreset.set(presetsnames, selected)

	def uiTrial(self):
		self.processTargetData(targetdata=None)

	def uiGetPresetNames(self):
		presetlist = self.presetsclient.getPresets()
		pnames = [p['name'] for p in presetlist]
		if pnames:
			sel = [0]
		else:
			sel = []
		self.uiselectpreset.set(pnames, sel) 

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

		getpresets = uidata.UIMethod('Get Names', self.uiGetPresetNames)
		self.uiselectpreset = uidata.UISelectFromList('Select Preset', [], [], 'r')
		toscopemethod = uidata.UIMethod('Apply Preset', self.uiToScope)
		toscopeandacquiremethod = uidata.UIMethod('Apply Preset and Acquire', self.uiToScopeAcquire)
		presetscontainer = uidata.UIContainer('Presets')
		presetscontainer.addUIObjects((self.uipresetsnames, self.uifromscopename, fromscopemethod, getpresets, self.uiselectpreset,
																		toscopemethod, toscopeandacquiremethod))
		trialmethod = uidata.UIMethod('Trial', self.uiTrial)

		self.ui_image = uidata.UIImage('Image', None, 'rw')


		container = uidata.UIMediumContainer('Acquisition')
		container.addUIObjects((settingscontainer, presetscontainer, trialmethod, self.ui_image))

		self.uiserver.addUIObject(container)

