'''
Acquisition node is a TargetWatcher, so it receives either an ImageTargetData
or an ImageTargetListData.  The method processTargetData is called on each
ImageTargetData.

The sequence of events leading from an ImageTargetData to an acquired image
of the target is as follows:


processTargetData():
  Takes an ImageTargetData instance and centers that target using the
  methods below.  Calls acquire() for each preset specified for this node.  


cleanTarget():
   takes an instance of ImageTargetData and produces a preset independent
   microscope state.  It does this by calling the next two methods...

targetToState(targetdata):
   Taking the necessary information from the ImageTargetData and
   also the user specified method of getting to the target 
   (stage, image shift, etc.), this function produces a valid 
   miscroscope state capable of centering the target on the camera.
   This only works if we are at the preset from which the target was 
   selected.

stripTarget

targetstate (original preset)



targetstate (no preset)
targetstate (new preset)
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
		targetwatcher.TargetWatcher.__init__(self, id, session,
																					nodelocations, **kwargs)
		self.cam = camerafuncs.CameraFuncs(self)

		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.presetsclient = presets.PresetsClient(self)

		self.defineUserInterface()
		self.start()

	def processTargetData(self, targetdata=None):
		'''
		This is called by TargetWatcher.processData when targets available
		If called with targetdata=None, this simulates what occurs at
		a target (going to preset, acquiring image, etc.)
		'''
		### should make both target data and preset an option

		print 'PROCESSING', targetdata

		if targetdata is not None:
			oldtargetemdata = self.targetToEMData(targetdata)

			oldpreset = targetdata['preset']

			newtargetemdata = self.removePreset(oldtargetemdata, oldpreset)
		else:
			newtargetemdata = None
		
		### do each preset for this acquisition
		presetnames = self.presetnames.get()

		if not presetnames:
			print 'NO PRESETS SPECIFIED'
		## maybe could acquire anyway at target with no preset?
		## default preset?  would have to rely on presetsmanager

		for presetname in presetnames:
			presetlist = self.presetsclient.retrievePresets(presetname)
			presetdata = presetlist[0]
			### simulated target is easy, real target requires
			### merge with preset
			if newtargetemdata is None:
				ptargetemdata = self.presetDataToEMData(presetdata)
			else:
				## make newtargetemdata with preset applied
				ptargetemdata = self.addPreset(newtargetemdata, presetdata)
			print 'PRESET NEWTARGET',
			print ptargetemdata

			## set the scope/camera state
			self.publishRemote(ptargetemdata)

			print 'sleeping 2 sec'
			time.sleep(2)

			print 'acquire'
			self.acquire(presetdata)

	def targetToEMData(self, targetdata, movetype):
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
		newscope = calclient.transform(pixelshift, targetscope, targetcamera)

		## create new EMData object to hole this
		emdata = data.EMData(('scope',), em=newscope)
		return emdata

	def removePreset(self, emdata, presetdata):
		# subtract the effects of a preset on an EMData object
		# Right now all this means is subtract image shift
		# It is assumed that other parameters of the preset
		# like magnification will be updated later.

		# make new EMData object
		emdict = emdata['em']
		newemdict = copy.deepcopy(emdict)
		newemdata = data.EMData(('scope',), em=newemdict)

		# update its values from PresetData object
		newemdict['image shift']['x'] -= presetdata['image shift']['x']
		newemdict['image shift']['y'] -= presetdata['image shift']['y']
		print 'TARGETSTATE', targetstate
		return newemdata

	def addPreset(self, emdata, presetdata):
		## applies a preset to an existing EMData object
		## the result is to overwrite values of the EMData
		## with new values from the preset.  However, image shift
		## has the special behavior that it added not overwritten,
		## because we don't want to interfere with the current
		## target.

		# make new EMData object
		emdict = emdata['em']
		newemdict = copy.deepcopy(emdict)
		newemdata = data.EMData(('scope',), em=newemdict)

		# image shift is added, other parameter just overwrite
		newimageshift = copy.deepcopy(newemdict['image shift'])
		newimageshift['x'] += presetdata['image shift']['x']
		newimageshift['y'] += presetdata['image shift']['y']

		# overwrite values from preset into emdict
		newemdict.update(presetdata)
		newemdict['image shift'] = newimageshift

		return newemdata

	def presetDataToEMData(self, presetdata):
		emdict = dict(presetdata)
		emdata = data.EMData(('scope',), em=emdict)
		return emdata

	def acquire(self, presetdata):
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
		pimagedata = data.PresetImageData(dataid, initializer=imagedata, preset=presetdata)

		print 'publishing image'
		self.publish(pimagedata, eventclass=event.PresetImagePublishEvent, database=True)
		print 'image published'

	def uiToScope(self, presetname):
		print 'Going to preset %s' % (presetname,)
		pre = self.presetsclient.getPreset(presetname)
		self.presetsclient.toScope(pre)
		return ''

	def uiFromScope(self, presetname):
		print 'Storing preset %s' % (presetname,)
		pre = self.presetsclient.fromScope()
		self.presetsclient.setPreset(presetname, pre)
		return ''

	def uiTrial(self):
		## calling this witout targetdata means test just the preset
		## and acquire
		self.processTargetData(targetdata=None)
		return ''

	def defineUserInterface(self):
		super = targetwatcher.TargetWatcher.defineUserInterface(self)

		movetypes = self.calclients.keys()
		temparam = self.registerUIData('temparam', 'array', default=movetypes)
		self.movetype = self.registerUIData('TEM Parameter', 'string', choices=temparam, permissions='rw', default='stage position')

		self.delaydata = self.registerUIData('Delay (sec)', 'float', default=2.5, permissions='rw')

		acqtypes = self.registerUIData('acqtypes', 'array', default=('raw', 'corrected'))
		self.acqtype = self.registerUIData('Acquisition Type', 'string', default='raw', permissions='rw', choices=acqtypes)


		prefs = self.registerUIContainer('Preferences', (self.movetype, self.delaydata, self.acqtype))

		self.presetnames = self.registerUIData('Preset Names', 'array', default=(), permissions='rw')
		presetarg = self.registerUIData('Preset', 'string', choices=self.presetnames)
		toscope = self.registerUIMethod(self.uiToScope, 'To Scope', (presetarg,))
		fromscope = self.registerUIMethod(self.uiFromScope, 'From Scope', (presetarg,))
		pre = self.registerUIContainer('Presets', (self.presetnames, toscope, fromscope))

		trial = self.registerUIMethod(self.uiTrial, 'Trial', ())

		myspec = self.registerUISpec('Acquisition', (prefs, pre, trial))
		myspec += super
		return myspec

